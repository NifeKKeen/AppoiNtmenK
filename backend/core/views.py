from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any
from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_date
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .google_calendar import (
    GoogleCalendarError,
    build_google_auth_url,
    create_google_calendar_event,
    exchange_code_for_tokens,
    is_google_oauth_configured,
    store_tokens_on_specialist,
)
from .models import Appointment, ChatMessage, SpecialistDetails
from .serializers import (
    AppointmentSerializer,
    ChatMessageSerializer,
    RegisterSerializer,
    SpecialistAvailabilitySerializer,
    SpecialistRequestSerializer,
    SpecialistSerializer,
    UpgradeToSpecialistSerializer,
    UserProfileSerializer,
    WEEKDAY_KEYS,
    build_default_weekly_availability,
)

User = get_user_model()

BOOKED_STATUSES = ('pending', 'accepted', 'confirmed')


def _weekday_key(value: date) -> str:
    return WEEKDAY_KEYS[value.weekday()]


def _specialist_day_slots(specialist: SpecialistDetails, day: date) -> list[str]:
    weekly = specialist.weekly_availability or {}
    key = _weekday_key(day)

    if key in weekly:
        return list(weekly.get(key) or [])

    if specialist.time_slots:
        return list(specialist.time_slots)

    return list(build_default_weekly_availability().get(key, []))


def _booked_slots_for_day(specialist: SpecialistDetails, day: date) -> list[str]:
    booked = (
        Appointment.objects
        .filter(specialist=specialist, date=day, status__in=BOOKED_STATUSES)
        .values_list('time_slot', flat=True)
    )
    return sorted(set(booked))


def _apply_time_window(slots: list[str], time_from: str | None, time_to: str | None) -> list[str]:
    filtered = list(slots)
    if time_from:
        filtered = [slot for slot in filtered if slot >= time_from]
    if time_to:
        filtered = [slot for slot in filtered if slot <= time_to]
    return filtered


class IsSpecialistPermission(BasePermission):
    message = 'Specialist account required.'

    def has_permission(self, request: Any, view: Any) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_specialist
            and hasattr(user, 'specialist_profile')
        )


class RegisterView(generics.CreateAPIView):
    """Public endpoint for user registration."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveAPIView):
    """Authenticated endpoint for current user profile and role flags."""

    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> Any:
        return self.request.user


class UpgradeToSpecialistView(generics.GenericAPIView):
    """Upgrade a logged-in user account to specialist and create profile data."""

    serializer_class = UpgradeToSpecialistSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)


class SpecialistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only endpoint for specialist profiles.
    - GET /api/specialists/         list all active specialists
    - GET /api/specialists/<slug>/  retrieve one specialist by slug
    """

    serializer_class = SpecialistSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'

    def get_queryset(self) -> Any:
        return SpecialistDetails.objects.filter(is_active=True)


class SpecialistDailyAvailabilityView(APIView):
    """
    Show free and booked slots for one specialist on a specific date.
    - GET /api/specialists/<slug>/availability/?date=YYYY-MM-DD
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Any, slug: str) -> Response:
        specialist = get_object_or_404(SpecialistDetails.objects.filter(is_active=True), slug=slug)

        raw_date = request.query_params.get('date')
        target_date = parse_date(raw_date) if raw_date else date.today()
        if target_date is None:
            return Response(
                {'detail': 'Invalid date. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        all_slots = sorted(set(_specialist_day_slots(specialist, target_date)))
        booked_slots = _booked_slots_for_day(specialist, target_date)
        available_slots = [slot for slot in all_slots if slot not in booked_slots]

        return Response(
            {
                'date': target_date.isoformat(),
                'specialist': {
                    'id': specialist.id,
                    'slug': specialist.slug,
                    'name': specialist.name,
                    'icon': specialist.icon,
                    'role': specialist.role,
                },
                'all_slots': all_slots,
                'booked_slots': booked_slots,
                'available_slots': available_slots,
            },
            status=status.HTTP_200_OK,
        )


class AvailabilityCalendarView(APIView):
    """
    Global availability calendar with filters.
    - GET /api/calendar/availability/?start_date=YYYY-MM-DD&days=7&specialist_slug=<slug>&time_from=09:00&time_to=18:00
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Any) -> Response:
        raw_start = request.query_params.get('start_date')
        start_date = parse_date(raw_start) if raw_start else date.today()
        if start_date is None:
            return Response({'detail': 'Invalid start_date. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        raw_days = request.query_params.get('days', '7')
        try:
            days = max(1, min(int(raw_days), 31))
        except ValueError:
            return Response({'detail': 'days must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        specialist_slug = request.query_params.get('specialist_slug', '').strip()
        time_from = (request.query_params.get('time_from') or '').strip() or None
        time_to = (request.query_params.get('time_to') or '').strip() or None

        specialists_qs = SpecialistDetails.objects.filter(is_active=True)
        if specialist_slug:
            specialists_qs = specialists_qs.filter(slug=specialist_slug)

        specialists = list(specialists_qs)
        rows: list[dict[str, Any]] = []

        for day_offset in range(days):
            current_day = start_date + timedelta(days=day_offset)

            for specialist in specialists:
                all_slots = sorted(set(_specialist_day_slots(specialist, current_day)))
                booked_slots = _booked_slots_for_day(specialist, current_day)
                available_slots = [slot for slot in all_slots if slot not in booked_slots]
                available_slots = _apply_time_window(available_slots, time_from, time_to)

                rows.append(
                    {
                        'date': current_day.isoformat(),
                        'weekday': _weekday_key(current_day),
                        'specialist': {
                            'id': specialist.id,
                            'slug': specialist.slug,
                            'name': specialist.name,
                            'icon': specialist.icon,
                            'role': specialist.role,
                        },
                        'available_slots': available_slots,
                        'available_count': len(available_slots),
                    }
                )

        return Response(
            {
                'filters': {
                    'start_date': start_date.isoformat(),
                    'days': days,
                    'specialist_slug': specialist_slug or None,
                    'time_from': time_from,
                    'time_to': time_to,
                },
                'rows': rows,
            },
            status=status.HTTP_200_OK,
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Authenticated endpoint for managing a student's appointments.
    """

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)


class SpecialistAvailabilityView(APIView):
    """
    Specialist weekly availability manager.
    - GET  /api/specialist/availability/
    - POST /api/specialist/availability/
    """

    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    @staticmethod
    def _default_weekly_availability(specialist: SpecialistDetails) -> dict[str, list[str]]:
        weekly = specialist.weekly_availability or {}
        defaults = {day: [] for day in WEEKDAY_KEYS}
        if not weekly and specialist.time_slots:
            return {day: list(specialist.time_slots) for day in WEEKDAY_KEYS}

        for day in WEEKDAY_KEYS:
            defaults[day] = list(weekly.get(day, []))
        return defaults

    def get(self, request: Any) -> Response:
        specialist = request.user.specialist_profile
        return Response(
            {
                'weekly_availability': self._default_weekly_availability(specialist),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request: Any) -> Response:
        serializer = SpecialistAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        specialist = request.user.specialist_profile
        weekly = serializer.validated_data['weekly_availability']

        specialist.weekly_availability = weekly
        specialist.time_slots = weekly.get('mon', [])
        specialist.save(update_fields=['weekly_availability', 'time_slots'])

        return Response({'weekly_availability': weekly}, status=status.HTTP_200_OK)


class SpecialistRequestListView(APIView):
    """
    Incoming SOS requests for specialists.
    - GET /api/specialist/requests/
    """

    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def get(self, request: Any) -> Response:
        specialist = request.user.specialist_profile
        queryset = Appointment.objects.filter(specialist=specialist).order_by('-created_at')
        data = SpecialistRequestSerializer(queryset, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class SpecialistAcceptRequestView(APIView):
    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def post(self, request: Any, appointment_id: int) -> Response:
        specialist = request.user.specialist_profile
        appointment = get_object_or_404(Appointment, id=appointment_id, specialist=specialist)

        if appointment.status == 'rejected':
            return Response(
                {'detail': 'Rejected request cannot be accepted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = 'accepted'
        appointment.save(update_fields=['status'])

        calendar_synced = False
        calendar_error = ''

        if specialist.google_calendar_connected:
            try:
                start_dt = datetime.combine(
                    appointment.date,
                    datetime.strptime(appointment.time_slot, '%H:%M').time(),
                )
                start_dt = start_dt.replace(tzinfo=ZoneInfo(settings.TIME_ZONE))
                end_dt = start_dt + timedelta(minutes=30)

                event_payload = {
                    'summary': f'SOS Session: {appointment.user.username}',
                    'description': appointment.description,
                    'start': {
                        'dateTime': start_dt.isoformat(),
                        'timeZone': settings.TIME_ZONE,
                    },
                    'end': {
                        'dateTime': end_dt.isoformat(),
                        'timeZone': settings.TIME_ZONE,
                    },
                }
                create_google_calendar_event(specialist, event_payload)
                calendar_synced = True
            except GoogleCalendarError as exc:
                calendar_error = str(exc)

        return Response(
            {
                'appointment': SpecialistRequestSerializer(appointment).data,
                'google_calendar_synced': calendar_synced,
                'google_calendar_error': calendar_error or None,
            },
            status=status.HTTP_200_OK,
        )


class SpecialistRejectRequestView(APIView):
    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def post(self, request: Any, appointment_id: int) -> Response:
        specialist = request.user.specialist_profile
        appointment = get_object_or_404(Appointment, id=appointment_id, specialist=specialist)

        if appointment.status == 'accepted':
            return Response(
                {'detail': 'Accepted request cannot be rejected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = 'rejected'
        appointment.save(update_fields=['status'])
        return Response(SpecialistRequestSerializer(appointment).data, status=status.HTTP_200_OK)


class SpecialistGoogleConnectView(APIView):
    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def get(self, request: Any) -> Response:
        if not is_google_oauth_configured():
            return Response(
                {'detail': 'Google OAuth is not configured on the server.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        state = signing.dumps({'user_id': request.user.id}, salt='specialist-google-state')
        auth_url = build_google_auth_url(state)
        return Response({'auth_url': auth_url}, status=status.HTTP_200_OK)


class SpecialistGoogleStatusView(APIView):
    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def get(self, request: Any) -> Response:
        specialist = request.user.specialist_profile
        missing_vars = []
        if not settings.GOOGLE_CLIENT_ID:
            missing_vars.append('GOOGLE_CLIENT_ID')
        if not settings.GOOGLE_CLIENT_SECRET:
            missing_vars.append('GOOGLE_CLIENT_SECRET')
        if not settings.GOOGLE_OAUTH_REDIRECT_URI:
            missing_vars.append('GOOGLE_OAUTH_REDIRECT_URI')

        return Response(
            {
                'connected': specialist.google_calendar_connected,
                'configured': is_google_oauth_configured(),
                'missing_vars': missing_vars,
                'oauth_redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
            },
            status=status.HTTP_200_OK,
        )


class SpecialistGoogleDisconnectView(APIView):
    permission_classes = [IsAuthenticated, IsSpecialistPermission]

    def post(self, request: Any) -> Response:
        specialist = request.user.specialist_profile
        specialist.google_calendar_connected = False
        specialist.google_access_token = ''
        specialist.google_refresh_token = ''
        specialist.google_token_expiry = None
        specialist.save(
            update_fields=[
                'google_calendar_connected',
                'google_access_token',
                'google_refresh_token',
                'google_token_expiry',
            ]
        )
        return Response({'connected': False}, status=status.HTTP_200_OK)


class SpecialistGoogleCallbackView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request: Any) -> Any:
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        error = request.query_params.get('error')
        code = request.query_params.get('code')
        state = request.query_params.get('state')

        if error:
            return redirect(f'{frontend_url}/specialist/dashboard?google=error&reason={quote_plus(error)}')

        if not code or not state:
            return redirect(f'{frontend_url}/specialist/dashboard?google=error&reason=missing_code')

        try:
            payload = signing.loads(state, salt='specialist-google-state', max_age=900)
        except (BadSignature, SignatureExpired):
            return redirect(f'{frontend_url}/specialist/dashboard?google=error&reason=invalid_state')

        user = get_object_or_404(User, id=payload.get('user_id'))
        specialist = getattr(user, 'specialist_profile', None)
        if specialist is None:
            return redirect(f'{frontend_url}/specialist/dashboard?google=error&reason=no_specialist_profile')

        try:
            token_data = exchange_code_for_tokens(code)
            store_tokens_on_specialist(specialist, token_data)
            return redirect(f'{frontend_url}/specialist/dashboard?google=connected')
        except GoogleCalendarError as exc:
            return redirect(
                f'{frontend_url}/specialist/dashboard?google=error&reason={quote_plus(str(exc))}'
            )


class ChatMessageListCreateView(generics.ListCreateAPIView):
   

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def _get_appointment(self) -> Appointment:
        appointment = get_object_or_404(Appointment, id=self.kwargs['appointment_id'])
        user = self.request.user
        is_owner = appointment.user_id == user.id
        is_specialist = (
            appointment.specialist.user_id is not None
            and appointment.specialist.user_id == user.id
        )
        if not (is_owner or is_specialist):
            raise PermissionDenied('You are not a participant of this appointment.')
        return appointment

    def get_queryset(self):
        appointment = self._get_appointment()
        qs = ChatMessage.objects.filter(appointment=appointment)
        after = self.request.query_params.get('after')
        if after:
            try:
                qs = qs.filter(id__gt=int(after))
            except (ValueError, TypeError):
                pass
        return qs

    def perform_create(self, serializer):
        appointment = self._get_appointment()
        serializer.save(sender=self.request.user, appointment=appointment)

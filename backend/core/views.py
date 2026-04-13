from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from typing import Any

from .models import Specialist, Appointment
from .serializers import (
    RegisterSerializer,
    SpecialistSerializer,
    AppointmentSerializer,
    UserProfileSerializer,
    UpgradeToSpecialistSerializer,
)

User = get_user_model()


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
    - GET /api/specialists/       → list all active specialists
    - GET /api/specialists/<slug>/ → retrieve a single specialist by slug
    """
    serializer_class = SpecialistSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'

    def get_queryset(self) -> Any:
        return Specialist.objects.filter(is_active=True)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Authenticated endpoint for managing appointments.
    - GET  /api/appointments/      → list current user's appointments
    - POST /api/appointments/      → create a new appointment
    - DELETE /api/appointments/<id>/ → cancel an appointment
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> Any:
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer: Any) -> None:
        serializer.save(user=self.request.user)

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import re
from typing import Dict, Any

from .models import Specialist, Appointment

User = get_user_model()

SPECIALIST_ROLE_OPTIONS = (
    'Math Whisperer',
    'Tourist-Consultant',
    'Code Debugger',
)

DEFAULT_SPECIALIST_COLOR = 'hsl(205, 75%, 52%)'
DEFAULT_SPECIALIST_ICON = '🧠'
DEFAULT_SPECIALIST_TIME_SLOTS = ['09:00', '09:30', '10:00', '10:30']
WEEKDAY_KEYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
TIME_SLOT_PATTERN = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')


def _build_unique_specialist_slug(base_slug: str) -> str:
    base = base_slug or 'specialist'
    candidate = base
    index = 2
    while Specialist.objects.filter(slug=candidate).exists():
        candidate = f'{base}-{index}'
        index += 1
    return candidate


def build_default_weekly_availability(slots: list[str] | None = None) -> Dict[str, list[str]]:
    base_slots = list(slots or DEFAULT_SPECIALIST_TIME_SLOTS)
    return {day: list(base_slots) for day in WEEKDAY_KEYS}


class UserSerializer(serializers.ModelSerializer):
    is_specialist = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_specialist']


class SpecialistProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = [
            'id', 'name', 'slug', 'role', 'description',
            'color', 'icon', 'avatar_url', 'time_slots',
            'weekly_availability', 'google_calendar_connected', 'is_active'
        ]


class SpecialistAvailabilitySerializer(serializers.Serializer):
    weekly_availability = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
    )

    def validate_weekly_availability(self, value: Dict[str, Any]) -> Dict[str, list[str]]:
        normalized: Dict[str, list[str]] = {day: [] for day in WEEKDAY_KEYS}

        for day, slots in value.items():
            if day not in WEEKDAY_KEYS:
                raise serializers.ValidationError(f'Invalid weekday key: {day}')
            if not isinstance(slots, list):
                raise serializers.ValidationError(f'Slots for {day} must be a list.')

            clean_slots: list[str] = []
            for slot in slots:
                slot_str = str(slot).strip()
                if not TIME_SLOT_PATTERN.match(slot_str):
                    raise serializers.ValidationError(
                        f'Invalid time slot format: {slot_str}. Use HH:MM.'
                    )
                clean_slots.append(slot_str)

            normalized[day] = sorted(list(set(clean_slots)))

        return normalized


class SpecialistRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='user.username', read_only=True)
    student_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'student_name', 'student_email',
            'date', 'time_slot', 'description',
            'status', 'created_at'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    is_specialist = serializers.BooleanField(read_only=True)
    specialist_profile = SpecialistProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'is_specialist', 'specialist_profile'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    become_specialist = serializers.BooleanField(write_only=True, required=False, default=False)
    specialist_role = serializers.ChoiceField(
        choices=SPECIALIST_ROLE_OPTIONS,
        write_only=True,
        required=False,
    )
    specialist_description = serializers.CharField(write_only=True, required=False)
    specialist_icon = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=10,
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password',
            'become_specialist', 'specialist_role',
            'specialist_description', 'specialist_icon'
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        become_specialist = attrs.get('become_specialist', False)
        if not become_specialist:
            return attrs

        role = attrs.get('specialist_role')
        description = (attrs.get('specialist_description') or '').strip()

        errors: Dict[str, str] = {}
        if not role:
            errors['specialist_role'] = 'Specialist role is required.'
        if not description:
            errors['specialist_description'] = 'Specialist bio is required.'

        if errors:
            raise serializers.ValidationError(errors)

        attrs['specialist_description'] = description
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Any:
        become_specialist = validated_data.pop('become_specialist', False)
        specialist_role = validated_data.pop('specialist_role', '')
        specialist_description = validated_data.pop('specialist_description', '')
        specialist_icon = validated_data.pop('specialist_icon', '')

        # Use create_user to properly hash the password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

        if become_specialist:
            user.role = User.Role.SPECIALIST
            user.save(update_fields=['role'])
            slug = _build_unique_specialist_slug(slugify(user.username) or f'user-{user.pk}')
            Specialist.objects.create(
                user=user,
                name=user.username,
                slug=slug,
                role=specialist_role,
                description=specialist_description,
                icon=specialist_icon or DEFAULT_SPECIALIST_ICON,
                color=DEFAULT_SPECIALIST_COLOR,
                time_slots=DEFAULT_SPECIALIST_TIME_SLOTS,
                weekly_availability=build_default_weekly_availability(),
            )

        return user


class UpgradeToSpecialistSerializer(serializers.Serializer):
    specialist_role = serializers.ChoiceField(choices=SPECIALIST_ROLE_OPTIONS)
    specialist_description = serializers.CharField()
    specialist_icon = serializers.CharField(required=False, allow_blank=True, max_length=10)

    def validate_specialist_description(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError('Specialist bio is required.')
        return trimmed

    def save(self, **kwargs: Any) -> Any:
        user = self.context['request'].user
        specialist_role = self.validated_data['specialist_role']
        specialist_description = self.validated_data['specialist_description']
        specialist_icon = self.validated_data.get('specialist_icon') or DEFAULT_SPECIALIST_ICON

        profile = getattr(user, 'specialist_profile', None)
        if profile is None:
            profile = Specialist.objects.create(
                user=user,
                name=user.username,
                slug=_build_unique_specialist_slug(slugify(user.username) or f'user-{user.pk}'),
                role=specialist_role,
                description=specialist_description,
                icon=specialist_icon,
                color=DEFAULT_SPECIALIST_COLOR,
                time_slots=DEFAULT_SPECIALIST_TIME_SLOTS,
                weekly_availability=build_default_weekly_availability(),
            )
        else:
            profile.name = user.username
            profile.role = specialist_role
            profile.description = specialist_description
            profile.icon = specialist_icon
            profile.save(update_fields=['name', 'role', 'description', 'icon'])

        if user.role != User.Role.SPECIALIST:
            user.role = User.Role.SPECIALIST
            user.save(update_fields=['role'])

        return user


class SpecialistSerializer(serializers.ModelSerializer):
    """Read-only serializer for specialist profiles, including time_slots."""
    class Meta:
        model = Specialist
        fields = [
            'id', 'name', 'slug', 'role', 'description',
            'color', 'icon', 'avatar_url', 'time_slots', 'weekly_availability', 'is_active'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    specialist_name = serializers.CharField(source='specialist.name', read_only=True)
    specialist_color = serializers.CharField(source='specialist.color', read_only=True)
    specialist_icon = serializers.CharField(source='specialist.icon', read_only=True)
    specialist_slug = serializers.CharField(source='specialist.slug', read_only=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        specialist = attrs.get('specialist')
        date = attrs.get('date')
        time_slot = attrs.get('time_slot')

        if specialist is None or date is None or time_slot is None:
            return attrs

        weekly = specialist.weekly_availability or {}
        weekday_key = WEEKDAY_KEYS[date.weekday()]
        if weekday_key in weekly:
            day_slots = weekly.get(weekday_key, [])
        else:
            day_slots = specialist.time_slots or []

        if time_slot not in day_slots:
            raise serializers.ValidationError(
                {'time_slot': 'This time is not available for the selected specialist on that day.'}
            )

        return attrs

    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'specialist', 'specialist_name',
            'specialist_color', 'specialist_icon', 'specialist_slug',
            'date', 'time_slot', 'description', 'status', 'created_at'
        ]
        read_only_fields = ['user', 'status']

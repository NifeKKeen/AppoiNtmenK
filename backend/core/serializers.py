from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.text import slugify
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


def _build_unique_specialist_slug(base_slug: str) -> str:
    base = base_slug or 'specialist'
    candidate = base
    index = 2
    while Specialist.objects.filter(slug=candidate).exists():
        candidate = f'{base}-{index}'
        index += 1
    return candidate


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
            'color', 'icon', 'avatar_url', 'time_slots', 'is_active'
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
            'color', 'icon', 'avatar_url', 'time_slots', 'is_active'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    specialist_name = serializers.CharField(source='specialist.name', read_only=True)
    specialist_color = serializers.CharField(source='specialist.color', read_only=True)
    specialist_icon = serializers.CharField(source='specialist.icon', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'specialist', 'specialist_name',
            'specialist_color', 'specialist_icon',
            'date', 'time_slot', 'description', 'status', 'created_at'
        ]
        read_only_fields = ['user', 'status']

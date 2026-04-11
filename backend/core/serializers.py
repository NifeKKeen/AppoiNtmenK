from rest_framework import serializers
from django.contrib.auth import get_user_model
from typing import Dict, Any

from .models import Specialist, Appointment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data: Dict[str, Any]) -> Any:
        # Use create_user to properly hash the password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
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

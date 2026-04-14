from django.contrib import admin
from .models import User, SpecialistDetails, Appointment, ChatMessage


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_specialist', 'is_staff']
    list_filter = ['is_specialist', 'is_staff']


@admin.register(SpecialistDetails)
class SpecialistDetailsAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'role', 'google_calendar_connected', 'is_active']
    list_filter = ['is_active', 'google_calendar_connected']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialist', 'date', 'time_slot', 'status', 'created_at']
    list_filter = ['status', 'specialist', 'date']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'sender', 'body', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['appointment', 'sender']

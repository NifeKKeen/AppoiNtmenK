from django.contrib import admin
from .models import User, Specialist, Appointment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff']


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'role', 'google_calendar_connected', 'is_active']
    list_filter = ['is_active', 'google_calendar_connected']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialist', 'date', 'time_slot', 'status', 'created_at']
    list_filter = ['status', 'specialist', 'date']

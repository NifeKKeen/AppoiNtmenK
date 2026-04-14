from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Custom user model with specialist flag."""

    is_specialist = models.BooleanField(default=False)


class Specialist(models.Model):
    """
    Dynamic specialist profile. All UI-facing data (name, role, color, 
    available time slots) is served from this model so the frontend 
    never hardcodes specialist information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_profile',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    role = models.CharField(max_length=200)
    description = models.TextField()
    color = models.CharField(
        max_length=50,
        default='hsl(205, 75%, 52%)',
        help_text="CSS color value, e.g. hsl(270, 70%, 60%)",
    )
    icon = models.CharField(
        max_length=10,
        default='🧠',
        help_text="Emoji icon for the specialist",
    )
    avatar_url = models.URLField(blank=True, default='')
    time_slots = models.JSONField(
        default=list,
        blank=True,
        help_text='List of available time slot strings, e.g. ["09:00","09:15","09:30"]'
    )
    weekly_availability = models.JSONField(
        default=dict,
        blank=True,
        help_text='Map weekdays to list of available slots, e.g. {"mon": ["09:00", "09:30"]}',
    )
    google_calendar_connected = models.BooleanField(default=False)
    google_access_token = models.TextField(blank=True, default='')
    google_refresh_token = models.TextField(blank=True, default='')
    google_token_expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} — {self.role}"


class Appointment(models.Model):
    """
    Core booking entity. Links a student (User) to a Specialist 
    with a date, time slot, and description of their emergency.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    date = models.DateField()
    time_slot = models.CharField(max_length=11)
    description = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # Prevent double-booking the same specialist at the same date+time
        unique_together = ['specialist', 'date', 'time_slot']

    def __str__(self) -> str:
        return f"{self.user.username} → {self.specialist.name} on {self.date} at {self.time_slot}"


class ChatMessage(models.Model):
    """Single message in an appointment's chat thread."""

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.sender.username} @ {self.created_at:%H:%M}: {self.body[:40]}"

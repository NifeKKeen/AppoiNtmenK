from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Custom user model for future extensibility."""
    pass


class Specialist(models.Model):
    """
    Dynamic specialist profile. All UI-facing data (name, role, color, 
    available time slots) is served from this model so the frontend 
    never hardcodes specialist information.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    role = models.CharField(max_length=200)
    description = models.TextField()
    color = models.CharField(max_length=50, help_text="CSS color value, e.g. hsl(270, 70%, 60%)")
    icon = models.CharField(max_length=10, help_text="Emoji icon for the specialist")
    avatar_url = models.URLField(blank=True, default='')
    time_slots = models.JSONField(
        help_text='List of available time slot strings, e.g. ["09:00","09:15","09:30"]'
    )
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

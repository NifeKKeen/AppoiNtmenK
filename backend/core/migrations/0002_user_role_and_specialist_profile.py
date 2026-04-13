from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('USER', 'User'), ('SPECIALIST', 'Specialist')],
                default='USER',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='specialist',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='specialist_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='specialist',
            name='color',
            field=models.CharField(
                default='hsl(205, 75%, 52%)',
                help_text='CSS color value, e.g. hsl(270, 70%, 60%)',
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='specialist',
            name='icon',
            field=models.CharField(
                default='🧠',
                help_text='Emoji icon for the specialist',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='specialist',
            name='time_slots',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of available time slot strings, e.g. ["09:00","09:15","09:30"]',
            ),
        ),
    ]

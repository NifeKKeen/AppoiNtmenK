from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_role_and_specialist_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialist',
            name='google_access_token',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='specialist',
            name='google_calendar_connected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='specialist',
            name='google_refresh_token',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='specialist',
            name='google_token_expiry',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='specialist',
            name='weekly_availability',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Map weekdays to list of available slots, e.g. {"mon": ["09:00", "09:30"]}',
            ),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('confirmed', 'Confirmed'),
                    ('completed', 'Completed'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
    ]

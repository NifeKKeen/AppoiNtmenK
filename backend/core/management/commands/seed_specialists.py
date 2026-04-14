from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import SpecialistDetails

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with the three AppoiNtmenK specialists'

    def handle(self, *args, **options):
        # Ensure superuser exists for Render deployment
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'kanich')
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created successfully!'))

        specialists = [
            {
                'name': 'Adilet',
                'slug': 'adilet',
                'role': 'Math & Logic Whisperer',
                'description': (
                    'МЛ модель құрап беруге еш қиындықсыз көмектесе аламын.'
                ),
                'color': 'hsl(270, 70%, 60%)',
                'icon': '📠',
                'avatar_url': '',
                'time_slots': [
                    '09:00', '09:15', '09:30', '09:45',
                ],
            },
            {
                'name': 'Nuridin',
                'slug': 'nuridin',
                'role': 'Code Debugger',
                'description': (
                    'Бааа, не болып калды тагы'
                ),
                'color': 'hsl(160, 70%, 50%)',
                'icon': '💻',
                'avatar_url': '',
                'time_slots': [
                    '10:00', '10:15', '10:30', '10:45',
                    '11:00', '11:15', '11:30', '11:45',
                    '13:00', '13:15', '13:30', '13:45',
                    '14:00', '14:15', '14:30', '14:45',
                    '16:00', '16:15', '16:30', '16:45',
                ],
            },
            {
                'name': 'Kanich',
                'slug': 'kanich',
                'role': 'Presentation & Design Polisher',
                'description': (
                    'Че там, не керек? Ақчаааа ақчааааааааа керек, тез тез'
                ),
                'color': 'hsl(60, 90%, 60%)',
                'icon': '🤑',
                'avatar_url': '',
                'time_slots': [
                    '16:00', '16:15', '16:30', '16:45',
                ],
            },
            {
                'name': 'Jeffery',
                'slug': 'jeff',
                'role': 'Tourist-Consultant',
                'description': (
                    'Love entertainment? Come here to my island and I will show how'
                    ' cool dudes hang out.'
                ),
                'color': 'hsl(10, 60%, 50%)',
                'icon': '🏝️',
                'avatar_url': '',
                'time_slots': [
                    '23:00', '01:00',
                ],
            },
        ]

        for spec_data in specialists:
            specialist, created = SpecialistDetails.objects.update_or_create(
                slug=spec_data['slug'],
                defaults=spec_data
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} specialist: {specialist.name} — {specialist.role}')
            )

        self.stdout.write(self.style.SUCCESS('\nAll specialists seeded successfully!'))

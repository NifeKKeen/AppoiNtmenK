from django.core.management.base import BaseCommand
from core.models import Specialist


class Command(BaseCommand):
    help = 'Seed the database with the three AppoiNtmenK specialists'

    def handle(self, *args, **options):
        specialists = [
            {
                'name': 'Adilet',
                'slug': 'adilet',
                'role': 'Math & Logic Whisperer',
                'description': (
                    'When numbers betray you and proofs crumble, Adilet is your lifeline. '
                    'Specializing in discrete mathematics, calculus, and algorithmic logic, '
                    'he can untangle the most convoluted equations in a single 15-minute session. '
                    'Known for turning "I have no idea" into "oh, it\'s actually simple" — '
                    'Adilet\'s whiteboard sessions are legendary on campus.'
                ),
                'color': 'hsl(270, 70%, 60%)',
                'icon': '🧮',
                'avatar_url': '',
                'time_slots': [
                    '09:00', '09:15', '09:30', '09:45',
                    '10:00', '10:15', '10:30', '10:45',
                    '11:00', '11:15', '11:30', '11:45',
                    '14:00', '14:15', '14:30', '14:45',
                    '15:00', '15:15', '15:30', '15:45',
                ],
            },
            {
                'name': 'Nuridin',
                'slug': 'nuridin',
                'role': 'Code Debugger',
                'description': (
                    'Runtime errors at 3 AM? Merge conflicts that make no sense? '
                    'Nuridin has seen it all. With deep expertise in Python, TypeScript, '
                    'and full-stack architecture, he can spot a missing semicolon from '
                    'across the room. His debugging sessions have saved more GPAs than '
                    'any textbook ever could. Bring your broken code — leave with working software.'
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
                    'Your slides look like a ransom note? Your poster has 47 fonts? '
                    'Kanich will fix that. A master of visual communication, UI/UX principles, '
                    'and slide design, he transforms chaotic presentations into compelling stories. '
                    'Whether it\'s a thesis defense or a class demo, Kanich ensures your delivery '
                    'matches your data. "Design is not how it looks — it\'s how it works."'
                ),
                'color': 'hsl(30, 90%, 60%)',
                'icon': '🎨',
                'avatar_url': '',
                'time_slots': [
                    '09:00', '09:15', '09:30', '09:45',
                    '10:00', '10:15', '10:30', '10:45',
                    '13:00', '13:15', '13:30', '13:45',
                    '15:00', '15:15', '15:30', '15:45',
                    '16:00', '16:15', '16:30', '16:45',
                ],
            },
        ]

        for spec_data in specialists:
            specialist, created = Specialist.objects.update_or_create(
                slug=spec_data['slug'],
                defaults=spec_data
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} specialist: {specialist.name} — {specialist.role}')
            )

        self.stdout.write(self.style.SUCCESS('\nAll specialists seeded successfully!'))

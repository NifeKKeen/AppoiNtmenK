from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Specialist, Appointment


User = get_user_model()


class SpecialistAccountFlowTests(APITestCase):
    def test_register_standard_user(self) -> None:
        payload = {
            'username': 'plain-user',
            'email': 'plain@example.com',
            'password': 'secret-pass-123',
        }

        response = self.client.post('/api/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='plain-user')
        self.assertEqual(user.role, User.Role.USER)
        self.assertFalse(Specialist.objects.filter(user=user).exists())

    def test_register_specialist_creates_profile(self) -> None:
        payload = {
            'username': 'hero-user',
            'email': 'hero@example.com',
            'password': 'secret-pass-123',
            'become_specialist': True,
            'specialist_role': 'Code Debugger',
            'specialist_description': 'I help fix production bugs quickly.',
            'specialist_icon': '💻',
        }

        response = self.client.post('/api/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='hero-user')
        self.assertEqual(user.role, User.Role.SPECIALIST)

        profile = Specialist.objects.get(user=user)
        self.assertEqual(profile.role, 'Code Debugger')
        self.assertEqual(profile.icon, '💻')

    def test_upgrade_existing_user_to_specialist(self) -> None:
        user = User.objects.create_user(
            username='upgradable',
            email='upgradable@example.com',
            password='secret-pass-123',
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            '/api/profile/upgrade-specialist/',
            {
                'specialist_role': 'Math Whisperer',
                'specialist_description': 'Can explain hard topics clearly.',
                'specialist_icon': '🧮',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.SPECIALIST)
        self.assertTrue(Specialist.objects.filter(user=user).exists())

    def test_register_specialist_requires_role_and_description(self) -> None:
        response = self.client.post(
            '/api/register/',
            {
                'username': 'broken-specialist',
                'email': 'broken@example.com',
                'password': 'secret-pass-123',
                'become_specialist': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('specialist_role', response.data)
        self.assertIn('specialist_description', response.data)

    def test_specialist_can_update_weekly_availability(self) -> None:
        specialist_user = User.objects.create_user(
            username='specialist-availability',
            email='specialist-availability@example.com',
            password='secret-pass-123',
            role=User.Role.SPECIALIST,
        )
        Specialist.objects.create(
            user=specialist_user,
            name='Availability Hero',
            slug='availability-hero',
            role='Code Debugger',
            description='Available for mentoring.',
            icon='💻',
            color='hsl(205, 75%, 52%)',
            time_slots=['09:00'],
        )
        self.client.force_authenticate(user=specialist_user)

        payload = {
            'weekly_availability': {
                'mon': ['09:00', '09:30'],
                'tue': ['10:00'],
                'wed': [],
                'thu': [],
                'fri': [],
                'sat': [],
                'sun': [],
            }
        }

        response = self.client.post('/api/specialist/availability/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        specialist_user.specialist_profile.refresh_from_db()
        self.assertEqual(
            specialist_user.specialist_profile.weekly_availability['mon'],
            ['09:00', '09:30'],
        )

    def test_specialist_can_accept_and_reject_requests(self) -> None:
        specialist_user = User.objects.create_user(
            username='specialist-actions',
            email='specialist-actions@example.com',
            password='secret-pass-123',
            role=User.Role.SPECIALIST,
        )
        specialist = Specialist.objects.create(
            user=specialist_user,
            name='Action Hero',
            slug='action-hero',
            role='Math Whisperer',
            description='Solves problems fast.',
            icon='🧠',
            color='hsl(205, 75%, 52%)',
            time_slots=['09:00'],
        )
        student = User.objects.create_user(
            username='student-1',
            email='student-1@example.com',
            password='secret-pass-123',
        )
        appointment = specialist.appointments.create(
            user=student,
            date='2026-04-15',
            time_slot='09:00',
            description='Need help with recursion.',
            status='pending',
        )

        self.client.force_authenticate(user=specialist_user)
        accept_response = self.client.post(
            f'/api/specialist/requests/{appointment.id}/accept/',
            {},
            format='json',
        )
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'accepted')

        second_appointment = specialist.appointments.create(
            user=student,
            date='2026-04-16',
            time_slot='09:00',
            description='Need help with testing.',
            status='pending',
        )
        reject_response = self.client.post(
            f'/api/specialist/requests/{second_appointment.id}/reject/',
            {},
            format='json',
        )
        self.assertEqual(reject_response.status_code, status.HTTP_200_OK)
        second_appointment.refresh_from_db()
        self.assertEqual(second_appointment.status, 'rejected')

    def test_daily_availability_excludes_booked_slots(self) -> None:
        specialist_user = User.objects.create_user(
            username='spec-daily',
            email='spec-daily@example.com',
            password='secret-pass-123',
            role=User.Role.SPECIALIST,
        )
        specialist = Specialist.objects.create(
            user=specialist_user,
            name='Daily Hero',
            slug='daily-hero',
            role='Code Debugger',
            description='Handles urgent incidents.',
            icon='💻',
            color='hsl(205, 75%, 52%)',
            time_slots=['09:00', '09:30', '10:00'],
            weekly_availability={
                'mon': ['09:00', '09:30', '10:00'],
                'tue': [],
                'wed': [],
                'thu': [],
                'fri': [],
                'sat': [],
                'sun': [],
            },
        )
        student = User.objects.create_user(
            username='student-daily',
            email='student-daily@example.com',
            password='secret-pass-123',
        )
        Appointment.objects.create(
            user=student,
            specialist=specialist,
            date='2026-04-13',
            time_slot='09:30',
            description='Need debugging support.',
            status='pending',
        )

        self.client.force_authenticate(user=student)
        response = self.client.get('/api/specialists/daily-hero/availability/?date=2026-04-13')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booked_slots'], ['09:30'])
        self.assertEqual(response.data['available_slots'], ['09:00', '10:00'])

    def test_global_calendar_supports_filters(self) -> None:
        specialist_user = User.objects.create_user(
            username='spec-filter',
            email='spec-filter@example.com',
            password='secret-pass-123',
            role=User.Role.SPECIALIST,
        )
        specialist = Specialist.objects.create(
            user=specialist_user,
            name='Filter Hero',
            slug='filter-hero',
            role='Math Whisperer',
            description='Helps with math and logic.',
            icon='🧠',
            color='hsl(205, 75%, 52%)',
            time_slots=['09:00', '10:00', '11:00'],
            weekly_availability={
                'mon': ['09:00', '10:00', '11:00'],
                'tue': [],
                'wed': [],
                'thu': [],
                'fri': [],
                'sat': [],
                'sun': [],
            },
        )
        student = User.objects.create_user(
            username='calendar-user',
            email='calendar-user@example.com',
            password='secret-pass-123',
        )
        Appointment.objects.create(
            user=student,
            specialist=specialist,
            date='2026-04-13',
            time_slot='10:00',
            description='Already booked slot.',
            status='accepted',
        )

        self.client.force_authenticate(user=student)
        response = self.client.get(
            '/api/calendar/availability/?start_date=2026-04-13&days=1&specialist_slug=filter-hero&time_from=09:30&time_to=11:00'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['rows']), 1)
        self.assertEqual(response.data['rows'][0]['available_slots'], ['11:00'])

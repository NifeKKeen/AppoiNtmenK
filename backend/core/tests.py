from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Specialist


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

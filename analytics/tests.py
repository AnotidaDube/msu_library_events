# Create a new file: analytics/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AnalyticsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='staff', password='pass', email='s@test.com')

    def test_dashboard_access_staff_only(self):
        # Test that a regular user or guest can't see analytics
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertNotEqual(response.status_code, 200)

        # Test that staff CAN see it
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(response.status_code, 200)
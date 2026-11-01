from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import SCALEUser, SCALEUserRole
from apps.audit.models import AuditLog


class SCALELoginSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = SCALEUser.objects.create_user(
            username='test.supervisor',
            password='TestPassword123!',
            email='test@scale.local',
            role=SCALEUserRole.MANAGER
        )

    def test_login_page_renders_cleanly(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SCALE.Core')
        self.assertContains(response, 'Authenticate &amp; Launch Console')

    def test_successful_authentication_creates_audit_record(self):
        initial_audit_count = AuditLog.objects.count()
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test.supervisor',
            'password': 'TestPassword123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

        # Confirm audit event was recorded
        audit = AuditLog.objects.filter(event_type='USER_AUTHENTICATION_SUCCESS').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor_username, 'test.supervisor')

    def test_failed_authentication_increments_attempts_and_records_audit(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test.supervisor',
            'password': 'WrongPassword999!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

        audit = AuditLog.objects.filter(event_type='USER_AUTHENTICATION_FAILURE').first()
        self.assertIsNotNone(audit)

    def test_logout_view_clears_session(self):
        self.client.login(username='test.supervisor', password='TestPassword123!')
        response = self.client.get(reverse('accounts:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'safely signed out')

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

User = get_user_model()


class EmailAuthBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='emailtestuser',
            email='emailtest@example.com',
            password='pass12345',
        )

    def test_authenticate_by_email_succeeds(self):
        user = authenticate(username='emailtest@example.com', password='pass12345')
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

    def test_authenticate_by_email_wrong_password_fails(self):
        user = authenticate(username='emailtest@example.com', password='wrongpass')
        self.assertIsNone(user)

    def test_authenticate_by_nonexistent_email_fails(self):
        user = authenticate(username='doesnotexist@example.com', password='pass12345')
        self.assertIsNone(user)

    def test_login_view_accepts_email_as_username(self):
        from django.urls import reverse
        response = self.client.post(reverse('authorization:login'), {
            'username': 'emailtest@example.com',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('index'))

    def test_session_persists_after_login_by_email(self):

        from django.urls import reverse
        self.client.post(reverse('authorization:login'), {
            'username': 'emailtest@example.com',
            'password': 'pass12345',
        })

        response = self.client.get(reverse('authorization:my_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'emailtestuser')
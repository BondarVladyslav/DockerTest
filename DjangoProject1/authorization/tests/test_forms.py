from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
 
from authorization.forms import RegisterForm
from authorization.models import UserProfile
 
User = get_user_model()
 
 
class RegisterFormTest(TestCase):
    def _get_valid_data(self, **overrides):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        data.update(overrides)
        return data
 
    def test_valid_data_passes(self):
        form = RegisterForm(data=self._get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
 
    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='existinguser', email='taken@example.com', password='pass12345'
        )
        form = RegisterForm(data=self._get_valid_data(
            username='anotheruser', email='taken@example.com'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
 
    def test_passwords_must_match(self):
        form = RegisterForm(data=self._get_valid_data(password2='DifferentPass456!'))
        self.assertFalse(form.is_valid())
 
    def test_save_creates_user_with_correct_fields(self):
        form = RegisterForm(data=self._get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
 
    def test_save_creates_user_profile(self):
        form = RegisterForm(data=self._get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
 
 
class RegisterViewTest(TestCase):
    def setUp(self):
        self.register_url = reverse('authorization:register')
        self.login_url = reverse('authorization:login')
 
    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
 
    def test_successful_registration_redirects_to_login(self):
        response = self.client.post(self.register_url, {
            'username': 'freshuser',
            'email': 'fresh@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username='freshuser').exists())
 
    def test_registration_creates_profile_through_view(self):
        self.client.post(self.register_url, {
            'username': 'profileuser',
            'email': 'profileuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        user = User.objects.get(username='profileuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
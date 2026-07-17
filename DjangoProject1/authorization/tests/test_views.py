from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
 
from books.models import Author, Book
from authorization.models import UserProfile
 
User = get_user_model()
 
 
class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loginuser', password='pass12345')
        self.login_url = reverse('authorization:login')
        self.index_url = reverse('index')
 
    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
 
    def test_successful_login_redirects_to_index(self):
        response = self.client.post(self.login_url, {
            'username': 'loginuser',
            'password': 'pass12345',
        })
        self.assertRedirects(response, self.index_url)
 
    def test_login_with_wrong_password_fails(self):
        response = self.client.post(self.login_url, {
            'username': 'loginuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
 
    def test_login_with_nonexistent_user_fails(self):
        response = self.client.post(self.login_url, {
            'username': 'doesnotexist',
            'password': 'pass12345',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
 
 
class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='logoutuser', password='pass12345')
        self.logout_url = reverse('authorization:logout')
        self.index_url = reverse('index')
 
    def test_logout_requires_post(self):
        self.client.login(username='logoutuser', password='pass12345')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)
 
    def test_logout_via_post_succeeds(self):
        self.client.login(username='logoutuser', password='pass12345')
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.index_url)
 
    def test_user_actually_logged_out(self):
        self.client.login(username='logoutuser', password='pass12345')
        self.client.post(self.logout_url)
        response = self.client.get(reverse('authorization:my_profile'))
        self.assertEqual(response.status_code, 302)
 
 
class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='pass12345')
        # UserProfile создаётся автоматически через signal при создании User
        self.other_user = User.objects.create_user(username='otheruser', password='pass12345')
 
        self.my_profile_url = reverse('authorization:my_profile')
        self.login_url = reverse('authorization:login')
 
    def test_anonymous_user_redirected_from_my_profile(self):
        response = self.client.get(self.my_profile_url)
        self.assertEqual(response.status_code, 302)
 
    def test_authenticated_user_can_view_own_profile(self):
        self.client.login(username='profileuser', password='pass12345')
        response = self.client.get(self.my_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'profileuser')
 
    def test_anonymous_user_can_view_other_user_profile_by_pk(self):
        url = reverse('authorization:user_profile', kwargs={'pk': self.other_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'otheruser')
 
    def test_profile_shows_favourite_books(self):
        author = Author.objects.create(name='Тестовый автор')
        book = Book.objects.create(title='Любимая книга', author=author, year=2020)
 
        self.user.additional_data.favourite_books.add(book)
 
        self.client.login(username='profileuser', password='pass12345')
        response = self.client.get(self.my_profile_url)
        self.assertIn(book, response.context['favourite_books'])
 
    def test_profile_shows_finished_books(self):
        author = Author.objects.create(name='Тестовый автор')
        book = Book.objects.create(title='Прочитанная книга', author=author, year=2020)
 
        self.user.additional_data.finished_books.add(book)
 
        self.client.login(username='profileuser', password='pass12345')
        response = self.client.get(self.my_profile_url)
        self.assertIn(book, response.context['finished_books'])
 
    def test_nonexistent_profile_pk_returns_404(self):
        url = reverse('authorization:user_profile', kwargs={'pk': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
 
 
class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='passuser', password='OldPass123!')
        self.change_password_url = reverse('authorization:change_password')
 
    def test_anonymous_user_redirected(self):
        response = self.client.get(self.change_password_url)
        self.assertEqual(response.status_code, 302)
 
    def test_authenticated_user_can_view_form(self):
        self.client.login(username='passuser', password='OldPass123!')
        response = self.client.get(self.change_password_url)
        self.assertEqual(response.status_code, 200)
 
    def test_successful_password_change(self):
        self.client.login(username='passuser', password='OldPass123!')
        response = self.client.post(self.change_password_url, {
            'old_password': 'OldPass123!',
            'new_password1': 'NewPass456!',
            'new_password2': 'NewPass456!',
        })
        self.assertRedirects(response, reverse('authorization:change_data'))
 
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456!'))
 
    def test_wrong_old_password_rejected(self):
        self.client.login(username='passuser', password='OldPass123!')
        response = self.client.post(self.change_password_url, {
            'old_password': 'WrongOldPassword!',
            'new_password1': 'NewPass456!',
            'new_password2': 'NewPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))
 
    def test_mismatched_new_passwords_rejected(self):
        self.client.login(username='passuser', password='OldPass123!')
        response = self.client.post(self.change_password_url, {
            'old_password': 'OldPass123!',
            'new_password1': 'NewPass456!',
            'new_password2': 'DifferentPass789!',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))
import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from books.forms import AddBookForm
from books.models import Author, Genre
 
User = get_user_model()
 
 
def make_test_image():
    buf = io.BytesIO()
    Image.new('RGB', (1, 1), color='white').save(buf, format='JPEG')
    buf.seek(0)
    return SimpleUploadedFile('test.jpg', buf.read(), content_type='image/jpeg')
 
 
class AddBookFormTest(TestCase):
 
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.moderator_user = User.objects.create_user(username='moder', password='pass12345')
        self.genre = Genre.objects.create(name='Роман')
 
    def _get_valid_form_data(self, **overrides):
        data = {
            'title': 'Новая книга',
            'author': 'Совершенно новый автор',
            'description': 'Описание',
            'year': 2020,
            'genre': [self.genre.id],
        }
        data.update(overrides)
        files = {
            'book_file': SimpleUploadedFile('test.txt', b'content'),
            'book_avatar': make_test_image(),
        }
        return data, files
 
    def test_save_creates_new_author_if_not_exists(self):
        data, files = self._get_valid_form_data()
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.author.name, 'Совершенно новый автор')
        self.assertTrue(Author.objects.filter(name='Совершенно новый автор').exists())
 
    def test_save_reuses_existing_author_case_insensitive(self):
        existing_author = Author.objects.create(name='Лев Толстой')
        data, files = self._get_valid_form_data(
            title='Ещё одна книга',
            author='лев толстой',
        )
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.author.id, existing_author.id)
        self.assertEqual(Author.objects.filter(name__iexact='лев толстой').count(), 1)
 
    def test_save_sets_posted_by_to_current_user(self):
        data, files = self._get_valid_form_data(title='Книга пользователя', author='Автор')
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.posted_by, self.user)
 
    def test_valid_year_passes(self):
        data, files = self._get_valid_form_data(year=2020)
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        form.is_valid()
        self.assertNotIn('year', form.errors)
 
    def test_year_too_far_in_future_fails(self):
        data, files = self._get_valid_form_data(year=9999999)
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)
 
    def test_year_too_far_in_past_fails(self):
        data, files = self._get_valid_form_data(year=-999999)
        form = AddBookForm(data=data, files=files)
        form.initial['user'] = self.user
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)
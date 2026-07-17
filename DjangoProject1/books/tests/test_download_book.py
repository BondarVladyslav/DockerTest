import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from books.models import Author, Book

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestDownloadBookView(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Тестовый автор')

        self.published_book = Book.objects.create(
            title='Опубликованная книга',
            author=self.author,
            year=2020,
            is_published=True,
            book_file=SimpleUploadedFile('test.txt', b'book content here'),
        )

        self.unpublished_book = Book.objects.create(
            title='Неопубликованная книга',
            author=self.author,
            year=2021,
            is_published=False,
            book_file=SimpleUploadedFile('test2.txt', b'draft content'),
        )

        self.regular_user = User.objects.create_user(
            username='reader', password='pass12345'
        )
        self.superuser = User.objects.create_superuser(
            username='admin', password='pass12345', email='admin@test.com'
        )

    def test_download_published_book_succeeds(self):
        url = reverse('download_book', kwargs={'book_id': self.published_book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_unpublished_book_returns_404_for_anonymous(self):
        url = reverse('download_book', kwargs={'book_id': self.unpublished_book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_download_unpublished_book_returns_404_for_regular_user(self):
        self.client.login(username='reader', password='pass12345')
        url = reverse('download_book', kwargs={'book_id': self.unpublished_book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_download_unpublished_book_succeeds_for_superuser(self):
        self.client.login(username='admin', password='pass12345')
        url = reverse('download_book', kwargs={'book_id': self.unpublished_book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_nonexistent_book_returns_404(self):
        url = reverse('download_book', kwargs={'book_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

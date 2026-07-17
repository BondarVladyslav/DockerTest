from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from books.models import Author, Book

User = get_user_model()


class TestPostBookView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.moderator = User.objects.create_user(username='testModer', password='testpass123')
        self.permission = Permission.objects.get(codename='can_moderate_books')
        self.moderator.user_permissions.add(self.permission)
        self.post_url = reverse('post_book')
        self.index_url = reverse('index')
        self.author = Author.objects.create(name='Тестовый автор')

        self.book = Book.objects.create(
            title='Тестовая книга',
            author=self.author,
            year=2000,
            is_published=True,
        )

        self.unpublished_book = Book.objects.create(
            title='Книга на модерации',
            author=self.author,
            year=2024,
            is_published=False,
        )

        self.unpulished_book_url = reverse('bookByID', kwargs={'book_id': self.unpublished_book.id})
        self.book_by_id_url = reverse('bookByID', kwargs={'book_id': self.book.id})
        self.book_list_url = reverse('bookslist')
        self.author_by_slug_url = reverse('authorbyslug', kwargs={'author_slug':self.author.slug})
        self.authors_url = reverse('authors')
        self.moderate_book_url = reverse('moderate')


    def test_post_book_redirects_anonymous_user(self):
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, 302)   

    def test_post_book_accessible_for_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, 200)

    def test_index_view_GET(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/index.html')

    def test_book_by_id_view_GET(self):
        response = self.client.get(self.book_by_id_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/one_book.html')

    def test_unpublished_book_returns_404_for_anonymous(self):
        response = self.client.get(self.unpulished_book_url)
        self.assertEqual(response.status_code, 404)

    def test_book_list_view_GET(self):
        response = self.client.get(self.book_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/books.html')
    
    def test_author_by_slug_view_GET(self):
        response = self.client.get(self.author_by_slug_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/author.html')

    def test_authors_view_GET(self):
        response = self.client.get(self.authors_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books/authors.html')

    def test_moderate_book_moderator(self):
        self.client.login(username='testModer', password='testpass123')
        response = self.client.get(self.moderate_book_url)
        self.assertEqual(response.status_code, 200)

    def test_moderate_book_default_user_forbidden(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.moderate_book_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

    def test_moderate_book_publish_action(self):
        self.client.login(username='testModer', password='testpass123')
        response = self.client.post(self.moderate_book_url, {
            'book_id': self.unpublished_book.id,
            'action': 'publicate',
        })
        self.unpublished_book.refresh_from_db()
        self.assertTrue(self.unpublished_book.is_published)
        self.assertRedirects(response, self.moderate_book_url)

    def test_moderate_book_delete_action(self):
        self.client.login(username='testModer', password='testpass123')
        book_id = self.unpublished_book.id
        response = self.client.post(self.moderate_book_url, {
            'book_id': book_id,
            'action': 'delete',
        })
        self.assertFalse(Book.objects.filter(id=book_id).exists())
        self.assertRedirects(response, self.moderate_book_url)

    def test_moderate_book_post_forbidden_for_regular_user(self):
        self.client.login(username='testuser', password='testpass123')
        self.unpublished_book.refresh_from_db()
        self.assertFalse(self.unpublished_book.is_published)



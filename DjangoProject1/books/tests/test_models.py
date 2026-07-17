from django.test import TestCase
 
from books.models import Author, Genre, Book
 
 
class AuthorModelTest(TestCase):
    def test_slug_generated_from_cyrillic_name(self):
        author = Author.objects.create(name='Лев Толстой')
        self.assertEqual(author.slug, 'lev-tolstoy')
 
    def test_existing_slug_not_overwritten_on_resave(self):
        author = Author.objects.create(name='Тест', slug='custom-slug')
        author.save()
        self.assertEqual(author.slug, 'custom-slug')
 
    def test_str_returns_name(self):
        author = Author.objects.create(name='Тестовый автор')
        self.assertEqual(str(author), 'Тестовый автор')
 
    def test_get_absolute_url(self):
        author = Author.objects.create(name='Тест Автор')
        expected_url = f'/authors/{author.slug}/'
        self.assertEqual(author.get_absolute_url(), expected_url)
 

    def test_cannot_create_two_authors_with_same_name(self):
        Author.objects.create(name='Дубликат')
        with self.assertRaises(Exception):
            Author.objects.create(name='Дубликат')
 
 
class GenreModelTest(TestCase):
    def test_slug_generated_automatically(self):
        genre = Genre.objects.create(name='Роман')
        self.assertTrue(genre.slug)
        self.assertEqual(genre.slug, 'roman')
 
    def test_str_returns_name(self):
        genre = Genre.objects.create(name='Фантастика')
        self.assertEqual(str(genre), 'Фантастика')
 
    def test_existing_slug_not_overwritten_on_resave(self):
        genre = Genre.objects.create(name='Тест', slug='my-custom-slug')
        genre.save()
        self.assertEqual(genre.slug, 'my-custom-slug')
 
 
class BookModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Тестовый автор')
        self.genre = Genre.objects.create(name='Драма')
 
    def test_str_returns_title(self):
        book = Book.objects.create(title='Тестовая книга', author=self.author, year=2020)
        self.assertEqual(str(book), 'Тестовая книга')
 
    def test_book_default_not_published(self):
        book = Book.objects.create(title='Книга', author=self.author, year=2020)
        self.assertFalse(book.is_published)
 
    def test_book_can_be_published_explicitly(self):
        book = Book.objects.create(
            title='Опубликованная книга', author=self.author, year=2020, is_published=True
        )
        self.assertTrue(book.is_published)
 
    def test_author_deletion_cascades_to_books(self):
        book = Book.objects.create(title='Книга', author=self.author, year=2020)
        book_id = book.id
        self.author.delete()
        self.assertFalse(Book.objects.filter(id=book_id).exists())
 
    def test_book_can_have_multiple_genres(self):
        second_genre = Genre.objects.create(name='Роман')
        book = Book.objects.create(title='Книга', author=self.author, year=2020)
        book.genre.set([self.genre, second_genre])
        self.assertEqual(book.genre.count(), 2)
 
    def test_genre_books_with_genre_reverse_relation(self):
        book = Book.objects.create(title='Книга', author=self.author, year=2020)
        book.genre.add(self.genre)
        self.assertIn(book, self.genre.books_with_genre.all())
 
    def test_posted_by_set_null_on_user_deletion(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='author_user', password='pass12345')
 
        book = Book.objects.create(
            title='Книга пользователя', author=self.author, year=2020, posted_by=user
        )
        user.delete()
        book.refresh_from_db()
        self.assertIsNone(book.posted_by)
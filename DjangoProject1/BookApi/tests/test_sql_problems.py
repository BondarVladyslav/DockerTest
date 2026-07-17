from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
 
from books.models import Author, Book, Genre
 
 
class BookViewSetQueryCountTest(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Тестовый автор')
        self.genre1 = Genre.objects.create(name='Роман')
        self.genre2 = Genre.objects.create(name='Драма')
 
    def _create_books(self, count):
        for i in range(count):
            book = Book.objects.create(
                title=f'Книга {i}',
                author=self.author,
                year=2020,
                is_published=True,
            )
            book.genre.set([self.genre1, self.genre2])
 
    def test_list_query_count_does_not_grow_with_more_books(self):
        self._create_books(3)
        with CaptureQueriesContext(connection) as captured_3:
            response = self.client.get('/api/books/')
            self.assertEqual(response.status_code, 200)
        queries_for_3_books = len(captured_3.captured_queries)
 
        Book.objects.all().delete()
        self._create_books(15)
        with CaptureQueriesContext(connection) as captured_15:
            response = self.client.get('/api/books/')
            self.assertEqual(response.status_code, 200)
        queries_for_15_books = len(captured_15.captured_queries)
        self.assertEqual(
            queries_for_3_books,
            queries_for_15_books,
            f'Количество запросов выросло с {queries_for_3_books} до '
            f'{queries_for_15_books} при увеличении числа книг — похоже на N+1.'
        )
 
    def test_retrieve_single_book_uses_few_queries(self):
        self._create_books(1)
        book = Book.objects.first()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(f'/api/books/{book.id}/')
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(captured.captured_queries), 3,
            f'Запросов: {len(captured.captured_queries)}\n' +
            '\n'.join(q['sql'] for q in captured.captured_queries)
        )
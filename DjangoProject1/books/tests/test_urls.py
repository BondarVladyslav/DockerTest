from django.test import SimpleTestCase
from django.urls import resolve, reverse

from books.views import Authors, BooksList, Index, ModerateBooks, OneBook, PostBook, authorbyslug, download_book

class TestUrls(SimpleTestCase):

    def test_index_url_is_resolved(self):
        url = reverse('index')
        self.assertEqual(resolve(url).func.view_class, Index)

    def test_index_url_is_resolved(self):
        url = reverse('bookByID', kwargs={'book_id': 1})
        self.assertEqual(resolve(url).func.view_class, OneBook)

    def test_books_list_url_is_resolved(self):
        url = reverse('bookslist')
        self.assertEqual(resolve(url).func.view_class, BooksList)

    def test_authors_url_is_resolved(self):
        url = reverse('authors')
        self.assertEqual(resolve(url).func.view_class, Authors)

    def test_author_by_slug_url_is_resolved(self):
        url = reverse('authorbyslug', kwargs={'author_slug':'lev-tolstoy'})
        self.assertEqual(resolve(url).func, authorbyslug)

    def test_post_book_url_is_resolved(self):
        url = reverse('post_book')
        self.assertEqual(resolve(url).func.view_class, PostBook)

    def test_download_books_url_is_resolved(self):
        url = reverse('download_book', kwargs={'book_id': 1})
        self.assertEqual(resolve(url).func, download_book)


    def test_moderate_books_url_is_resolved(self):
        url = reverse('moderate')
        self.assertEqual(resolve(url).func.view_class, ModerateBooks)



import io
 
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
 
from books.models import Author, Book, Comment, Genre
 
User = get_user_model()
 
 
def make_test_image():
    buf = io.BytesIO()
    Image.new('RGB', (1, 1), color='white').save(buf, format='JPEG')
    buf.seek(0)
    return SimpleUploadedFile('test.jpg', buf.read(), content_type='image/jpeg')
 
 
def make_test_file():
    return SimpleUploadedFile('test.txt', b'book content')
 
 
class BookViewSetListRetrieveTest(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Тестовый автор')
        self.genre = Genre.objects.create(name='Роман')
 
        self.published_book = Book.objects.create(
            title='Опубликованная книга',
            author=self.author,
            year=2020,
            is_published=True,
        )
        self.unpublished_book = Book.objects.create(
            title='Неопубликованная книга',
            author=self.author,
            year=2021,
            is_published=False,
        )
 
    def test_list_returns_200(self):
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_retrieve_published_book_returns_200(self):
        response = self.client.get(f'/api/books/{self.published_book.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Опубликованная книга')
 
 
class BookViewSetCreateTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass12345')
        self.moderator = User.objects.create_user(username='apimoder', password='pass12345')
        permission = Permission.objects.get(codename='can_moderate_books')
        self.moderator.user_permissions.add(permission)
 
        self.genre = Genre.objects.create(name='Драма')
 
    def _valid_payload(self, **overrides):
        data = {
            'title': 'Новая книга через API',
            'author': 'Новый автор API',
            'description': 'Описание',
            'year': 2022,
            'genre': [self.genre.id],
        }
        data.update(overrides)
        return data
 
    def test_anonymous_cannot_create_book(self):
        response = self.client.post('/api/books/', self._valid_payload(), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
 
    def test_authenticated_user_can_create_book(self):
        self.client.force_authenticate(user=self.user)
        payload = self._valid_payload()
        payload['book_file'] = make_test_file()
        payload['book_avatar'] = make_test_image()
        response = self.client.post('/api/books/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
 
    def test_created_book_is_unpublished_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        payload = self._valid_payload()
        payload['book_file'] = make_test_file()
        payload['book_avatar'] = make_test_image()
        response = self.client.post('/api/books/', payload, format='multipart')
        self.assertFalse(response.data['is_published'])
 
    def test_created_book_is_published_for_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        payload = self._valid_payload()
        payload['book_file'] = make_test_file()
        payload['book_avatar'] = make_test_image()
        response = self.client.post('/api/books/', payload, format='multipart')
        self.assertTrue(response.data['is_published'])
 
    def test_posted_by_cannot_be_overridden_by_client(self):
        self.client.force_authenticate(user=self.user)
        payload = self._valid_payload()
        payload['book_file'] = make_test_file()
        payload['book_avatar'] = make_test_image()
        payload['posted_by'] = 999999  # клиент пытается подменить
        response = self.client.post('/api/books/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_book = Book.objects.get(id=response.data['id'])
        self.assertEqual(created_book.posted_by, self.user)
 
    def test_author_created_automatically_if_not_exists(self):
        self.client.force_authenticate(user=self.user)
        payload = self._valid_payload(author='Совершенно новый автор API')
        payload['book_file'] = make_test_file()
        payload['book_avatar'] = make_test_image()
        response = self.client.post('/api/books/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Author.objects.filter(name='Совершенно новый автор API').exists())
 
 
class BookViewSetUpdateDeleteTest(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Автор')
        self.regular_user = User.objects.create_user(username='regular', password='pass12345')
        self.moderator = User.objects.create_user(username='moder', password='pass12345')
        permission = Permission.objects.get(codename='can_moderate_books')
        self.moderator.user_permissions.add(permission)
 
        self.unpublished_book = Book.objects.create(
            title='На модерации', author=self.author, year=2023, is_published=False
        )
        self.published_book = Book.objects.create(
            title='Опубликована', author=self.author, year=2023, is_published=True
        )
 
    def test_regular_user_cannot_update_book(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(
            f'/api/books/{self.unpublished_book.id}/', {'is_published': True}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_moderator_can_publish_unpublished_book(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(
            f'/api/books/{self.unpublished_book.id}/', {'is_published': True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unpublished_book.refresh_from_db()
        self.assertTrue(self.unpublished_book.is_published)
 
    def test_moderator_cannot_change_other_fields_on_update(self):
        self.client.force_authenticate(user=self.moderator)
        original_title = self.unpublished_book.title
        response = self.client.patch(
            f'/api/books/{self.unpublished_book.id}/',
            {'is_published': True, 'title': 'Подменённое название'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unpublished_book.refresh_from_db()
        self.assertEqual(self.unpublished_book.title, original_title)
 
    def test_cannot_republish_already_published_book(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(
            f'/api/books/{self.published_book.id}/', {'is_published': False}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 
    def test_regular_user_cannot_delete_book(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(f'/api/books/{self.unpublished_book.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_moderator_can_delete_unpublished_book(self):
        self.client.force_authenticate(user=self.moderator)
        book_id = self.unpublished_book.id
        response = self.client.delete(f'/api/books/{book_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book_id).exists())
 
    def test_moderator_cannot_delete_published_book(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(f'/api/books/{self.published_book.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(id=self.published_book.id).exists())
 
 
class BookViewSetCustomActionsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='actionuser', password='pass12345')
        self.author = Author.objects.create(name='Автор')
        self.book = Book.objects.create(
            title='Книга', author=self.author, year=2020, is_published=True
        )
 
    def test_like_book_requires_authentication(self):
        response = self.client.post(f'/api/books/{self.book.id}/like_book/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
 
    def test_like_book_adds_to_favourites(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/books/{self.book.id}/like_book/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'liked')
        self.assertTrue(
            self.user.additional_data.favourite_books.filter(id=self.book.id).exists()
        )
 
    def test_like_book_twice_removes_from_favourites(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f'/api/books/{self.book.id}/like_book/')
        response = self.client.post(f'/api/books/{self.book.id}/like_book/')
        self.assertEqual(response.data['status'], 'unliked')
        self.assertFalse(
            self.user.additional_data.favourite_books.filter(id=self.book.id).exists()
        )
 
    def test_finish_book_adds_to_finished(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/books/{self.book.id}/finish_book/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            self.user.additional_data.finished_books.filter(id=self.book.id).exists()
        )
 
    def test_get_newest_books_returns_limited_count(self):
        for i in range(10):
            Book.objects.create(
                title=f'Книга {i}', author=self.author, year=2020, is_published=True
            )
        response = self.client.get('/api/books/get_newest_books/?number=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['newest_books']), 3)
 
    def test_download_published_book_succeeds(self):
        self.book.book_file = make_test_file()
        self.book.save()
        response = self.client.get(f'/api/books/{self.book.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_download_unpublished_book_forbidden_for_anonymous(self):
        unpublished = Book.objects.create(
            title='Не опубликована', author=self.author, year=2020, is_published=False
        )
        unpublished.book_file = make_test_file()
        unpublished.save()
        response = self.client.get(f'/api/books/{unpublished.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
 


class CommentViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='pass12345')
        self.other_user = User.objects.create_user(username='othercommenter', password='pass12345')
 
        self.author = Author.objects.create(name='Тестовый автор')
        self.book1 = Book.objects.create(
            title='Книга 1', author=self.author, year=2020, is_published=True
        )
        self.book2 = Book.objects.create(
            title='Книга 2', author=self.author, year=2021, is_published=True
        )
 
        self.comment_on_book1 = Comment.objects.create(
            book=self.book1, user=self.user, text='Отличная книга'
        )
        self.comment_on_book2 = Comment.objects.create(
            book=self.book2, user=self.other_user, text='Так себе'
        )
 
    def test_list_comments_returns_200(self):
        response = self.client.get('/api/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_filter_comments_by_book(self):
        response = self.client.get(f'/api/comments/?book={self.book1.id}')
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        texts = [c['text'] for c in results]
        self.assertIn('Отличная книга', texts)
        self.assertNotIn('Так себе', texts)
 
    def test_anonymous_cannot_create_comment(self):
        response = self.client.post('/api/comments/', {
            'book': self.book1.id,
            'text': 'Новый комментарий',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
 
    def test_authenticated_user_can_create_comment(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/comments/', {
            'book': self.book1.id,
            'text': 'Новый комментарий',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
 
    def test_comment_user_set_automatically_not_from_client(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/comments/', {
            'book': self.book1.id,
            'user': self.other_user.id,
            'text': 'Подделанный комментарий',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_comment = Comment.objects.get(id=response.data['id'])
        self.assertEqual(created_comment.user, self.user)
 
    def test_update_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/comments/{self.comment_on_book1.id}/', {
            'text': 'Изменённый текст',
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
 
    def test_delete_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/comments/{self.comment_on_book1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
 

class AuthorViewSetTest(APITestCase):
    def setUp(self):
        self.author_with_books = Author.objects.create(name='Автор с книгами')
        self.author_without_books = Author.objects.create(name='Автор без книг')
 
        Book.objects.create(
            title='Книга автора',
            author=self.author_with_books,
            year=2020,
            is_published=True,
        )
 
    def test_list_returns_200(self):
        response = self.client.get('/api/authors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
 
    def test_author_without_books_excluded_from_list(self):
        response = self.client.get('/api/authors/')
        results = response.data['results'] if 'results' in response.data else response.data
        names = [a['name'] for a in results]
        self.assertIn('Автор с книгами', names)
        self.assertNotIn('Автор без книг', names)
 
    def test_retrieve_by_slug(self):
        response = self.client.get(f'/api/authors/{self.author_with_books.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Автор с книгами')
 
    def test_retrieve_by_numeric_id_fails(self):
        response = self.client.get(f'/api/authors/{self.author_with_books.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
 
    def test_create_not_allowed(self):
        response = self.client.post('/api/authors/', {'name': 'Новый автор через API'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 
    def test_update_not_allowed(self):
        response = self.client.patch(
            f'/api/authors/{self.author_with_books.slug}/', {'name': 'Изменённое имя'}
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 
    def test_delete_not_allowed(self):
        response = self.client.delete(f'/api/authors/{self.author_with_books.slug}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 
    def test_only_published_books_counted(self):
        author = Author.objects.create(name='Автор со скрытой книгой')
        Book.objects.create(
            title='Неопубликованная книга',
            author=author,
            year=2020,
            is_published=False,
        )
        response = self.client.get('/api/authors/')
        results = response.data['results'] if 'results' in response.data else response.data
        names = [a['name'] for a in results]
        self.assertNotIn('Автор со скрытой книгой', names)
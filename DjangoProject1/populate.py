import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from django.contrib.auth import get_user_model
from books.models import Author, Book, Genre
from authorization.models import UserProfile

User = get_user_model()


def run():
    print('Очистка старых данных...')
    Book.objects.all().delete()
    Author.objects.all().delete()
    Genre.objects.all().delete()

    print('Создание жанров...')
    genres_data = ['Роман', 'История', 'Художественная', 'Драма', 'Фантастика']
    genres = {}
    for name in genres_data:
        genre = Genre.objects.create(name=name)
        genres[name] = genre
    print(f'  Создано жанров: {len(genres)}')

    print('Создание авторов...')
    authors_data = [
        ('Лев Толстой', 'Русский писатель, классик мировой литературы.'),
        ('Фёдор Достоевский', 'Один из крупнейших русских писателей и мыслителей.'),
        ('Михаил Булгаков', 'Русский писатель, драматург и театральный режиссёр.'),
    ]
    authors = {}
    for name, description in authors_data:
        author = Author.objects.create(name=name, author_description=description)
        authors[name] = author
    print(f'  Создано авторов: {len(authors)}')

    print('Создание книг...')
    books_data = [
        {
            'title': 'Война и мир',
            'author': 'Лев Толстой',
            'year': 1869,
            'description': 'Роман-эпопея, описывающий русское общество в эпоху войн против Наполеона.',
            'genres': ['Роман', 'История'],
            'is_published': True,
        },
        {
            'title': 'Анна Каренина',
            'author': 'Лев Толстой',
            'year': 1877,
            'description': 'Роман о трагической любви замужней женщины к молодому офицеру.',
            'genres': ['Роман', 'Драма'],
            'is_published': True,
        },
        {
            'title': 'Воскресение',
            'author': 'Лев Толстой',
            'year': 1899,
            'description': 'Последний роман Толстого о духовном перерождении человека.',
            'genres': ['Роман', 'Драма'],
            'is_published': True,
        },
        {
            'title': 'Преступление и наказание',
            'author': 'Фёдор Достоевский',
            'year': 1866,
            'description': 'Роман о студенте, совершившем убийство и его моральных терзаниях.',
            'genres': ['Роман', 'Драма'],
            'is_published': True,
        },
        {
            'title': 'Идиот',
            'author': 'Фёдор Достоевский',
            'year': 1869,
            'description': 'Роман о князе Мышкине и его столкновении с окружающим миром.',
            'genres': ['Драма'],
            'is_published': True,
        },
        {
            'title': 'Братья Карамазовы',
            'author': 'Фёдор Достоевский',
            'year': 1880,
            'description': 'Последний роман Достоевского о семье Карамазовых.',
            'genres': ['Роман', 'Драма'],
            'is_published': True,
        },
        {
            'title': 'Бесы',
            'author': 'Фёдор Достоевский',
            'year': 1872,
            'description': 'Роман о революционном движении в России.',
            'genres': ['Драма'],
            'is_published': True,
        },
        {
            'title': 'Мастер и Маргарита',
            'author': 'Михаил Булгаков',
            'year': 1967,
            'description': 'Роман о визите дьявола в советскую Москву.',
            'genres': ['Роман', 'Фантастика'],
            'is_published': True,
        },
        {
            'title': 'Собачье сердце',
            'author': 'Михаил Булгаков',
            'year': 1925,
            'description': 'Повесть о собаке, превращённой в человека.',
            'genres': ['Фантастика'],
            'is_published': True,
        },
        {
            'title': 'Белая гвардия',
            'author': 'Михаил Булгаков',
            'year': 1925,
            'description': 'Роман о гражданской войне в Киеве.',
            'genres': ['История', 'Драма'],
            'is_published': True,
        },
        {
            'title': 'Черновик новой книги',
            'author': 'Михаил Булгаков',
            'year': 2024,
            'description': 'Книга на модерации, ещё не опубликована.',
            'genres': ['Роман'],
            'is_published': False,
        },
    ]

    created_count = 0
    for data in books_data:
        book = Book.objects.create(
            title=data['title'],
            author=authors[data['author']],
            year=data['year'],
            description=data['description'],
            is_published=data['is_published'],
        )
        book.genre.set([genres[g] for g in data['genres']])
        created_count += 1

    print(f'  Создано книг: {created_count}')

    print('Создание тестовых пользователей...')
    if not User.objects.filter(username='moderator').exists():
        moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='moderator12345',
            first_name='Модератор',
        )
        UserProfile.objects.create(user=moderator)
        print('  Создан пользователь moderator / moderator12345 (назначь permission can_moderate_books вручную через админку)')

    if not User.objects.filter(username='reader').exists():
        reader = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='reader12345',
            first_name='Читатель',
        )
        profile = UserProfile.objects.create(user=reader)
        profile.favourite_books.add(Book.objects.get(title='Мастер и Маргарита'))
        profile.finished_books.add(Book.objects.get(title='Война и мир'))
        print('  Создан пользователь reader / reader12345')

    print('\nГотово!')
    print(f'Авторов: {Author.objects.count()}')
    print(f'Жанров: {Genre.objects.count()}')
    print(f'Книг: {Book.objects.count()} (опубликовано: {Book.objects.filter(is_published=True).count()})')


if __name__ == '__main__':
    run()

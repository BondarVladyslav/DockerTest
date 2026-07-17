# Book4Read — книжный трекер с REST API

Веб-приложение для каталогизации книг с системой модерации контента, ролевой моделью пользователей и полноценным REST API. Реализовано как гибрид: классический Django с шаблонами для основного веб-интерфейса и DRF API для программного доступа.

## Функционал

- Каталог книг с фильтрацией по автору, жанру, году и полнотекстовым поиском
- Система модерации — новые книги попадают на проверку, публикует модератор
- Связи многие-ко-многим между книгами и жанрами
- Личный кабинет — избранное, отметки «прочитано»
- Комментарии к книгам
- Аутентификация по username или email
- REST API с JWT-аутентификацией, кастомными permissions и пагинацией
- Скачивание файлов книг с контролем доступа по статусу публикации

## Стек

- Python 3.13, Django 6.0
- Django REST Framework + Simple JWT + Djoser
- PostgreSQL
- pytest / Django test framework (тесты для models, forms, views, API)

## Архитектурные решения

**Транслитерация для слагов.** Встроенный `django.utils.text.slugify` не обрабатывает кириллицу. Реализован собственный словарь транслитерации, чтобы URL авторов и жанров оставались читаемыми (`/authors/lev-tolstoy/`, а не закодированная кириллица).

**Оптимизация запросов.** Списки книг используют `select_related('author')` и `prefetch_related('genre')`, чтобы избежать N+1 при выводе связанных данных. Поведение покрыто тестом, который сравнивает количество SQL-запросов на 3 и на 15 книгах — если оптимизация когда-нибудь будет случайно убрана, тест сразу это покажет.

**Модель прав на модерацию.** Обычный пользователь может только создавать книги — они автоматически попадают в очередь на модерацию (`is_published=False`). Модератор (отдельное право `can_moderate_books`) может публиковать книги и удалять только неопубликованные — это разделение реализовано как на уровне Django-форм, так и на уровне DRF-сериализатора через переопределение `get_fields()`, в зависимости от того, идёт ли создание или редактирование объекта.

**Гарантия существования профиля пользователя.** Изначально `UserProfile` создавался только внутри формы регистрации — это означало, что пользователь, созданный любым другим способом (`createsuperuser`, импорт данных), оставался без профиля и ронял страницу профиля ошибкой. Исправлено через Django-сигнал `post_save` на модели `User`, который гарантирует создание профиля при любом способе создания пользователя.

**Аутентификация по email.** Кастомный backend `EmailAuthBackend` позволяет логиниться как по username, так и по email, не дублируя стандартную модель пользователя.

**Гибридная архитектура API.** Часть функционала (создание книг с файлами) сделана через `multipart/form-data` с явными `parser_classes` на конкретном ViewSet, остальной API работает через чистый JSON — баланс между удобством загрузки файлов и строгостью контракта API.

## Установка

### 1. PostgreSQL

Проект требует установленный и запущенный PostgreSQL (рекомендуется версия 14+).

**Установка:**
- Windows/Mac — скачать инсталлятор с [postgresql.org/download](https://www.postgresql.org/download/)
- Linux (Ubuntu/Debian): `sudo apt install postgresql postgresql-contrib`

**Создание базы данных и пользователя.** Зайди в `psql` от имени суперпользователя БД:

```bash
psql -U postgres
```

Внутри `psql` выполни:

```sql
CREATE DATABASE library_db;
CREATE USER library_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE library_db TO library_user;
\c library_db
GRANT ALL ON SCHEMA public TO library_user;
ALTER USER library_user CREATEDB;
\q
```

`ALTER USER library_user CREATEDB` — отдельная команда, без которой упадёт запуск тестов: Django создаёт отдельную тестовую базу данных при каждом прогоне `python manage.py test`, и для этого пользователю нужно явное право на создание баз.

**Если используешь Windows и видишь `UnicodeDecodeError` при первом подключении** — это известная проблема, связанная с тем, что PostgreSQL генерирует системные сообщения в локали по умолчанию (например, `Russian_Ukraine.1251`), а драйвер `psycopg` ожидает UTF-8. Чинится так:

```sql
ALTER SYSTEM SET lc_messages = 'English_United States.1252';
```

После этого нужно перезапустить сервис PostgreSQL (через `services.msc` на Windows или `sudo systemctl restart postgresql` на Linux).

### 2. Проект

```bash
git clone <repository-url>
cd DjangoProject1
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
```

Создай `.env` в корне проекта по образцу `.env.example`, используя те же значения `DB_NAME`/`DB_USER`/`DB_PASSWORD`, что задавал в `psql` на предыдущем шаге:

```
SECRET_KEY=your-secret-key-here
DB_NAME=library_db
DB_USER=library_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API

Полный список эндпоинтов доступен через Browsable API DRF на `/api/`. Основные:

```
GET    /api/books/                      — список книг (пагинация, фильтры: ?author=, ?year=, ?genre=, ?search=, ?sort=)
POST   /api/books/                      — создать книгу (требует аутентификации)
GET    /api/books/{id}/                 — детали книги
PATCH  /api/books/{id}/                 — изменить статус публикации (только модератор)
DELETE /api/books/{id}/                 — удалить книгу (только модератор, только неопубликованную)
GET    /api/books/{id}/download/        — скачать файл книги
POST   /api/books/{id}/like_book/       — добавить/убрать из избранного
POST   /api/books/{id}/finish_book/     — отметить/снять отметку «прочитано»
GET    /api/books/get_newest_books/     — последние опубликованные книги (?number=)

GET    /api/authors/                    — список авторов (только с опубликованными книгами)
GET    /api/authors/{slug}/             — детали автора

GET    /api/comments/?book={id}         — комментарии к книге
POST   /api/comments/                   — оставить комментарий

POST   /api/token/                      — получить JWT access/refresh токены
POST   /api/token/refresh/              — обновить access токен
```

## Тесты

```bash
python manage.py test
```

Покрыты модели, формы, права доступа, основные пользовательские сценарии (регистрация, логин, модерация) и весь DRF API, включая защиту от N+1-запросов.

## Скрипт наполнения тестовыми данными

```bash
python populate.py
```
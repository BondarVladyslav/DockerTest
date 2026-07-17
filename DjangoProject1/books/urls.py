from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.Index.as_view(), name = 'index'),
    path('books/<int:book_id>/', views.OneBook.as_view(), name = 'bookByID'),
    path('books/', views.BooksList.as_view(), name = 'bookslist'),
    path('authors/<slug:author_slug>/', views.authorbyslug, name='authorbyslug'),
    path('authors/', views.Authors.as_view(), name='authors'),
    path('post/', views.PostBook.as_view(), name = 'post_book'),
    path('download/<int:book_id>/', views.download_book, name='download_book'),
    path('moderate/', views.ModerateBooks.as_view(), name = 'moderate')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
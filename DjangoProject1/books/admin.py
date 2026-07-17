from django.contrib import admin
from .models import Author, Book, Genre


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'year', 'is_published', 'posted_by']
    list_filter = ['is_published', 'year']
    search_fields = ['title', 'author__name']
    list_editable = ['is_published']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
from rest_framework import viewsets,mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from BookApi.permissions import IsModerator
from BookApi.serializers import AuthorsListSerializer, BookSerializer, CommentSerializer, NewestBooksQuerySerializer
from books.models import Book, Comment, Author
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count
from rest_framework.exceptions import NotFound
from django.http import FileResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from books.views import ALLOWED_ORDERINGS
from .pagination import *

class BookViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Book.objects.all().order_by('-id')
    serializer_class = BookSerializer
    pagination_class = BooksPagination
    def get_permissions(self):
        if self.action in ['create','like_book','finish_book']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsModerator()]
        
        return [AllowAny()]
    

    def get_queryset(self):
        books = Book.objects.select_related('author').prefetch_related('genre')

        if self.action == 'list':
            books = books.filter(is_published=True)

            ordering = self.request.query_params.get('sort')
            if ordering in ALLOWED_ORDERINGS:
                books = books.order_by(ordering)
            else:
                books = books.order_by('-id')

            author = self.request.query_params.get('author')
            if author:
                books = books.filter(author__slug=author)

            year = self.request.query_params.get('year')
            if year:
                try:
                    books = books.filter(year=int(year))
                except ValueError:
                    pass

            genres = self.request.query_params.get('genre')
            if genres:
                books = books.filter(genre__slug__in=genres.split('.')).distinct()

            search = self.request.query_params.get('search')
            if search:
                books = books.filter(
                    Q(title__icontains=search) | Q(author__name__icontains=search)
                )
        else:
            books = books.order_by('-id')

        return books

    @action(methods = ['get'], detail = False)
    def get_newest_books(self, request):
        number_of_books_serializer = NewestBooksQuerySerializer(data = request.query_params)
        number_of_books_serializer.is_valid(raise_exception=True)
        number = number_of_books_serializer.validated_data['number']
        newest_books = Book.objects.filter(is_published = True).select_related('author').prefetch_related('genre').order_by('-id')[:number]
        serializer = self.get_serializer(newest_books, many = True)
        return Response({'newest_books':serializer.data})
    
    @action(methods = ['post'], detail=True, permission_classes=[IsAuthenticated])
    def like_book(self, request, pk = None):
        book = self.get_object()
        favourite_books = request.user.additional_data.favourite_books
        if favourite_books.filter(pk = book.pk).exists():
            favourite_books.remove(book)
            return Response({'status': 'unliked', 'book': book.title})
        favourite_books.add(book)
        return Response({'status': 'liked', 'book': book.title})
    

    @action(methods = ['post'], detail=True, permission_classes=[IsAuthenticated])
    def finish_book(self, request, pk = None):
        book = self.get_object()
        finished_books = request.user.additional_data.finished_books
        if finished_books.filter(pk = book.pk).exists():
            finished_books.remove(book)
            return Response({'status': 'unfinished', 'book': book.title})
        finished_books.add(book)
        return Response({'status': 'finished', 'book': book.title})
    
    @action(methods=['get'], detail=True)
    def download(self, request, pk=None):
        book = self.get_object()
        
        if not book.is_published and not request.user.is_superuser:
            raise NotFound('File not found')
        
        if not book.book_file:
            raise NotFound('File not found')
        
        try:
            return FileResponse(
                open(book.book_file.path, 'rb'),
                as_attachment=True,
                filename=book.book_file.name
            )
        except FileNotFoundError:
            raise NotFound('File not found')
        
    @action(methods=['get'], detail=False)
    def get_unpublished_books(self, request):
        books = self.get_queryset().filter(is_published=False)
        serializer = self.get_serializer(books,many=True)
        return Response({'books':serializer.data})

        


    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            posted_by=user,
            is_published=user.has_perm('books.can_moderate_books')
        )
    

class CommentViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = Comment.objects.select_related('user', 'book')
        book_id = self.request.query_params.get('book')
        if book_id:
            qs = qs.filter(book_id=book_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    queryset = Author.objects.annotate(
        books_count=Count('books', filter=Q(books__is_published=True))
    ).filter(books_count__gt=0)
    serializer_class = AuthorsListSerializer


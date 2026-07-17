from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.db.models import Q, Count
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from authorization.models import UserProfile
from books.models import Author, Book, Genre
from .forms import AddBookForm, CommentForm, SearchBookForm
from django.urls import reverse_lazy
from .utils import BaseMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


SiteName = 'Book4Read'
menu = [
    {'title': 'Главная', 'link':'index'},
    {'title': 'Книги', 'link':'bookslist'},
    {'title': 'Авторы', 'link':'authors'},
    ]
ALLOWED_ORDERINGS = ['title', '-title', 'year', '-year', 'author__name']



class Index(BaseMixin, TemplateView):
    template_name = 'books/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_mixin_context(context)
        latest_books = Book.objects.filter(is_published=True).select_related('author').order_by('-id')[:6]   
        context['latest_books'] = latest_books
        return context
    

class OneBook(BaseMixin,DetailView):
    template_name = 'books/one_book.html'
    model = Book
    pk_url_kwarg = 'book_id'    
    def get_context_data(self, **kwargs):
        book = self.get_object()
        if not book.is_published and not self.request.user.has_perm('books.can_moderate_books'):
            raise Http404('Книга не найдена')
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = book.comments.all()
        return self.get_mixin_context(context)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authorization:login')
        person_profile = UserProfile.objects.filter(user=request.user).first() 
        book_object = self.get_object()
        action = request.POST.get('action')
        if action == 'toggle_favorite':
            if not person_profile.favourite_books.filter(id=book_object.id).exists():
                person_profile.favourite_books.add(book_object)

            else:
                person_profile.favourite_books.remove(book_object)

            person_profile.save()
        elif action == 'toggle_finished_read':
            if not person_profile.finished_books.filter(id=book_object.id).exists():
                person_profile.finished_books.add(book_object)

            else:
                person_profile.finished_books.remove(book_object)

            person_profile.save()
        elif action == 'add_comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.book = book_object
                comment.user = request.user
                comment.save()
        return redirect('bookByID', book_id=book_object.id)
        

     

class BooksList(BaseMixin,ListView):
    model = Book
    template_name = 'books/books.html'
    context_object_name = 'books'
    paginate_by = 9
    def get_queryset(self):
        books = Book.objects.select_related('author').filter(is_published=True)
        
        ordering = self.request.GET.get('sort')

        if ordering in ALLOWED_ORDERINGS:
            books = books.order_by(ordering)
        else:
            books = books.order_by('-id')
        
        author = self.request.GET.get('author')
        if author:
            books = books.filter(author__slug=author)
        
        year = self.request.GET.get('year')
        if year:
            try:
                year = int(year)
                if year <= 2026:
                    books = books.filter(year=year)
            except ValueError:
                pass
        
        genres = self.request.GET.get('genre')
        if genres:
            books = books.filter(genre__slug__in=genres.split('.'))
        
        form = SearchBookForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data['search']
            if search:
                books = books.filter(
                    Q(title__icontains=search) | Q(author__name__icontains=search)
                )

        return books


        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_mixin_context(context)
        context['search'] = SearchBookForm(self.request.GET or None)
        return context
    

def authorbyslug(request, author_slug):
    author = get_object_or_404(Author, slug=author_slug)

    #Prefetch + annotate на ManyToMany не работают нормально
    genre_counts = dict(
        Genre.objects.annotate(c=Count('books_with_genre', filter=Q(books_with_genre__is_published=True))).values_list('id', 'c')
    )
    books = author.books.prefetch_related('genre').filter(is_published=True)
    for book in books:
        for gen in book.genre.all():
            gen.books_count = genre_counts.get(gen.id, 0)


    data = {
        'SiteName': SiteName,
        'menu': menu,
        'author': author,
        'books': books,
    }
    return render(request, 'books/author.html', context=data)

def page_not_found(request, exception = None):
    return render(request, 'books/404.html', status=404)

def server_error(request, exception = None):
    return render(request, 'books/500.html', status=500)

def premission_denied(request, exception=None):
    return redirect('index')


class Authors(BaseMixin,ListView):
    model = Author
    template_name = "books/authors.html"
    context_object_name = 'authors'
    
    
    def get_queryset(self):
        return Author.objects.annotate(
            books_count=Count('books', filter=Q(books__is_published=True))
        ).order_by('-books_count')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_mixin_context(context)
        return context


class PostBook(LoginRequiredMixin, BaseMixin, CreateView):
    model = Book
    form_class = AddBookForm 
    template_name = 'books/postbook.html'
    success_url = reverse_lazy('index')
    
    def get_initial(self):
        initial = super().get_initial()
        initial['user'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_mixin_context(context)
        return context
    

def download_book(request, book_id):

    book = get_object_or_404(Book, id=book_id)
    if not book.is_published and not request.user.is_superuser :
        raise Http404('File not found')
    if not book.book_file:
        raise Http404('File not found')
    try:
        f = open(book.book_file.path, 'rb')
        return FileResponse(f, as_attachment=True, filename=book.book_file.name)
    except FileNotFoundError:
        raise Http404('File not found')
    except Exception:
        raise Http404('Something went wrong')
    

class ModerateBooks(PermissionRequiredMixin, ListView):
    model = Book
    template_name = 'books/moderate_book.html'
    context_object_name = 'books'
    paginate_by = 5
    permission_required = 'books.can_moderate_books'
    raise_exception = True   
    def get_queryset(self):
        books = Book.objects.filter(is_published = False).order_by('-id')
        return books
    def post(self, request, *args, **kwargs):
        book_id = request.POST.get('book_id')
        changed_publicating = get_object_or_404(Book, pk=book_id)
        if request.POST.get('action') == 'publicate':
            changed_publicating.is_published = True
            changed_publicating.save()
        elif request.POST.get('action') == 'delete':
            changed_publicating.delete()
        return redirect('moderate')

            
    
from books.utils import menu

def get_books_context(request):
    return {'menu' : menu}
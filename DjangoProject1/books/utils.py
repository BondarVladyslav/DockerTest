SiteName = 'Book4Read'
menu = [
    {'title': 'Главная', 'link':'index'},
    {'title': 'Книги', 'link':'bookslist'},
    {'title': 'Авторы', 'link':'authors'},
    {'title': 'Опубликовать', 'link':'post_book'},
    ]
class BaseMixin:
    def get_mixin_context(self, context, **kwargs):

        context['menu'] = menu
        context['SiteName'] = SiteName
        context.update(kwargs)
        return context
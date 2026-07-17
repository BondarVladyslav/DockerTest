from django import template
from books.views import menu
register = template.Library()


@register.simple_tag()
def get_menu_data():
    return menu

@register.simple_tag(takes_context=True)
def remove_param(context, key, url=None):
    request = context['request']
    updated = request.GET.copy()
    if key in updated:
        del updated[key]
    if url is not None:
        return url + f"?{updated.urlencode()}"
    return f"?{updated.urlencode()}"
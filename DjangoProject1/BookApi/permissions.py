from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('books.can_moderate_books')
    def has_object_permission(self, request, view, obj):
        if view.action == 'destroy':
            return not obj.is_published
        return True
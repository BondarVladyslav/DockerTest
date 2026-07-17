from django.urls import include, path   
from django.conf import settings
from django.conf.urls.static import static
from .views import *
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView, TokenVerifyView

app_name = 'api'
simple_router = routers.SimpleRouter()
simple_router.register('books', BookViewSet, basename='book')
simple_router.register('comments', CommentViewSet, basename='comment')
simple_router.register('authors', AuthorViewSet, basename='author')

urlpatterns = [
    path('', include(simple_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
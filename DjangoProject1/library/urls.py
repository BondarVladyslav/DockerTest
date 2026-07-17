"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from books.views import page_not_found, server_error, premission_denied
from debug_toolbar.toolbar import debug_toolbar_urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('books.urls')),
    path('auth/',include('authorization.urls', namespace='authorization')),
    path('api/',include('BookApi.urls', namespace='api')),

]+ debug_toolbar_urls()

handler404 = page_not_found
handler500 = server_error
handler403 = premission_denied


admin.site.site_header = 'Панель администратора'
admin.site.index_title = 'Библиотека'
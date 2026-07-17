from django.urls import path, reverse_lazy
from django.contrib.auth.views import LogoutView, PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from . import views
app_name = 'authorization'
urlpatterns = [
    path('login/', views.LoginUser.as_view(), name = 'login'),
    path('logout/', LogoutView.as_view(), name = 'logout'),
    path('register/', views.RegisterUser.as_view(), name = 'register'),


    path ('profile/<int:pk>/', views.UserProfileView.as_view(), name = 'user_profile'),
    path ('profile/', views.UserProfileView.as_view(), name = 'my_profile'),
    path('change-data/',
          views.UserChangeDataView.as_view(),
          name = 'change_data'),


    path('change-password/', 
         views.ChangePasswordView.as_view(),
         name = 'change_password'),


    path('password-reset/',
         PasswordResetView.as_view(template_name='authorization/password_reset_enter.html',
           email_template_name='authorization/password_reset_email.html',
           success_url=reverse_lazy('authorization:password_reset_done')),
         name = 'password_reset'),


    path('password-reset/done/',
          PasswordResetDoneView.as_view(
              template_name='authorization/password_reset_done.html',
          ), name = 'password_reset_done'),


    path('password-reset-confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='authorization/password_reset_confirm.html',
             success_url=reverse_lazy('authorization:password_reset_complete'),
         ),
         name='password_reset_confirm'),


    path('password-reset-complete/',
         PasswordResetCompleteView.as_view(
             template_name='authorization/password_reset_complete.html'),
          name = 'password_reset_complete'),
    ]
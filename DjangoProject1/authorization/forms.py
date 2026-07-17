from django import forms
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from authorization.models import UserProfile


class LoginForm(AuthenticationForm):
    username =  forms.CharField(label='Логин', widget=forms.TextInput())
    password =  forms.CharField(label='Пароль', widget=forms.PasswordInput())





class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput())
    password1 = forms.CharField(label='Пароль',widget=forms.PasswordInput())
    password2 = forms.CharField(label='Пароль',widget=forms.PasswordInput())
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2']
        labels={
            'email':"почта",
            'password1':'пароль',
            'password2':'Повторите пароль',
        }
    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError('Email занят')
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()

        return user
    

class UserProfileChangeData(forms.ModelForm):
    username = forms.CharField(disabled=True, widget=forms.TextInput())
    email = forms.CharField(disabled=True, widget=forms.TextInput())
    bio = forms.CharField(label='О себе', required=False, widget=forms.Textarea(attrs={'rows': 4}))
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'bio']


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(label='Старый пароль', widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='Повторите новый пароль', widget=forms.PasswordInput())
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from authorization.models import UserProfile
from .forms import ChangePasswordForm, LoginForm, RegisterForm, UserProfileChangeData






class LoginUser(LoginView):
    form_class = LoginForm
    template_name = "authorization/login.html"

class RegisterUser(CreateView):
    form_class = RegisterForm
    template_name = 'authorization/register.html'
    success_url = reverse_lazy('authorization:login')


class UserChangeDataView(LoginRequiredMixin,UpdateView):
    model = get_user_model()
    form_class = UserProfileChangeData
    template_name = 'authorization/change_my_data.html'
    def get_success_url(self):
        return reverse_lazy('authorization:change_data')
    
    def get_object(self, queryset=None):
        return self.request.user
    def form_valid(self, form):
        response = super().form_valid(form)
        bio = form.cleaned_data.get('bio')
        if bio is not None:
            profile = UserProfile.objects.get(user=self.object)
            profile.bio = bio
            profile.save()
        return response
    
    def get_initial(self):
        initial = super().get_initial()
        profile = UserProfile.objects.get(user=self.request.user)
        initial['bio'] = profile.bio
        return initial

class UserProfileView(TemplateView):
    template_name = 'authorization/profile.html'

    def get(self, request, *args, **kwargs):
        if 'pk' not in kwargs and not request.user.is_authenticated:
            return redirect('authorization:login')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'pk' in kwargs:
            user = get_object_or_404(get_user_model(), pk=kwargs['pk'])
        else:
            user = self.request.user

        context['favourite_books'] = user.additional_data.favourite_books.all()
        context['finished_books'] = user.additional_data.finished_books.all()
        context['bio'] = user.additional_data.bio
        context['username'] = user.username
        context['profile_pk'] = user.pk
        return context


class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'authorization/change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('authorization:change_data')

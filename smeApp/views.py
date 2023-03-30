from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomUserForm
from django.contrib.auth.views import LoginView, LogoutView
from .models import CustomUser, Job
# from django.views import View

# Create your views here.
class IndexView(TemplateView):
    template_name = "base.html"

class DashboardView(TemplateView):
    template_name = "dashboard.html"

from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        email = form.cleaned_data.get('email')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(email=email, password=raw_password)
        login(self.request, user)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['navbarTopStyle'] = 'darker'
        context['navbarVerticalStyle'] = 'darker'
        return context


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('smeApp:index')

    def form_valid(self, form):
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(reverse('smeApp:index'))
        else:
            messages.error(self.request, 'Invalid email or password.')
            return super().form_invalid(form)

class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'
    context_object_name = 'jobs'

class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

class JobCreateView(CreateView):
    model = Job
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')
    fields = '__all__'


class JobUpdateView(UpdateView):
    model = Job
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')
    fields = '__all__'


class JobDeleteView(DeleteView):
    model = Job
    template_name = 'job_confirm_delete.html'
    success_url = reverse_lazy('smeApp:job_list')

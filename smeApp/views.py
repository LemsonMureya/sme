from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login
from django.views.generic import CreateView
from django.utils import timezone
from django.db.models.functions import TruncMonth
import datetime
from datetime import datetime, timedelta
import requests
import tempfile
from django.db.models import Q
from .forms import (CustomUserCreationForm, CustomUserForm, ExpenseForm, ProductTypeForm,
                    IncomeForm, JobForm, JobItemForm, ClientForm, CompanyProfileForm, InvoiceForm,
                    InvoiceItemForm, NoteForm, ReceiptUploadForm, CustomUserEditForm,
                    AvatarUpdateForm, PurchaseOrderItemForm, SaleForm, SaleItemForm,  BasePurchaseOrderItemFormSet,
                    SupplierForm, StockItemForm, PurchaseOrderForm, BaseSaleItemFormSet)
from django.contrib.auth.views import LoginView, LogoutView
from .models import (CustomUser, Job, JobItem, Client, Expense, Income, CompanyProfile, ProductType,
                    Invoice, InvoiceItem, Note, Supplier, StockItem, PurchaseOrder,
                    PurchaseOrderItem, Sale, SaleItem)
from django.db.models import Sum, F
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.dates import (
    YearMixin, MonthMixin, WeekMixin,
    DayMixin, DateMixin, _date_from_string
)
from django.forms import formset_factory, inlineformset_factory
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.units import inch
from decimal import Decimal
from .utils import get_thumbnail_url, render_to_pdf
from django.views.generic.edit import FormView
from django.core.files.storage import FileSystemStorage
from PIL import Image
import re
from urllib.parse import urlencode
from pprint import pprint
from mindee import Client as MindeeClient, documents
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import os
from django.conf import settings
from django.core.files import File
from django.contrib import messages
from django.core.files.base import ContentFile
from django.template.loader import get_template
from weasyprint import HTML
from formtools.wizard.views import SessionWizardView
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist


class IndexView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['GA_MEASUREMENT_ID'] = settings.GA_MEASUREMENT_ID
        return context

class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_count'] = Job.objects.filter(company=self.request.user.company).count()
        context['client_count'] = Client.objects.filter(company=self.request.user.company).count()
        context['invoice_count'] = Invoice.objects.filter(company=self.request.user.company).count()
        context['expense_count'] = Expense.objects.filter(company=self.request.user.company).count()
        context['google_maps_key'] = settings.GOOGLE_MAPS_API_KEY
        context['GA_MEASUREMENT_ID'] = settings.GA_MEASUREMENT_ID
        return context

@login_required
def jobs_to_json(request):
    jobs = Job.objects.filter(company=request.user.company)
    job_list = []
    for job in jobs:
        start = job.start_date.isoformat() if job.start_date else None
        end = job.end_date.isoformat() if job.end_date else None
        job_list.append({
            'id': job.id,
            'title': job.description,
            'start': start,
            'end': end,
            'color': '#F0E68C',  # Here you can specify the color for this event
            'className': 'text-success'
        })
    return JsonResponse(job_list, safe=False)

def calculate_net_profit(company, start_date=None):
    if start_date:
        expenses = Expense.objects.filter(company=company, date_created__gte=start_date).aggregate(sum=Sum('amount'))['sum'] or 0
        invoices = Invoice.objects.filter(company=company, invoice_date__gte=start_date)
        jobs = Job.objects.filter(company=company, revenue_recorded=True, created_at__date__gte=start_date)
    else:
        expenses = Expense.objects.filter(company=company).aggregate(sum=Sum('amount'))['sum'] or 0
        invoices = Invoice.objects.filter(company=company)
        jobs = Job.objects.filter(company=company, revenue_recorded=True)

    incomes = sum(invoice.get_total_amount() for invoice in invoices)

    for job in jobs:
        try:
            # Check if an invoice associated with the job exists
            job.invoices
        except ObjectDoesNotExist:
            # If it doesn't exist, add job total cost to the incomes
            incomes += job.total_cost

    return incomes - expenses

class MainDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main_dashboard.html'

    def get(self, request):
        user_company = request.user.company
        time_filter = request.GET.get('time_filter', 'all')

        if time_filter == 'today':
            start_date = timezone.now().date()
        elif time_filter == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
        elif time_filter == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
        elif time_filter == '6 months':
            start_date = timezone.now().date() - timedelta(days=182)
        elif time_filter == 'year':
            start_date = timezone.now().date() - timedelta(days=365)
        else:  # 'all' or any other unexpected value
            start_date = None

        if start_date:
            jobs = Job.objects.filter(company=user_company, created_at__date__gte=start_date)
            expenses = Expense.objects.filter(company=user_company, date_created__gte=start_date)
            invoices = Invoice.objects.filter(company=user_company, invoice_date__gte=start_date)
        else:
            jobs = Job.objects.filter(company=user_company)
            expenses = Expense.objects.filter(company=user_company)
            invoices = Invoice.objects.filter(company=user_company)

        total_revenue = sum(invoice.get_total_amount() for invoice in invoices)
        for job in jobs.filter(revenue_recorded=True):
            try:
                # Check if an invoice associated with the job exists
                job.invoices
            except ObjectDoesNotExist:
                # If it doesn't exist, add job total cost to the total revenue
                total_revenue += job.total_cost

        total_expenses = expenses.aggregate(sum=Sum('amount'))['sum'] or 0

        context = {
            'company': user_company,
            'total_expenses': total_expenses,
            'total_revenue': total_revenue,
            'clients': Client.objects.filter(company=user_company),
            'jobs': jobs,
            'expenses': expenses,
            'net_profit': calculate_net_profit(user_company, start_date),
        }

        return render(request, self.template_name, context)

class RegisterView(View):
    template_name = 'registration/register_wizard.html'

    def get(self, request):
        user_form = CustomUserCreationForm()
        company_form = CompanyProfileForm()
        context = {
            'user_form': user_form,
            'company_form': company_form,
            'navbarTopStyle': 'darker',
            'navbarVerticalStyle': 'darker',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        print(request.POST)  # output form data
        print(request.FILES)  # output uploaded files
        user_data = request.POST.copy()
        user_data['email'] = request.POST.get('user_email')

        company_data = request.POST.copy()
        company_data['email'] = request.POST.get('company_email')

        user_form = CustomUserCreationForm(user_data)
        company_form = CompanyProfileForm(company_data, request.FILES)

        if user_form.is_valid() and company_form.is_valid():
            print(company_form.cleaned_data)  # output cleaned form data
            user = user_form.save(commit=False)
            company = company_form.save()
            user.company = company
            user.save()
            login(request, user)
            return redirect(reverse_lazy('smeApp:main_dashboard'))

        context = {
            'user_form': user_form,
            'company_form': company_form,
            'navbarTopStyle': 'darker',
            'navbarVerticalStyle': 'darker',
        }

        return render(request, self.template_name, context)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('smeApp:main_dashboard')

    def form_valid(self, form):
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(reverse('smeApp:main_dashboard'))
        else:
            messages.error(self.request, 'Invalid email or password.')
            return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    next_page = 'smeApp:index'

class UserProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'profile/user_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomUserForm(instance=self.request.user)
        if self.request.user.company:
            context['company_form'] = CompanyProfileForm(instance=self.request.user.company)
        else:
            context['company_form'] = CompanyProfileForm()
        return context

class EditAvatarView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        remove_photo = request.POST.get("remove_photo") == "true"
        form = AvatarUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            user = form.save(commit=False)
            if remove_photo:
                if user.photo:
                    user.photo.delete(save=False)
                    user.photo = None
            elif request.FILES.get("photo"):
                user.photo.save(f"{user.email}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg", ContentFile(request.FILES["photo"].read()))
            user.save()

            if request.is_ajax():
                return JsonResponse({"success": True})
            else:
                messages.success(request, 'Avatar updated successfully.')
                return redirect('smeApp:user_profile')
        else:

            if request.is_ajax():
                return JsonResponse({"success": False, "errors": form.errors})
            else:
                messages.error(request, 'Error updating avatar.')
                return redirect('smeApp:user_profile')


class UserProfileUpdateView(LoginRequiredMixin, View):
    template_name = 'profile/user_profile.html'
    success_url = reverse_lazy('smeApp:user_profile')

    def get(self, request, *args, **kwargs):
        context = {}
        context['form'] = CustomUserForm(instance=self.request.user)
        if self.request.user.company:
            context['company_form'] = CompanyProfileForm(instance=self.request.user.company)
        else:
            context['company_form'] = CompanyProfileForm()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        remove_photo = request.POST.get("remove_photo") == "true"
        user_form = CustomUserForm(request.POST, request.FILES, instance=self.request.user)
        if self.request.user.company:
            company_form = CompanyProfileForm(request.POST, request.FILES, instance=self.request.user.company)
        else:
            company_form = CompanyProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and company_form.is_valid():
            user = user_form.save(commit=False)
            if remove_photo:
                if user.photo:
                    user.photo.delete(save=False)
                    user.photo = None
            elif request.FILES.get("photo"):
                user.photo.save(f"{user.email}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg", ContentFile(request.FILES["photo"].read()))
            user.save()
            company = company_form.save(commit=False)
            company.save()
            user.company = company
            user.save()
            return redirect(self.success_url)

        context = {'form': user_form, 'company_form': company_form}
        return render(request, self.template_name, context)

class UserProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'profile/delete_profile.html'
    success_url = reverse_lazy('smeApp:index')

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(request, f"{user.email}'s account has been deleted.")
        return super().delete(request, *args, **kwargs)

# CompanyProfile views
class CompanyProfileDetailView(LoginRequiredMixin, DetailView):
    model = CompanyProfile
    template_name = 'profile/company_profile_detail.html'

    def get_object(self, queryset=None):
        return self.request.user.company

class CompanyProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CompanyProfile
    form_class = CompanyProfileForm
    template_name = 'profile/company_profile_update.html'

    def get_object(self, queryset=None):
        return self.request.user.company

    def get_success_url(self):
        return reverse('smeApp:company_profile_detail')

class CompanyProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = CompanyProfile
    template_name = 'profile/company_profile_delete.html'

    def get_object(self, queryset=None):
        return self.request.user.company

    def get_success_url(self):
        return reverse('smeApp:index')

    def delete(self, request, *args, **kwargs):
        company = self.get_object()
        messages.success(request, f"{company.name}'s profile has been deleted.")
        return super().delete(request, *args, **kwargs)

class CompanyProfileCreateView(LoginRequiredMixin, CreateView):
    model = CompanyProfile
    form_class = CompanyProfileForm
    template_name = 'registration/create_company_profile.html'
    success_url = reverse_lazy('smeApp:job_list')

    def form_valid(self, form):
        company_profile = form.save(commit=False)
        company_profile.save()
        # Associate the company profile with the logged-in user
        user = self.request.user
        user.company = company_profile
        user.save()

        return super().form_valid(form)

class ClientsListView(LoginRequiredMixin, View): #client list from modal form
    def get(self, request, *args, **kwargs):
        user_company = request.user.company
        clients = Client.objects.filter(company=user_company).values('id', 'name')
        return JsonResponse(list(clients), safe=False)

@csrf_exempt
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            new_client = form.save(commit=False)
            new_client.company = request.user.company
            new_client.save()
            return JsonResponse({"id": new_client.id, "name": new_client.name})
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)

class ClientsList(LoginRequiredMixin, TemplateView):
    model = Client
    template_name = 'client_list.html'

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.filter(company=user.company)
        role = self.request.GET.get('role')
        create_date = self.request.GET.get('create_date')

        if role:
            queryset = queryset.filter(role=role)

        if create_date == 'today':
            queryset = queryset.filter(created_at=timezone.now().date())
        elif create_date == 'last7Days':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=7))
        elif create_date == 'last30Days':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=30))
        elif create_date == 'last6Months':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=182))
        elif create_date == 'lastYear':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=365))
        elif create_date == 'all':
            queryset = queryset

        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(address__icontains=search_term) |
                Q(contact_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone__icontains=search_term) |
                Q(role__icontains=search_term)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ClientForm()
        context['clients'] = self.get_queryset()
        context['role_choices'] = Client.ROLE_CHOICES
        return context

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'client_form.html'
    success_url = reverse_lazy('smeApp:client_list')

    def form_valid(self, form):
        client = form.save(commit=False)
        client.company = self.request.user.company
        client.save()
        return HttpResponseRedirect(self.success_url)

class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'client_detail.html'

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(company=user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client = self.object
        context['jobs'] = Job.objects.filter(client=client)
        context['invoices'] = Invoice.objects.filter(client=client)

        total_revenue = sum(job.total_cost for job in context['jobs'] if job.total_cost is not None)
        total_jobs = context['jobs'].count()
        total_invoices = context['invoices'].count()
        average_job_cost = total_revenue / total_jobs if total_jobs else 0

        context['total_revenue'] = total_revenue
        context['average_job_cost'] = average_job_cost
        context['total_jobs'] = total_jobs
        context['total_invoices'] = total_invoices

        return context

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'client_form.html'
    success_url = reverse_lazy('smeApp:client_list')

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(company=user.company)

    def form_valid(self, form):
        client = form.save(commit=False)
        client.company = self.request.user.company
        client.save()
        return HttpResponseRedirect(self.success_url)

class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'client_confirm_delete.html'
    success_url = reverse_lazy('smeApp:client_list')

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(company=user.company)

    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        client.delete()
        return HttpResponseRedirect(self.success_url)

#formset rendered though this view too
class JobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'job_list.html'

    def get_queryset(self):
        queryset = Job.objects.filter(company=self.request.user.company)
        status = self.request.GET.get('status')
        search_term = self.request.GET.get('q', '')
        payment_type = self.request.GET.get('payment_type')
        create_date = self.request.GET.get('start_date')

        if status:
            queryset = queryset.filter(status=status)

        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)

        if create_date == 'today':
            queryset = queryset.filter(start_date=timezone.now().date())
        elif create_date == 'last7Days':
            queryset = queryset.filter(start_date__gte=timezone.now().date() - timedelta(days=7))
        elif create_date == 'last30Days':
            queryset = queryset.filter(start_date__gte=timezone.now().date() - timedelta(days=30))
        elif create_date == 'last6Months':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=182))
        elif create_date == 'lastYear':
            queryset = queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=365))
        elif create_date == 'all':
            queryset = queryset

        if search_term:
            queryset = queryset.filter(
                Q(client__name__icontains=search_term) |
                Q(po_number__icontains=search_term) |
                Q(status__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(notes__text__icontains=search_term) |
                Q(payment_status__icontains=search_term) |
                Q(payment_type__icontains=search_term) |
                Q(assigned_worker__icontains=search_term) |
                Q(jobitem__item_name__icontains=search_term) |
                Q(jobitem__item_description__icontains=search_term)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        context['form'] = JobForm(user=self.request.user)
        context['formset'] = formset_factory(JobItemForm, extra=1)(prefix='jobitem_set')
        context['status_choices'] = Job.STATUS_CHOICES
        context['payment_type_choices'] = Job.PAYMENT_TYPE_CHOICES
        return context

class JobDetailView(LoginRequiredMixin, DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        user = self.request.user
        return Job.objects.filter(company=user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = JobForm(instance=self.object)
        JobItemFormSet = inlineformset_factory(Job, JobItem, form=JobItemForm, extra=0)
        context['formset'] = JobItemFormSet(instance=self.object)
        context['notes'] = Note.objects.filter(related_object=self.object, related_object__company=self.request.user.company)
        return context

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'job_list.html'
    success_url = reverse_lazy('smeApp:job_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = formset_factory(JobItemForm, extra=1)(self.request.POST, prefix='jobitem_set')
        else:
            context['formset'] = formset_factory(JobItemForm, extra=1)(prefix='jobitem_set')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        job = form.save(commit=False)
        job.company = self.request.user.company
        job.save()

        if formset.is_valid():
            for item_form in formset:
                job_item = item_form.save(commit=False)
                job_item.job = job
                job_item.save()
            job.total_cost = job.calculate_total_cost()
            job.save()
        else:
            return self.form_invalid(form)

        return HttpResponseRedirect(self.success_url)

class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'job_edit.html'
    success_url = reverse_lazy('smeApp:job_list')

    def get_queryset(self):
        user = self.request.user
        return Job.objects.filter(company=user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        JobItemFormSet = formset_factory(JobItemForm, extra=0)
        if self.request.method == 'POST':
            context['formset'] = JobItemFormSet(self.request.POST, prefix='jobitem_set')
        else:
            initial_data = [{'item_name': job_item.item_name, 'item_description': job_item.item_description, 'quantity': job_item.quantity, 'unit_price': job_item.unit_price} for job_item in JobItem.objects.filter(job=self.object)]
            context['formset'] = JobItemFormSet(initial=initial_data, prefix='jobitem_set')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        job = form.save(commit=False)
        job.company = self.request.user.company

        if form.is_valid() and formset.is_valid():
            job.save()

            # Keep track of formset data
            formset_data = []
            for item_form in formset:
                if item_form.cleaned_data:
                    formset_data.append(item_form.cleaned_data)

            # Delete JobItems that were removed in the formset
            for job_item in job.jobitem_set.all():
                if not any(d['item_name'] == job_item.item_name and d['item_description'] == job_item.item_description for d in formset_data):
                    job_item.delete()

            # Update and Create JobItems
            for index, item_form in enumerate(formset):
                if item_form.cleaned_data:
                    if index < len(job.jobitem_set.all()):
                        # Update existing JobItem
                        job_item = job.jobitem_set.all()[index]
                        job_item.item_name = item_form.cleaned_data['item_name']
                        job_item.item_description = item_form.cleaned_data['item_description']
                        job_item.quantity = item_form.cleaned_data['quantity']
                        job_item.unit_price = item_form.cleaned_data['unit_price']
                        job_item.save()
                    else:
                        # Create new JobItem
                        job_item = JobItem(job=job)
                        job_item.item_name = item_form.cleaned_data['item_name']
                        job_item.item_description = item_form.cleaned_data['item_description']
                        job_item.quantity = item_form.cleaned_data['quantity']
                        job_item.unit_price = item_form.cleaned_data['unit_price']
                        job_item.save()
            job.total_cost = job.calculate_total_cost()
            job.save()
        else:
            return self.form_invalid(form)

        return HttpResponseRedirect(self.success_url)

class JobDeleteView(LoginRequiredMixin, DeleteView):
    model = Job
    template_name = 'job_confirm_delete.html'
    success_url = reverse_lazy('smeApp:job_list')

    def get_queryset(self):
        user = self.request.user
        return Job.objects.filter(company=user.company)

    def delete(self, request, *args, **kwargs):
        job = self.get_object()
        job.delete()
        return HttpResponseRedirect(self.success_url)

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        queryset = Invoice.objects.filter(company=self.request.user.company)

        # Handle the due date filter
        due_date_option = self.request.GET.get('due_date', 'all')
        if due_date_option == 'today':
            queryset = queryset.filter(due_date=datetime.now().date())
        elif due_date_option == 'last7Days':
            queryset = queryset.filter(due_date__gte=datetime.now().date()-timedelta(days=7))
        elif due_date_option == 'last30Days':
            queryset = queryset.filter(due_date__gte=datetime.now().date()-timedelta(days=30))
        elif due_date_option == 'last6Months':
            queryset = queryset.filter(due_date__gte=datetime.now().date()-timedelta(days=6*30))
        elif due_date_option == 'lastYear':
            queryset = queryset.filter(due_date__gte=datetime.now().date()-timedelta(days=365))

        return queryset

        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_term) |
                Q(client__name__icontains=search_term) |
                Q(job__po_number__icontains=search_term) |
                Q(payment_status__icontains=search_term) |
                Q(invoiceitem__item_name__icontains=search_term) |
                Q(invoiceitem__item_description__icontains=search_term)
            ).distinct()

        payment_status = self.request.GET.get('payment_status', '')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_form'] = InvoiceForm(user=self.request.user)
        InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1)
        context['invoice_item_formset'] = InvoiceItemFormSet(prefix='invoiceitem_set')
        context['payment_status_choices'] = Invoice.PAYMENT_STATUS_CHOICES
        return context

InvoiceItemFormSet = inlineformset_factory(Invoice, InvoiceItem, form=InvoiceItemForm, fields=('item_name', 'item_description', 'quantity', 'unit_price'), extra=0,can_delete=False)

class UpdateInvoiceView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'update_invoice.html'

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse_lazy('smeApp:view_invoice', kwargs={'invoice_id': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            data['formset'] = InvoiceItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        invoice = form.save(commit=False)
        invoice.company = self.request.user.company

        if form.is_valid() and formset.is_valid():
            invoice.save()
            # Keep track of formset data
            formset_data = []
            for item_form in formset:
                if item_form.cleaned_data:
                    formset_data.append(item_form.cleaned_data)

            # Delete InvoiceItems that were removed in the formset
            for invoice_item in invoice.invoiceitem_set.all():
                if not any(d['item_name'] == invoice_item.item_name and d['item_description'] == invoice_item.item_description for d in formset_data):
                    invoice_item.delete()

            # Update and Create InvoiceItems
            for index, item_form in enumerate(formset):
                if item_form.cleaned_data:
                    if index < len(invoice.invoiceitem_set.all()):
                        # Update existing InvoiceItem
                        invoice_item = invoice.invoiceitem_set.all()[index]
                        invoice_item.item_name = item_form.cleaned_data['item_name']
                        invoice_item.item_description = item_form.cleaned_data['item_description']
                        invoice_item.quantity = item_form.cleaned_data['quantity']
                        invoice_item.unit_price = item_form.cleaned_data['unit_price']
                        invoice_item.save()
                    else:
                        # Create new InvoiceItem
                        invoice_item = InvoiceItem(invoice=invoice)
                        invoice_item.item_name = item_form.cleaned_data['item_name']
                        invoice_item.item_description = item_form.cleaned_data['item_description']
                        invoice_item.quantity = item_form.cleaned_data['quantity']
                        invoice_item.unit_price = item_form.cleaned_data['unit_price']
                        invoice_item.save()
            invoice.total = invoice.get_total_amount()
            invoice.save()
        else:
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

class DeleteInvoiceView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'delete_invoice.html'
    success_url = reverse_lazy('smeApp:invoices_list')

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

class CreateJobInvoiceView(LoginRequiredMixin, View):
    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id, company=request.user.company)
        invoice, created = Invoice.objects.get_or_create(job=job, defaults={
            'company': job.company,
            'client': job.client,
            # pad the invoice number with zeros, so it's always at least 4 digits
            'invoice_number': "{:04d}".format(Invoice.objects.filter(company=request.user.company).count() + 1),
            'invoice_date': job.created_at,
            'due_date': job.created_at + timedelta(days=30),
            'payment_status': job.payment_status,
            'tax': 0,
            'discount': 0,
        })
        if not created:
            # If an invoice for the job already exists, redirect to the existing invoice
            return redirect('smeApp:view_invoice', invoice_id=invoice.id)

        # no invoice exists for this job, we just created a new one
        job.total_cost = job.calculate_total_cost()
        job.save()

        for item in job.jobitem_set.all():
            invoice_item_data = {
                'invoice': invoice,  # Use the invoice instance after saving it
                'item_name': item.item_name,
                'item_description': item.item_description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
            }
            invoice_item_form = InvoiceItemForm(data=invoice_item_data)

            if invoice_item_form.is_valid():
                invoice_item = invoice_item_form.save(commit=False)
                invoice_item.invoice = invoice
                invoice_item.save()
            else:
                return HttpResponse("An error occurred while creating the invoice items. Please try again.")
        return redirect('smeApp:view_invoice', invoice_id=invoice.id)

class CreateInvoiceView(LoginRequiredMixin, View):
    def get(self, request):
        invoice_form = InvoiceForm(user=request.user)
        InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1)
        formset = InvoiceItemFormSet(prefix='invoiceitem_set')
        return render(request, 'create_invoice.html', {'invoice_form': invoice_form, 'invoice_item_formset': formset})

    def post(self, request):
        invoice_form = InvoiceForm(request.POST, user=request.user)
        InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1)
        formset = InvoiceItemFormSet(request.POST, prefix='invoiceitem_set')

        if invoice_form.is_valid() and formset.is_valid():
            invoice = invoice_form.save(commit=False)
            invoice.company = request.user.company
            invoice.save()
            for form in formset:
                if form.cleaned_data:
                    invoice_item = form.save(commit=False)
                    invoice_item.invoice = invoice
                    invoice_item.save()
            return redirect('smeApp:view_invoice', invoice_id=invoice.id)
        else:
            return render(request, 'create_invoice.html', {'invoice_form': invoice_form, 'invoice_item_formset': formset})

class ViewInvoiceView(View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id, company=request.user.company)
        invoice_items = invoice.invoiceitem_set.all().annotate(total=F('quantity') * F('unit_price'))
        # Calculate the subtotal
        subtotal = sum(item.total for item in invoice_items)

        context = {
            'invoice': invoice,
            'invoice_items': invoice_items,
            'subtotal': subtotal,
            'total': invoice.get_total_amount(),
            'color_accent': invoice.color_accent
        }
        return render(request, 'view_invoice.html', context)

    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id, company=request.user.company)

        if 'download_pdf' in request.POST:
            invoice_items = invoice.invoiceitem_set.all().annotate(total=F('quantity') * F('unit_price'))
            subtotal = sum(item.total for item in invoice_items)

            context = {
                'invoice': invoice,
                'invoice_items': invoice_items,
                'subtotal': subtotal,
                'total': invoice.get_total_amount(),
                'MEDIA_URL': request.build_absolute_uri(settings.MEDIA_URL),
            }

            # Render the 'invoice_pdf.html' template with the given context
            template = get_template('invoice_pdf.html')
            html_string = template.render(context)

            # Convert the HTML string to a PDF using WeasyPrint
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
            pdf_content = html.write_pdf()

            # Create a ContentFile with the PDF data
            pdf_file = ContentFile(pdf_content)

            # Return the PDF as a file response
            return FileResponse(pdf_file, content_type='application/pdf', as_attachment=True, filename=f"Invoice-{invoice_id}.pdf")
        else:
            return JsonResponse({"error": "Invalid request"})

class PreviewInvoiceView(View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id, company=request.user.company)
        invoice_items = invoice.invoiceitem_set.all().annotate(total=F('quantity') * F('unit_price'))
        subtotal = sum(item.total for item in invoice_items)

        context = {
            'invoice': invoice,
            'invoice_items': invoice_items,
            'subtotal': subtotal,
            'total': invoice.get_total_amount(),
            'MEDIA_URL': request.build_absolute_uri(settings.MEDIA_URL),
        }
        return render(request, 'invoice_pdf.html', context)

def get_attachment_icon(file_url):
    if file_url:
        file_ext = file_url.split('.')[-1].lower()
        if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            return 'fa-image'
        # Add more file types and their respective icons if needed
    return None

class AddJobNoteView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm

    def form_valid(self, form):
        note = form.save(commit=False)
        note.related_object_id = self.kwargs['pk']
        note.author = self.request.user

        # Check if both text and attachment fields are empty
        if not note.text and not note.attachment:
            form.add_error(None, "Please enter a note or select an attachment.")
            return self.form_invalid(form)
        note.save()

        note_data = {
                'text': note.text,
                'author_name': f"{note.author.first_name} {note.author.last_name}" if (note.author.first_name and note.author.last_name) else note.author.username,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'attachment_icon': get_attachment_icon(note.attachment.url) if note.attachment else None,
                'attachment_url': note.attachment.url if note.attachment else None,
            }

        if note.attachment:
            note_data['attachment_url'] = note.attachment.url
            note_data['attachment_thumbnail_url'] = get_thumbnail_url(note.attachment.url)  # Function to be implemented
        else:
            note_data['attachment_url'] = None
            note_data['attachment_thumbnail_url'] = None
        return JsonResponse({'status': 'ok', 'note': note_data})

    def form_invalid(self, form):
        # Pass the form back to the template to display the errors
        return JsonResponse({'status': 'error', 'errors': form.errors})

class GetNoteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        note_id = self.kwargs['pk']
        note = get_object_or_404(Note, pk=note_id)
        note_data = {
            'text': note.text,
            'author_name': f"{note.author.first_name} {note.author.last_name}" if (note.author.first_name and note.author.last_name) else note.author.username,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'attachment_icon': get_attachment_icon(note.attachment.url) if note.attachment else None,
            'attachment_url': note.attachment.url if note.attachment else None,
        }

        return JsonResponse({'status': 'ok', 'note': note_data})

class UpdateNoteView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm

    def form_valid(self, form):
        note = form.save(commit=False)
        note.author = self.request.user
        note.save()
        # Return the updated note data as JSON
        return JsonResponse({'status': 'ok', 'note_id': note.pk, 'text': note.text, 'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M:%S')})

    def form_invalid(self, form):
        # Pass the form back to the template to display the errors
        return JsonResponse({'status': 'error', 'errors': form.errors})

class DeleteNoteView(LoginRequiredMixin, DeleteView):
    model = Note

    def delete(self, request, *args, **kwargs):
        note = self.get_object()
        note.delete()
        return JsonResponse({'status': 'ok'})

class ProfitLossDataView(LoginRequiredMixin, View):
    @csrf_exempt
    def get(self, request):
        time_filter = request.GET.get('time_filter', 'all')

        if time_filter == '12_months':
            start_date = timezone.now().date() - datetime.timedelta(days=365)
        elif time_filter == '24_months':
            start_date = timezone.now().date() - datetime.timedelta(days=730)
        else:
            start_date = None

        if start_date:
            expenses = Expense.objects.filter(date_created__gte=start_date, company=request.user.company)
            incomes = Income.objects.filter(date_created__gte=start_date, company=request.user.company)
        else:
            expenses = Expense.objects.filter(company=request.user.company)
            incomes = Income.objects.filter(company=request.user.company)

        expenses_data = expenses.annotate(month=TruncMonth('date_created')).values('month').annotate(total_amount=Sum('amount'))
        incomes_data = incomes.annotate(month=TruncMonth('date_created')).values('month').annotate(total_amount=Sum('amount'))
        return JsonResponse({'expenses': list(expenses_data), 'incomes': list(incomes_data)}, safe=False)

class AddIncomeView(LoginRequiredMixin, View):
    def get(self, request):
        form = IncomeForm()
        return render(request, 'add_income.html', {'form': form})

    def post(self, request):
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            income = form.save(commit=False)
            income.company = request.user.company
            income.save()
            return redirect('smeApp:transactions')
        return render(request, 'add_income.html', {'form': form})

class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = Income
    template_name = 'income_confirm_delete.html'

    def get_queryset(self):
        return Income.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:transactions')

class IncomeUpdateView(LoginRequiredMixin, UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = 'add_income.html'

    def get_queryset(self):
        return Income.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:transactions')

class TransactionsView(LoginRequiredMixin, View):
    def get(self, request):
        expenses = Expense.objects.filter(company=request.user.company)
        incomes = Income.objects.filter(company=request.user.company)
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        total_incomes = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
        profit_loss = total_incomes - total_expenses
        context = {
            'expenses': expenses,
            'incomes': incomes,
            'total_expenses': total_expenses,
            'total_incomes': total_incomes,
            'profit_loss': profit_loss,
        }
        return render(request, 'transactions.html', context)

class ExpensesDataView(LoginRequiredMixin, View):
    @csrf_exempt
    def get(self, request):
        time_filter = request.GET.get('time_filter', 'all')
        if time_filter == 'day':
            start_date = timezone.now().date()
        elif time_filter == 'month':
            start_date = timezone.now().date().replace(day=1)
        elif time_filter == 'year':
            start_date = timezone.now().date().replace(day=1, month=1)
        else:
            start_date = None

        if start_date:
            expenses = Expense.objects.filter(date_created__gte=start_date, company=request.user.company)
        else:
            expenses = Expense.objects.filter(company=request.user.company)

        expenses_data = expenses.values('category').annotate(total_amount=Sum('amount'))
        return JsonResponse(list(expenses_data), safe=False)

class ExpenseListView(LoginRequiredMixin, View):
    def get(self, request):
        time_filter = request.GET.get('time_filter', 'all')
        date_range = request.GET.get('date_range', 'all')
        category_filter = request.GET.get('category_filter', 'all')
        search_term = request.GET.get('q', '')

        if time_filter == 'day':
            start_date = timezone.now().date()
        elif time_filter == 'month':
            start_date = timezone.now().date().replace(day=1)
        elif time_filter == 'year':
            start_date = timezone.now().date().replace(day=1, month=1)
        else:
            start_date = None

        if date_range == 'today':
            range_start_date = timezone.now().date()
        elif date_range == 'last7Days':
            range_start_date = timezone.now().date() - timedelta(days=7)
        elif date_range == 'last30Days':
            range_start_date = timezone.now().date() - timedelta(days=30)
        elif date_range == 'last6Months':
            range_start_date = timezone.now().date() - timedelta(days=182)
        elif date_range == 'lastYear':
            range_start_date = timezone.now().date() - timedelta(days=365)
        elif date_range == 'all':
            range_start_date = None

        expenses = Expense.objects.filter(company=request.user.company)

        if start_date:
            expenses = expenses.filter(date_created__gte=start_date)

        if range_start_date:
            expenses = expenses.filter(date_created__gte=range_start_date)

        if category_filter != 'all':
            expenses = expenses.filter(category=category_filter)

        if search_term:
            expenses = expenses.filter(
                Q(description__icontains=search_term) |
                Q(notes__icontains=search_term) |
                Q(vendor__icontains=search_term) |
                Q(category__icontains=search_term) |
                Q(amount__icontains=search_term)
            )

        categories = Expense.objects.values_list('category', flat=True).distinct()

        context = {
            'expenses': expenses,
            'categories': categories,
        }

        return render(request, 'expenses.html', context)

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'expense_detail.html'

    def get_queryset(self):
        return Expense.objects.filter(company=self.request.user.company)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'add_expense.html'

    def get_queryset(self):
        return Expense.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:expense_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['job'].queryset = Job.objects.filter(company=self.request.user.company)
        return form

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expense_confirm_delete.html'

    def get_queryset(self):
        return Expense.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:expense_list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)

        if request.is_ajax():
            return JsonResponse({"result": "success"})
        else:
            return response

@csrf_exempt
@require_http_methods(["DELETE"])
def expense_delete(request):
    try:
        data = json.loads(request.body)
        if 'ids' not in data or not isinstance(data['ids'], list):
            return JsonResponse({"error": "Invalid data format"}, status=400)

        expenses = Expense.objects.filter(id__in=data['ids'], company=request.user.company)
        expenses_deleted = expenses.count()
        expenses.delete()

        return JsonResponse({"status": "success", "count": expenses_deleted}, status=204)
    except (Expense.DoesNotExist, KeyError):
        return JsonResponse({"error": "Expense not found"}, status=400)

class AddExpenseView(LoginRequiredMixin, View):
    def _initialize_form(self, request, initial_data=None):
        form = ExpenseForm(initial=initial_data)
        user_jobs = Job.objects.filter(company=request.user.company)
        form.fields['job'].queryset = user_jobs
        return form
    def get(self, request):
        user_jobs = Job.objects.filter(company=request.user.company)

        if request.GET:
            # If data is provided, pre-fill the form with the data
            data_dict = {key: request.GET[key] for key in request.GET}
            form = self._initialize_form(request, initial_data=data_dict)
            # Add the uploaded_receipt_path from the session to the form
            if 'uploaded_receipt_filename' in request.session:
                form.fields['uploaded_receipt_path'].initial = request.session['uploaded_receipt_filename']
                form.fields['uploaded_receipt_image'].initial = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, request.session['uploaded_receipt_filename']))
        else:
            form = self._initialize_form(request)
        return render(request, 'add_expense.html', {'form': form})

    def post(self, request):
        form = ExpenseForm(request.POST, request.FILES)
        form.fields['job'].queryset = Job.objects.filter(company=request.user.company)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.company = request.user.company

            # Add the uploaded receipt file from the form to the Expense object
            if form.cleaned_data['uploaded_receipt_path']:
                fs = FileSystemStorage()
                filename = form.cleaned_data['uploaded_receipt_path']
                uploaded_receipt = fs.open(filename)
                # Save the receipt to the Expense object
                expense.receipt.save(filename, File(uploaded_receipt), save=False)
                # Close the uploaded_receipt file
                uploaded_receipt.close()
                # Remove the session variable
                del request.session['uploaded_receipt_filename']
            expense.save()
            return redirect('smeApp:expense_list')
        return render(request, 'add_expense.html', {'form': form})

mindee_client = MindeeClient(api_key=settings.MINDEE_API_KEY)

MINDEE_CATEGORY_MAPPING = {
    'accommodation': 'Rent',
    'food': 'Meals and Entertainment',
    'food.restaurant': 'Meals and Entertainment',
    'food.shopping': 'Meals and Entertainment',
    'gasoline': 'Travel',
    'parking': 'Travel',
    'transport': 'Travel',
    'transport.plane': 'Travel',
    'transport.train': 'Travel',
    'transport.taxi': 'Travel',
    'toll': 'Travel',
    'telecom': 'Telephone',
    'miscellaneous': 'Other',
}

def map_mindee_category(mindee_category, mindee_subcategory):
    category_key = mindee_category
    if mindee_subcategory:
        category_key += '.' + mindee_subcategory
    return MINDEE_CATEGORY_MAPPING.get(category_key, 'Other')

def extract_data_from_receipt(image_path):
    input_doc = mindee_client.doc_from_path(image_path)
    api_response = input_doc.parse(documents.TypeReceiptV4)

    document = api_response.document
    extracted_data = {
        'amount': round(float(document.total_amount.value), 2),
        'date_created': document.date.value,
        'vendor': document.supplier.value,
        'category': map_mindee_category(document.category.value, document.subcategory.value),
    }
    return extracted_data

class UploadReceiptView(LoginRequiredMixin, FormView):
    form_class = ReceiptUploadForm
    template_name = 'upload_receipt.html'

    def form_valid(self, form):
        uploaded_image = self.request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_image.name, uploaded_image)
        uploaded_image_path = fs.path(filename)
        extracted_data = extract_data_from_receipt(uploaded_image_path)
        # Save the filename to the session
        self.request.session['uploaded_receipt_filename'] = filename
        data_str = urlencode(extracted_data)
        # Redirect to the AddExpenseView with the pre-filled data
        return redirect(f"{reverse('smeApp:add_expense')}?{data_str}")

##Sales and Inventory Management

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_create.html'
    success_url = reverse_lazy('smeApp:supplier_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        supplier = form.save(commit=False)
        supplier.company = self.request.user.company
        supplier.save()
        return super().form_valid(form)

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_update.html'

    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        supplier = form.save(commit=False)
        supplier.company = self.request.user.company
        supplier.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('smeApp:supplier_list')

class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/supplier_delete.html'

    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:supplier_list')

class ProductTypeListView(LoginRequiredMixin, ListView):
    model = ProductType
    template_name = 'inventory/product_type_list.html'

    def get_queryset(self):
        return ProductType.objects.filter(company=self.request.user.company)

class ProductTypeCreateView(LoginRequiredMixin, CreateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = 'inventory/product_type_create.html'
    success_url = reverse_lazy('smeApp:product_type_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        product_type = form.save(commit=False)
        product_type.company = self.request.user.company
        product_type.save()
        return super().form_valid(form)

class ProductTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = 'inventory/product_type_update.html'

    def get_queryset(self):
        return ProductType.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('smeApp:product_type_list')

class ProductTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductType
    template_name = 'inventory/product_type_delete.html'

    def get_queryset(self):
        return ProductType.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:product_type_list')

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'

    def get_queryset(self):
        return Supplier.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suppliers'] = self.get_queryset()
        return context

class StockItemListView(LoginRequiredMixin, View):
    template_name = 'inventory/stock_item_list.html'

    def get(self, request, *args, **kwargs):
        stock_items = StockItem.objects.filter(company=self.request.user.company)
        context = {
            'stock_items': stock_items,
        }
        return render(request, self.template_name, context)

class StockItemCreateView(LoginRequiredMixin, CreateView):
    model = StockItem
    form_class = StockItemForm
    template_name = 'inventory/stock_item_create.html'
    success_url = reverse_lazy('smeApp:stock_item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        stock_item = form.save(commit=False)
        stock_item.company = self.request.user.company
        stock_item.save()
        return super().form_valid(form)

class StockItemUpdateView(LoginRequiredMixin, UpdateView):
    model = StockItem
    form_class = StockItemForm
    template_name = 'inventory/stock_item_create.html'

    def get_queryset(self):
        return StockItem.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('smeApp:stock_item_list')

class StockItemDeleteView(LoginRequiredMixin, DeleteView):
    model = StockItem
    template_name = 'inventory/stock_item_delete.html'

    def get_queryset(self):
        return StockItem.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:stock_item_list')

class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order_list.html'

    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)

class PurchaseOrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        purchase_order_form = PurchaseOrderForm(user=request.user)
        PurchaseOrderItemFormSet = formset_factory(PurchaseOrderItemForm, extra=1, formset=BasePurchaseOrderItemFormSet)
        formset = PurchaseOrderItemFormSet(prefix='purchaseorderitem_set', user=request.user)
        return render(request, 'inventory/purchase_order_create.html', {'purchase_order_form': purchase_order_form, 'purchase_order_item_formset': formset})

    def post(self, request):
        purchase_order_form = PurchaseOrderForm(user=request.user, data=request.POST)
        PurchaseOrderItemFormSet = formset_factory(PurchaseOrderItemForm, extra=1, formset=BasePurchaseOrderItemFormSet)
        formset = PurchaseOrderItemFormSet(request.POST, prefix='purchaseorderitem_set', user=request.user)

        purchase_order_form.instance.company = request.user.company
        if purchase_order_form.is_valid():
            if all(form.is_valid() for form in formset):
                purchase_order = purchase_order_form.save(commit=False)
                purchase_order.company = request.user.company
                purchase_order.save()

                for form in formset:
                    if form.cleaned_data:
                        purchase_order_item = form.save(commit=False)
                        purchase_order_item.purchase_order = purchase_order
                        purchase_order_item.save()
                    else:
                        print("Form has no cleaned_data.")

                return redirect('smeApp:purchase_order_list')

            else:
                print("Some forms in formset are not valid")
        else:
            print("Purchase form errors:", purchase_order_form.errors)  # Add this line to show form errors

        return render(request, 'inventory/purchase_order_create.html', {'purchase_order_form': purchase_order_form, 'purchase_order_item_formset': formset})

class PurchaseOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'inventory/purchase_order_update.html'

    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST, prefix='formset', instance=self.object, user=self.request.user)
        else:
            context['formset'] = PurchaseOrderItemFormSet(prefix='formset', instance=self.object, user=self.request.user)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('smeApp:purchase_order_list')

class PurchaseOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order_delete.html'

    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:purchase_order_list')

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'inventory/sale_list.html'

    def get_queryset(self):
        return Sale.objects.filter(company=self.request.user.company)

class SaleCreateView(LoginRequiredMixin, View):
    def get(self, request):
        sale_form = SaleForm(user=request.user)
        SaleItemFormSet = formset_factory(SaleItemForm, extra=1, formset=BaseSaleItemFormSet)
        formset = SaleItemFormSet(prefix='saleitem_set', user=request.user)
        return render(request, 'inventory/sale_create.html', {'sale_form': sale_form, 'sale_item_formset': formset})

    def post(self, request):
        sale_form = SaleForm(user=request.user, data=request.POST)
        SaleItemFormSet = formset_factory(SaleItemForm, extra=1, formset=BaseSaleItemFormSet)
        formset = SaleItemFormSet(request.POST, prefix='saleitem_set', user=request.user)

        for form in formset:
            form.fields['stock_item'].queryset = StockItem.objects.filter(company=request.user.company)

        sale_form.instance.company = request.user.company
        if sale_form.is_valid():
            if all(form.is_valid() for form in formset):
                sale = sale_form.save(commit=False)
                sale.company = request.user.company
                sale.save()

                for form in formset:
                    if form.cleaned_data:
                        sale_item = form.save(commit=False)
                        sale_item.sale = sale
                        sale_item.save()

                return redirect('smeApp:sale_list')
            else:
                print("Some forms in formset are not valid")
        else:
            print("Sale form is not valid")
            print("Sale form errors:", sale_form.errors)

        print("Formset errors:", formset.errors)
        return render(request, 'inventory/sale_create.html', {'sale_form': sale_form, 'sale_item_formset': formset})

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'inventory/sale_update.html'

    def get_queryset(self):
        return Sale.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SaleUpdateView, self).get_context_data(**kwargs)
        SaleItemFormSet = inlineformset_factory(
            Sale,
            SaleItem,
            form=SaleItemForm,
            extra=1,
            formset=BaseSaleItemFormSet,
            can_delete=True
        )
        if self.request.POST:
            context['sale_item_formset'] = SaleItemFormSet(self.request.POST, instance=self.object, prefix='saleitem_set', user=self.request.user)
        else:
            context['sale_item_formset'] = SaleItemFormSet(instance=self.object, prefix='saleitem_set', user=self.request.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        sale_item_formset = context['sale_item_formset']

        if sale_item_formset.is_valid():
            sale_item_formset.instance = self.object
            sale_item_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('smeApp:sale_list')


class SaleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sale
    template_name = 'sale_delete.html'

    def get_queryset(self):
        return Sale.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse('smeApp:sale_list')

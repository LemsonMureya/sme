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
from .forms import (CustomUserCreationForm, CustomUserForm, ExpenseForm, ProductTypeForm,
                    IncomeForm, JobForm, ClientForm, CompanyProfileForm, InvoiceForm,
                    InvoiceItemForm, NoteForm, ReceiptUploadForm, CustomUserEditForm,
                    AvatarUpdateForm, PurchaseOrderItemForm, SaleForm, SaleItemForm,  BasePurchaseOrderItemFormSet,
                    SupplierForm, StockItemForm, PurchaseOrderForm, BaseSaleItemFormSet)
from django.contrib.auth.views import LoginView, LogoutView
from .models import (CustomUser, Job, Client, Expense, Income, CompanyProfile, ProductType,
                    Invoice, InvoiceItem, Note, Supplier, StockItem, PurchaseOrder,
                    PurchaseOrderItem, Sale, SaleItem)
from django.db.models import Sum, F
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect, FileResponse
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

class IndexView(TemplateView):
    template_name = "base.html"

class DashboardView(TemplateView):
    template_name = "dashboard.html"

def calculate_net_profit(company):
    incomes = 0
    expenses = Expense.objects.filter(company=company).aggregate(sum=Sum('amount'))['sum'] or 0

    if company.business_type == 'sales':
        incomes = Sale.objects.filter(company=company, revenue_recorded=True).annotate(total_amount=Sum(F('sale_items__selling_price') * F('sale_items__quantity'))).aggregate(sum=Sum('total_amount'))['sum'] or 0
    elif company.business_type == 'services':
        incomes = Job.objects.filter(company=company, revenue_recorded=True).aggregate(sum=Sum('total_cost'))['sum'] or 0

    return incomes - expenses

class MainDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main_dashboard.html'

    def get(self, request):
        user_company = request.user.company

        context = {
            'company': user_company,
            'total_expenses': Expense.objects.filter(company=user_company).aggregate(sum=Sum('amount'))['sum'] or 0,
        }

        if user_company.business_type == 'service':
            context.update({
                'total_revenue': Job.objects.filter(company=user_company, revenue_recorded=True).aggregate(total_revenue=Sum('total_cost'))['total_revenue'] or 0,
                'clients': Client.objects.filter(company=user_company),
                'jobs': Job.objects.filter(company=user_company),
                'expenses': Expense.objects.filter(company=user_company),
                'net_profit': calculate_net_profit(user_company),
            })
        elif user_company.business_type == 'sales':
            context.update({
                'total_revenue': Sale.objects.filter(company=user_company, revenue_recorded=True).annotate(total_amount=Sum(F('sale_items__selling_price') * F('sale_items__quantity'))).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0,
                'sales_orders': Sale.objects.filter(company=user_company),
                'stock': StockItem.objects.filter(company=user_company),
                'expenses': Expense.objects.filter(company=user_company),
                'net_profit': calculate_net_profit(user_company),
            })

        return render(request, 'main_dashboard.html', context)

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('smeApp:create_company_profile')

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
    success_url = reverse_lazy('smeApp:job_list')

    def form_valid(self, form):
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(reverse('smeApp:job_list'))
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
        print("Remove photo:", remove_photo)  # Debugging print statement
        form = AvatarUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            user = form.save(commit=False)
            if remove_photo:
                print("Removing photo...")  # Debugging print statement
                if user.photo:
                    user.photo.delete(save=False)
                    user.photo = None
            elif request.FILES.get("photo"):
                print("Photo exists in request.FILES:", request.FILES.get("photo"))  # Debugging print statement
                print("Updating photo...")  # Debugging print statement
                user.photo.save(f"{user.email}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg", ContentFile(request.FILES["photo"].read()))
            user.save()

            if request.is_ajax():
                return JsonResponse({"success": True})
            else:
                messages.success(request, 'Avatar updated successfully.')
                return redirect('smeApp:user_profile')
        else:
            print("Form errors:", form.errors)  # Debugging print statement

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
                print("Removing photo")
                if user.photo:
                    user.photo.delete(save=False)
                    user.photo = None
            elif request.FILES.get("photo"):
                print("Saving new photo")
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

class ClientsList(LoginRequiredMixin, TemplateView): #client list usinf templates
    model = Client
    template_name = 'client_list.html'

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(company=user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = self.get_queryset()
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

class JobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'job_list.html'

    def get_queryset(self):
        queryset = Job.objects.filter(company=self.request.user.company)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        context['all_count'] = Job.objects.filter(company=company).count()
        context['ongoing_count'] = Job.objects.filter(status='ongoing', company=company).count()
        context['cancelled_count'] = Job.objects.filter(status='cancelled', company=company).count()
        context['completed_count'] = Job.objects.filter(status='completed', company=company).count()
        context['postponed_count'] = Job.objects.filter(status='postponed', company=company).count()
        context['work_order_count'] = Job.objects.filter(status='work order', company=company).count()
        context['quotes_count'] = Job.objects.filter(status='quotes', company=company).count()
        context['form'] = JobForm(user=self.request.user)
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
        context['notes'] = Note.objects.filter(related_object=self.object, related_object__company=self.request.user.company)
        return context

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        job = form.save(commit=False)
        job.company = self.request.user.company
        job.save()
        return HttpResponseRedirect(self.success_url)

class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')

    def get_queryset(self):
        user = self.request.user
        return Job.objects.filter(company=user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        job = form.save(commit=False)
        job.company = self.request.user.company
        job.save()
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

        context = {
            'expenses': expenses,
        }
        return render(request, 'expenses.html', context)

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
            print("Initial Data:")
            pprint(data_dict)
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
            else:
                print("Form is not valid")
                print(form.errors)

            expense.save()
            return redirect('smeApp:expense_list')
        return render(request, 'add_expense.html', {'form': form})


MINDEE_API_KEY = '2189f2fa766d0adcc9aa5df09e28f8a0'
mindee_client = MindeeClient(api_key=MINDEE_API_KEY)

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
    # Add any other Mindee categories and subcategories that you want to map to your categories
}

def map_mindee_category(mindee_category, mindee_subcategory):
    category_key = mindee_category
    if mindee_subcategory:
        category_key += '.' + mindee_subcategory
    return MINDEE_CATEGORY_MAPPING.get(category_key, 'Other')

def extract_data_from_receipt(image_path):
    input_doc = mindee_client.doc_from_path(image_path)
    api_response = input_doc.parse(documents.TypeReceiptV4)
    print(api_response.document)

    document = api_response.document
    extracted_data = {
        'description': document.time.value,
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

def pnl_data(request):
    time_filter = request.GET.get('time_filter', 'all')
    company = request.user.company
    today = date.today()

    if time_filter == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif time_filter == 'month':
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = today - timedelta(days=6)
        end_date = today

    # Get income and expense data based on time filter
    if time_filter == 'all':
        incomes = Income.objects.filter(company=company)
        expenses = Expense.objects.filter(company=company)
    else:
        incomes = Income.objects.filter(date__range=[start_date, end_date], company=company)
        expenses = Expense.objects.filter(date__range=[start_date, end_date], company=company)

    # Calculate total income and expense for each day in date range
    income_totals = {}
    expense_totals = {}
    date_range = [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 1)]
    for date in date_range:
        # Calculate total income for current date
        daily_incomes = incomes.filter(date=date)
        if daily_incomes:
            income_totals[date] = daily_incomes.aggregate(Sum('amount'))['amount__sum']
        else:
            income_totals[date] = 0
        # Calculate total expense for current date
        daily_expenses = expenses.filter(date=date)
        if daily_expenses:
            expense_totals[date] = daily_expenses.aggregate(Sum('amount'))['amount__sum']
        else:
            expense_totals[date] = 0

    data = {
        'date_range': [str(date) for date in date_range],
        'income_totals': income_totals,
        'expense_totals': expense_totals
    }
    return JsonResponse(data)

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_form'] = InvoiceForm(user=self.request.user)
        InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1)
        context['invoice_item_formset'] = InvoiceItemFormSet(prefix='invoiceitem_set')
        return context

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

class DeleteInvoiceView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'delete_invoice.html'
    success_url = reverse_lazy('smeApp:invoices_list')

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.company)

class CreateInvoiceView(LoginRequiredMixin, View):
    def get(self, request):
        invoice_form = InvoiceForm(user=request.user)
        InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1)
        formset = InvoiceItemFormSet(prefix='invoiceitem_set')
        return render(request, 'create_invoice.html', {'invoice_form': invoice_form, 'invoice_item_formset': formset})

    def post(self, request):
        invoice_form = InvoiceForm(request.user, request.POST)
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
        print("Supplier created:", supplier.name)

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
        print("form errors:", form.errors)  # Debug print
        stock_item = form.save(commit=False)
        stock_item.company = self.request.user.company
        print("form_valid called")  # Debug print
        print("stock_item:", stock_item)  # Debug print
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

        print("Purchase form raw data:", request.POST)
        purchase_order_form.instance.company = request.user.company
        if purchase_order_form.is_valid():
            print("Purchase form is valid")
            if all(form.is_valid() for form in formset):
                print("All forms in formset are valid")

                purchase_order = purchase_order_form.save(commit=False)
                purchase_order.company = request.user.company
                print("Purchase data errors:", purchase_order_form.errors)
                purchase_order.save()
                print("Purchase order saved:", purchase_order)

                for form in formset:
                    if form.cleaned_data:
                        purchase_order_item = form.save(commit=False)
                        purchase_order_item.purchase_order = purchase_order
                        print("Saving purchase order item:", purchase_order_item)
                        purchase_order_item.save()
                        print("Purchase order item saved:", purchase_order_item)
                    else:
                        print("Form has no cleaned_data.")

                return redirect('smeApp:purchase_order_list')

            else:
                print("Some forms in formset are not valid")
        else:
            print("Purchase form is not valid")
            print("Purchase form errors:", purchase_order_form.errors)  # Add this line to show form errors


        print("Formset errors:", formset.errors)
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

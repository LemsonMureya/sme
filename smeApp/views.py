from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login
from django.views.generic import CreateView
from django.utils import timezone
from django.db.models.functions import TruncMonth
import datetime
from .forms import CustomUserCreationForm, CustomUserForm, ExpenseForm, IncomeForm, JobForm, ClientForm
from django.contrib.auth.views import LoginView, LogoutView
from .models import CustomUser, Job, Client, Expense, Income
from django.db.models import Sum, F
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.dates import (
    YearMixin, MonthMixin, WeekMixin,
    DayMixin, DateMixin, _date_from_string
)


class IndexView(TemplateView):
    template_name = "base.html"

class DashboardView(TemplateView):
    template_name = "dashboard.html"

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

@csrf_exempt
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            new_client = form.save()
            return JsonResponse({"id": new_client.id, "name": new_client.name})
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)

class ClientsListView(View):
    def get(self, request, *args, **kwargs):
        clients = Client.objects.all().values('id', 'name')
        return JsonResponse(list(clients), safe=False)

class ClientsList(TemplateView):
    template_name = "client_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all()
        return context

class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_count'] = Job.objects.count()
        context['ongoing_count'] = Job.objects.filter(status='ongoing').count()
        context['cancelled_count'] = Job.objects.filter(status='cancelled').count()
        context['finished_count'] = Job.objects.filter(status='finished').count()
        context['postponed_count'] = Job.objects.filter(status='postponed').count()
        context['work_order_count'] = Job.objects.filter(status='work_order').count()
        context['quotes_count'] = Job.objects.filter(status='quotes').count()
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

class JobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')

class JobUpdateView(UpdateView):
    model = Job
    template_name = 'job_form.html'
    success_url = reverse_lazy('smeApp:job_list')
    fields = '__all__'

class JobDeleteView(DeleteView):
    model = Job
    template_name = 'job_confirm_delete.html'
    success_url = reverse_lazy('smeApp:job_list')

class AddExpenseView(View):
    def get(self, request):
        form = ExpenseForm()
        return render(request, 'add_expense.html', {'form': form})

    def post(self, request):
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('smeApp:transactions')
        return render(request, 'add_expense.html', {'form': form})

class ExpensesDataView(View):
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
            expenses = Expense.objects.filter(date_created__gte=start_date)
        else:
            expenses = Expense.objects.all()

        expenses_data = expenses.values('category').annotate(total_amount=Sum('amount'))
        return JsonResponse(list(expenses_data), safe=False)

class ProfitLossDataView(View):
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
            expenses = Expense.objects.filter(date_created__gte=start_date)
            incomes = Income.objects.filter(date_created__gte=start_date)
        else:
            expenses = Expense.objects.all()
            incomes = Income.objects.all()

        expenses_data = expenses.annotate(month=TruncMonth('date_created')).values('month').annotate(total_amount=Sum('amount'))
        incomes_data = incomes.annotate(month=TruncMonth('date_created')).values('month').annotate(total_amount=Sum('amount'))

        return JsonResponse({'expenses': list(expenses_data), 'incomes': list(incomes_data)}, safe=False)


class AddIncomeView(View):
    def get(self, request):
        form = IncomeForm()
        return render(request, 'add_income.html', {'form': form})

    def post(self, request):
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('smeApp:transactions')
        return render(request, 'add_income.html', {'form': form})

class TransactionsView(View):
    def get(self, request):
        expenses = Expense.objects.all()
        incomes = Income.objects.all()
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

class IncomeUpdateView(UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = 'add_income.html'

    def get_success_url(self):
        return reverse('smeApp:transactions')

class ExpenseUpdateView(UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'add_expense.html'

    def get_success_url(self):
        return reverse('smeApp:transactions')

class IncomeDeleteView(DeleteView):
    model = Income
    template_name = 'income_confirm_delete.html'  # Add this line

    def get_success_url(self):
        return reverse('smeApp:transactions')

class ExpenseDeleteView(DeleteView):
    model = Expense
    template_name = 'expense_confirm_delete.html'  # Add this line

    def get_success_url(self):
        return reverse('smeApp:transactions')

def pnl_data(request):
    time_filter = request.GET.get('time_filter', 'all')
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
        incomes = Income.objects.all()
        expenses = Expense.objects.all()
    else:
        incomes = Income.objects.filter(date__range=[start_date, end_date])
        expenses = Expense.objects.filter(date__range=[start_date, end_date])

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

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Income, Expense, Job, Client, CompanyProfile, Invoice, InvoiceItem


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role']

class JobForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    po_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(choices=Job.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ChoiceField(choices=Job.CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    total_cost = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    payment_status = forms.ChoiceField(choices=Job.PAYMENT_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    payment_type = forms.ChoiceField(choices=Job.PAYMENT_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    assigned_worker = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Job
        fields = ['client', 'po_number', 'status', 'category', 'description', 'start_date', 'end_date', 'total_cost', 'payment_status', 'payment_type', 'assigned_worker']

class ClientForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Client
        fields = ['name', 'address', 'contact_name', 'email', 'phone', 'role']


class IncomeForm(forms.ModelForm):
    category = forms.ChoiceField(choices=Income.INCOME_CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    date_created = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})) # Add a calendar widget
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    invoice = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    customer = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Income
        fields = ['category', 'description', 'amount', 'date_created', 'notes', 'invoice', 'customer']

class ExpenseForm(forms.ModelForm):
    category = forms.ChoiceField(choices=Expense.EXPENSE_CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    date_created = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})) # Add a calendar widget
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    receipt = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    vendor = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'date_created', 'notes', 'receipt', 'vendor']

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            'name',
            'address_line_1',
            'address_line_2',
            'phone',
            'email',
            'logo',
            'industry',
        ]

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['user', 'company', 'client', 'invoice_number', 'invoice_date', 'due_date']

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'item_description', 'quantity', 'unit_price']

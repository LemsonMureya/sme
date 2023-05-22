from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (CustomUser, Income, Expense, Job, Client, CompanyProfile, Invoice, ProductType, JobItem,
                    InvoiceItem, Note, Supplier, StockItem, PurchaseOrder, PurchaseOrderItem, Sale, SaleItem)
from django.forms import widgets, ImageField
from django.utils.html import format_html
from datetime import timedelta
from django.forms import formset_factory, BaseFormSet

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

class CustomUserEditForm(forms.ModelForm):
    photo = ImageField(required=False)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role', 'company', 'photo']

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
            'business_type',
            'num_employees',
            'city',
            'country',
            'website',
            'zip_code',
        ]

class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['photo']

    remove_photo = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )

class JobForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    po_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(choices=Job.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ChoiceField(choices=Job.CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(
                attrs={'class': 'form-control flatpickr-date', 'autocomplete': 'off'}
            )
        )
    end_date = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control flatpickr-date', 'autocomplete': 'off'}
        )
    )
    total_cost = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    payment_status = forms.ChoiceField(choices=Job.PAYMENT_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    payment_type = forms.ChoiceField(choices=Job.PAYMENT_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    assigned_worker = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    revenue_recorded = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Job
        fields = ['client', 'po_number', 'status', 'category', 'description', 'start_date', 'end_date', 'total_cost', 'payment_status', 'payment_type', 'assigned_worker', 'revenue_recorded']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(JobForm, self).__init__(*args, **kwargs)

        if user and user.company:
            self.fields['client'].queryset = Client.objects.filter(company=user.company)

    def save(self, commit=True):
        job = super().save(commit=False)
        if commit:
            job.save()
            if self.instance and self.instance.id:
                job.notes.set(self.instance.notes.all())
        return job

class JobItemForm(forms.ModelForm):
    class Meta:
        model = JobItem
        fields = ('item_name', 'item_description', 'quantity', 'unit_price')
        exclude = ['id', 'delete', 'job']

class ClientForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'address-input'}))
    contact_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=Client.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

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

class UploadedReceiptImageWidget(widgets.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if value:
            return format_html('<img src="{}" alt="Uploaded Receipt" width="300" height="auto" />', value)
        else:
            return ""

class ExpenseForm(forms.ModelForm):
    category = forms.ChoiceField(choices=Expense.EXPENSE_CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    job = forms.ModelChoiceField(queryset=Job.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    date_created = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})) # Add a calendar widget
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    receipt = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    vendor = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    uploaded_receipt_image = forms.CharField(required=False, widget=UploadedReceiptImageWidget(attrs={'class': 'form-control'})) # Add this line
    uploaded_receipt_path = forms.CharField(widget=forms.HiddenInput(), required=False)  # Add this line

    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'job', 'date_created', 'notes', 'receipt', 'vendor', 'uploaded_receipt_path', 'uploaded_receipt_image']  # Add 'uploaded_receipt_image'

class InvoiceForm(forms.ModelForm):
    color_accent = forms.CharField(
        required=False,
        initial='#0097eb',
        widget=forms.TextInput(attrs={'type': 'color'})
    )
    payment_status = forms.ChoiceField(choices=Invoice.PAYMENT_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Invoice
        fields = ['company', 'client', 'invoice_number', 'invoice_date', 'due_date', 'notes', 'tax', 'discount', 'color_accent', 'payment_status']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)

        if user and user.company:
            self.fields['client'].queryset = Client.objects.filter(company=user.company)
            self.fields['company'].queryset = CompanyProfile.objects.filter(id=user.company.id)
            invoice_count = Invoice.objects.filter(company=user.company).count()

        if job:
            self.fields['client'].initial = job.client
            self.fields['company'].initial = job.company
            self.fields['invoice_number'].initial = invoice_count + 1
            self.fields['invoice_date'].initial = job.created_at
            self.fields['due_date'].initial = job.created_at + timedelta(days=30)
            self.fields['payment_status'].initial = job.payment_status

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'item_description', 'quantity', 'unit_price']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'DELETE' in self.fields:
            del self.fields['DELETE']

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['text', 'attachment']
        widgets = {
            'text': forms.TextInput(attrs={'id': 'id_text'}),
        }

class ReceiptUploadForm(forms.Form):
    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'accept': 'image/*', 'capture': 'camera'})
    )

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'address', 'phone', 'email']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = ProductType
        fields = ['name']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].queryset = ProductType.objects.filter(company=user.company)

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = '__all__'
        exclude = ('company',)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StockItemForm, self).__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(company=user.company)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'purchase_date', 'receive_by_date', 'status']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company=user.company)

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['stock_item', 'quantity', 'unit_purchase_cost']
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_purchase_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['stock_item'].queryset = StockItem.objects.filter(company=user.company)

class BasePurchaseOrderItemFormSet(BaseFormSet):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['user'] = self.user
        return super()._construct_form(i, **kwargs)


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['client', 'sale_date', 'revenue_recorded']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['client'].queryset = Client.objects.filter(company=user.company)

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['stock_item', 'quantity', 'selling_price']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['stock_item'].queryset = StockItem.objects.filter(company=user.company)

class BaseSaleItemFormSet(BaseFormSet):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['user'] = self.user
        return super()._construct_form(i, **kwargs)

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CompanyProfile(models.Model):
    BUSINESS_CATEGORY_CHOICES = (
        ('art_photography_creative', 'Art, Photography & Creative Services'),
        ('construction_home_improvement', 'Construction & Home Improvement'),
        ('consulting_professional', 'Consulting & Professional Services'),
        ('financial_services_insurance', 'Financial Services & Insurance'),
        ('hair_spa_aesthetics', 'Hair, Spa & Aesthetics'),
        ('nonprofits_associations_groups', 'Non-profits, Associations & Groups'),
        ('real_estate', 'Real Estate'),
        ('retailers_resellers_sales', 'Retailers, Resellers & Sales'),
        ('web_tech_media', 'Web, Tech & Media'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=255)
    address_line_1 = models.TextField(blank=True, null=True)
    address_line_2 = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])], blank=True, null=True)
    industry = models.CharField(max_length=50, choices=BUSINESS_CATEGORY_CHOICES, default='other')

    def __str__(self):
        return self.name

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Employee', 'Employee'),
        ('Manager', 'Manager'),
        ('Admin', 'Admin'),
        ('Other', 'Other'),
    ]

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Other')
    company =  models.OneToOneField(CompanyProfile, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, default='user_photos/default-avatar.png')
    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'


class Client(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    ROLE_CHOICES = (
        ('job_contact', 'Job Contact'),
        ('property_owner', 'Property Owner'),
        ('tenant', 'Tenant'),
        ('manager', 'Manager'),
        ('vendor', 'Vendor'),
        ('Other', 'Other'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name

class Note(models.Model):
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='attachments/', blank=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    related_object = models.ForeignKey('Job', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.author_id:
            self.author = get_user_model().objects.first()  # Set the author to the currently logged in user
        super(Note, self).save(*args, **kwargs)

    def __str__(self):
        return self.related_object.client.name

class Job(models.Model):
    STATUS_CHOICES = (
        ('quote', 'Quote'),
        ('work_order', 'Work Order'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )

    CATEGORY_CHOICES = (
        ('after_hours', 'After Hours'),
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('warranty', 'Warranty'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('late', 'Late Payment'),
        ('pending', 'Pending Payment'),
        ('overdue', 'Overdue'),
        ('not_invoiced', 'Not Yet Invoiced'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
        ('other', 'Other'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='quote')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='standard')
    description = models.TextField(blank=True, null=True)
    notes = models.ManyToManyField(Note, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_status = models.CharField(max_length=20, blank=True, null=True, choices=PAYMENT_STATUS_CHOICES)
    payment_type = models.CharField(max_length=20, blank=True, null=True, choices=PAYMENT_TYPE_CHOICES)
    assigned_worker = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.client.name

class Expense(models.Model):
    RENT = 'Rent'
    REPAIRS_MAINTENANCE = 'Repairs and Maintenance'
    PAYROLL = 'Payroll'
    MEALS_ENTERTAINMENT = 'Meals and Entertainment'
    TELEPHONE = 'Telephone'
    TRAVEL = 'Travel'
    UTILITIES = 'Utilities'
    ADVERTISING_PROMOTION = 'Advertising and Promotion'
    OTHER = 'Other'
    EXPENSE_CATEGORY_CHOICES = [
        (RENT, 'Rent'),
        (REPAIRS_MAINTENANCE, 'Repairs and Maintenance'),
        (PAYROLL, 'Payroll'),
        (MEALS_ENTERTAINMENT, 'Meals and Entertainment'),
        (TELEPHONE, 'Telephone'),
        (TRAVEL, 'Travel'),
        (UTILITIES, 'Utilities'),
        (ADVERTISING_PROMOTION, 'Advertising and Promotion'),
        (OTHER, 'Other'),
    ]
    category = models.CharField(
        max_length=50,
        choices=EXPENSE_CATEGORY_CHOICES,
        default=OTHER,
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateField(auto_now_add=False)
    date_modified = models.DateField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.description

class Income(models.Model):
    SALE = 'Sale'
    SERVICE = 'Service'
    PRODUCT = 'Product'
    OTHER = 'Other'
    INCOME_CATEGORY_CHOICES = [
        (SALE, 'Sale'),
        (SERVICE, 'Service'),
        (PRODUCT, 'Product'),
        (OTHER, 'Other'),
    ]
    category = models.CharField(
        max_length=20,
        choices=INCOME_CATEGORY_CHOICES,
        default=SALE,
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateField(auto_now_add=False)
    date_modified = models.DateField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    invoice = models.FileField(upload_to='invoices/', blank=True, null=True)
    customer = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.description

class Invoice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()

    def get_total_amount(self):
        total = 0
        for item in self.invoiceitem_set.all():
            total += item.quantity * item.unit_price
        return total

    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    item_description = models.CharField(max_length=255)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.item_name

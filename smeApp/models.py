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
        ('art', 'Art, Photography & Creative Services'),
        ('construction', 'Construction & Home Improvement'),
        ('consulting', 'Consulting & Professional Services'),
        ('financial', 'Financial Services & Insurance'),
        ('hair_spa', 'Hair, Spa & Aesthetics'),
        ('non_profit', 'Non-profits, Associations & Groups'),
        ('real_estate', 'Real Estate'),
        ('retail', 'Retailers, Resellers & Sales'),
        ('web_tech', 'Web, Tech & Media'),
        ('other', 'Other'),
    )

    BUSINESS_TYPE_CHOICES = [
        ('service', 'Service'),
        ('sales', 'Sales'),
    ]

    NUM_EMPLOYEES_CHOICES = (
        ('1', '1'),
        ('2_to_10', '2-10'),
        ('11_to_50', '11-50'),
        ('51_to_200', '51-199'),
        ('200_plus', '200+'),
    )

    name = models.CharField(max_length=255)
    address_line_1 = models.TextField(blank=True, null=True)
    address_line_2 = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])], blank=True, null=True)
    industry = models.CharField(max_length=50, choices=BUSINESS_CATEGORY_CHOICES, default='other')
    business_type = models.CharField(max_length=10, choices=BUSINESS_TYPE_CHOICES, default='service')
    num_employees = models.CharField(max_length=20, choices=NUM_EMPLOYEES_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    date_joined = models.DateField(default=timezone.now, blank=True, null=True)

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
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Employee')
    company = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, null=True, related_query_name="customuser")
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
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='clients')
    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return self.related_object.client.name

class Job(models.Model):
    STATUS_CHOICES = (
        ('quote', 'Quote'),
        ('work order', 'Work Order'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )

    CATEGORY_CHOICES = (
        ('after hours', 'After Hours'),
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('warranty', 'Warranty'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('credit card', 'Credit Card'),
        ('debit card', 'Debit Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    )
    PAYMENT_STATUS_CHOICES = (
    ('Unpaid', 'Unpaid'),
    ('Partially Paid', 'Partially Paid'),
    ('Paid', 'Paid'),
    ('Late Payment', 'Late Payment'),
    ('Pending Payment', 'Pending Payment'),
    ('Overdue', 'Overdue'),
    ('Not Yet Invoiced', 'Not Yet Invoiced'),
    ('Refunded', 'Refunded'),
    ('Cancelled', 'Cancelled'),
    ('Other', 'Other'),
    )


    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='quote')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='standard')
    description = models.TextField(blank=True, null=True)
    notes = models.ManyToManyField(Note, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_status = models.CharField(max_length=20, blank=True, null=True, choices=PAYMENT_STATUS_CHOICES)
    payment_type = models.CharField(max_length=20, blank=True, null=True, choices=PAYMENT_TYPE_CHOICES)
    assigned_worker = models.CharField(max_length=255, blank=True, null=True)
    revenue_recorded = models.BooleanField(default=False)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total_cost(self):
        return sum(item.quantity * item.unit_price for item in self.jobitem_set.all())

    def __str__(self):
        return self.client.name

class JobItem(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100, verbose_name='Item Name', help_text='Enter the name of the item or service.')
    item_description = models.CharField(max_length=255, verbose_name='Item Description', help_text='Enter a brief description of the item or service.', blank=True, null=True)
    quantity = models.IntegerField(verbose_name='Quantity', help_text='Enter the quantity of the item or service.', validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price', help_text='Enter the unit price of the item or service.', validators=[MinValueValidator(0)])

    def __str__(self):
        return self.item_name

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
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True, related_name='expenses')
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='expenses')

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
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='incomes')

    def __str__(self):
        return self.description

class Invoice(models.Model):
    UNPAID = 'Unpaid'
    PARTIALLY_PAID = 'Partially Paid'
    PAID = 'Paid'
    LATE = 'Late Payment'
    PENDING = 'Pending Payment'
    OVERDUE = 'Overdue'
    NOT_INVOICED = 'Not Yet Invoiced'
    REFUNDED = 'Refunded'
    CANCELLED = 'Cancelled'
    OTHER = 'Other'

    PAYMENT_STATUS_CHOICES = [
        (UNPAID, 'Unpaid'),
        (PARTIALLY_PAID, 'Partially Paid'),
        (PAID, 'Paid'),
        (LATE, 'Late Payment'),
        (PENDING, 'Pending Payment'),
        (OVERDUE, 'Overdue'),
        (NOT_INVOICED, 'Not Yet Invoiced'),
        (REFUNDED, 'Refunded'),
        (CANCELLED, 'Cancelled'),
        (OTHER, 'Other'),
    ]

    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Tax in percentage
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Discount in currency value
    notes = models.TextField(blank=True, null=True)
    color_accent = models.CharField(max_length=7, default='#0097eb')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True, related_name='invoices')  # New field added
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=UNPAID)

    def get_total_amount(self):
        subtotal = 0
        for item in self.invoiceitem_set.all():
            subtotal += item.quantity * item.unit_price

        total_tax = (subtotal * self.tax) / 100
        total = subtotal + total_tax - self.discount
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

class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name='Supplier Name')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Address', help_text='Street address, city, and zip code.')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Phone Number')
    email = models.EmailField(blank=True, null=True, verbose_name='Email Address')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='suppliers')

    def __str__(self):
        return self.name

class ProductType(models.Model):
    name = models.CharField(max_length=255, verbose_name='Type Name')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='product_types')

    @staticmethod
    def get_default_type(company):
        default_type, created = ProductType.objects.get_or_create(name='Default Type', company=company)
        return default_type.id

    def __str__(self):
        return self.name

class StockItem(models.Model):
    item_id = models.CharField(max_length=255, primary_key=True, verbose_name='Item ID')
    name = models.CharField(max_length=255, verbose_name='Item Name')
    product_type = models.ForeignKey(ProductType, on_delete=models.SET_NULL, null=True, related_name='stock_items', verbose_name='Product Type', default=None)
    image = models.ImageField(upload_to='stock_items/', blank=True, null=True, verbose_name='Item Image')
    barcode = models.CharField(max_length=255, blank=True, null=True, verbose_name='Barcode', help_text='Optional barcode for the item.')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='stock_items', verbose_name='Supplier')
    unit_selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Selling Price')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Quantity in Inventory')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='stock_items', verbose_name='Company')

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    PENDING = 'Pending'
    CONFIRMED = 'Confirmed'
    RECEIVED = 'Received'
    CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (RECEIVED, 'Received'),
        (CANCELLED, 'Cancelled'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='Supplier')
    purchase_date = models.DateField(verbose_name='Purchase Date')
    receive_by_date = models.DateField(verbose_name='Receive By Date')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=PENDING, verbose_name='Order Status')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='purchase_orders', verbose_name='Company')

    def get_total_purchase_cost(self):
        total_cost = 0
        for item in self.purchase_order_items.all():
            total_cost += item.total_price
        return total_cost

    def __str__(self):
        return f'Purchase Order {self.pk} - {self.supplier.name}'

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='purchase_order_items', verbose_name='Purchase Order')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, verbose_name='Stock Item')
    quantity = models.PositiveIntegerField(verbose_name='Quantity Ordered', help_text='The number of items ordered.')
    unit_purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Purchase Cost')
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def total_purchase_price(self):
        return self.quantity * self.unit_purchase_cost

    def __str__(self):
        return f'{self.stock_item.name} - {self.quantity}'

class Sale(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    sale_date = models.DateField(verbose_name='Sale Date', help_text='The date the sale was made.')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='sales')
    revenue_recorded = models.BooleanField(default=False)

    def get_total_amount(self):
        total = 0
        for item in self.sale_items.all():
            total += item.selling_price * item.quantity
        return total

    def __str__(self):
        return f'Sale {self.pk} - {self.client.name}'

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='sale_items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Quantity Sold', help_text='The number of items sold in this transaction.')
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.stock_item.name} - {self.quantity}'

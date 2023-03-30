from django.db import models
# from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

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
    company = models.CharField(max_length=255, blank=True)
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

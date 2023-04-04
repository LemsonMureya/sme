# Register your models here.
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Client, Note, Job, Expense, Income, CompanyProfile, Invoice, InvoiceItem


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'company', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'user_permissions')}),
        ('Role', {'fields': ('role',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'company', 'photo', 'role', 'is_active', 'is_staff', 'user_permissions')}
        ),
    )

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'contact_name', 'email', 'phone', 'role')
    list_filter = ('role',)
    search_fields = ('name', 'address', 'contact_name', 'email')
    ordering = ('name',)

class NoteAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'created_at', 'updated_at', 'related_object')
    search_fields = ('text', 'author__email', 'related_object__client__name')
    list_filter = ('created_at', 'updated_at')

class JobAdmin(admin.ModelAdmin):
    list_display = ('client', 'po_number', 'status', 'category', 'start_date', 'end_date', 'total_cost', 'payment_status', 'payment_type', 'assigned_worker')
    search_fields = ('client__name', 'po_number',)
    list_filter = ('status', 'category', 'payment_status', 'payment_type')

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date_created', 'vendor')
    search_fields = ('category', 'description', 'vendor',)
    list_filter = ('category', 'vendor')

class IncomeAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date_created', 'customer')
    search_fields = ('category', 'description', 'customer',)
    list_filter = ('category', 'customer')

class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'address_line_1', 'address_line_2', 'phone', 'email')
    list_filter = ('industry',)
    search_fields = ('name', 'industry', 'email')
    ordering = ('name',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'company', 'client', 'invoice_date', 'due_date')
    list_filter = ('invoice_date', 'due_date')
    search_fields = ('invoice_number', 'user__email', 'company__name', 'client__name')
    inlines = [InvoiceItemInline]
    ordering = ('-invoice_date',)

class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_description', 'quantity', 'unit_price', 'invoice')
    list_filter = ('invoice',)
    search_fields = ('item_name', 'item_description', 'invoice__invoice_number')
    ordering = ('invoice', 'item_name',)

admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem, InvoiceItemAdmin)
admin.site.register(CompanyProfile, CompanyProfileAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(CustomUser, CustomUserAdmin)

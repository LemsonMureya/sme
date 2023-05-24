from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.contrib.auth.admin import UserAdmin
from .models import (CustomUser, Client, Note, Job, Expense, Supplier, StockItem, PurchaseOrder,ProductType, JobItem,
                    PurchaseOrderItem, Sale, SaleItem, Income, CompanyProfile, Invoice, InvoiceItem)

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
    list_display = ('name', 'address', 'contact_name', 'email', 'phone', 'role', 'associated_user')
    list_filter = ('role',)
    search_fields = ('name', 'address', 'contact_name', 'email')
    ordering = ('name',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class NoteAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'created_at', 'updated_at', 'related_object')
    search_fields = ('text', 'author__email', 'related_object__client__name')
    list_filter = ('created_at', 'updated_at')

class JobItemInline(admin.TabularInline):
    model = JobItem
    extra = 1

class JobAdmin(admin.ModelAdmin):
    list_display = ('client', 'po_number', 'status', 'start_date', 'end_date', 'total_cost', 'payment_status', 'payment_type', 'assigned_worker', 'revenue_recorded', 'associated_user', 'total_cost_for_user')
    search_fields = ('client__name', 'po_number',)
    list_filter = ('status', 'payment_status', 'payment_type')
    inlines = [JobItemInline]

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

    def total_cost_for_user(self, obj):
        user = obj.company.customuser_set.first()
        if user:
            job_items = JobItem.objects.filter(job__company=user.company)
            total_cost = 0
            for item in job_items:
                total_cost += item.quantity * item.unit_price
            return total_cost
        else:
            return None
    total_cost_for_user.short_description = 'Total Cost for User'


class JobItemAdmin(admin.ModelAdmin):
    list_display = ('job', 'item_name', 'item_description', 'quantity', 'unit_price')
    search_fields = ('job__client__name', 'item_name',)
    list_filter = ('job',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date_created', 'vendor', 'associated_user')
    search_fields = ('category', 'description', 'vendor',)
    list_filter = ('category', 'vendor')

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class IncomeAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date_created', 'customer', 'associated_user')
    search_fields = ('category', 'description', 'customer',)
    list_filter = ('category', 'customer')

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry','business_type', 'num_employees', 'city', 'country', 'address_line_1', 'address_line_2', 'zip_code', 'phone', 'email', 'website', 'date_joined')
    list_filter = ('industry', 'business_type', 'num_employees', 'city', 'country')
    search_fields = ('name', 'industry', 'city', 'country', 'email')
    ordering = ('name',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'company', 'client', 'invoice_date', 'due_date', 'job', 'payment_status', 'associated_user')  # Add 'job' and 'payment_status'
    list_filter = ('invoice_date', 'due_date', 'job', 'payment_status')  # 'job' and 'payment_status' if you want to filter by these fields
    search_fields = ('invoice_number', 'notes', 'company__name', 'client__name', 'job__description')  # Add 'job__description' and 'job__client__name'
    inlines = [InvoiceItemInline]
    ordering = ('-invoice_date',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'


class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_description', 'quantity', 'unit_price', 'invoice')
    list_filter = ('invoice',)
    search_fields = ('item_name', 'item_description', 'invoice__invoice_number')
    ordering = ('invoice', 'item_name',)

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'email', 'company', 'associated_user')
    search_fields = ('name', 'address', 'email')
    ordering = ('name',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'associated_user')
    search_fields = ('name',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class StockItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'product_type', 'barcode', 'description', 'supplier', 'unit_selling_price', 'quantity', 'company', 'associated_user')
    list_filter = ('product_type', 'supplier', 'company')
    search_fields = ('item_id', 'name', 'type', 'barcode', 'description')
    ordering = ('name',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'purchase_date', 'receive_by_date', 'status', 'company', 'associated_user')
    list_filter = ('supplier', 'status', 'company')
    search_fields = ('supplier__name',)
    ordering = ('purchase_date',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'stock_item', 'quantity', 'unit_purchase_cost')
    list_filter = ('purchase_order',)
    search_fields = ('stock_item__name', 'purchase_order__supplier__name')
    ordering = ('purchase_order', 'stock_item__name',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('client', 'sale_date', 'company', 'revenue_recorded', 'associated_user')
    list_filter = ('client', 'company')
    search_fields = ('client__name',)
    ordering = ('sale_date',)

    def associated_user(self, obj):
        user = obj.company.customuser_set.first()
        return user.email if user else None
    associated_user.short_description = 'Associated User'

class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'stock_item', 'quantity', 'selling_price')
    list_filter = ('sale',)
    search_fields = ('stock_item__name', 'sale__client__name')
    ordering = ('sale', 'stock_item__name',)

admin.site.register(JobItem, JobItemAdmin)
admin.site.register(ProductType, ProductTypeAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderItem, PurchaseOrderItemAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem, SaleItemAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem, InvoiceItemAdmin)
admin.site.register(CompanyProfile, CompanyProfileAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(CustomUser, CustomUserAdmin)

from django.contrib import admin
from .models import FeeCategory, FeeStructure, Invoice, InvoiceItem, Payment, Expense

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['category', 'class_level', 'session', 'amount']
    list_filter = ['session', 'class_level', 'category']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'total_amount', 'amount_paid', 'balance', 'status']
    list_filter = ['status', 'session']
    search_fields = ['invoice_number', 'student__first_name', 'student__last_name']

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'fee_category', 'amount']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'invoice', 'amount', 'payment_method', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['receipt_number']
    date_hierarchy = 'payment_date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'amount', 'date']
    list_filter = ['category', 'date']
    date_hierarchy = 'date'

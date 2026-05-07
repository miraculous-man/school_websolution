from django.contrib import admin
from .models import ScratchCard, ScratchCardPurchase, ExamAccess


@admin.register(ScratchCard)
class ScratchCardAdmin(admin.ModelAdmin):
    list_display = ('card_code', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('card_code',)
    readonly_fields = ('card_code', 'created_at', 'updated_at')


@admin.register(ScratchCardPurchase)
class ScratchCardPurchaseAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_status', 'payment_ref', 'purchased_at')
    list_filter = ('payment_status', 'purchased_at')
    search_fields = ('payment_ref', 'student__admission_number', 'student__first_name')
    readonly_fields = ('payment_ref', 'purchased_at')


@admin.register(ExamAccess)
class ExamAccessAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'granted_at')
    list_filter = ('granted_at',)
    search_fields = ('student__admission_number', 'exam__title')

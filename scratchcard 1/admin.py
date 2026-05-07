from django.contrib import admin
from .models import ScratchCardBatch, ScratchCard, ScratchCardRedemption
import random
import string

@admin.register(ScratchCardBatch)
class ScratchCardBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'value_per_card', 'purpose', 'created_at']
    list_filter = ['purpose', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)

@admin.register(ScratchCard)
class ScratchCardAdmin(admin.ModelAdmin):
    list_display = ['card_code', 'batch', 'value', 'status', 'redeemed_by', 'expiry_date']
    list_filter = ['status', 'batch', 'created_at', 'expiry_date']
    search_fields = ['card_code', 'pin']
    readonly_fields = ['card_code', 'pin', 'created_at', 'redeemed_at']
    
    fieldsets = (
        ('Card Details', {'fields': ('batch', 'card_code', 'pin', 'value')}),
        ('Status', {'fields': ('status', 'expiry_date')}),
        ('Redemption', {'fields': ('redeemed_by', 'redeemed_at')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.card_code = self.generate_card_code()
            obj.pin = self.generate_pin()
        super().save_model(request, obj, form, change)
    
    @staticmethod
    def generate_card_code():
        return 'SC' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    @staticmethod
    def generate_pin():
        return ''.join(random.choices(string.digits, k=8))

@admin.register(ScratchCardRedemption)
class ScratchCardRedemptionAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'card', 'student', 'amount_redeemed', 'redemption_date']
    list_filter = ['redemption_date', 'card__batch']
    search_fields = ['reference_number', 'card__card_code', 'student__user__first_name']
    readonly_fields = ['reference_number', 'redemption_date', 'card']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['student', 'amount_redeemed']
        return self.readonly_fields

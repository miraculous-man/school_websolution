import uuid
from django.db import models
from django.utils import timezone
from students.models import Student
from core.models import AcademicSession

class ScratchCardBatch(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    value_per_card = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=100, choices=[
        ('discount', 'Discount Voucher'),
        ('fee_waiver', 'Fee Waiver'),
        ('library_credit', 'Library Credit'),
        ('exam_credit', 'Exam Credit'),
        ('reward', 'Reward Points'),
        ('other', 'Other'),
    ])
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.quantity} cards)"

class ScratchCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
    ]
    
    batch = models.ForeignKey(ScratchCardBatch, on_delete=models.CASCADE, related_name='cards')
    card_code = models.CharField(max_length=50, unique=True)
    pin = models.CharField(max_length=20)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    redeemed_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.card_code} - {self.status}"
    
    def is_valid(self):
        if self.status != 'active':
            return False
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        return True

class ScratchCardRedemption(models.Model):
    card = models.OneToOneField(ScratchCard, on_delete=models.CASCADE, related_name='redemption')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    amount_redeemed = models.DecimalField(max_digits=10, decimal_places=2)
    redemption_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=50, unique=True)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"Redemption - {self.card.card_code}"

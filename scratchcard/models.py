from django.db import models
from students.models import Student
from cbt.models import Exam
import secrets
import string


class ScratchCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    
    card_code = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.card_code:
            self.card_code = self.generate_card_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_card_code():
        while True:
            # Generate a 12-character alphanumeric code (shorter for better fit)
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            if not ScratchCard.objects.filter(card_code=code).exists():
                return code
    
    def __str__(self):
        return f"{self.card_code} - {self.status}"


class ScratchCardPurchase(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scratchcard_purchases')
    scratch_card = models.ForeignKey(ScratchCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_ref = models.CharField(max_length=100, unique=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    paystack_auth_url = models.URLField(blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.payment_ref}"
    
    class Meta:
        ordering = ['-purchased_at']


class ExamAccess(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_accesses')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_accesses')
    scratch_card_purchase = models.ForeignKey(ScratchCardPurchase, on_delete=models.CASCADE, related_name='exam_accesses')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'exam']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.exam.title}"


from core.models import Term

class ResultAccess(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='result_accesses')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='result_accesses')
    scratch_card = models.OneToOneField(ScratchCard, on_delete=models.CASCADE, related_name='result_access')
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'term']

    def __str__(self):
        return f"{self.student.full_name} - {self.term}"

from django.db import models
from students.models import Student
from core.models import ClassLevel, AcademicSession, Term


class FeeCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ['category', 'class_level', 'session', 'term']

    def __str__(self):
        return f"{self.category.name} - {self.class_level.name} - {self.amount}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.balance = self.total_amount - self.amount_paid
        if self.balance <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.student}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.fee_category.name} - {self.amount}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('cheque', 'Cheque'),
        ('paystack', 'Paystack'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    receipt_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    paystack_reference = models.CharField(max_length=100, blank=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    received_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        invoice.save()

    def __str__(self):
        return f"{self.receipt_number} - {self.amount}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('utilities', 'Utilities'),
        ('supplies', 'Supplies'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    approved_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"

from django.db import models
from students.models import Student
from teachers.models import Teacher


class BookCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Book Categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True)
    publication_year = models.IntegerField(null=True, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    cover_image = models.ImageField(upload_to='books/', blank=True, null=True)
    description = models.TextField(blank=True)
    shelf_location = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookIssue(models.Model):
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    issued_by = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.book.available_copies -= 1
            self.book.save()
        super().save(*args, **kwargs)

    def return_book(self):
        self.status = 'returned'
        self.book.available_copies += 1
        self.book.save()
        self.save()

    def __str__(self):
        borrower = self.student or self.teacher
        return f"{self.book.title} - {borrower}"

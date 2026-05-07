from django.db import models
from django.contrib.auth.models import User
from core.models import ClassRoom, AcademicSession


class Student(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('graduated', 'Graduated'), ('transferred', 'Transferred')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    admission_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    other_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    admission_date = models.DateField()
    current_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True)
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_address = models.TextField(blank=True)
    parent_occupation = models.CharField(max_length=100, blank=True)
    parent_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_students')
    qr_code = models.ImageField(upload_to='students/qrcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"

    def generate_qr_code(self):
        import qrcode
        from io import BytesIO
        from django.core.files import File
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"STUDENT:{self.admission_number}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f"qr_{self.admission_number}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class StudentClassHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='class_history')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    promoted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['student', 'session']


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey('core.Subject', on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey('core.Term', on_delete=models.CASCADE)
    ca_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="CA Score (40)")
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Exam Score (60)")
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, blank=True)
    remark = models.CharField(max_length=50, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject', 'session', 'term']

    def save(self, *args, **kwargs):
        self.total = self.ca_score + self.exam_score
        self.grade = self.calculate_grade()
        self.remark = self.get_remark()
        super().save(*args, **kwargs)

    def calculate_grade(self):
        if self.total >= 70:
            return 'A'
        elif self.total >= 60:
            return 'B'
        elif self.total >= 50:
            return 'C'
        elif self.total >= 45:
            return 'D'
        elif self.total >= 40:
            return 'E'
        else:
            return 'F'

    def get_remark(self):
        remarks = {
            'A': 'Excellent',
            'B': 'Very Good',
            'C': 'Good',
            'D': 'Fair',
            'E': 'Pass',
            'F': 'Fail'
        }
        return remarks.get(self.grade, '')

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.term}"

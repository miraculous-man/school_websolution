from django.db import models
from django.contrib.auth.models import User
from core.models import Subject, ClassRoom


class Teacher(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('on_leave', 'On Leave')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    date_employed = models.DateField()
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    classes = models.ManyToManyField(ClassRoom, blank=True)
    is_class_teacher = models.BooleanField(default=False)
    class_assigned = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_teacher')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    qr_code = models.ImageField(upload_to='teachers/qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_id} - {self.first_name} {self.last_name}"

    def generate_qr_code(self):
        import qrcode
        from io import BytesIO
        from django.core.files import File
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"TEACHER:{self.staff_id}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f"qr_{self.staff_id}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

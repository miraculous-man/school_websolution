from django.db import models
from django.contrib.auth.models import User


class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='homepage/slides/')
    button_text = models.CharField(max_length=50, blank=True)
    button_link = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class AboutSection(models.Model):
    title = models.CharField(max_length=200, default="About Our School")
    content = models.TextField()
    image = models.ImageField(upload_to='homepage/', blank=True, null=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "About Section"

    def __str__(self):
        return self.title


class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Gallery Categories"

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE, related_name='images')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='homepage/gallery/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube Video URL")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='homepage/blog/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='homepage/events/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    content = models.TextField()
    photo = models.ImageField(upload_to='homepage/testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class StaffMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='homepage/staff/', blank=True, null=True)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Staff Members"

    def __str__(self):
        return self.name


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Admission(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    
    first_name = models.CharField(max_length=50, default='')
    last_name = models.CharField(max_length=50, default='')
    other_name = models.CharField(max_length=50, blank=True, default='')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(default='')
    phone = models.CharField(max_length=20, default='')
    address = models.TextField(default='')
    grade = models.CharField(max_length=20, default='')
    
    parent_name = models.CharField(max_length=100, default='')
    parent_phone = models.CharField(max_length=20, default='')
    parent_email = models.EmailField(default='')
    parent_address = models.TextField(default='')
    parent_occupation = models.CharField(max_length=100, default='')
    
    status = models.CharField(max_length=20, default='Pending')
    
    # Document Uploads
    passport_photo = models.ImageField(upload_to='admissions/passports/', blank=True, null=True)
    nin_image = models.ImageField(upload_to='admissions/nin/', blank=True, null=True)
    state_of_origin_cert = models.ImageField(upload_to='admissions/origin/', blank=True, null=True)
    first_school_leaving_cert = models.ImageField(upload_to='admissions/certificates/', blank=True, null=True)
    other_documents = models.FileField(upload_to='admissions/others/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def student_name(self):
        return f"{self.first_name} {self.last_name}"

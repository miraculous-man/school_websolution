from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('librarian', 'Librarian'),
        ('accountant', 'Accountant'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    theme_mode = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    theme_image = models.ImageField(upload_to='theme_images/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#0d6efd')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    accent_color = models.CharField(max_length=7, default='#198754')
    navbar_color = models.CharField(max_length=7, default='#2c3e50')
    sidebar_color = models.CharField(max_length=7, default='#34495e')
    background_color = models.CharField(max_length=7, default='#ffffff')
    text_color = models.CharField(max_length=7, default='#333333')
    
    # Dashboard background images
    library_bg = models.ImageField(upload_to='dashboard_bg/', blank=True, null=True)
    finance_bg = models.ImageField(upload_to='dashboard_bg/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'admin' if instance.is_superuser else 'student'
        UserProfile.objects.create(user=instance, role=role)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        role = 'admin' if instance.is_superuser else 'student'
        UserProfile.objects.create(user=instance, role=role)

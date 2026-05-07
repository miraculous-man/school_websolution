from django import forms
from .models import UserProfile


class ThemeSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['theme_mode', 'theme_image', 'library_bg', 'finance_bg', 'primary_color', 'secondary_color', 
                  'accent_color', 'navbar_color', 'sidebar_color', 'background_color', 'text_color']
        widgets = {
            'theme_mode': forms.RadioSelect(choices=UserProfile.THEME_CHOICES),
            'theme_image': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
            'library_bg': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
            'finance_bg': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'navbar_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'sidebar_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

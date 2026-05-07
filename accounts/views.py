from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import ThemeSettingsForm, ProfileForm
from .utils import extract_dominant_colors


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not username or not email or not password:
            messages.error(request, 'Please fill in all required fields.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('accounts:login')
    
    return render(request, 'accounts/signup.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        profile.phone = request.POST.get('phone', '')
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def theme_settings_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ThemeSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            
            if 'theme_image' in request.FILES:
                colors = extract_dominant_colors(request.FILES['theme_image'])
                profile.primary_color = colors[0] if len(colors) > 0 else profile.primary_color
                profile.secondary_color = colors[1] if len(colors) > 1 else profile.secondary_color
                profile.accent_color = colors[2] if len(colors) > 2 else profile.accent_color
                profile.navbar_color = colors[3] if len(colors) > 3 else profile.navbar_color
                profile.sidebar_color = colors[4] if len(colors) > 4 else profile.sidebar_color
            
            profile.save()
            messages.success(request, 'Theme settings updated successfully!')
            return redirect('accounts:theme_settings')
    else:
        form = ThemeSettingsForm(instance=profile)
    
    return render(request, 'accounts/theme_settings.html', {'form': form, 'profile': profile})


@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully! Please login again.')
            return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')

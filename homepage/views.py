from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import (
    HeroSlide, AboutSection, GalleryCategory, GalleryImage,
    BlogPost, Event, Testimonial, ContactMessage, StaffMember, FAQ, Admission
)
from core.models import SchoolSettings


def verify_student_api(request):
    admission_number = request.GET.get('admission_number')
    if not admission_number:
        return JsonResponse({'success': False, 'error': 'No admission number provided'})
    
    from students.models import Student
    try:
        # Check if it has the "STUDENT:" prefix from QR code
        if admission_number.startswith('STUDENT:'):
            admission_number = admission_number.replace('STUDENT:', '')
            
        student = Student.objects.get(admission_number=admission_number)
        data = {
            'success': True,
            'full_name': student.full_name,
            'admission_number': student.admission_number,
            'current_class': str(student.current_class or 'N/A'),
            'photo_url': student.photo.url if student.photo else 'https://ui-avatars.com/api/?name=' + student.full_name.replace(' ', '+'),
            'status': student.get_status_display(),
            'gender': student.get_gender_display(),
            'admission_date': student.admission_date.strftime('%d %b, %Y') if student.admission_date else 'N/A',
            'date_of_birth': student.date_of_birth.strftime('%d %b, %Y') if student.date_of_birth else 'N/A',
            'phone': student.phone or 'N/A',
            'email': student.email or 'N/A',
        }
        return JsonResponse(data)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})

def home(request):
    settings = SchoolSettings.objects.first()
    slides = HeroSlide.objects.filter(is_active=True)
    about = AboutSection.objects.first()
    events = Event.objects.filter(is_featured=True)[:3]
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    staff = StaffMember.objects.filter(is_featured=True)[:4]
    blog_posts = BlogPost.objects.filter(is_published=True)[:3]
    faqs = FAQ.objects.filter(is_active=True)[:5]

    context = {
        'settings': settings,
        'slides': slides,
        'about': about,
        'events': events,
        'testimonials': testimonials,
        'staff': staff,
        'blog_posts': blog_posts,
        'faqs': faqs,
    }
    return render(request, 'homepage/home.html', context)


def home_v2(request):
    settings = SchoolSettings.objects.first()
    slides = HeroSlide.objects.filter(is_active=True)
    about = AboutSection.objects.first()
    events = Event.objects.filter(is_featured=True)[:3]
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    staff = StaffMember.objects.filter(is_featured=True)
    blog_posts = BlogPost.objects.filter(is_published=True)[:5]
    faqs = FAQ.objects.filter(is_active=True)[:5]

    context = {
        'settings': settings,
        'slides': slides,
        'about': about,
        'events': events,
        'testimonials': testimonials,
        'staff': staff,
        'blog_posts': blog_posts,
        'faqs': faqs,
    }
    return render(request, 'homepage/home_v2.html', context)


def about(request):
    settings = SchoolSettings.objects.first()
    about_section = AboutSection.objects.first()
    staff = StaffMember.objects.filter(is_featured=True)
    
    context = {
        'settings': settings,
        'about': about_section,
        'staff': staff,
    }
    return render(request, 'homepage/about.html', context)


def contact(request):
    settings = SchoolSettings.objects.first()
    
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            subject=request.POST.get('subject', ''),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('homepage:contact')
    
    context = {
        'settings': settings,
    }
    return render(request, 'homepage/contact.html', context)


def gallery(request):
    settings = SchoolSettings.objects.first()
    categories = GalleryCategory.objects.all()
    category_id = request.GET.get('category')
    
    if category_id:
        images = GalleryImage.objects.filter(category_id=category_id)
    else:
        images = GalleryImage.objects.all()
    
    paginator = Paginator(images, 12)
    page = request.GET.get('page')
    images = paginator.get_page(page)
    
    context = {
        'settings': settings,
        'categories': categories,
        'images': images,
        'selected_category': category_id,
    }
    return render(request, 'homepage/gallery.html', context)


def blog(request):
    settings = SchoolSettings.objects.first()
    posts = BlogPost.objects.filter(is_published=True)
    
    paginator = Paginator(posts, 9)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'settings': settings,
        'posts': posts,
    }
    return render(request, 'homepage/blog.html', context)


def blog_detail(request, slug):
    settings = SchoolSettings.objects.first()
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    related_posts = BlogPost.objects.filter(is_published=True).exclude(id=post.id)[:3]
    
    context = {
        'settings': settings,
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'homepage/blog_detail.html', context)


def events(request):
    settings = SchoolSettings.objects.first()
    events_list = Event.objects.all()
    
    paginator = Paginator(events_list, 9)
    page = request.GET.get('page')
    events_list = paginator.get_page(page)
    
    context = {
        'settings': settings,
        'events': events_list,
    }
    return render(request, 'homepage/events.html', context)


def event_detail(request, pk):
    settings = SchoolSettings.objects.first()
    event = get_object_or_404(Event, pk=pk)
    
    context = {
        'settings': settings,
        'event': event,
    }
    return render(request, 'homepage/event_detail.html', context)


def faqs(request):
    settings = SchoolSettings.objects.first()
    faqs_list = FAQ.objects.filter(is_active=True)
    
    context = {
        'settings': settings,
        'faqs': faqs_list,
    }
    return render(request, 'homepage/faqs.html', context)


def apply(request):
    settings_obj = SchoolSettings.objects.first()
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        other_name = request.POST.get('other_name', '')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        grade = request.POST.get('grade')
        
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        parent_email = request.POST.get('parent_email')
        parent_address = request.POST.get('parent_address')
        parent_occupation = request.POST.get('parent_occupation')
        
        new_admission = Admission.objects.create(
            first_name=first_name,
            last_name=last_name,
            other_name=other_name,
            gender=gender,
            date_of_birth=date_of_birth,
            email=email,
            phone=phone,
            address=address,
            grade=grade,
            parent_name=parent_name,
            parent_phone=parent_phone,
            parent_email=parent_email,
            parent_address=parent_address,
            parent_occupation=parent_occupation,
            status='Pending'
        )
        
        # Notify Admins
        from notifications.models import Notification
        from django.contrib.auth.models import User
        from django.core.mail import send_mail
        from django.conf import settings
        
        admins = User.objects.filter(profile__role='admin')
        notification_title = "New Student Application"
        notification_message = f"A new student, {first_name} {last_name}, has applied for {grade}."
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title=notification_title,
                message=notification_message,
                notification_type='info',
                link='/dashboard/admissions/'
            )
            
            # Send Email to Admin
            if admin.email:
                try:
                    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
                    send_mail(
                        subject=f"Admission Alert: {name}",
                        message=f"Hello {admin.get_full_name() or admin.username},\n\n{notification_message}\n\nPlease login to the admin portal to review the application.",
                        from_email=from_email,
                        recipient_list=[admin.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    # Log the error if mail fails but don't stop the process
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send admission alert email to {admin.email}: {e}")
        
        return redirect('homepage:letter', pk=new_admission.pk)
    
    context = {
        'settings': settings_obj,
    }
    return render(request, 'homepage/apply.html', context)


def letter(request, pk):
    settings = SchoolSettings.objects.first()
    admission = get_object_or_404(Admission, pk=pk)
    context = {
        'settings': settings,
        'admission': admission,
    }
    return render(request, 'homepage/letter.html', context)


def download_letter_pdf(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Simple PDF generation
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "MODERN EXCELLENCE SCHOOL")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, "Admission Letter")
    p.drawString(100, 710, f"Date: {admission.created_at.strftime('%B %d, %Y')}")
    
    p.drawString(100, 670, f"Dear {admission.student_name},")
    p.drawString(100, 650, f"We are pleased to inform you that your application for admission to {admission.grade}")
    p.drawString(100, 630, "has been reviewed and approved.")
    
    p.drawString(100, 590, "Sincerely,")
    p.drawString(100, 570, "The Admissions Office")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', 
                        headers={'Content-Disposition': f'attachment; filename="admission_letter_{admission.pk}.pdf"'})


@login_required
def admission_list(request):
    admissions = Admission.objects.all().order_by('-created_at')
    return render(request, 'homepage/admission_list.html', {'admissions': admissions})


from datetime import date, timedelta
import random
import string

@login_required
def convert_to_student(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    settings_obj = SchoolSettings.objects.first()
    
    # Logic to create student and user account from admission
    from django.contrib.auth.models import User
    from students.models import Student
    from core.models import ClassRoom
    import random
    import string
    
    # Try to find a matching classroom for the grade
    grade_map = {
        'Grade 1': 'Primary 1',
        'Grade 2': 'Primary 2',
        'Grade 3': 'Primary 3',
        'Grade 4': 'Primary 4',
        'Grade 5': 'Primary 5',
    }
    class_name = grade_map.get(admission.grade)
    classroom = ClassRoom.objects.filter(name__icontains=admission.grade).first() or ClassRoom.objects.first()

    adm_no = "ADM" + "".join(random.choices(string.digits, k=5))
    
    # Create User Account
    username = admission.email.split('@')[0] + "".join(random.choices(string.digits, k=3))
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    user = User.objects.create_user(
        username=username,
        email=admission.email,
        password=password,
        first_name=admission.first_name,
        last_name=admission.last_name
    )
    
    # Ensure UserProfile role is set to student
    if hasattr(user, 'profile'):
        user.profile.role = 'student'
        user.profile.save()

    # Create Student record
    student = Student.objects.create(
        user=user,
        admission_number=adm_no,
        first_name=admission.first_name,
        last_name=admission.last_name,
        other_name=admission.other_name,
        gender=admission.gender,
        date_of_birth=admission.date_of_birth,
        email=admission.email,
        phone=admission.phone,
        address=admission.address,
        current_class=classroom,
        admission_date=date.today(),
        parent_name=admission.parent_name,
        parent_phone=admission.parent_phone,
        parent_email=admission.parent_email,
        parent_address=admission.parent_address,
        parent_occupation=admission.parent_occupation,
    )
    
    admission.status = 'Enrolled'
    admission.save()
    
    # Notify Student (In-app)
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=user,
            title="Welcome to School!",
            message=f"Your admission has been confirmed. Welcome to {settings_obj.school_name if settings_obj else 'our school'}!",
            notification_type='success',
            link='/dashboard/'
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create student welcome notification: {e}")

    # Send Acceptance Email
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        
        # Fresh fetch to ensure we have the absolute latest data for this specific PK
        current_admission = Admission.objects.get(pk=pk)
        
        subject = f"Admission Accepted - {settings_obj.school_name if settings_obj else 'School Management System'}"
        from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
        
        context = {
            'student_name': current_admission.student_name,
            'school_name': settings_obj.school_name if settings_obj else 'Our School',
            'grade': current_admission.grade,
            'username': username,
            'password': password,
            'login_url': request.build_absolute_uri('/accounts/login/'),
        }
        
        html_content = render_to_string('emails/admission_acceptance.html', context)
        text_content = f"Congratulations {current_admission.student_name}! Your admission to {context['school_name']} has been accepted. Login: {context['login_url']} Username: {username}, Password: {password}"
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [current_admission.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send admission acceptance email to {admission.email}: {e}")

    messages.success(request, f'Student {student.full_name} enrolled! Username: {username}, Password: {password}')
    return redirect('homepage:admission_list')

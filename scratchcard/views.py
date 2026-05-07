import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from students.models import Student
from cbt.models import Exam, ExamAttempt
from .models import ScratchCardPurchase, ScratchCard, ExamAccess


from core.models import SchoolSettings

@login_required
def buy_scratch_card(request):
    try:
        if request.user.profile.role == 'parent':
            # For parents, show student selection if they have multiple
            student_id = request.GET.get('student_id')
            if student_id:
                student = get_object_or_404(Student, id=student_id, parent_user=request.user)
            else:
                student = Student.objects.filter(parent_user=request.user).first()
                if not student:
                    messages.error(request, "No students linked to your account.")
                    return redirect('students:parent_dashboard')
        else:
            student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Only students or parents can purchase scratch cards.")
        return redirect('core:dashboard')
    
    # Get current price from school settings
    school_settings = SchoolSettings.objects.first()
    card_price = school_settings.scratch_card_price if school_settings else 1000.00
    
    if request.method == 'POST':
        try:
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            
            import uuid
            payment_ref = f"SCRATCH-{student.admission_number}-{uuid.uuid4().hex[:8].upper()}"
            
            purchase = ScratchCardPurchase.objects.create(
                student=student,
                amount=card_price,
                payment_ref=payment_ref,
            )
            
            payload = {
                "email": student.email or student.user.email,
                "amount": int(card_price * 100),
                "reference": payment_ref,
                "callback_url": request.build_absolute_uri('/scratchcard/callback/'),
                "metadata": {
                    "student_id": student.id,
                    "purchase_id": purchase.id,
                }
            }
            
            # Print for debugging in logs
            print(f"Initializing Paystack with ref: {payment_ref}")
            print(f"Payload: {payload}")
            
            response = requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"Paystack Status Code: {response.status_code}")
            print(f"Paystack Raw Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    purchase.paystack_access_code = data['data']['access_code']
                    purchase.paystack_auth_url = data['data']['authorization_url']
                    purchase.save()
                    return redirect(data['data']['authorization_url'])
                else:
                    messages.error(request, "Failed to initialize payment.")
            else:
                messages.error(request, "Payment service unavailable.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('scratchcard:dashboard')
    
    # Get current price from school settings
    school_settings = SchoolSettings.objects.first()
    card_price = school_settings.scratch_card_price if school_settings else 1000.00
    
    return render(request, 'scratchcard/buy_scratch_card.html', {
        'student': student,
        'card_price': card_price,
    })


@login_required
def payment_callback(request):
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, "Invalid payment reference")
        return redirect('scratchcard:dashboard')
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }
        
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                purchase = ScratchCardPurchase.objects.get(payment_ref=reference)
                purchase.payment_status = 'completed'
                purchase.completed_at = timezone.now()
                
                available_card = ScratchCard.objects.filter(status='active').first()
                if available_card:
                    purchase.scratch_card = available_card
                    available_card.status = 'used'
                    available_card.save()
                
                purchase.save()
                messages.success(request, "Payment successful! Scratch card activated.")
                return redirect('scratchcard:dashboard')
            else:
                purchase = ScratchCardPurchase.objects.get(payment_ref=reference)
                purchase.payment_status = 'failed'
                purchase.save()
                messages.error(request, "Payment failed.")
                return redirect('scratchcard:buy')
    except ScratchCardPurchase.DoesNotExist:
        messages.error(request, "Payment record not found.")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('scratchcard:dashboard')


@login_required
def scratchcard_dashboard(request):
    try:
        if request.user.profile.role == 'parent':
            student_id = request.GET.get('student_id')
            if student_id:
                student = get_object_or_404(Student, id=student_id, parent_user=request.user)
            else:
                student = Student.objects.filter(parent_user=request.user).first()
                if not student:
                    messages.error(request, "No students linked to your account.")
                    return redirect('students:parent_dashboard')
        else:
            student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Only students or parents can access the scratch card dashboard.")
        return redirect('core:dashboard')
    
    active_purchase = ScratchCardPurchase.objects.filter(
        student=student,
        payment_status='completed'
    ).first()
    
    if active_purchase:
        accessible_exams = Exam.objects.filter(
            student_accesses__scratch_card_purchase=active_purchase
        ).distinct()
    else:
        accessible_exams = Exam.objects.none()
    
    all_exams = Exam.objects.filter(status='published')
    
    # Get current price from school settings
    school_settings = SchoolSettings.objects.first()
    card_price = school_settings.scratch_card_price if school_settings else 1000.00
    
    context = {
        'student': student,
        'active_purchase': active_purchase,
        'accessible_exams': accessible_exams,
        'all_exams': all_exams,
        'card_price': card_price,
    }
    
    return render(request, 'scratchcard/dashboard.html', context)


@login_required
def activate_exam_for_student(request, exam_id):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Only students can activate exams.")
        return redirect('core:dashboard')
    exam = get_object_or_404(Exam, id=exam_id)
    
    active_purchase = ScratchCardPurchase.objects.filter(
        student=student,
        payment_status='completed'
    ).first()
    
    if not active_purchase:
        messages.error(request, "Please purchase a scratch card first.")
        return redirect('scratchcard:buy')
    
    exam_access, created = ExamAccess.objects.get_or_create(
        student=student,
        exam=exam,
        defaults={'scratch_card_purchase': active_purchase}
    )
    
    if created:
        messages.success(request, f"Access granted to {exam.title}")
    else:
        messages.info(request, f"You already have access to {exam.title}")
    
    return redirect('cbt:exam_list')

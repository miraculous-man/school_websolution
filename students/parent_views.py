from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Student, Result
from attendance.models import StudentAttendance
from finance.models import Invoice, Payment
import uuid
from django.conf import settings
import requests

@login_required
def parent_student_pay_paystack(request, invoice_id):
    if request.user.profile.role != 'parent':
        return redirect('core:dashboard')
    
    invoice = get_object_or_404(Invoice, id=invoice_id, student__parent_user=request.user)
    
    if invoice.balance <= 0:
        messages.info(request, 'Invoice is already fully paid.')
        return redirect('students:parent_student_detail', student_id=invoice.student.id)
    
    if not settings.PAYSTACK_SECRET_KEY:
        messages.error(request, "Paystack is not configured. Please contact the administrator.")
        return redirect('students:parent_student_detail', student_id=invoice.student.id)
    
    amount_kobo = int(float(invoice.balance) * 100)
    email = invoice.student.parent_email or request.user.email or f"{invoice.student.admission_number}@school.edu"
    reference = f"PAY{uuid.uuid4().hex[:12].upper()}"
    
    payment = Payment.objects.create(
        receipt_number=reference,
        invoice=invoice,
        amount=invoice.balance,
        payment_method='paystack',
        payment_status='pending',
        paystack_reference=reference,
        payment_date=timezone.now().date(),
    )
    
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    data = {
        'email': email,
        'amount': amount_kobo,
        'reference': reference,
        'callback_url': request.build_absolute_uri(f'/finance/paystack/verify/{payment.pk}/'),
        'metadata': {
            'invoice_id': invoice.pk,
            'student_id': invoice.student.pk,
            'payment_id': payment.pk,
            'parent_id': request.user.id
        }
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            json=data,
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        if result.get('status'):
            payment.paystack_access_code = result['data']['access_code']
            payment.save()
            return redirect(result['data']['authorization_url'])
        else:
            payment.payment_status = 'failed'
            payment.save()
            messages.error(request, f"Payment initialization failed: {result.get('message', 'Unknown error')}")
            return redirect('students:parent_student_detail', student_id=invoice.student.id)
    except Exception as e:
        payment.payment_status = 'failed'
        payment.save()
        messages.error(request, f"Payment error: {str(e)}")
        # Log the error for debugging
        print(f"PAYSTACK ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect('students:parent_student_detail', student_id=invoice.student.id)

@login_required
def parent_dashboard(request):
    if request.user.profile.role != 'parent':
        return render(request, '403.html', status=403)
    
    students = Student.objects.filter(parent_user=request.user)
    return render(request, 'students/parent_dashboard.html', {'students': students})

@login_required
def parent_student_detail(request, student_id):
    if request.user.profile.role != 'parent':
        return render(request, '403.html', status=403)
    
    student = get_object_or_404(Student, id=student_id, parent_user=request.user)
    
    from scratchcard.models import ResultAccess
    from core.models import Term, AcademicSession
    
    selected_session_id = request.GET.get('session')
    selected_term_id = request.GET.get('term')
    
    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    
    results = []
    has_access = False
    term = None
    
    if selected_session_id and selected_term_id:
        term = get_object_or_404(Term, id=selected_term_id)
        # Check if parent has access via scratch card for this student and term
        has_access = ResultAccess.objects.filter(student=student, term=term).exists()
        
        if has_access:
            results = Result.objects.filter(
                student=student,
                session_id=selected_session_id,
                term_id=selected_term_id
            ).select_related('subject')
    
    attendance = StudentAttendance.objects.filter(student=student).order_by('-date')[:10]
    invoices = Invoice.objects.filter(student=student).order_by('-created_at')
    
    return render(request, 'students/parent_student_detail.html', {
        'student': student,
        'results': results,
        'attendance': attendance,
        'sessions': sessions,
        'terms': terms,
        'selected_session': selected_session_id,
        'selected_term': selected_term_id,
        'has_access': has_access,
        'term': term,
        'invoices': invoices
    })

@login_required
def pay_invoice_offline(request, invoice_id):
    if request.user.profile.role != 'parent':
        return redirect('core:dashboard')
    
    invoice = get_object_or_404(Invoice, id=invoice_id, student__parent_user=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            from decimal import Decimal
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount > invoice.balance:
                messages.error(request, "Amount exceeds balance.")
                return redirect('students:parent_student_detail', student_id=invoice.student.id)
            
            # Create a pending payment record
            Payment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method='bank_transfer',
                payment_status='pending',
                payment_date=timezone.now().date(),
                receipt_number=f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                remarks=f"Payment request submitted by parent for {invoice.invoice_number}"
            )
            messages.success(request, f"Payment request for {amount} submitted. Please complete the bank transfer and notify the school.")
        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            
    return redirect('students:parent_student_detail', student_id=invoice.student.id)

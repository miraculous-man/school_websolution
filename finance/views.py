from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from datetime import date
from .models import FeeCategory, FeeStructure, Invoice, InvoiceItem, Payment, Expense
from students.models import Student
from core.models import ClassLevel, AcademicSession, Term
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
import io
import uuid


@login_required
def finance_dashboard(request):
    total_invoiced = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_collected = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = Invoice.objects.filter(status__in=['pending', 'partial']).aggregate(total=Sum('balance'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    recent_payments = Payment.objects.select_related('invoice__student').order_by('-created_at')[:10]
    pending_invoices = Invoice.objects.filter(status__in=['pending', 'partial']).select_related('student')[:10]
    
    context = {
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_expenses': total_expenses,
        'net_income': total_collected - total_expenses,
        'recent_payments': recent_payments,
        'pending_invoices': pending_invoices,
    }
    return render(request, 'finance/dashboard.html', context)


@login_required
def fee_category_list(request):
    categories = FeeCategory.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        FeeCategory.objects.create(name=name, description=description)
        messages.success(request, f'Fee category "{name}" created!')
        return redirect('finance:fee_categories')
    
    return render(request, 'finance/fee_categories.html', {'categories': categories})


@login_required
def fee_structure_list(request):
    structures = FeeStructure.objects.select_related('category', 'class_level', 'session').all()
    categories = FeeCategory.objects.all()
    class_levels = ClassLevel.objects.all()
    sessions = AcademicSession.objects.all()
    
    if request.method == 'POST':
        FeeStructure.objects.create(
            category_id=request.POST.get('category'),
            class_level_id=request.POST.get('class_level'),
            session_id=request.POST.get('session'),
            amount=request.POST.get('amount'),
        )
        messages.success(request, 'Fee structure created!')
        return redirect('finance:fee_structures')
    
    context = {
        'structures': structures,
        'categories': categories,
        'class_levels': class_levels,
        'sessions': sessions,
    }
    return render(request, 'finance/fee_structures.html', context)


@login_required
def invoice_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    invoices = Invoice.objects.select_related('student').all()
    
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    invoices = invoices.order_by('-created_at')
    
    return render(request, 'finance/invoice_list.html', {
        'invoices': invoices,
        'query': query,
        'status_filter': status_filter,
    })


@login_required
def invoice_create(request):
    students = Student.objects.filter(status='active')
    categories = FeeCategory.objects.all()
    sessions = AcademicSession.objects.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        session_id = request.POST.get('session')
        due_date = request.POST.get('due_date') or None
        
        category_ids = request.POST.getlist('categories')
        amounts = request.POST.getlist('amounts')
        
        total = sum(float(a) for a in amounts if a)
        
        invoice = Invoice.objects.create(
            invoice_number=f"INV{uuid.uuid4().hex[:8].upper()}",
            student_id=student_id,
            session_id=session_id,
            total_amount=total,
            balance=total,
            due_date=due_date,
        )
        
        for cat_id, amount in zip(category_ids, amounts):
            if cat_id and amount:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    fee_category_id=cat_id,
                    amount=float(amount),
                )
        
        messages.success(request, f'Invoice {invoice.invoice_number} created!')
        return redirect('finance:invoice_detail', pk=invoice.pk)
    
    return render(request, 'finance/invoice_form.html', {
        'students': students,
        'categories': categories,
        'sessions': sessions,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.select_related('fee_category').all()
    payments = invoice.payments.all().order_by('-payment_date')
    
    return render(request, 'finance/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments,
    })


@login_required
def record_payment(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    
    if request.method == 'POST':
        payment = Payment.objects.create(
            receipt_number=f"RCP{uuid.uuid4().hex[:8].upper()}",
            invoice=invoice,
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('payment_method', 'cash'),
            payment_date=request.POST.get('payment_date', date.today()),
            reference=request.POST.get('reference', ''),
            remarks=request.POST.get('remarks', ''),
        )
        messages.success(request, f'Payment of {payment.amount} recorded!')
        return redirect('finance:invoice_detail', pk=invoice.pk)
    
    return render(request, 'finance/payment_form.html', {'invoice': invoice})


@login_required
def print_receipt(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 2*cm, "PAYMENT RECEIPT")
    
    p.setFont("Helvetica", 12)
    y = height - 4*cm
    
    p.drawString(2*cm, y, f"Receipt No: {payment.receipt_number}")
    p.drawString(12*cm, y, f"Date: {payment.payment_date}")
    
    y -= 1*cm
    p.drawString(2*cm, y, f"Student: {payment.invoice.student.full_name}")
    
    y -= 0.7*cm
    p.drawString(2*cm, y, f"Invoice: {payment.invoice.invoice_number}")
    
    y -= 1.5*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, f"Amount Paid: ${payment.amount}")
    
    y -= 0.7*cm
    p.setFont("Helvetica", 12)
    p.drawString(2*cm, y, f"Payment Method: {payment.get_payment_method_display()}")
    
    if payment.reference:
        y -= 0.7*cm
        p.drawString(2*cm, y, f"Reference: {payment.reference}")
    
    y -= 2*cm
    p.drawString(2*cm, y, f"Invoice Total: ${payment.invoice.total_amount}")
    p.drawString(2*cm, y - 0.5*cm, f"Total Paid: ${payment.invoice.amount_paid}")
    p.drawString(2*cm, y - 1*cm, f"Balance: ${payment.invoice.balance}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
    return response


@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    
    if request.method == 'POST':
        Expense.objects.create(
            title=request.POST.get('title'),
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description', ''),
            date=request.POST.get('date', date.today()),
        )
        messages.success(request, 'Expense recorded!')
        return redirect('finance:expenses')
    
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'finance/expense_list.html', {
        'expenses': expenses,
        'total': total,
    })


@login_required
def paystack_initialize(request, invoice_pk):
    import requests
    from django.conf import settings
    
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    
    if invoice.balance <= 0:
        messages.info(request, 'Invoice is already fully paid.')
        return redirect('finance:invoice_detail', pk=invoice.pk)
    
    amount_kobo = int(float(invoice.balance) * 100)
    
    email = invoice.student.email or invoice.student.parent_email or f"{invoice.student.admission_number}@school.edu"
    
    reference = f"PAY{uuid.uuid4().hex[:12].upper()}"
    
    payment = Payment.objects.create(
        receipt_number=reference,
        invoice=invoice,
        amount=invoice.balance,
        payment_method='paystack',
        payment_status='pending',
        paystack_reference=reference,
        payment_date=date.today(),
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
            return redirect('finance:invoice_detail', pk=invoice.pk)
    except Exception as e:
        payment.payment_status = 'failed'
        payment.save()
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('finance:invoice_detail', pk=invoice.pk)


def paystack_verify(request, payment_pk):
    import requests
    from django.conf import settings
    
    payment = get_object_or_404(Payment, pk=payment_pk)
    
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    
    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{payment.paystack_reference}',
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        if result.get('status') and result['data']['status'] == 'success':
            payment.payment_status = 'completed'
            payment.save()
            
            invoice = payment.invoice
            total_paid = invoice.payments.filter(payment_status='completed').aggregate(total=Sum('amount'))['total'] or 0
            invoice.amount_paid = total_paid
            invoice.save()
            
            messages.success(request, 'Payment successful! Thank you.')
        else:
            payment.payment_status = 'failed'
            payment.save()
            messages.error(request, 'Payment verification failed.')
    except Exception as e:
        messages.error(request, f"Verification error: {str(e)}")
    
    return redirect('finance:invoice_detail', pk=payment.invoice.pk)


def paystack_webhook(request):
    import json
    import hashlib
    import hmac
    from django.conf import settings
    from django.views.decorators.csrf import csrf_exempt
    
    signature = request.headers.get('x-paystack-signature', '')
    
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        request.body,
        hashlib.sha512
    ).hexdigest()
    
    if signature != computed:
        return JsonResponse({'status': 'invalid signature'}, status=400)
    
    try:
        data = json.loads(request.body)
        event = data.get('event')
        
        if event == 'charge.success':
            reference = data['data']['reference']
            payment = Payment.objects.filter(paystack_reference=reference).first()
            
            if payment and payment.payment_status != 'completed':
                payment.payment_status = 'completed'
                payment.save()
                
                invoice = payment.invoice
                total_paid = invoice.payments.filter(payment_status='completed').aggregate(total=Sum('amount'))['total'] or 0
                invoice.amount_paid = total_paid
                invoice.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

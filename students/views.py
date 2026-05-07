from django.shortcuts import render, redirect, get_object_or_404
from .parent_views import parent_dashboard, parent_student_detail, pay_invoice_offline, parent_student_pay_paystack
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Avg, Sum
from .models import Student, StudentClassHistory, Result
from core.models import ClassRoom, ClassLevel, Subject, AcademicSession, Term
from teachers.models import Teacher
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from decimal import Decimal
import io
import uuid


@login_required
def student_list(request):
    query = request.GET.get('q', '')
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', 'active')
    
    students = Student.objects.all()
    
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query)
        )
    
    if class_filter:
        students = students.filter(current_class_id=class_filter)
    
    if status_filter:
        students = students.filter(status=status_filter)
    
    classrooms = ClassRoom.objects.all()
    
    context = {
        'students': students,
        'classrooms': classrooms,
        'query': query,
        'class_filter': class_filter,
        'status_filter': status_filter,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    class_history = student.class_history.select_related('classroom', 'session').all()
    return render(request, 'students/student_detail.html', {
        'student': student,
        'class_history': class_history,
    })


@login_required
def student_add(request):
    from django.contrib.auth.models import User
    classrooms = ClassRoom.objects.all()
    parent_users = User.objects.filter(profile__role='parent')
    
    if request.method == 'POST':
        admission_number = request.POST.get('admission_number') or f"STU{uuid.uuid4().hex[:6].upper()}"
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email', '')
        
        student = Student(
            admission_number=admission_number,
            first_name=first_name,
            last_name=last_name,
            other_name=request.POST.get('other_name', ''),
            gender=request.POST.get('gender'),
            date_of_birth=request.POST.get('date_of_birth'),
            admission_date=request.POST.get('admission_date'),
            current_class_id=request.POST.get('current_class') or None,
            address=request.POST.get('address', ''),
            phone=request.POST.get('phone', ''),
            email=email,
            parent_name=request.POST.get('parent_name', ''),
            parent_phone=request.POST.get('parent_phone', ''),
            parent_email=request.POST.get('parent_email', ''),
            parent_address=request.POST.get('parent_address', ''),
            parent_occupation=request.POST.get('parent_occupation', ''),
            parent_user_id=request.POST.get('parent_user') or None,
        )
        
        if 'photo' in request.FILES:
            student.photo = request.FILES['photo']
        
        student.save()
        student.generate_qr_code()
        student.save()
        
        try:
            username = f"{first_name.lower()}.{last_name.lower()}"
            if User.objects.filter(username=username).exists():
                username = f"{username}_{admission_number.lower()}"
            password = f"{admission_number}@2024"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            student.user = user
            student.save()
            messages.success(request, f'Student {student.full_name} added! Login: {username} / {password}')
        except Exception as e:
            messages.success(request, f'Student {student.full_name} added! (Account creation failed)')
        
        return redirect('students:student_list')
    
    return render(request, 'students/student_form.html', {
        'classrooms': classrooms,
        'parent_users': parent_users
    })


@login_required
def student_edit(request, pk):
    from django.contrib.auth.models import User
    student = get_object_or_404(Student, pk=pk)
    classrooms = ClassRoom.objects.all()
    parent_users = User.objects.filter(profile__role='parent')
    
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.other_name = request.POST.get('other_name', '')
        student.gender = request.POST.get('gender')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.admission_date = request.POST.get('admission_date')
        student.current_class_id = request.POST.get('current_class') or None
        student.address = request.POST.get('address', '')
        student.phone = request.POST.get('phone', '')
        student.email = request.POST.get('email', '')
        student.status = request.POST.get('status', 'active')
        student.parent_name = request.POST.get('parent_name', '')
        student.parent_phone = request.POST.get('parent_phone', '')
        student.parent_email = request.POST.get('parent_email', '')
        student.parent_address = request.POST.get('parent_address', '')
        student.parent_occupation = request.POST.get('parent_occupation', '')
        student.parent_user_id = request.POST.get('parent_user') or None
        
        if 'photo' in request.FILES:
            student.photo = request.FILES['photo']
        
        student.save()
        messages.success(request, f'Student {student.full_name} updated successfully!')
        return redirect('students:student_detail', pk=student.pk)
    
    return render(request, 'students/student_form.html', {
        'student': student, 
        'classrooms': classrooms,
        'parent_users': parent_users
    })


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} deleted successfully!')
        return redirect('students:student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


@login_required
def generate_id_card(request, pk):
    from reportlab.pdfgen.textobject import PDFTextObject
    student = get_object_or_404(Student, pk=pk)
    
    if not student.qr_code:
        student.generate_qr_code()
        student.save()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(3.5*inch, 2.25*inch))
    
    p.setTitle(f"Student ID - {student.full_name}")
    
    p.setLineWidth(2)
    p.setStrokeColor(colors.HexColor('#1e40af'))
    p.rect(0.05*inch, 0.05*inch, 3.4*inch, 2.15*inch)
    
    p.setFillColor(colors.HexColor('#1e40af'))
    p.rect(0.05*inch, 1.8*inch, 3.4*inch, 0.4*inch, fill=True)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(1.75*inch, 2.05*inch, "STUDENT ID CARD")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(0.2*inch, 1.6*inch, student.full_name.upper())
    
    p.setFont("Helvetica", 7)
    p.drawString(0.2*inch, 1.35*inch, f"ID: {student.admission_number}")
    p.drawString(0.2*inch, 1.15*inch, f"Class: {student.current_class or 'N/A'}")
    p.drawString(0.2*inch, 0.95*inch, f"DOB: {student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else 'N/A'}")
    p.drawString(0.2*inch, 0.75*inch, f"Status: {student.get_status_display()}")
    
    if student.qr_code:
        from django.core.files.storage import default_storage
        import os
        try:
            qr_path = student.qr_code.path if hasattr(student.qr_code, 'path') else None
            if qr_path and os.path.exists(qr_path):
                p.drawImage(qr_path, 2.6*inch, 0.8*inch, width=0.7*inch, height=0.7*inch)
        except:
            pass
    
    p.setFont("Helvetica", 6)
    p.drawString(0.2*inch, 0.35*inch, f"Admission: {student.admission_date.strftime('%d/%m/%Y') if student.admission_date else 'N/A'}")
    
    p.setFillColor(colors.HexColor('#1e40af'))
    p.rect(0.05*inch, 0.05*inch, 3.4*inch, 0.2*inch, fill=True)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica", 5)
    p.drawCentredString(1.75*inch, 0.1*inch, "Valid for Current Academic Year | Keep Card Safe")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_id_{student.admission_number}.pdf"'
    return response


@login_required
def results_dashboard(request):
    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    classrooms = ClassRoom.objects.all()
    
    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()
    
    context = {
        'sessions': sessions,
        'terms': terms,
        'classrooms': classrooms,
        'current_session': current_session,
        'current_term': current_term,
    }
    return render(request, 'students/results_dashboard.html', context)


@login_required
def mark_results(request):
    classrooms = ClassRoom.objects.all()
    subjects = Subject.objects.all()
    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    
    selected_class = request.GET.get('class')
    selected_subject = request.GET.get('subject')
    selected_session = request.GET.get('session')
    selected_term = request.GET.get('term')
    
    students = []
    existing_results = {}
    
    if selected_class and selected_subject and selected_session and selected_term:
        students = Student.objects.filter(current_class_id=selected_class, status='active')
        results = Result.objects.filter(
            classroom_id=selected_class,
            subject_id=selected_subject,
            session_id=selected_session,
            term_id=selected_term
        )
        existing_results = {r.student_id: r for r in results}
    
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        subject_id = request.POST.get('subject')
        session_id = request.POST.get('session')
        term_id = request.POST.get('term')
        
        student_ids = request.POST.getlist('student_ids')
        
        for student_id in student_ids:
            ca_score = request.POST.get(f'ca_{student_id}', 0)
            exam_score = request.POST.get(f'exam_{student_id}', 0)
            
            try:
                ca_score = Decimal(ca_score) if ca_score else Decimal(0)
                exam_score = Decimal(exam_score) if exam_score else Decimal(0)
            except:
                ca_score = Decimal(0)
                exam_score = Decimal(0)
            
            result, created = Result.objects.update_or_create(
                student_id=student_id,
                subject_id=subject_id,
                session_id=session_id,
                term_id=term_id,
                defaults={
                    'classroom_id': classroom_id,
                    'ca_score': ca_score,
                    'exam_score': exam_score,
                    'recorded_by': request.user,
                }
            )
        
        messages.success(request, 'Results saved successfully!')
        return redirect(f"{request.path}?class={classroom_id}&subject={subject_id}&session={session_id}&term={term_id}")
    
    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'sessions': sessions,
        'terms': terms,
        'students': students,
        'existing_results': existing_results,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'selected_session': selected_session,
        'selected_term': selected_term,
    }
    return render(request, 'students/mark_results.html', context)


from scratchcard.models import ScratchCard, ResultAccess

@login_required
def view_results(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Only students can view their results.")
        return redirect('core:dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    
    selected_session_id = request.GET.get('session')
    selected_term_id = request.GET.get('term')
    
    results = []
    total_score = 0
    average = 0
    has_access = False
    
    if selected_session_id and selected_term_id:
        term = get_object_or_404(Term, id=selected_term_id)
        # Check if student has access for this term
        has_access = ResultAccess.objects.filter(student=student, term=term).exists()
        
        if request.method == 'POST' and not has_access:
            card_code = request.POST.get('card_code')
            try:
                card = ScratchCard.objects.get(card_code=card_code, status='active')
                ResultAccess.objects.create(student=student, term=term, scratch_card=card)
                card.status = 'used'
                card.save()
                has_access = True
                messages.success(request, f"Access granted for {term}")
            except ScratchCard.DoesNotExist:
                messages.error(request, "Invalid or already used scratch card code.")
        
        if has_access:
            results = Result.objects.filter(
                student=student,
                session_id=selected_session_id,
                term_id=selected_term_id
            ).select_related('subject')
            
            if results.exists():
                total_score = sum(r.total for r in results)
                average = total_score / len(results)
    
    context = {
        'student': student,
        'sessions': sessions,
        'terms': terms,
        'results': results,
        'total_score': total_score,
        'average': round(average, 2) if average else 0,
        'selected_session': selected_session_id,
        'selected_term': selected_term_id,
        'has_access': has_access,
    }
    return render(request, 'students/view_results.html', context)


@login_required
def student_results(request, pk):
    student = get_object_or_404(Student, pk=pk)
    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    
    selected_session = request.GET.get('session')
    selected_term = request.GET.get('term')
    
    results = []
    total_score = 0
    average = 0
    
    if selected_session and selected_term:
        results = Result.objects.filter(
            student=student,
            session_id=selected_session,
            term_id=selected_term
        ).select_related('subject')
        
        if results.exists():
            total_score = sum(r.total for r in results)
            average = total_score / len(results)
    
    context = {
        'student': student,
        'sessions': sessions,
        'terms': terms,
        'results': results,
        'total_score': total_score,
        'average': round(average, 2) if average else 0,
        'selected_session': selected_session,
        'selected_term': selected_term,
    }
    return render(request, 'students/student_results.html', context)


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from core.models import SchoolSettings
import os

@login_required
def print_result(request, pk):
    student = get_object_or_404(Student, pk=pk)
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    
    if not session_id or not term_id:
        messages.error(request, 'Please select session and term.')
        return redirect('students:student_results', pk=pk)
    
    session = get_object_or_404(AcademicSession, pk=session_id)
    term = get_object_or_404(Term, pk=term_id)
    
    results = Result.objects.filter(
        student=student,
        session=session,
        term=term
    ).select_related('subject').order_by('subject__name')
    
    if not results.exists():
        messages.error(request, 'No results found for the selected period.')
        return redirect('students:student_results', pk=pk)
    
    # Get school settings
    school_settings = SchoolSettings.objects.first()
    school_name = school_settings.school_name if school_settings else "SCHOOL SUITE PRO"
    school_address = school_settings.school_address if school_settings else "School Address Not Set"
    school_phone = school_settings.school_phone if school_settings else ""
    school_email = school_settings.school_email if school_settings else ""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=2
    )
    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=9,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=14,
        fontWeight='Bold',
        spaceAfter=15,
        textColor=colors.black
    )
    
    elements = []
    
    # Header Section with Logo and School Info
    col_widths = [1.2*inch, 4.5*inch, 1.2*inch]
    
    # Logo
    logo_img = ""
    if school_settings and school_settings.school_logo:
        try:
            logo_path = school_settings.school_logo.path
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=1*inch, height=1*inch)
        except:
            pass

    # Student Photo
    student_img = ""
    if student.photo:
        try:
            photo_path = student.photo.path
            if os.path.exists(photo_path):
                student_img = Image(photo_path, width=1*inch, height=1*inch)
        except:
            pass

    school_info = [
        [Paragraph(school_name.upper(), title_style)],
        [Paragraph(school_address, address_style)],
        [Paragraph(f"Tel: {school_phone} | Email: {school_email}", address_style)],
        [Paragraph("STUDENT ACADEMIC REPORT", subtitle_style)]
    ]
    school_info_table = Table(school_info, colWidths=[4.5*inch])
    school_info_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    header_row = [logo_img, school_info_table, student_img]
    header_table = Table([header_row], colWidths=col_widths)
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Table([[""]], colWidths=[7.2*inch], rowHeights=[1]).setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#1e40af'))])))
    elements.append(Spacer(1, 0.2*inch))
    
    info_data = [
        ['STUDENT NAME:', student.full_name.upper(), 'ADMISSION NO:', student.admission_number],
        ['CLASS:', str(student.current_class or 'N/A').upper(), 'SESSION:', session.name],
        ['TERM:', term.name.upper(), 'DATE:', term.end_date.strftime('%d %b, %Y')],
    ]
    
    info_table = Table(info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#1e40af')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    result_data = [['SUBJECT', 'CA (40)', 'EXAM (60)', 'TOTAL (100)', 'GRADE', 'REMARK']]
    
    for result in results:
        result_data.append([
            result.subject.name.upper(),
            str(result.ca_score),
            str(result.exam_score),
            str(result.total),
            result.grade,
            result.remark
        ])
    
    total_score = sum(r.total for r in results)
    average = total_score / len(results) if results else 0
    
    result_data.append(['TOTAL', '', '', str(total_score), '', ''])
    result_data.append(['AVERAGE', '', '', f'{average:.2f}', '', ''])
    
    result_table = Table(result_data, colWidths=[2.2*inch, 0.9*inch, 0.9*inch, 1.1*inch, 0.8*inch, 1.3*inch])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -2), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#f1f5f9')),
    ]))
    elements.append(result_table)
    elements.append(Spacer(1, 0.5*inch))
    
    signature_data = [
        ['CLASS TEACHER', '_______________________'],
        ['PRINCIPAL', '_______________________'],
        ['DATE PRINTED', term.end_date.strftime('%d/%m/%Y')],
    ]
    sig_table = Table(signature_data, colWidths=[2*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 25),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="result_{student.admission_number}_{term.name}.pdf"'
    return response

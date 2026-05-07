from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from .models import Teacher
from core.models import ClassRoom, Subject
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import uuid


@login_required
def teacher_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'active')
    
    teachers = Teacher.objects.all()
    
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(staff_id__icontains=query)
        )
    
    if status_filter:
        teachers = teachers.filter(status=status_filter)
    
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'query': query,
        'status_filter': status_filter,
    })


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})


@login_required
def teacher_add(request):
    from django.contrib.auth.models import User
    classrooms = ClassRoom.objects.all()
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id') or f"TCH{uuid.uuid4().hex[:6].upper()}"
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email', '')
        
        teacher = Teacher(
            staff_id=staff_id,
            first_name=first_name,
            last_name=last_name,
            gender=request.POST.get('gender'),
            date_of_birth=request.POST.get('date_of_birth') or None,
            date_employed=request.POST.get('date_employed'),
            phone=request.POST.get('phone', ''),
            email=email,
            address=request.POST.get('address', ''),
            qualification=request.POST.get('qualification', ''),
            is_class_teacher=request.POST.get('is_class_teacher') == 'on',
            class_assigned_id=request.POST.get('class_assigned') or None,
        )
        
        if 'photo' in request.FILES:
            teacher.photo = request.FILES['photo']
        
        teacher.save()
        teacher.generate_qr_code()
        teacher.save()
        
        subject_ids = request.POST.getlist('subjects')
        teacher.subjects.set(subject_ids)
        
        class_ids = request.POST.getlist('classes')
        teacher.classes.set(class_ids)
        
        try:
            username = f"{first_name.lower()}.{last_name.lower()}"
            if User.objects.filter(username=username).exists():
                username = f"{username}_{staff_id.lower()}"
            password = f"{staff_id}@2024"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            teacher.user = user
            teacher.save()
            messages.success(request, f'Teacher {teacher.full_name} added! Login: {username} / {password}')
        except Exception as e:
            messages.success(request, f'Teacher {teacher.full_name} added! (Account creation failed)')
        
        return redirect('teachers:teacher_list')
    
    return render(request, 'teachers/teacher_form.html', {
        'classrooms': classrooms,
        'subjects': subjects,
    })


@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    classrooms = ClassRoom.objects.all()
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.gender = request.POST.get('gender')
        teacher.date_of_birth = request.POST.get('date_of_birth') or None
        teacher.date_employed = request.POST.get('date_employed')
        teacher.phone = request.POST.get('phone', '')
        teacher.email = request.POST.get('email', '')
        teacher.address = request.POST.get('address', '')
        teacher.qualification = request.POST.get('qualification', '')
        teacher.status = request.POST.get('status', 'active')
        teacher.is_class_teacher = request.POST.get('is_class_teacher') == 'on'
        teacher.class_assigned_id = request.POST.get('class_assigned') or None
        
        if 'photo' in request.FILES:
            teacher.photo = request.FILES['photo']
        
        teacher.save()
        
        subject_ids = request.POST.getlist('subjects')
        teacher.subjects.set(subject_ids)
        
        class_ids = request.POST.getlist('classes')
        teacher.classes.set(class_ids)
        
        messages.success(request, f'Teacher {teacher.full_name} updated successfully!')
        return redirect('teachers:teacher_detail', pk=teacher.pk)
    
    return render(request, 'teachers/teacher_form.html', {
        'teacher': teacher,
        'classrooms': classrooms,
        'subjects': subjects,
    })


@login_required
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        name = teacher.full_name
        teacher.delete()
        messages.success(request, f'Teacher {name} deleted successfully!')
        return redirect('teachers:teacher_list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})


@login_required
def generate_staff_id_card(request, pk):
    import os
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if not teacher.qr_code:
        teacher.generate_qr_code()
        teacher.save()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(3.5*inch, 2.25*inch))
    
    p.setTitle(f"Teacher ID - {teacher.full_name}")
    
    p.setLineWidth(2)
    p.setStrokeColor(colors.HexColor('#059669'))
    p.rect(0.05*inch, 0.05*inch, 3.4*inch, 2.15*inch)
    
    p.setFillColor(colors.HexColor('#059669'))
    p.rect(0.05*inch, 1.8*inch, 3.4*inch, 0.4*inch, fill=True)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(1.75*inch, 2.05*inch, "STAFF ID CARD")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(0.2*inch, 1.6*inch, teacher.full_name.upper())
    
    p.setFont("Helvetica", 7)
    p.drawString(0.2*inch, 1.35*inch, f"Staff ID: {teacher.staff_id}")
    p.drawString(0.2*inch, 1.15*inch, f"Position: Teacher")
    if teacher.qualification:
        qual_short = teacher.qualification[:25]
        p.drawString(0.2*inch, 0.95*inch, f"Qualification: {qual_short}")
    p.drawString(0.2*inch, 0.75*inch, f"Status: {teacher.get_status_display()}")
    
    if teacher.qr_code:
        try:
            qr_path = teacher.qr_code.path if hasattr(teacher.qr_code, 'path') else None
            if qr_path and os.path.exists(qr_path):
                p.drawImage(qr_path, 2.6*inch, 0.8*inch, width=0.7*inch, height=0.7*inch)
        except:
            pass
    
    p.setFont("Helvetica", 6)
    p.drawString(0.2*inch, 0.35*inch, f"Employed: {teacher.date_employed.strftime('%d/%m/%Y') if teacher.date_employed else 'N/A'}")
    
    p.setFillColor(colors.HexColor('#059669'))
    p.rect(0.05*inch, 0.05*inch, 3.4*inch, 0.2*inch, fill=True)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica", 5)
    p.drawCentredString(1.75*inch, 0.1*inch, "Valid for Current Academic Year | Keep Card Safe")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_id_{teacher.staff_id}.pdf"'
    return response

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from .models import Timetable, TimeSlot
from core.models import ClassRoom, Term, AcademicSession, Subject
from django.contrib.auth.models import User
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


@login_required
def timetable_list(request):
    timetables = Timetable.objects.filter(is_active=True).select_related('classroom', 'term')
    return render(request, 'timetable/timetable_list.html', {'timetables': timetables})


@login_required
def timetable_detail(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    slots = timetable.slots.all().order_by('day', 'start_time')
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    schedule = {day: slots.filter(day=day) for day in days}
    return render(request, 'timetable/timetable_detail.html', {'timetable': timetable, 'schedule': schedule})


@login_required
def export_timetable_pdf(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    slots = timetable.slots.all().order_by('start_time')
    
    # Get unique time slots to create headers
    unique_slots = []
    seen_times = set()
    for s in slots:
        time_range = f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
        if time_range not in seen_times:
            unique_slots.append(time_range)
            seen_times.add(time_range)
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"School Timetable: {timetable.name}", styles['Title']))
    elements.append(Paragraph(f"Class: {timetable.classroom.name} | Term: {timetable.term.name}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    data = [['Day / Time'] + unique_slots]
    for day in days:
        row = [day]
        for slot_time in unique_slots:
            display_text = ""
            for s in timetable.slots.filter(day=day):
                s_time = f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                if s_time == slot_time:
                    display_text = f"{s.subject.name}\n({s.teacher.get_full_name() if s.teacher else 'No Teacher'})"
                    break
            row.append(display_text)
        data.append(row)
    
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="timetable_{timetable.pk}.pdf"'
    return response


@login_required
def timetable_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        classroom_id = request.POST.get('classroom')
        term_id = request.POST.get('term')
        session_id = request.POST.get('academic_session')
        
        if not all([name, classroom_id, term_id, session_id]):
            messages.error(request, 'All fields are required.')
            return redirect('timetable:create')
        
        # Check if a timetable already exists for this combination
        if Timetable.objects.filter(classroom_id=classroom_id, term_id=term_id, academic_session_id=session_id).exists():
            messages.error(request, 'A timetable already exists for this class, term, and session.')
            return redirect('timetable:create')

        timetable = Timetable.objects.create(
            name=name, classroom_id=classroom_id, term_id=term_id,
            academic_session_id=session_id, created_by=request.user
        )
        messages.success(request, 'Timetable created successfully!')
        return redirect('timetable:detail', pk=timetable.pk)
    
    classrooms = ClassRoom.objects.all()
    terms = Term.objects.all()
    sessions = AcademicSession.objects.all()
    return render(request, 'timetable/timetable_form.html', 
                  {'classrooms': classrooms, 'terms': terms, 'sessions': sessions})


@login_required
def slot_create(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    
    if request.method == 'POST':
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        room = request.POST.get('room', '')
        
        TimeSlot.objects.create(
            timetable=timetable, day=day, start_time=start_time, end_time=end_time,
            subject_id=subject_id, teacher_id=teacher_id if teacher_id else None, room=room
        )
        messages.success(request, 'Time slot added successfully!')
        return redirect('timetable:detail', pk=timetable_id)
    
    subjects = Subject.objects.all()
    teachers = User.objects.filter(profile__role='teacher')
    days = [('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')]
    
    return render(request, 'timetable/slot_form.html', 
                  {'timetable': timetable, 'subjects': subjects, 'teachers': teachers, 'days': days})


@login_required
@require_http_methods(["POST"])
def slot_delete(request, pk):
    slot = get_object_or_404(TimeSlot, pk=pk)
    timetable_id = slot.timetable.pk
    slot.delete()
    messages.success(request, 'Time slot deleted successfully!')
    return redirect('timetable:detail', pk=timetable_id)

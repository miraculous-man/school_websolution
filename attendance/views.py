from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import date, datetime, timedelta
from .models import StudentAttendance, TeacherAttendance
from students.models import Student
from teachers.models import Teacher
from core.models import ClassRoom, Term


@login_required
def attendance_dashboard(request):
    today = date.today()
    
    present_students = StudentAttendance.objects.filter(date=today, status='present').count()
    absent_students = StudentAttendance.objects.filter(date=today, status='absent').count()
    late_students = StudentAttendance.objects.filter(date=today, status='late').count()
    
    present_teachers = TeacherAttendance.objects.filter(date=today, status='present').count()
    absent_teachers = TeacherAttendance.objects.filter(date=today, status='absent').count()
    
    classrooms = ClassRoom.objects.all()
    
    context = {
        'today': today,
        'present_students': present_students,
        'absent_students': absent_students,
        'late_students': late_students,
        'present_teachers': present_teachers,
        'absent_teachers': absent_teachers,
        'classrooms': classrooms,
    }
    return render(request, 'attendance/dashboard.html', context)


@login_required
def mark_student_attendance(request):
    classrooms = ClassRoom.objects.all()
    selected_class = request.GET.get('class')
    selected_date = request.GET.get('date', date.today().isoformat())
    
    students = []
    attendance_records = {}
    
    if selected_class:
        students = Student.objects.filter(current_class_id=selected_class, status='active')
        existing = StudentAttendance.objects.filter(
            student__current_class_id=selected_class,
            date=selected_date
        )
        attendance_records = {a.student_id: a.status for a in existing}
    
    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        class_id = request.POST.get('class_id')
        
        students_in_class = Student.objects.filter(current_class_id=class_id, status='active')
        
        for student in students_in_class:
            status = request.POST.get(f'status_{student.id}', 'present')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            StudentAttendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    'classroom_id': class_id,
                    'status': status,
                    'remarks': remarks,
                }
            )
        
        messages.success(request, 'Attendance marked successfully!')
        return redirect(f"{request.path}?class={class_id}&date={attendance_date}")
    
    context = {
        'classrooms': classrooms,
        'students': students,
        'selected_class': selected_class,
        'selected_date': selected_date,
        'attendance_records': attendance_records,
    }
    return render(request, 'attendance/mark_student.html', context)


@login_required
def mark_teacher_attendance(request):
    selected_date = request.GET.get('date', date.today().isoformat())
    
    teachers = Teacher.objects.filter(status='active')
    existing = TeacherAttendance.objects.filter(date=selected_date)
    attendance_records = {a.teacher_id: a for a in existing}
    
    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        
        for teacher in teachers:
            status = request.POST.get(f'status_{teacher.id}', 'present')
            time_in = request.POST.get(f'time_in_{teacher.id}') or None
            time_out = request.POST.get(f'time_out_{teacher.id}') or None
            remarks = request.POST.get(f'remarks_{teacher.id}', '')
            
            TeacherAttendance.objects.update_or_create(
                teacher=teacher,
                date=attendance_date,
                defaults={
                    'status': status,
                    'time_in': time_in,
                    'time_out': time_out,
                    'remarks': remarks,
                }
            )
        
        messages.success(request, 'Teacher attendance marked successfully!')
        return redirect(f"{request.path}?date={attendance_date}")
    
    context = {
        'teachers': teachers,
        'selected_date': selected_date,
        'attendance_records': attendance_records,
    }
    return render(request, 'attendance/mark_teacher.html', context)


@login_required
def attendance_report(request):
    report_type = request.GET.get('type', 'student')
    class_filter = request.GET.get('class', '')
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.GET.get('end_date', date.today().isoformat())
    
    classrooms = ClassRoom.objects.all()
    
    if report_type == 'student':
        records = StudentAttendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related('student', 'classroom')
        
        if class_filter:
            records = records.filter(classroom_id=class_filter)
        
        summary = records.values('status').annotate(count=Count('id'))
    else:
        records = TeacherAttendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related('teacher')
        
        summary = records.values('status').annotate(count=Count('id'))
    
    context = {
        'report_type': report_type,
        'records': records[:100],
        'summary': {s['status']: s['count'] for s in summary},
        'classrooms': classrooms,
        'class_filter': class_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'attendance/report.html', context)


@login_required
def qr_scanner(request):
    return render(request, 'attendance/qr_scanner.html')


@login_required
def scan_qr_attendance(request):
    if request.method == 'POST':
        import json
        
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_code', '')
            
            if qr_data.startswith('STUDENT:'):
                admission_number = qr_data.replace('STUDENT:', '')
                student = Student.objects.filter(admission_number=admission_number).first()
                
                if student:
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        date=date.today(),
                        defaults={
                            'classroom': student.current_class,
                            'status': 'present',
                            'remarks': 'Marked via QR scan',
                        }
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Attendance marked for {student.full_name}',
                        'student': {
                            'name': student.full_name,
                            'admission_number': student.admission_number,
                            'class': str(student.current_class),
                            'photo': student.photo.url if student.photo else None,
                        },
                        'already_marked': not created,
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Student not found',
                    }, status=404)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid QR code format',
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request data',
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

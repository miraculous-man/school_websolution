from datetime import date
from .charts import get_attendance_chart, get_revenue_chart, get_student_distribution, get_performance_chart
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, F
from django.core.paginator import Paginator
from students.models import Student
from teachers.models import Teacher
from finance.models import Invoice, Payment
from library.models import Book, BookIssue
from attendance.models import StudentAttendance
from cbt.models import Exam, ExamAttempt
from .models import ClassLevel, ClassRoom, Subject, AcademicSession, Term, AuditLog, SubjectVideo, SubjectDocument


@login_required
def subject_upload(request):
    if request.user.profile.role not in ['admin', 'teacher']:
        return render(request, '403.html', status=403)
    
    subjects = Subject.objects.all()
    levels = ClassLevel.objects.all()
    
    if request.method == 'POST':
        upload_type = request.POST.get('upload_type')
        subject_id = request.POST.get('subject')
        level_id = request.POST.get('class_level')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        if upload_type == 'video':
            youtube_url = request.POST.get('youtube_url')
            SubjectVideo.objects.create(
                subject_id=subject_id,
                class_level_id=level_id,
                title=title,
                youtube_url=youtube_url,
                description=description
            )
            messages.success(request, 'Video link added successfully!')
        else:
            file = request.FILES.get('file')
            if file:
                SubjectDocument.objects.create(
                    subject_id=subject_id,
                    class_level_id=level_id,
                    title=title,
                    file=file,
                    description=description
                )
                messages.success(request, 'Document uploaded successfully!')
            else:
                messages.error(request, 'Please select a file to upload.')
                
        return redirect('core:subject_list')
        
    return render(request, 'core/subject_upload.html', {
        'subjects': subjects,
        'levels': levels
    })


@login_required
def dashboard(request):
    role = getattr(request.user.profile, 'role', 'student')

    if role == 'parent':
        return redirect('students:parent_dashboard')

    total_students = Student.objects.filter(status='active').count()
    total_teachers = Teacher.objects.filter(status='active').count()
    total_classes = ClassRoom.objects.count()
    total_subjects = Subject.objects.count()

    from homepage.models import Admission
    new_admissions_count = Admission.objects.filter(status='Approved').count()

    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    pending_fees = Invoice.objects.filter(status__in=['pending', 'partial']).aggregate(total=Sum('balance'))['total'] or 0

    total_books = Book.objects.count()
    books_issued = BookIssue.objects.filter(status='issued').count()

    today = date.today()
    present_today = StudentAttendance.objects.filter(date=today, status='present').count()
    absent_today = StudentAttendance.objects.filter(date=today, status='absent').count()

    recent_students = Student.objects.order_by('-created_at')[:5]
    recent_payments = Payment.objects.order_by('-created_at')[:5]

    active_exams = Exam.objects.filter(status='published').count()

    selected_session = request.GET.get('session')
    selected_term = request.GET.get('term')
    selected_class = request.GET.get('class')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    terms = Term.objects.all()
    classrooms = ClassRoom.objects.all()

    attendance_chart = get_attendance_chart()
    revenue_chart = get_revenue_chart()
    student_chart = get_student_distribution()
    performance_chart = get_performance_chart(selected_session, selected_term, selected_class)

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'new_admissions_count': new_admissions_count,
        'total_revenue': total_revenue,
        'pending_fees': pending_fees,
        'total_books': total_books,
        'books_issued': books_issued,
        'present_today': present_today,
        'absent_today': absent_today,
        'recent_students': recent_students,
        'recent_payments': recent_payments,
        'active_exams': active_exams,
        'attendance_chart': attendance_chart,
        'revenue_chart': revenue_chart,
        'student_chart': student_chart,
        'performance_chart': performance_chart,
        'sessions': sessions,
        'terms': terms,
        'classrooms': classrooms,
        'selected_session': selected_session,
        'selected_term': selected_term,
        'selected_class': selected_class,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def class_list(request):
    class_levels = ClassLevel.objects.prefetch_related('classroom_set').all()
    return render(request, 'core/class_list.html', {'class_levels': class_levels})


@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'core/subject_list.html', {'subjects': subjects})


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    videos = subject.videos.all()
    documents = subject.documents.all()
    return render(request, 'core/subject_detail.html', {
        'subject': subject,
        'videos': videos,
        'documents': documents
    })


@login_required
def session_list(request):
    sessions = AcademicSession.objects.all().order_by('-start_date')
    return render(request, 'core/session_list.html', {'sessions': sessions})


@login_required
def class_add(request):
    levels = ClassLevel.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        level_id = request.POST.get('class_level')
        capacity = request.POST.get('capacity', 30)
        ClassRoom.objects.create(name=name, class_level_id=level_id, capacity=capacity)
        messages.success(request, 'Class created successfully!')
        return redirect('core:class_list')
    return render(request, 'core/classroom_form.html', {'levels': levels})


@login_required
def class_edit(request, pk):
    classroom = get_object_or_404(ClassRoom, pk=pk)
    levels = ClassLevel.objects.all()
    if request.method == 'POST':
        classroom.name = request.POST.get('name')
        classroom.class_level_id = request.POST.get('class_level')
        classroom.capacity = request.POST.get('capacity')
        classroom.save()
        messages.success(request, 'Class updated successfully!')
        return redirect('core:class_list')
    return render(request, 'core/classroom_form.html', {'classroom': classroom, 'levels': levels})


@login_required
def subject_add(request):
    levels = ClassLevel.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        level_ids = request.POST.getlist('class_levels')
        subject = Subject.objects.create(name=name, code=code, description=description)
        subject.class_levels.set(level_ids)
        messages.success(request, 'Subject added successfully!')
        return redirect('core:subject_list')
    return render(request, 'core/subject_form.html', {'levels': levels})


@login_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    levels = ClassLevel.objects.all()
    if request.method == 'POST':
        subject.name = request.POST.get('name')
        subject.code = request.POST.get('code')
        subject.description = request.POST.get('description')
        level_ids = request.POST.getlist('class_levels')
        subject.class_levels.set(level_ids)
        subject.save()
        messages.success(request, 'Subject updated successfully!')
        return redirect('core:subject_list')
    return render(request, 'core/subject_form.html', {'subject': subject, 'levels': levels})


@login_required
def session_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        AcademicSession.objects.create(name=name, start_date=start, end_date=end, is_current=is_current)
        messages.success(request, 'Session added successfully!')
        return redirect('core:session_list')
    return render(request, 'core/session_form.html')


@login_required
def session_edit(request, pk):
    session = get_object_or_404(AcademicSession, pk=pk)
    if request.method == 'POST':
        session.name = request.POST.get('name')
        session.start_date = request.POST.get('start_date')
        session.end_date = request.POST.get('end_date')
        session.is_current = request.POST.get('is_current') == 'on'
        session.save()
        messages.success(request, 'Session updated successfully!')
        return redirect('core:session_list')
    return render(request, 'core/session_form.html', {'session': session})


@login_required
def term_list(request):
    terms = Term.objects.all().select_related('session')
    return render(request, 'core/term_list.html', {'terms': terms})


@login_required
def term_add(request):
    sessions = AcademicSession.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        session_id = request.POST.get('session')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        Term.objects.create(name=name, session_id=session_id, start_date=start, end_date=end, is_current=is_current)
        messages.success(request, 'Term added successfully!')
        return redirect('core:term_list')
    return render(request, 'core/term_form.html', {'sessions': sessions})


@login_required
def term_edit(request, pk):
    term = get_object_or_404(Term, pk=pk)
    sessions = AcademicSession.objects.all()
    if request.method == 'POST':
        term.name = request.POST.get('name')
        term.session_id = request.POST.get('session')
        term.start_date = request.POST.get('start_date')
        term.end_date = request.POST.get('end_date')
        term.is_current = request.POST.get('is_current') == 'on'
        term.save()
        messages.success(request, 'Term updated successfully!')
        return redirect('core:term_list')
    return render(request, 'core/term_form.html', {'term': term, 'sessions': sessions})


@login_required
def audit_logs(request):
    if request.user.profile.role != 'admin':
        return render(request, '403.html', status=403)
    
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    return render(request, 'core/audit_logs.html', {'logs': logs})

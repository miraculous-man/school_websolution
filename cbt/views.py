from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import QuestionBank, Exam, ExamAttempt, ExamAnswer
from core.models import Subject, ClassLevel
from students.models import Student
import random


@login_required
def cbt_dashboard(request):
    total_questions = QuestionBank.objects.count()
    total_exams = Exam.objects.count()
    published_exams = Exam.objects.filter(status='published').count()
    total_attempts = ExamAttempt.objects.count()
    
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    subjects = Subject.objects.all()
    
    context = {
        'total_questions': total_questions,
        'total_exams': total_exams,
        'published_exams': published_exams,
        'total_attempts': total_attempts,
        'recent_exams': recent_exams,
        'subjects': subjects,
    }
    return render(request, 'cbt/dashboard.html', context)


@login_required
def question_list(request):
    query = request.GET.get('q', '')
    subject_filter = request.GET.get('subject', '')
    class_filter = request.GET.get('class', '')
    
    questions = QuestionBank.objects.all()
    
    if query:
        questions = questions.filter(question_text__icontains=query)
    if subject_filter:
        questions = questions.filter(subject_id=subject_filter)
    if class_filter:
        questions = questions.filter(class_level_id=class_filter)
    
    subjects = Subject.objects.all()
    class_levels = ClassLevel.objects.all()
    
    context = {
        'questions': questions,
        'subjects': subjects,
        'class_levels': class_levels,
        'query': query,
        'subject_filter': subject_filter,
        'class_filter': class_filter,
    }
    return render(request, 'cbt/question_list.html', context)


@login_required
def question_add(request):
    subjects = Subject.objects.all()
    class_levels = ClassLevel.objects.all()
    
    if request.method == 'POST':
        question = QuestionBank(
            subject_id=request.POST.get('subject'),
            class_level_id=request.POST.get('class_level'),
            question_text=request.POST.get('question_text'),
            question_type=request.POST.get('question_type', 'multiple_choice'),
            option_a=request.POST.get('option_a', ''),
            option_b=request.POST.get('option_b', ''),
            option_c=request.POST.get('option_c', ''),
            option_d=request.POST.get('option_d', ''),
            correct_answer=request.POST.get('correct_answer'),
            explanation=request.POST.get('explanation', ''),
            difficulty=request.POST.get('difficulty', 'medium'),
        )
        question.save()
        messages.success(request, 'Question added successfully!')
        
        if request.POST.get('add_another'):
            return redirect('cbt:question_add')
        return redirect('cbt:question_list')
    
    return render(request, 'cbt/question_form.html', {
        'subjects': subjects,
        'class_levels': class_levels,
    })


@login_required
def exam_list(request):
    exams = Exam.objects.all().order_by('-created_at')
    return render(request, 'cbt/exam_list.html', {'exams': exams})


@login_required
def exam_add(request):
    subjects = Subject.objects.all()
    class_levels = ClassLevel.objects.all()
    
    if request.method == 'POST':
        exam = Exam(
            title=request.POST.get('title'),
            subject_id=request.POST.get('subject'),
            class_level_id=request.POST.get('class_level'),
            duration_minutes=int(request.POST.get('duration_minutes', 60)),
            total_marks=int(request.POST.get('total_marks', 100)),
            passing_marks=int(request.POST.get('passing_marks', 40)),
            instructions=request.POST.get('instructions', ''),
            shuffle_questions=request.POST.get('shuffle_questions') == 'on',
            show_result=request.POST.get('show_result') == 'on',
        )
        exam.save()
        
        question_ids = request.POST.getlist('questions')
        exam.questions.set(question_ids)
        
        messages.success(request, f'Exam "{exam.title}" created successfully!')
        return redirect('cbt:exam_list')
    
    questions = QuestionBank.objects.all()
    
    return render(request, 'cbt/exam_form.html', {
        'subjects': subjects,
        'class_levels': class_levels,
        'questions': questions,
    })


@login_required
def exam_detail(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    attempts = exam.attempts.select_related('student').order_by('-started_at')
    
    return render(request, 'cbt/exam_detail.html', {
        'exam': exam,
        'attempts': attempts,
    })


@login_required
def exam_publish(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if exam.questions.count() == 0:
        messages.error(request, 'Cannot publish exam without questions!')
    else:
        exam.status = 'published'
        exam.save()
        messages.success(request, f'Exam "{exam.title}" published successfully!')
    return redirect('cbt:exam_detail', pk=pk)


@login_required
def take_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk, status='published')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Only students can take exams.')
        return redirect('cbt:exam_list')
    
    attempt, created = ExamAttempt.objects.get_or_create(
        exam=exam,
        student=student,
        defaults={
            'total_questions': exam.questions.count(),
        }
    )
    
    if attempt.is_completed:
        return redirect('cbt:exam_result', pk=attempt.pk)
    
    questions = list(exam.questions.all())
    if exam.shuffle_questions:
        random.shuffle(questions)
    
    if request.method == 'POST':
        correct_count = 0
        
        for question in exam.questions.all():
            selected = request.POST.get(f'question_{question.id}', '')
            is_correct = selected.lower() == question.correct_answer.lower()
            
            if is_correct:
                correct_count += 1
            
            ExamAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_answer': selected,
                    'is_correct': is_correct,
                }
            )
        
        attempt.correct_answers = correct_count
        attempt.score = int((correct_count / attempt.total_questions) * exam.total_marks)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        messages.success(request, 'Exam submitted successfully!')
        return redirect('cbt:exam_result', pk=attempt.pk)
    
    return render(request, 'cbt/take_exam.html', {
        'exam': exam,
        'attempt': attempt,
        'questions': questions,
    })


@login_required
def exam_result(request, pk):
    attempt = get_object_or_404(ExamAttempt, pk=pk)
    answers = attempt.answers.select_related('question').all()
    
    return render(request, 'cbt/exam_result.html', {
        'attempt': attempt,
        'answers': answers,
    })


@login_required
def practice_mode(request):
    subjects = Subject.objects.all()
    class_levels = ClassLevel.objects.all()
    
    subject_filter = request.GET.get('subject', '')
    class_filter = request.GET.get('class', '')
    
    questions = QuestionBank.objects.all()
    if subject_filter:
        questions = questions.filter(subject_id=subject_filter)
    if class_filter:
        questions = questions.filter(class_level_id=class_filter)
    
    questions = list(questions)
    if questions:
        random.shuffle(questions)
        questions = questions[:10]
    
    context = {
        'subjects': subjects,
        'class_levels': class_levels,
        'questions': questions,
        'subject_filter': subject_filter,
        'class_filter': class_filter,
    }
    return render(request, 'cbt/practice.html', context)

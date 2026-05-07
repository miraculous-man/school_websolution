from django.contrib import admin
from .models import QuestionBank, Exam, ExamAttempt, ExamAnswer

@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['subject', 'class_level', 'question_type', 'difficulty']
    list_filter = ['subject', 'class_level', 'question_type', 'difficulty']
    search_fields = ['question_text']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_level', 'duration_minutes', 'status']
    list_filter = ['status', 'subject', 'class_level']
    filter_horizontal = ['questions']

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['exam', 'student', 'score', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'exam']

@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct']
    list_filter = ['is_correct']

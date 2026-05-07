from django.contrib import admin
from .models import Student, StudentClassHistory, Result

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'first_name', 'last_name', 'current_class', 'status']
    list_filter = ['status', 'current_class', 'gender']
    search_fields = ['admission_number', 'first_name', 'last_name']

@admin.register(StudentClassHistory)
class StudentClassHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'classroom', 'session', 'promoted']
    list_filter = ['session', 'promoted']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'classroom', 'term', 'ca_score', 'exam_score', 'total', 'grade']
    list_filter = ['session', 'term', 'classroom', 'subject', 'grade']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']

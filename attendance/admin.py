from django.contrib import admin
from .models import StudentAttendance, TeacherAttendance

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'classroom']
    list_filter = ['status', 'date', 'classroom']
    search_fields = ['student__first_name', 'student__last_name']
    date_hierarchy = 'date'

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'status', 'time_in', 'time_out']
    list_filter = ['status', 'date']
    search_fields = ['teacher__first_name', 'teacher__last_name']
    date_hierarchy = 'date'

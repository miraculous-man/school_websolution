from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'first_name', 'last_name', 'status', 'is_class_teacher']
    list_filter = ['status', 'is_class_teacher', 'gender']
    search_fields = ['staff_id', 'first_name', 'last_name']
    filter_horizontal = ['subjects', 'classes']

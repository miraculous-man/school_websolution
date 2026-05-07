from django.contrib import admin
from .models import AcademicSession, Term, ClassLevel, ClassRoom, Subject, SubjectVideo, SchoolSettings, AuditLog

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'session', 'start_date', 'end_date', 'is_current']
    list_filter = ['session', 'is_current']

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering = ['order']

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_level', 'capacity']
    list_filter = ['class_level']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    filter_horizontal = ['class_levels']

@admin.register(SubjectVideo)
class SubjectVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_level', 'order', 'created_at']
    list_filter = ['subject', 'class_level']
    search_fields = ['title', 'description']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'description', 'ip_address']
    list_filter = ['action', 'timestamp', 'model_name']
    search_fields = ['description', 'user__username', 'model_name']
    readonly_fields = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'description', 'ip_address']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

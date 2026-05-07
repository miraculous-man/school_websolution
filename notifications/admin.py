from django.contrib import admin
from .models import Notification, EmailLog, SMSLog, Announcement


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipient_email', 'subject']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipient_phone', 'message']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'is_active', 'created_at']
    list_filter = ['audience', 'is_active', 'created_at']
    search_fields = ['title', 'content']

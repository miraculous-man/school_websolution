from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('mark-read/<int:pk>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('recent/', views.get_recent_notifications, name='recent'),
    path('announcements/', views.announcement_list, name='announcements'),
    path('notification/<int:pk>/', views.notification_detail, name='detail'),
    # Messaging
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent_messages'),
    path('compose/', views.compose_message, name='compose'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    path('delete/<int:pk>/', views.delete_notification, name='delete'),
    path('message/delete/<int:pk>/', views.delete_message, name='delete_message'),
    path('logs/', views.activity_logs, name='activity_logs'),
    path('logs/delete/<int:pk>/', views.delete_audit_log, name='delete_log'),
]

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_dashboard, name='dashboard'),
    path('students/', views.mark_student_attendance, name='mark_student'),
    path('teachers/', views.mark_teacher_attendance, name='mark_teacher'),
    path('report/', views.attendance_report, name='report'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('scan-qr/', views.scan_qr_attendance, name='scan_qr'),
]

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.class_add, name='class_add'),
    path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/upload/', views.subject_upload, name='subject_upload'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/add/', views.session_add, name='session_add'),
    path('sessions/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('terms/', views.term_list, name='term_list'),
    path('terms/add/', views.term_add, name='term_add'),
    path('terms/<int:pk>/edit/', views.term_edit, name='edit_term'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
]

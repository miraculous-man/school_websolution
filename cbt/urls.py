from django.urls import path
from . import views

app_name = 'cbt'

urlpatterns = [
    path('', views.cbt_dashboard, name='dashboard'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/add/', views.question_add, name='question_add'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/publish/', views.exam_publish, name='exam_publish'),
    path('exams/<int:pk>/take/', views.take_exam, name='take_exam'),
    path('result/<int:pk>/', views.exam_result, name='exam_result'),
    path('practice/', views.practice_mode, name='practice'),
]

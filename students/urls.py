from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/id-card/', views.generate_id_card, name='generate_id_card'),
    path('results/', views.results_dashboard, name='results_dashboard'),
    path('results/mark/', views.mark_results, name='mark_results'),
    path('results/view/', views.view_results, name='view_results'),
    path('<int:pk>/results/', views.student_results, name='student_results'),
    path('<int:pk>/results/print/', views.print_result, name='print_result'),
    # Parent Portal
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/student/<int:student_id>/', views.parent_student_detail, name='parent_student_detail'),
    path('parent/invoice/<int:invoice_id>/pay/', views.pay_invoice_offline, name='pay_invoice_offline'),
    path('parent/invoice/<int:invoice_id>/pay/paystack/', views.parent_student_pay_paystack, name='parent_student_pay_paystack'),
]

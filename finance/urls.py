from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('categories/', views.fee_category_list, name='fee_categories'),
    path('structures/', views.fee_structure_list, name='fee_structures'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_pk>/pay/', views.record_payment, name='record_payment'),
    path('receipt/<int:pk>/', views.print_receipt, name='print_receipt'),
    path('expenses/', views.expense_list, name='expenses'),
    path('paystack/pay/<int:invoice_pk>/', views.paystack_initialize, name='paystack_pay'),
    path('paystack/verify/<int:payment_pk>/', views.paystack_verify, name='paystack_verify'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
]

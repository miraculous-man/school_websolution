from django.urls import path
from . import views

app_name = 'scratchcard'

urlpatterns = [
    path('dashboard/', views.scratchcard_dashboard, name='dashboard'),
    path('buy/', views.buy_scratch_card, name='buy'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('exam/<int:exam_id>/activate/', views.activate_exam_for_student, name='activate_exam'),
]

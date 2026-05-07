from django.urls import path
from . import views

app_name = 'scratchcard'

urlpatterns = [
    path('', views.scratch_card_list, name='card_list'),
    path('create-batch/', views.create_scratch_batch, name='create_batch'),
    path('redeem/', views.redeem_scratch_card, name='redeem'),
    path('receipt/<str:ref_number>/', views.redemption_receipt, name='redemption_receipt'),
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('export/<int:batch_id>/', views.export_cards_csv, name='export_csv'),
]

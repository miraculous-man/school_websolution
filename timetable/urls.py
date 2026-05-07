from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('', views.timetable_list, name='list'),
    path('create/', views.timetable_create, name='create'),
    path('<int:pk>/', views.timetable_detail, name='detail'),
    path('<int:pk>/pdf/', views.export_timetable_pdf, name='export_pdf'),
    path('<int:timetable_id>/slot/add/', views.slot_create, name='slot_create'),
    path('slot/<int:pk>/delete/', views.slot_delete, name='slot_delete'),
]

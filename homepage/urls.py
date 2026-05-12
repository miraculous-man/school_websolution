from django.urls import path
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/verify-student/', views.verify_student_api, name='verify_student_api'),
    path('home-v2/', views.home_v2, name='home_v2'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('gallery/', views.gallery, name='gallery'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('events/', views.events, name='events'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('faqs/', views.faqs, name='faqs'),
    path('apply/', views.apply, name='apply'),
    path('letter/<int:pk>/', views.letter, name='letter'),
    path('letter/<int:pk>/pdf/', views.download_letter_pdf, name='letter_pdf'),
    path('dashboard/admissions/', views.admission_list, name='admission_list'),
    path('dashboard/admissions/<int:pk>/convert/', views.convert_to_student, name='convert_to_student'),
]

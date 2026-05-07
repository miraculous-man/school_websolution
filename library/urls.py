from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.library_dashboard, name='dashboard'),
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('issue/', views.issue_book, name='issue_book'),
    path('issues/', views.issue_list, name='issue_list'),
    path('return/<int:pk>/', views.return_book, name='return_book'),
    path('categories/', views.category_list, name='categories'),
]

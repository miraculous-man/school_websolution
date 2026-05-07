from django.contrib import admin
from .models import BookCategory, Book, BookIssue

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['isbn', 'title', 'author', 'category', 'total_copies', 'available_copies']
    list_filter = ['category']
    search_fields = ['isbn', 'title', 'author']

@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'teacher', 'issue_date', 'due_date', 'status']
    list_filter = ['status', 'issue_date']
    date_hierarchy = 'issue_date'

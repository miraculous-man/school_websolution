from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from .models import BookCategory, Book, BookIssue
from students.models import Student
from teachers.models import Teacher


@login_required
def library_dashboard(request):
    total_books = Book.objects.count()
    total_copies = Book.objects.aggregate(total=models.Sum('total_copies'))['total'] or 0
    available_copies = Book.objects.aggregate(total=models.Sum('available_copies'))['total'] or 0
    books_issued = BookIssue.objects.filter(status='issued').count()
    overdue_books = BookIssue.objects.filter(status='issued', due_date__lt=date.today()).count()
    
    recent_issues = BookIssue.objects.select_related('book', 'student', 'teacher').order_by('-issue_date')[:10]
    categories = BookCategory.objects.all()
    
    context = {
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'books_issued': books_issued,
        'overdue_books': overdue_books,
        'recent_issues': recent_issues,
        'categories': categories,
    }
    return render(request, 'library/dashboard.html', context)


@login_required
def book_list(request):
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    
    books = Book.objects.all()
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )
    if category_filter:
        books = books.filter(category_id=category_filter)
    
    categories = BookCategory.objects.all()
    
    return render(request, 'library/book_list.html', {
        'books': books,
        'categories': categories,
        'query': query,
        'category_filter': category_filter,
    })


@login_required
def book_add(request):
    categories = BookCategory.objects.all()
    
    if request.method == 'POST':
        book = Book(
            isbn=request.POST.get('isbn'),
            title=request.POST.get('title'),
            author=request.POST.get('author'),
            publisher=request.POST.get('publisher', ''),
            category_id=request.POST.get('category') or None,
            publication_year=request.POST.get('publication_year') or None,
            total_copies=int(request.POST.get('total_copies', 1)),
            available_copies=int(request.POST.get('total_copies', 1)),
            description=request.POST.get('description', ''),
            shelf_location=request.POST.get('shelf_location', ''),
        )
        
        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
        
        book.save()
        messages.success(request, f'Book "{book.title}" added successfully!')
        return redirect('library:book_list')
    
    return render(request, 'library/book_form.html', {'categories': categories})


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    issues = book.issues.select_related('student', 'teacher').order_by('-issue_date')[:20]
    
    return render(request, 'library/book_detail.html', {
        'book': book,
        'issues': issues,
    })


@login_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    categories = BookCategory.objects.all()
    
    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.publisher = request.POST.get('publisher', '')
        book.category_id = request.POST.get('category') or None
        book.publication_year = request.POST.get('publication_year') or None
        book.total_copies = int(request.POST.get('total_copies', 1))
        book.description = request.POST.get('description', '')
        book.shelf_location = request.POST.get('shelf_location', '')
        
        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
        
        book.save()
        messages.success(request, f'Book "{book.title}" updated!')
        return redirect('library:book_detail', pk=book.pk)
    
    return render(request, 'library/book_form.html', {
        'book': book,
        'categories': categories,
    })


@login_required
def issue_book(request):
    books = Book.objects.filter(available_copies__gt=0)
    students = Student.objects.filter(status='active')
    teachers = Teacher.objects.filter(status='active')
    
    if request.method == 'POST':
        book_id = request.POST.get('book')
        borrower_type = request.POST.get('borrower_type')
        borrower_id = request.POST.get('borrower')
        issue_date = request.POST.get('issue_date', date.today())
        due_date = request.POST.get('due_date')
        
        issue = BookIssue(
            book_id=book_id,
            issue_date=issue_date,
            due_date=due_date,
        )
        
        if borrower_type == 'student':
            issue.student_id = borrower_id
        else:
            issue.teacher_id = borrower_id
        
        issue.save()
        messages.success(request, 'Book issued successfully!')
        return redirect('library:issue_list')
    
    return render(request, 'library/issue_form.html', {
        'books': books,
        'students': students,
        'teachers': teachers,
    })


@login_required
def issue_list(request):
    status_filter = request.GET.get('status', 'issued')
    
    issues = BookIssue.objects.select_related('book', 'student', 'teacher').all()
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    issues = issues.order_by('-issue_date')
    
    return render(request, 'library/issue_list.html', {
        'issues': issues,
        'status_filter': status_filter,
    })


@login_required
def return_book(request, pk):
    issue = get_object_or_404(BookIssue, pk=pk)
    
    if request.method == 'POST':
        issue.return_date = date.today()
        
        if issue.return_date > issue.due_date:
            days_overdue = (issue.return_date - issue.due_date).days
            issue.fine_amount = days_overdue * 1.00
        
        issue.return_book()
        messages.success(request, f'Book "{issue.book.title}" returned successfully!')
        return redirect('library:issue_list')
    
    return render(request, 'library/return_confirm.html', {'issue': issue})


@login_required
def category_list(request):
    categories = BookCategory.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        BookCategory.objects.create(name=name, description=description)
        messages.success(request, f'Category "{name}" created!')
        return redirect('library:categories')
    
    return render(request, 'library/category_list.html', {'categories': categories})


from django.db import models

import plotly.graph_objects as go
from datetime import date
from .models import ClassRoom
from attendance.models import StudentAttendance
from finance.models import Invoice
from students.models import Student, Result
from django.db.models import Count, Sum, Avg, F


def get_attendance_chart():
    """Generate attendance statistics pie chart"""
    today = date.today()
    present = StudentAttendance.objects.filter(date=today, status='present').count()
    absent = StudentAttendance.objects.filter(date=today, status='absent').count()

    fig = go.Figure(data=[go.Pie(
        labels=['Present', 'Absent'],
        values=[present, absent],
        marker=dict(colors=['#28a745', '#dc3545'])
    )])
    fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=0, b=0))
    return fig.to_html(include_plotlyjs=False, div_id="attendance_chart", config={'displaylogo': False})

def get_revenue_chart():
    """Generate revenue trends line chart"""
    invoice = Invoice.objects.all()

    names = [str(p.student.first_name) for p in invoice]
    amounts = [float(p.amount_paid or 0) for p in invoice]

    fig = go.Figure(data=[go.Scatter(x=names, y=amounts, mode='lines+markers', fill='tozeroy', line=dict(color='#007bff'))])
    fig.update_layout(height=300, xaxis_title="students", yaxis_title="Revenue ($)", margin=dict(l=40, r=20, t=20, b=40))
    return fig.to_html(include_plotlyjs=False, div_id="revenue_chart",config={'displaylogo': False})


def get_student_distribution():
    """Generate student per class bar chart"""
    classrooms = ClassRoom.objects.annotate(student_count=Count('student')).values('name', 'student_count').order_by('name')

    names = [c['name'] for c in classrooms] if classrooms else ['No Data']
    counts = [c['student_count'] for c in classrooms] if classrooms else [0]

    fig = go.Figure(data=[go.Bar(x=names, y=counts, marker_color='#28a745')])
    fig.update_layout(height=300, xaxis_title="Class", yaxis_title="Students", margin=dict(l=40, r=20, t=20, b=40))
    return fig.to_html(include_plotlyjs=False, div_id="students_chart",config={'displaylogo': False})


def get_performance_chart(session_id=None, term_id=None, class_id=None):
    """Generate student performance bar chart (Name vs Average)"""
    results_query = Result.objects.select_related('student')
    if session_id:
        results_query = results_query.filter(session_id=session_id)
    if term_id:
        results_query = results_query.filter(term_id=term_id)
    if class_id:
        results_query = results_query.filter(classroom_id=class_id)

    performance_data = results_query.values('student__first_name', 'student__last_name').annotate(avg_score=Avg(F('ca_score') + F('exam_score'))).order_by('-avg_score')[:20]

    names = [f"{p['student__first_name']} {p['student__last_name']}" for p in performance_data]
    scores = [float(p['avg_score'] or 0) for p in performance_data]

    if not names:
        names, scores = ['No Data'], [0]

    fig = go.Figure(data=[go.Bar(x=names, y=scores, marker_color='#6366f1')])
    fig.update_layout(
        height=400,
        xaxis_title="Student Name",
        yaxis_title="Average Score",
        margin=dict(l=40, r=20, t=20, b=80),
        xaxis_tickangle=-45
    )
    return fig.to_html(include_plotlyjs=False, div_id="performance_chart", config={'displaylogo': False})
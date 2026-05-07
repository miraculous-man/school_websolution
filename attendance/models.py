from django.db import models
from students.models import Student
from teachers.models import Teacher
from core.models import ClassRoom, Term


class StudentAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True)
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class TeacherAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('on_leave', 'On Leave'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.status}"

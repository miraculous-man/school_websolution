from django.db import models
from django.contrib.auth.models import User
from core.models import ClassRoom, Subject, Term, AcademicSession


class Timetable(models.Model):
    name = models.CharField(max_length=200)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='timetables')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['classroom', 'term', 'academic_session']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.classroom.name}"


class TimeSlot(models.Model):
    DAY_CHOICES = [('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
                   ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')]
    
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.day} {self.start_time} - {self.subject.name}"

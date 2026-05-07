from django.contrib import admin
from .models import Timetable, TimeSlot

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('name', 'classroom', 'term', 'is_active', 'created_at')
    list_filter = ('is_active', 'term', 'academic_session')
    search_fields = ('name', 'classroom__name')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day', 'start_time', 'end_time', 'subject', 'teacher', 'timetable')
    list_filter = ('day', 'timetable__classroom')
    search_fields = ('subject__name', 'teacher__username')

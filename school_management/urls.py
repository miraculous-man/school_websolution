from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
    path('admin/', admin.site.urls),
    path('dashboard/', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('attendance/', include('attendance.urls')),
    path('cbt/', include('cbt.urls')),
    path('finance/', include('finance.urls')),
    path('library/', include('library.urls')),
    path('timetable/', include('timetable.urls')),
    path('notifications/', include('notifications.urls')),
    path('scratchcard/', include('scratchcard.urls')),
    path('', include('homepage.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

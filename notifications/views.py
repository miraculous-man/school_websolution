from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .models import Notification, Announcement, Message
from django.contrib.auth.models import User

@login_required
def inbox(request):
    messages_list = Message.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications/inbox.html', {'messages': messages_list})

@login_required
def sent_messages(request):
    messages_list = Message.objects.filter(sender=request.user).order_by('-created_at')
    return render(request, 'notifications/sent_messages.html', {'messages': messages_list})

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@login_required
def compose_message(request):
    if request.method == 'POST':
        recipient_ids = request.POST.getlist('recipients')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        for r_id in recipient_ids:
            recipient = get_object_or_404(User, id=r_id)
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body
            )
            
            # Create a Notification for each recipient
            Notification.objects.create(
                user=recipient,
                title=f"New Message: {subject}",
                message=f"You have received a new message from {request.user.get_full_name() or request.user.username}",
                notification_type='info',
                link='/notifications/inbox/'
            )

            # Send Email if recipient has email
            if recipient.email:
                try:
                    # Use the provided host user if settings.DEFAULT_FROM_EMAIL is empty
                    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
                    send_mail(
                        subject=f"New School Message: {subject}",
                        message=f"Hello {recipient.get_full_name() or recipient.username},\n\nYou have received a new message from {request.user.get_full_name() or request.user.username}.\n\nSubject: {subject}\n\nMessage Content:\n{body}\n\nPlease login to the school portal to reply.",
                        from_email=from_email,
                        recipient_list=[recipient.email],
                        fail_silently=False,
                    )
                    logger.info(f"Email sent successfully to {recipient.email}")
                    messages.success(request, f"Email notification sent to {recipient.email}")
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient.email}: {e}")
                    messages.error(request, f"Failed to send email to {recipient.email}. Error: {str(e)}")

            # SMS sending
            if hasattr(recipient, 'profile') and recipient.profile.phone:
                from .models import SMSLog
                from twilio.rest import Client
                import os
                
                sms_body = f"New School Message: {subject}. Check your portal."
                sms_log = SMSLog.objects.create(
                    recipient_phone=recipient.profile.phone,
                    recipient_name=recipient.get_full_name(),
                    message=sms_body,
                    status='pending'
                )
                
                try:
                    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
                    
                    # Normalize phone number to E.164 format for Twilio (starts with +)
                    raw_phone = recipient.profile.phone.strip()
                    formatted_phone = raw_phone
                    if not raw_phone.startswith('+'):
                        if raw_phone.startswith('0') and len(raw_phone) == 11:
                            formatted_phone = '+234' + raw_phone[1:]
                        else:
                            formatted_phone = '+' + raw_phone
                    
                    if account_sid and auth_token and twilio_number:
                        # Ensure twilio_number is also in E.164 format if it's not already
                        # Twilio phone numbers are usually already formatted correctly (+123...)
                        # but some users might provide them without the plus.
                        from_number = twilio_number.strip()
                        if not from_number.startswith('+'):
                            if from_number.startswith('0') and len(from_number) == 11:
                                from_number = '+234' + from_number[1:]
                            else:
                                from_number = '+' + from_number

                        if formatted_phone == from_number:
                            sms_log.status = 'failed'
                            sms_log.error_message = f"Recipient number {formatted_phone} is same as Twilio sender number."
                            sms_log.save()
                            messages.warning(request, "SMS not sent: Recipient cannot be the same as the Twilio sender.")
                            continue

                        client = Client(account_sid, auth_token)
                        client.messages.create(
                            body=sms_body,
                            from_=from_number,
                            to=formatted_phone
                        )
                        sms_log.status = 'sent'
                        sms_log.sent_at = timezone.now()
                        sms_log.save()
                        messages.success(request, f"SMS notification sent to {formatted_phone}")
                    else:
                        sms_log.status = 'failed'
                        sms_log.error_message = "Twilio credentials missing in environment."
                        sms_log.save()
                        messages.warning(request, "SMS not sent: Twilio credentials missing.")
                except Exception as e:
                    sms_log.status = 'failed'
                    sms_log.error_message = str(e)
                    sms_log.save()
                    logger.error(f"Failed to send SMS to {recipient.profile.phone}: {e}")
                    messages.error(request, f"Failed to send SMS to {recipient.profile.phone}.")
        
        messages.success(request, f'Message sent successfully and notifications dispatched!')
        return redirect('notifications:sent_messages')
    
    # Simple recipient selection logic for Admin
    if request.user.profile.role == 'admin':
        recipients = User.objects.exclude(id=request.user.id)
    else:
        # Others can only message admins for now as a simple rule
        recipients = User.objects.filter(profile__role='admin')
        
    return render(request, 'notifications/compose.html', {'recipients': recipients})

@login_required
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if message.recipient != request.user and message.sender != request.user:
        return render(request, '403.html', status=403)
    
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
        
    return render(request, 'notifications/message_detail.html', {'message': message})


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_POST
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def mark_all_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
def get_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def get_recent_notifications(request):
    notifications = Notification.objects.filter(user=request.user)[:5]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message[:100],
        'type': n.notification_type,
        'is_read': n.is_read,
        'link': n.link,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notifications]
    return JsonResponse({'notifications': data})


@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    if notification.link:
        return redirect(notification.link)
    
    return render(request, 'notifications/notification_detail.html', {'notification': notification})

@login_required
@require_POST
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def delete_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if message.recipient != request.user and message.sender != request.user:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    message.delete()
    return JsonResponse({'status': 'success'})

@login_required
def activity_logs(request):
    if request.user.profile.role != 'admin':
        return render(request, '403.html', status=403)
    
    from school_project_ai.core.models import AuditLog
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    return render(request, 'core/audit_logs.html', {'logs': logs})

@login_required
@require_POST
def delete_audit_log(request, pk):
    if request.user.profile.role != 'admin':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    from school_project_ai.core.models import AuditLog
    log = get_object_or_404(AuditLog, pk=pk)
    log.delete()
    return JsonResponse({'status': 'success'})


@login_required
def announcement_list(request):
    now = timezone.now()
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
    else:
        role = 'student'
    
    role_map = {
        'student': 'students',
        'teacher': 'teachers',
        'parent': 'parents',
        'admin': 'all',
        'accountant': 'staff',
        'librarian': 'staff',
    }
    
    audience = role_map.get(role, 'students')
    
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(audience='all') | models.Q(audience=audience)
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    )
    
    context = {
        'announcements': announcements,
    }
    return render(request, 'notifications/announcement_list.html', context)

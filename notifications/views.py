from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .models import Notification, Announcement, Message, PushSubscription
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

            # SMS sending via Termii
            if hasattr(recipient, 'profile') and recipient.profile.phone:
                from .models import SMSLog
                import requests
                import json
                import os
                
                sms_body = f"New School Message: {subject}. Check your portal."
                sms_log = SMSLog.objects.create(
                    recipient_phone=recipient.profile.phone,
                    recipient_name=recipient.get_full_name(),
                    message=sms_body,
                    status='pending'
                )
                
                try:
                    termii_api_key = os.environ.get('TERMII_API_KEY')
                    termii_sender_id = os.environ.get('TERMII_SENDER_ID', 'SchoolApp')
                    
                    # Normalize phone number for Termii
                    raw_phone = recipient.profile.phone.strip()
                    formatted_phone = raw_phone
                    if raw_phone.startswith('+'):
                        formatted_phone = raw_phone[1:]
                    elif raw_phone.startswith('0') and len(raw_phone) == 11:
                        formatted_phone = '234' + raw_phone[1:]
                    
                    if termii_api_key:
                        payload = {
                            "to": formatted_phone,
                            "from": termii_sender_id,
                            "sms": sms_body,
                            "type": "plain",
                            "channel": "generic",
                            "api_key": termii_api_key
                        }
                        headers = {
                            'Content-Type': 'application/json',
                        }
                        
                        response = requests.post(
                            "https://api.ng.termii.com/api/sms/send",
                            headers=headers,
                            data=json.dumps(payload),
                            timeout=30
                        )
                        result = response.json()
                        
                        if response.status_code == 200 and (result.get('status') == 'success' or result.get('message') == 'Successfully Sent'):
                            sms_log.status = 'sent'
                            sms_log.sent_at = timezone.now()
                            sms_log.save()
                            messages.success(request, f"SMS notification sent to {formatted_phone}")
                        else:
                            sms_log.status = 'failed'
                            sms_log.error_message = result.get('message', 'Unknown error from Termii')
                            sms_log.save()
                            messages.warning(request, f"SMS failed: {sms_log.error_message}")
                    else:
                        sms_log.status = 'failed'
                        sms_log.error_message = "Termii API key missing in environment."
                        sms_log.save()
                        messages.warning(request, "SMS not sent: Termii configuration missing.")
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
    selected_audience = request.GET.get('audience')

    all_qs = Announcement.objects.filter(is_active=True)

    if role == 'admin' and selected_audience:
        announcements = all_qs.filter(audience=selected_audience)
    elif role == 'admin':
        announcements = all_qs
    else:
        announcements = all_qs.filter(
            models.Q(audience='all') | models.Q(audience=audience)
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )

    total_count = all_qs.count()
    active_count = all_qs.filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    ).count()
    today_count = all_qs.filter(created_at__date=now.date()).count()
    expired_count = all_qs.filter(expires_at__lt=now).count()

    context = {
        'announcements': announcements,
        'selected_audience': selected_audience,
        'total_count': total_count,
        'active_count': active_count,
        'today_count': today_count,
        'expired_count': expired_count,
    }
    return render(request, 'notifications/announcement_list.html', context)


def _get_audience_users(audience):
    role_map = {
        'all': None,
        'students': 'student',
        'teachers': 'teacher',
        'parents': 'parent',
        'staff': ['accountant', 'librarian', 'teacher'],
    }
    mapping = role_map.get(audience)
    if mapping is None:
        return User.objects.all()
    if isinstance(mapping, list):
        return User.objects.filter(profile__role__in=mapping)
    return User.objects.filter(profile__role=mapping)


def _send_push_to_users(target_users, title, body, url='/notifications/announcements/'):
    from django.conf import settings as django_settings
    from pywebpush import webpush, WebPushException
    import json

    vapid_private = django_settings.VAPID_PRIVATE_KEY
    vapid_claims = {"sub": f"mailto:{django_settings.VAPID_ADMIN_EMAIL}"}

    subscriptions = PushSubscription.objects.filter(user__in=target_users)
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=vapid_private,
                vapid_claims=vapid_claims,
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code in (404, 410):
                sub.delete()
        except Exception:
            pass


@login_required
def create_announcement(request):
    if request.user.profile.role not in ('admin', 'teacher'):
        return redirect('notifications:announcements')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        audience = request.POST.get('audience', 'all')
        expires_at = request.POST.get('expires_at') or None
        do_send_email = request.POST.get('send_email') == 'on'
        do_send_sms = request.POST.get('send_sms') == 'on'

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return redirect('notifications:announcements')

        announcement = Announcement.objects.create(
            title=title,
            content=content,
            audience=audience,
            expires_at=expires_at,
            send_email=do_send_email,
            send_sms=do_send_sms,
            is_active=True,
            created_by=request.user,
        )

        target_users = _get_audience_users(audience)

        # 1. In-app notifications for all target users
        notifications_to_create = []
        for u in target_users:
            notifications_to_create.append(Notification(
                user=u,
                title=f"📢 {title}",
                message=content[:200],
                notification_type='announcement',
                link='/notifications/announcements/',
            ))
        Notification.objects.bulk_create(notifications_to_create, ignore_conflicts=True)

        # 2. Email notifications
        if do_send_email:
            from django.core.mail import send_mail
            from django.conf import settings as django_settings
            email_recipients = [u.email for u in target_users if u.email]
            if email_recipients:
                try:
                    from_email = django_settings.DEFAULT_FROM_EMAIL or django_settings.EMAIL_HOST_USER
                    send_mail(
                        subject=f"📢 Announcement: {title}",
                        message=f"{content}\n\n---\nThis is an official announcement from School Suite Pro.\nLogin to your portal for more details.",
                        from_email=from_email,
                        recipient_list=email_recipients,
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send announcement emails: {e}")

        # 3. Browser push notifications to all subscribed target users
        try:
            _send_push_to_users(target_users, f"📢 {title}", content[:120], '/notifications/announcements/')
        except Exception as e:
            logger.error(f"Push notification error: {e}")

        messages.success(request, f'Announcement "{title}" posted and notifications sent!')

    return redirect('notifications:announcements')


@login_required
def push_subscribe(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            p256dh = data.get('keys', {}).get('p256dh')
            auth = data.get('keys', {}).get('auth')

            if endpoint and p256dh and auth:
                PushSubscription.objects.update_or_create(
                    endpoint=endpoint,
                    defaults={
                        'user': request.user,
                        'p256dh': p256dh,
                        'auth': auth,
                    }
                )
                return JsonResponse({'status': 'subscribed'})
        except Exception as e:
            logger.error(f"Push subscribe error: {e}")
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def push_unsubscribe(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            if endpoint:
                PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
                return JsonResponse({'status': 'unsubscribed'})
        except Exception as e:
            logger.error(f"Push unsubscribe error: {e}")
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def push_public_key(request):
    from django.conf import settings as django_settings
    return JsonResponse({'public_key': django_settings.VAPID_PUBLIC_KEY})


@login_required
def delete_announcement(request, pk):
    if request.user.profile.role != 'admin':
        return redirect('notifications:announcements')

    if request.method == 'POST':
        announcement = get_object_or_404(Announcement, pk=pk)
        title = announcement.title
        announcement.delete()
        messages.success(request, f'Announcement "{title}" deleted.')

    return redirect('notifications:announcements')

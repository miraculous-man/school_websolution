from ..models import AuditLog

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Capture basic info for mutating requests
            path = request.path.strip('/').split('/')
            app_name = path[0] if path else 'system'
            
            # Create a more readable description
            action_verb = "performed an action on"
            if request.method == 'POST': action_verb = "created/submitted data to"
            elif request.method == 'PUT' or request.method == 'PATCH': action_verb = "updated information in"
            elif request.method == 'DELETE': action_verb = "deleted data from"
            
            # Map common paths to friendly names
            friendly_path = request.path
            if 'notifications' in request.path: friendly_path = "Notifications/Messages"
            elif 'finance' in request.path: friendly_path = "Finance/Payments"
            elif 'students' in request.path: friendly_path = "Student Records"
            elif 'teachers' in request.path: friendly_path = "Staff Records"
            elif 'attendance' in request.path: friendly_path = "Attendance System"
            elif 'cbt' in request.path: friendly_path = "CBT/Exams"
            
            description = f"User {action_verb} {friendly_path}"
            
            # Get IP Address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            AuditLog.objects.create(
                user=request.user,
                action='UPDATE' if request.method != 'DELETE' else 'DELETE',
                description=description,
                ip_address=ip
            )
            
        return response

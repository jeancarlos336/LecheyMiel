from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            
            if not last_activity:
                request.session['last_activity'] = timezone.now().isoformat()
            else:
                last_activity = timezone.datetime.fromisoformat(last_activity)
                time_elapsed = timezone.now() - last_activity
                
                if time_elapsed.total_seconds() > 4800:
                    logout(request)
                    messages.warning(request, 'Su sesión ha expirado por inactividad.')
                    return redirect('users:login')
            
            # Si la petición es para actualizar la actividad desde JavaScript
            if request.path == '/usuarios/update_activity/' and request.method == 'POST':
                request.session['last_activity'] = timezone.now().isoformat()
                
        response = self.get_response(request)
        return response
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages

# ===============================
# RUTAS QUE NO DEBEN DISPARAR
# EL CHEQUEO DE TIMEOUT
# ===============================
EXEMPT_PATHS = [
    '/static/',
    '/media/',
    '/favicon.ico',
]

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:

            # ✅ CORRECCIÓN 1: Rutas estáticas no deben renovar ni chequear sesión
            # En el original, cada imagen/CSS/JS cargado en móvil tocaba la sesión
            path = request.path
            is_exempt = any(path.startswith(p) for p in EXEMPT_PATHS)

            if not is_exempt:

                # ✅ CORRECCIÓN 2: Verificar update_activity ANTES del chequeo de timeout
                # En el original, si la sesión expiraba hacía logout ANTES de
                # poder renovar la actividad desde el JS del celular
                if path == '/usuarios/update_activity/' and request.method == 'POST':
                    request.session['last_activity'] = timezone.now().isoformat()

                else:
                    last_activity = request.session.get('last_activity')

                    if not last_activity:
                        # Primera visita: inicializar la actividad
                        request.session['last_activity'] = timezone.now().isoformat()
                    else:
                        try:
                            last_activity_dt = timezone.datetime.fromisoformat(last_activity)
                            time_elapsed = timezone.now() - last_activity_dt

                            if time_elapsed.total_seconds() > 4800:
                                logout(request)
                                messages.warning(request, 'Su sesión ha expirado por inactividad.')
                                return redirect('users:login')
                            else:
                                # ✅ CORRECCIÓN 3: Solo actualizar cada 60 segundos
                                # En el original actualizaba en CADA request,
                                # generando escrituras constantes a la BD desde móvil
                                if time_elapsed.total_seconds() > 60:
                                    request.session['last_activity'] = timezone.now().isoformat()

                        except (ValueError, TypeError):
                            # ✅ CORRECCIÓN 4: Manejo de error si el isoformat está corrupto
                            # En el original, un valor corrupto en sesión crasheaba el middleware
                            # silenciosamente y dejaba la página colgada
                            request.session['last_activity'] = timezone.now().isoformat()

        response = self.get_response(request)
        return response
from .signals import set_current_user, get_current_user

class AuditMiddleware:
    """
    Middleware para capturar el usuario actual y hacerlo disponible
    para el sistema de auditoría
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Almacenar el usuario en el thread local
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
            
        response = self.get_response(request)
        
        # Limpiar después de la respuesta
        set_current_user(None)
        
        return response
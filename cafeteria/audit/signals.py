from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.apps import apps
from .models import LogActividad
from threading import local

# Thread local para almacenar el usuario actual
_thread_locals = local()

# Función para establecer el usuario actual
def set_current_user(user):
    _thread_locals.user = user

# Función para obtener el usuario actual
def get_current_user():
    return getattr(_thread_locals, 'user', None)

# Lista de modelos que queremos auditar
MODELOS_AUDITADOS = [
    'users.Usuario',
    'users.Rol',
    'products.Producto',
    'products.Categoria',    
    'products.AreaPreparacion',
    'orders.Mesa',
    'orders.Pedido',
    'orders.DetallePedido',
    'orders.Pago',
]

def registrar_log(sender, instance, created, **kwargs):
    """
    Registra un log cuando un objeto es creado o modificado
    """
    # Intenta obtener el usuario actual
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Intenta obtener el usuario desde el thread local
    usuario = get_current_user()
    
    # Si no hay usuario en thread local, intenta obtenerlo del request actual
    if usuario is None:
        try:
            from django.contrib.auth.middleware import get_user
            from django.contrib.auth.models import AnonymousUser
            
            # Este es un intento más avanzado que puede no funcionar en todas las configuraciones
            from django.core.handlers.wsgi import WSGIRequest
            from django.contrib.sessions.middleware import SessionMiddleware
            
            # Esto es una aproximación y puede no funcionar en todos los casos
            from threading import current_thread
            for frame in sys._current_frames().values():
                if 'request' in frame.f_locals:
                    request = frame.f_locals['request']
                    if isinstance(request, WSGIRequest):
                        usuario = request.user if hasattr(request, 'user') else None
                        break
        except:
            usuario = None
    
    # Obtener el tipo de contenido para el modelo
    content_type = ContentType.objects.get_for_model(sender)
    
    # Determinar la acción realizada
    accion = 'crear' if created else 'actualizar'
    
    # Crear el log
    LogActividad.objects.create(
        usuario=usuario,
        accion=accion,
        modelo=content_type.model,
        objeto_id=instance.pk,
        detalles={
            'app_label': content_type.app_label,
            'model': content_type.model,
            'object_repr': str(instance)
        }
    )

# La función registrar_eliminacion es similar pero cambia el código de acción
def registrar_eliminacion(sender, instance, **kwargs):
    """Registra un log cuando un objeto es eliminado"""
    # Código similar al anterior pero con acción='eliminar'
    usuario = get_current_user()
    
    # Obtener el tipo de contenido para el modelo
    content_type = ContentType.objects.get_for_model(sender)
    
    # Crear el log
    LogActividad.objects.create(
        usuario=usuario,
        accion='eliminar',
        modelo=content_type.model,
        objeto_id=instance.pk,
        detalles={
            'app_label': content_type.app_label,
            'model': content_type.model,
            'object_repr': str(instance)
        }
    )

def conectar_signals():
    """
    Conecta las señales para todos los modelos que queremos auditar
    """
    for modelo_path in MODELOS_AUDITADOS:
        app_label, model_name = modelo_path.split('.')
        model = apps.get_model(app_label, model_name)
        
        # Conectar signal para creación/actualización
        post_save.connect(registrar_log, sender=model, weak=False)
        
        # Conectar signal para eliminación
        post_delete.connect(registrar_eliminacion, sender=model, weak=False)

# Conectar las señales
conectar_signals()
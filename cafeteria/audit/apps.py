from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"
    
    def ready(self):
        """
        Importar y conectar las señales cuando la app está lista
        """
        from . import signals
        signals.conectar_signals()
from django.db import models

# audit/models.py
class LogActividad(models.Model):
    """Registra todas las acciones importantes realizadas en el sistema"""
    usuario = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=255)
    modelo = models.CharField(max_length=100)
    objeto_id = models.IntegerField()
    detalles = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha_hora}"
    
    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-fecha_hora']

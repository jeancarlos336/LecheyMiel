from django.db import models

# notifications/models.py
class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('nuevo_pedido', 'Nuevo Pedido'),
        ('pedido_listo', 'Pedido Listo'),
        ('pedido_cancelado', 'Pedido Cancelado'),
        ('item_listo', 'Item Listo'),
        ('cambio_estado', 'Cambio de Estado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]
    
    destinatario = models.ForeignKey('users.Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    enlace = models.CharField(max_length=255, blank=True, null=True)  # URL para redirigir al usuario
    pedido = models.ForeignKey('orders.Pedido', on_delete=models.CASCADE, null=True, blank=True)
    detalle_pedido = models.ForeignKey('orders.DetallePedido', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.destinatario}"
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

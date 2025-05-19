from django.db import models
from django.urls import reverse
from django.utils import timezone 


class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('mantenimiento', 'Mantenimiento')
    ]
    numero = models.IntegerField(unique=True)
    capacidad = models.IntegerField()
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='disponible'
    )
    area = models.CharField(max_length=50, blank=True, null=True)
    codigo_qr = models.ImageField(upload_to='mesas_qr/', blank=True, null=True)  # Para identificación rápida
    
    @property
    def esta_disponible(self):
        return self.estado == 'disponible'
        
    def __str__(self):
        return f"Mesa {self.numero} - {self.area}" if self.area else f"Mesa {self.numero}"
    
    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['numero']

class TipoOrden(models.Model):
    """Modelo para definir los diferentes tipos de órdenes"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    requiere_mesa = models.BooleanField(default=True)
    codigo = models.CharField(max_length=10, unique=True)  # Código corto para identificar tipo
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Orden"
        verbose_name_plural = "Tipos de Órdenes"
        ordering = ['nombre']

class Pedido(models.Model):
    ESTADO_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En Preparación'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado')
    ]
   
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('impago','Impago'),
        ('cancelado', 'Cancelado')
    ]
   
    # Hacemos mesa opcional para permitir pedidos sin mesa
    mesa = models.ForeignKey(Mesa, on_delete=models.PROTECT, null=True, blank=True)
    # Nuevo campo para tipo de orden
    tipo_orden = models.ForeignKey(TipoOrden, on_delete=models.PROTECT)
    mesero = models.ForeignKey('users.Usuario', on_delete=models.PROTECT, related_name='pedidos_tomados')
    cajero = models.ForeignKey('users.Usuario', on_delete=models.PROTECT, related_name='pedidos_cobrados', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO, default='pendiente')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    notas = models.TextField(blank=True, null=True)
    numero_comensales = models.IntegerField(default=1)
    # Nuevo campo para identificar pedidos sin mesa
    nombre_cliente = models.CharField(max_length=100, blank=True, null=True, 
                                     help_text="Nombre del cliente para pedidos para llevar")
    numero_orden = models.CharField(max_length=20, blank=True, null=True, 
                                   help_text="Número de orden para identificar pedidos para llevar")
   
    def __str__(self):
        if self.mesa:
            return f"Pedido #{self.id} - Mesa {self.mesa.numero}"
        else:
            return f"Pedido #{self.id} - {self.tipo_orden.nombre} - {self.nombre_cliente or 'Sin nombre'}"
   
    def calcular_total(self):
        """Recalcula el total del pedido basado en sus detalles activos (no cancelados)"""
        # Solo suma los detalles que no están cancelados
        total = sum(detalle.subtotal for detalle in self.detalles.all().exclude(estado='cancelado'))
        self.monto_total = total
        self.save()
        return total
    
    def calcular_total_sin_guardar(self):
        """Calcula el total del pedido sin guardar el modelo, útil para previsualización"""
        return sum(detalle.subtotal for detalle in self.detalles.all().exclude(estado='cancelado'))
    
    @property
    def items_activos(self):
        """Devuelve solo los detalles del pedido que no están cancelados"""
        return self.detalles.all().exclude(estado='cancelado')
    


    def save(self, *args, **kwargs):
        """Sobrescribe el método save para generar un número de orden automático si es necesario"""
        if not self.mesa and not self.numero_orden:
            # Genera un número de orden para pedidos sin mesa
            fecha_actual = timezone.now()
            
            ultimo_numero = Pedido.objects.filter(
                tipo_orden=self.tipo_orden, 
                fecha_creacion__date=fecha_actual.date()
            ).count() + 1
            
            # Formato: TipoOrden-YYYYMMDD-NNN (ejemplo: LLEV-20240502-001)
            fecha_str = fecha_actual.strftime('%Y%m%d')
            self.numero_orden = f"{self.tipo_orden.codigo}-{fecha_str}-{ultimo_numero:03d}"
        
        super().save(*args, **kwargs)
   
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

class DetallePedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En Preparación'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado')
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('products.Producto', on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    preparado_por = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='items_preparados')
    hora_solicitud = models.DateTimeField(auto_now_add=True)
    hora_preparacion = models.DateTimeField(null=True, blank=True)
    hora_listo = models.DateTimeField(null=True, blank=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    @property
    def area_preparacion(self):
        """Devuelve el área de preparación del producto"""
        return self.producto.area_preparacion
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"
        
class Pago(models.Model):
    METODOS_PAGO = (
        ('efectivo', 'Efectivo'),
        ('pendiente','Pendiente'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
    )
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cambio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pago {self.id} - Pedido {self.pedido.id}"
    
class PagoPendiente(models.Model):
    pago = models.OneToOneField('Pago', on_delete=models.CASCADE, related_name='pendiente_info')
    cliente_nombre = models.CharField(max_length=255)
    fecha_promesa = models.DateField()
    esta_pagado = models.BooleanField(default=False)
    fecha_pago_real = models.DateField(null=True, blank=True)
    notas_adicionales = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pendiente: {self.cliente_nombre} - ${self.pago.monto}"
    
    def get_absolute_url(self):
        return reverse('orders:pagos_pendientes')
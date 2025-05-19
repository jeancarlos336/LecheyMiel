from django.db import models
from django.utils import timezone

class Proveedor(models.Model):
    """Modelo para almacenar información básica de proveedores"""
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

class Compra(models.Model):
    """Modelo para registrar compras de forma simple"""
    TIPO_DOCUMENTO_CHOICES = (
        ('boleta', 'Boleta'),
        ('factura', 'Factura'),
        ('sin_documento', 'Sin Documento'),
        ('transferencia', 'Transferencia'),
        ('otro', 'Otro'),
    )
    
    fecha = models.DateField(default=timezone.now)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='compras')
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, default='boleta')
    numero_documento = models.CharField(max_length=30, blank=True, null=True, 
                                       help_text="Número de boleta, factura o transferencia")
    destino = models.CharField(max_length=100, help_text="Área o departamento de destino")
    detalle = models.TextField(help_text="Descripción de artículos comprados")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True, 
                                 help_text="Imagen o PDF del comprobante")
    notas_adicionales = models.TextField(blank=True, null=True)
    
    def __str__(self):
        tipo_doc = dict(self.TIPO_DOCUMENTO_CHOICES).get(self.tipo_documento, 'Documento')
        numero = self.numero_documento if self.numero_documento else 'S/N'
        return f"{tipo_doc} {numero} - {self.proveedor.nombre} ({self.fecha})"
    
    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha']
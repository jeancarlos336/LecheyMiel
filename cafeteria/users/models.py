# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Rol(models.Model):
    ADMINISTRADOR = 'administrador'
    CAJA = 'caja'
    COCINA = 'cocina'
    MESERO = 'mesero'
    BAR = 'bar'  
    BARRA = 'barra'  
    
    ROL_CHOICES = [
        (ADMINISTRADOR, 'Administrador'),
        (CAJA, 'Caja'),
        (COCINA, 'Cocina'),
        (MESERO, 'Mesero'),
        (BAR, 'Bar'),
        (BARRA, 'Barra'), 
    ]
    
    nombre = models.CharField(max_length=100, choices=ROL_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    permisos = models.JSONField(default=dict)
    
    def __str__(self):
        return self.get_nombre_display()

class Usuario(AbstractUser):
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True)
    esta_activo = models.BooleanField(default=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)  # Para contacto móvil
    foto_perfil = models.ImageField(upload_to='usuarios/', blank=True, null=True)
    device_token = models.CharField(max_length=255, blank=True, null=True)  # Para notificaciones push
    
    def __str__(self):
        return f"{self.username} - {self.rol}" if self.rol else self.username

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

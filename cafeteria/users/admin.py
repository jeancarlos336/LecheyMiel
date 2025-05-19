from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Rol, Usuario

class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'esta_activo')
    list_filter = ('esta_activo', 'rol', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'telefono', 'foto_perfil')}),
        ('Permisos', {'fields': ('rol', 'esta_activo', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
        ('Notificaciones', {'fields': ('device_token',)}),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

admin.site.register(Rol, RolAdmin)
admin.site.register(Usuario, CustomUserAdmin)
from django.contrib import admin
from .models import LogActividad

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'accion', 'modelo', 'objeto_id')
    list_filter = ('accion', 'modelo', 'fecha_hora', 'usuario')
    search_fields = ('usuario__username', 'accion', 'modelo', 'objeto_id')
    readonly_fields = ('fecha_hora', 'usuario', 'accion', 'modelo', 'objeto_id', 'detalles')
    
    def has_add_permission(self, request):
        # No permitir añadir logs manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # No permitir modificar logs
        return False
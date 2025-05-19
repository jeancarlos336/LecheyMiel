from django.contrib import admin
from django.utils.html import format_html
from .models import Proveedor, Compra

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'total_compras')
    search_fields = ('nombre', 'email')
    
    def total_compras(self, obj):
        """Muestra el total de compras realizadas a este proveedor"""
        count = obj.compras.count()
        return format_html(
            '<a href="/admin/compras/compra/?proveedor__id__exact={}">{} compras</a>',
            obj.id, count
        )
    
    total_compras.short_description = "Total de compras"

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'proveedor', 'tipo_documento', 'numero_documento', 
                    'destino', 'mostrar_total', 'ver_comprobante')
    list_filter = ('tipo_documento', 'fecha', 'proveedor', 'destino')
    search_fields = ('numero_documento', 'detalle', 'proveedor__nombre')
    date_hierarchy = 'fecha'
    
    fieldsets = (
        (None, {
            'fields': (('fecha', 'proveedor'), ('tipo_documento', 'numero_documento'))
        }),
        ('Detalles de la compra', {
            'fields': ('destino', 'detalle', 'total', 'comprobante')
        }),
        ('Información adicional', {
            'fields': ('notas_adicionales',),
            'classes': ('collapse',),
        }),
    )

    def mostrar_total(self, obj):
        """Muestra el total con formato de moneda"""
        total_str = "${:.2f}".format(float(obj.total))  # Asegúrate de que sea float
        return format_html("{}", total_str)  # Pasa una cadena segura a format_html      
    
    mostrar_total.short_description = "Total"
    
    def ver_comprobante(self, obj):
        """Muestra un enlace al comprobante si existe"""
        if obj.comprobante:
            return format_html('<a href="{}" target="_blank">Ver</a>', obj.comprobante.url)
        return "—"
    
    ver_comprobante.short_description = "Comprobante"
from django.contrib import admin
from .models import Producto, Categoria, AreaPreparacion

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'esta_disponible')
    list_filter = ('categoria', 'esta_disponible')
    search_fields = ('nombre', 'descripcion')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'area_preparacion')
    search_fields = ('nombre', 'descripcion')

@admin.register(AreaPreparacion)
class AreaPreparacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
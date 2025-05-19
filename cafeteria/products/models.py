from django.db import models


# products/models.py
class AreaPreparacion(models.Model):
    """Representa las áreas donde se preparan los productos"""
    COCINA = 'cocina'
    BAR = 'bar'
    BARRA = 'barra'
    
    AREA_CHOICES = [
        (COCINA, 'Cocina'),
        (BAR, 'Bar'),
        (BARRA, 'Barra'),
    ]
    
    nombre = models.CharField(max_length=50, choices=AREA_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_nombre_display()
    
    class Meta:
        verbose_name = "Área de Preparación"
        verbose_name_plural = "Áreas de Preparación"

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True, help_text="Nombre de la categoría")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción de la categoría")
    area_preparacion = models.ForeignKey(
        AreaPreparacion, 
        on_delete=models.PROTECT,
        help_text="Área donde se prepara esta categoría de productos",
        null=True
    )
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

class Producto(models.Model):
    nombre = models.CharField(max_length=100, help_text="Nombre del producto")
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del producto"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        help_text="Categoría del producto"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción del producto"
    )
    esta_disponible = models.BooleanField(
        default=True,
        help_text="Indica si el producto está disponible para venta"
    )
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True,
        help_text="Subir imagen cuadrada de 500x500px para mejor calidad"
    )
    
    tiempo_preparacion = models.IntegerField(
        help_text="Tiempo de preparación en minutos",
        default=15
    )
    
    def __str__(self):
        return self.nombre
    
    @property
    def area_preparacion(self):
        """Devuelve el área de preparación del producto basado en su categoría"""
        return self.categoria.area_preparacion
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['categoria', 'nombre']

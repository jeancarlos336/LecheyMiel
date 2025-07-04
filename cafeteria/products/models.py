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
        help_text="Precio de venta del producto"
    )
    # NUEVO CAMPO: Costo del producto
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo del producto"
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
    
    @property
    def ganancia_unitaria(self):
        """Ganancia por unidad del producto"""
        return self.precio - self.costo
    
    @property
    def margen_porcentaje(self):
        """Margen de ganancia en porcentaje"""
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return 0
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['categoria', 'nombre']


class Stock(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='stock')
    cantidad_actual = models.IntegerField(default=0, help_text="Cantidad en inventario")
    stock_minimo = models.IntegerField(default=5, help_text="Cantidad mínima para alertas")
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    @property
    def tiene_stock(self):
        return self.cantidad_actual > 0
    
    @property
    def necesita_reposicion(self):
        return self.cantidad_actual <= self.stock_minimo
    
    @property
    def estado_stock(self):
        if self.cantidad_actual == 0:
            return "sin_stock"
        elif self.necesita_reposicion:
            return "stock_bajo"
        else:
            return "stock_ok"
    
    def agregar_stock(self, cantidad, motivo=""):
        """Agrega stock al producto"""
        if cantidad > 0:
            self.cantidad_actual += cantidad
            self.save()
            
            # Crear registro de movimiento
            MovimientoStock.objects.create(
                producto=self.producto,
                tipo='entrada',
                cantidad=cantidad,
                motivo=motivo or "Entrada manual de stock"
            )
            return True
        return False
    
    def descontar_stock(self, cantidad, motivo=""):
        """Descuenta stock del producto"""
        if self.cantidad_actual >= cantidad:
            self.cantidad_actual -= cantidad
            self.save()
            
            # Crear registro de movimiento
            MovimientoStock.objects.create(
                producto=self.producto,
                tipo='salida',
                cantidad=cantidad,
                motivo=motivo or "Venta"
            )
            return True
        return False
    
    def puede_vender(self, cantidad):
        """Verifica si hay suficiente stock para vender"""
        return self.cantidad_actual >= cantidad
    
    def __str__(self):
        return f"{self.producto.nombre}: {self.cantidad_actual} unidades"
    
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        ordering = ['producto__nombre']

class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=200, help_text="Razón del movimiento")
    referencia = models.CharField(max_length=100, blank=True, null=True, 
                                help_text="ID de pedido, compra o referencia")
    usuario = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        tipo_display = dict(self.TIPO_MOVIMIENTO)[self.tipo]
        return f"{tipo_display}: {self.cantidad} - {self.producto.nombre}"
    
    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-fecha']
from django import forms
from .models import Producto, Categoria, AreaPreparacion,Stock, MovimientoStock


class AreaPreparacionForm(forms.ModelForm):
    class Meta:
        model = AreaPreparacion
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'area_preparacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'costo', 
            'precio', 
            'categoria', 
            'descripcion', 
            'esta_disponible', 
            'imagen', 
            'tiempo_preparacion'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'step': '0.01'}),
        }
        


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['cantidad_actual', 'stock_minimo']
        widgets = {
            'cantidad_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Cantidad actual'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Stock mínimo'
            }),
        }
        labels = {
            'cantidad_actual': 'Cantidad Actual',
            'stock_minimo': 'Stock Mínimo'
        }

class AgregarStockForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cantidad a agregar'
        }),
        label='Cantidad a Agregar'
    )
    motivo = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Motivo (opcional)'
        }),
        label='Motivo'
    )

class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['tipo', 'cantidad', 'motivo', 'referencia']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón del movimiento'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referencia (opcional)'
            }),
        }
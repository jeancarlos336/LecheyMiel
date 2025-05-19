from django import forms
from .models import Producto, Categoria, AreaPreparacion

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
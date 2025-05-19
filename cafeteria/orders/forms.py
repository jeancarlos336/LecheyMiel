from django import forms
from .models import Pedido, DetallePedido, Mesa
from django.db import transaction
from .models import Pedido, DetallePedido
from products.models import Categoria, Producto  # Importación desde el módulo de productos

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['mesa', 'estado']
        widgets = {
            'mesa': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

class DetallePedidoForm(forms.ModelForm):
    # Campo de categoría para filtrar productos
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),  # Ahora usando la importación correcta
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),  # También importado desde products
        widget=forms.Select(attrs={'class': 'form-control'})
    )
   
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'notas']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'default': 1
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Este código hace que el campo producto se filtre si se selecciona una categoría
        if 'categoria' in self.data:
            try:
                categoria_id = int(self.data.get('categoria'))
                self.fields['producto'].queryset = Producto.objects.filter(categoria_id=categoria_id)
            except (ValueError, TypeError):
                pass

class SeleccionMesaForm(forms.Form):
    mesa = forms.ModelChoiceField(
        queryset=Mesa.objects.filter(estado='disponible'),
        empty_label="Seleccione una mesa",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
   
    
class MesaForm(forms.ModelForm):
    """Formulario para crear y editar mesas"""
    class Meta:
        model = Mesa
        fields = ['numero', 'capacidad', 'estado', 'area']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'capacidad': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'estado': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'area': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'})
        }
        
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        try:
            numero_int = int(numero)
            if numero_int <= 0:
                raise forms.ValidationError("El número de mesa debe ser mayor que cero")
        
        # Verificar si el número de mesa ya existe (solo para nuevas mesas)
            if not self.instance.pk:  # Si es una nueva mesa
                if Mesa.objects.filter(numero=numero_int).exists():
                    raise forms.ValidationError("Este número de mesa ya está en uso")
        
            return numero_int  # Devuelve el número como entero
        except ValueError:
            raise forms.ValidationError("El número de mesa debe ser un valor numérico")   
    
    def clean_capacidad(self):
        capacidad = self.cleaned_data.get('capacidad')
        if capacidad <= 0:
            raise forms.ValidationError("La capacidad debe ser mayor que cero")
        if capacidad > 20:
            raise forms.ValidationError("La capacidad máxima es de 20 personas")
        return capacidad
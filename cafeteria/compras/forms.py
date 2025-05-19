# compras/forms.py
from django import forms
from .models import Proveedor, Compra

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'email', 'direccion', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CompraForm(forms.ModelForm):
    # Reemplazar el campo fecha con un campo CharField para más control
    fecha = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        required=True
    )
    
    class Meta:
        model = Compra
        fields = ['fecha', 'proveedor', 'tipo_documento', 'numero_documento',
                 'destino', 'detalle', 'total', 'comprobante', 'notas_adicionales']
        widgets = {
            # Ya no necesitamos definir widget para fecha aquí
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'detalle': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprobante': forms.FileInput(attrs={'class': 'form-control'}),
            'notas_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha al formato dd-mm-yyyy para visualización cuando se edita
        if self.instance and self.instance.pk and self.instance.fecha:
            # Convertir la fecha al formato dd-mm-yyyy
            self.initial['fecha'] = self.instance.fecha.strftime('%d-%m-%Y')
    
    def clean_fecha(self):
        fecha_str = self.cleaned_data.get('fecha')
        try:
            # Parsear la fecha en formato dd-mm-yyyy
            import datetime
            fecha_obj = datetime.datetime.strptime(fecha_str, '%d-%m-%Y').date()
            return fecha_obj
        except ValueError:
            # Si falla el formato dd-mm-yyyy, intentar con yyyy-mm-dd
            try:
                fecha_obj = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
                return fecha_obj
            except ValueError:
                raise forms.ValidationError("Formato de fecha inválido. Use DD-MM-AAAA.")
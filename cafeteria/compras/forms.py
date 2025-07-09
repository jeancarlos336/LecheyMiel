# compras/forms.py
from django import forms
from .models import Proveedor, Compra,TipoCompra


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
        fields = ['fecha', 'proveedor', 'tipo_compra', 'tipo_documento', 'numero_documento',
                 'destino', 'detalle', 'total', 'comprobante', 'notas_adicionales']
        widgets = {
            # Ya no necesitamos definir widget para fecha aquí
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'tipo_compra': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'detalle': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comprobante': forms.FileInput(attrs={'class': 'form-control'}),
            'notas_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fecha': 'Fecha',
            'proveedor': 'Proveedor',
            'tipo_compra': 'Tipo de Compra',
            'tipo_documento': 'Tipo de Documento',
            'numero_documento': 'Número de Documento',
            'destino': 'Destino',
            'detalle': 'Detalle',
            'total': 'Total',
            'comprobante': 'Comprobante',
            'notas_adicionales': 'Notas Adicionales',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Formatear la fecha al formato dd-mm-yyyy para visualización cuando se edita
        if self.instance and self.instance.pk and self.instance.fecha:
            # Convertir la fecha al formato dd-mm-yyyy
            self.initial['fecha'] = self.instance.fecha.strftime('%d-%m-%Y')
        
        # Configurar el queryset para tipo_compra ordenado por categoría
        self.fields['tipo_compra'].queryset = TipoCompra.objects.all().order_by('id', 'nombre')
        
        # Hacer que algunos campos sean obligatorios
        self.fields['tipo_compra'].required = True
        self.fields['proveedor'].required = True
        self.fields['detalle'].required = True
        self.fields['total'].required = True
        
        # Agregar placeholder y ayuda contextual
        self.fields['fecha'].widget.attrs.update({
            'placeholder': 'DD-MM-AAAA',
            'data-bs-toggle': 'tooltip',
            'title': 'Formato: DD-MM-AAAA'
        })
        
        self.fields['numero_documento'].widget.attrs.update({
            'placeholder': 'Número de boleta, factura, etc.'
        })
        
        self.fields['destino'].widget.attrs.update({
            'placeholder': 'Área o departamento de destino'
        })
        
        self.fields['detalle'].widget.attrs.update({
            'placeholder': 'Describe los productos o servicios comprados'
        })
        
        self.fields['total'].widget.attrs.update({
            'placeholder': '0.00',
            'min': '0'
        })
        
        self.fields['notas_adicionales'].widget.attrs.update({
            'placeholder': 'Notas adicionales (opcional)'
        })
        
        # Agregar atributos para mejor UX
        self.fields['tipo_compra'].widget.attrs.update({
            'data-bs-toggle': 'tooltip',
            'title': 'Selecciona si es para venta, gasto o inversión'
        })
    
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
    
    def clean_total(self):
        total = self.cleaned_data.get('total')
        if total is not None and total <= 0:
            raise forms.ValidationError("El total debe ser mayor a 0.")
        return total
    
    def clean_numero_documento(self):
        numero = self.cleaned_data.get('numero_documento')
        tipo_documento = self.cleaned_data.get('tipo_documento')
        
        # Si el tipo de documento no es "sin_documento", el número es obligatorio
        if tipo_documento and tipo_documento != 'sin_documento' and not numero:
            raise forms.ValidationError("El número de documento es obligatorio para este tipo de documento.")
        
        return numero


####TIPO DE COMPRAS



class TipoCompraForm(forms.ModelForm):
    class Meta:
        model = TipoCompra
        fields = ['nombre', 'categoria', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del tipo de compra'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del tipo de compra'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'categoria': 'Categoría',
            'descripcion': 'Descripción'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False
        
        
        
#informe de compras



class FiltroComprasForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha inicio'
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha fin'
    )
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(),
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_compra = forms.ModelChoiceField(
        queryset=TipoCompra.objects.all(),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_documento = forms.ChoiceField(
        choices=[('', 'Todos los documentos')] + list(Compra.TIPO_DOCUMENTO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destino = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por destino'}),
        label='Destino'
    )
    total_min = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Total mínimo'
    )
    total_max = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Total máximo'
    )
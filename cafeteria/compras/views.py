# compras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView,View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Proveedor, Compra,TipoCompra
from .forms import ProveedorForm, CompraForm,TipoCompraForm
import calendar
from datetime import datetime
from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
from django.utils.translation import gettext as _
from compras.models import Compra
from orders.models import Pago
from django.utils import timezone

# Vistas para Proveedor
class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'compras/proveedor_list.html'
    context_object_name = 'proveedores'
    ordering = ['nombre']

class ProveedorDetailView(DetailView):
    model = Proveedor
    template_name = 'compras/proveedor_detail.html'
    context_object_name = 'proveedor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['compras'] = self.object.compras.all().order_by('-fecha')
        return context

class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'compras/proveedor_form.html'
    success_url = reverse_lazy('compras:proveedor_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Proveedor creado exitosamente.')
        return super().form_valid(form)

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'compras/proveedor_form.html'
    
    def get_success_url(self):
        return reverse_lazy('compras:proveedor_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Proveedor actualizado exitosamente.')
        return super().form_valid(form)

class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Proveedor
    template_name = 'compras/proveedor_confirm_delete.html'
    success_url = reverse_lazy('compras:proveedor_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Proveedor eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)





class CompraListView(ListView):
    model = Compra
    template_name = 'compras/compra_list.html'
    context_object_name = 'compras'
    paginate_by = 25
    ordering = ['-fecha']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('proveedor', 'tipo_compra')

        # Filtros
        proveedor_id = self.request.GET.get('proveedor')
        tipo_doc = self.request.GET.get('tipo_documento')
        tipo_compra_id = self.request.GET.get('tipo_compra')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        destino = self.request.GET.get('destino')
        monto_min = self.request.GET.get('monto_min')
        monto_max = self.request.GET.get('monto_max')

        if proveedor_id:
            queryset = queryset.filter(proveedor_id=proveedor_id)

        if tipo_doc:
            queryset = queryset.filter(tipo_documento=tipo_doc)

        if tipo_compra_id:
            queryset = queryset.filter(tipo_compra_id=tipo_compra_id)

        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__gte=fecha_desde)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__lte=fecha_hasta)
            except ValueError:
                pass

        if destino:
            queryset = queryset.filter(destino__icontains=destino)

        if monto_min:
            try:
                queryset = queryset.filter(total__gte=float(monto_min))
            except ValueError:
                pass

        if monto_max:
            try:
                queryset = queryset.filter(total__lte=float(monto_max))
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos para los filtros
        context['proveedores'] = Proveedor.objects.all().order_by('nombre')
        context['tipos_documento'] = dict(Compra.TIPO_DOCUMENTO_CHOICES)
        context['tipos_compra'] = TipoCompra.objects.all().order_by('nombre')
        
        # Datos para los filtros aplicados
        context['has_filters'] = any(
            key in self.request.GET 
            for key in ['proveedor', 'tipo_documento', 'tipo_compra', 
                       'fecha_desde', 'fecha_hasta', 'destino', 
                       'monto_min', 'monto_max']
        )
        
        # Obtener los objetos completos para mostrar en los filtros aplicados
        proveedor_id = self.request.GET.get('proveedor')
        if proveedor_id:
            context['selected_proveedor'] = Proveedor.objects.filter(id=proveedor_id).first()
        
        tipo_compra_id = self.request.GET.get('tipo_compra')
        if tipo_compra_id:
            context['selected_tipo_compra'] = TipoCompra.objects.filter(id=tipo_compra_id).first()
        
        # Calcular total de compras filtradas
        queryset = self.get_queryset()
        context['total_compras'] = queryset.aggregate(total=Sum('total'))['total'] or 0
        
        # Configuración de paginación
        page_obj = context.get('page_obj')
        if page_obj:
            context['compras'] = page_obj.object_list
            # Agregar índices de elementos mostrados
            start_index = page_obj.start_index()
            end_index = page_obj.end_index()
            context['compras'].start_index = start_index
            context['compras'].end_index = end_index
        
        return context

class CompraDetailView(DetailView):
    model = Compra
    template_name = 'compras/compra_detail.html'
    context_object_name = 'compra'

class CompraCreateView(LoginRequiredMixin, CreateView):
    model = Compra
    form_class = CompraForm
    template_name = 'compras/compra_form.html'
    success_url = reverse_lazy('compras:compra_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Compra registrada exitosamente.')
        return super().form_valid(form)

class CompraUpdateView(LoginRequiredMixin, UpdateView):
    model = Compra
    form_class = CompraForm
    template_name = 'compras/compra_form.html'
    
    def get_success_url(self):
        return reverse_lazy('compras:compra_list')
        
    
    def form_valid(self, form):
        messages.success(self.request, 'Compra actualizada exitosamente.')
        return super().form_valid(form)

class CompraDeleteView(LoginRequiredMixin, DeleteView):
    model = Compra
    template_name = 'compras/compra_confirm_delete.html'
    success_url = reverse_lazy('compras:compra_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Compra eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vista para el dashboard o resumen
@login_required
def dashboard(request):
    # Obtener estadísticas básicas
    total_compras = Compra.objects.count()
    total_proveedores = Proveedor.objects.count()
    
    # Compras recientes
    compras_recientes = Compra.objects.all().order_by('-fecha')[:5]
    
    # Contexto
    context = {
        'total_compras': total_compras,
        'total_proveedores': total_proveedores,
        'compras_recientes': compras_recientes,
    }
    
    return render(request, 'compras/dashboard.html', context)


#BALANCE ANUAL

class BalanceAnualView(LoginRequiredMixin, View):
    template_name = 'compras/balance_anual.html'
    
    def get(self, request, *args, **kwargs):
        # Obtener año seleccionado, por defecto el año actual
        year = int(request.GET.get('year', datetime.now().year))
        
        # Obtener años disponibles para el selector
        years_compras = Compra.objects.dates('fecha', 'year').values_list('fecha__year', flat=True)
        years_pagos = Pago.objects.dates('fecha', 'year').values_list('fecha__year', flat=True)
        available_years = sorted(set(list(years_compras) + list(years_pagos)), reverse=True)
        
        # Si no hay datos, usar el año actual
        if not available_years:
            available_years = [datetime.now().year]
        
        # Inicializar datos mensuales
        monthly_data = []
        total_ventas = Decimal('0.00')
        total_compras = Decimal('0.00')
        total_saldo = Decimal('0.00')
        
        # Calcular datos para cada mes
        for month_num in range(1, 13):
            # Obtener ventas del mes
            month_ventas = Pago.objects.filter(
                fecha__year=year, 
                fecha__month=month_num
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            # Obtener compras del mes
            month_compras = Compra.objects.filter(
                fecha__year=year, 
                fecha__month=month_num
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            # Calcular saldo
            month_saldo = month_ventas - month_compras
            
            # Actualizar totales
            total_ventas += month_ventas
            total_compras += month_compras
            total_saldo += month_saldo
            
            # Nombre del mes
            month_name = _(calendar.month_name[month_num])
            
            # Agregar a los datos mensuales
            monthly_data.append({
                'month_number': month_num,
                'month_name': month_name,
                'ventas': month_ventas,
                'compras': month_compras,
                'saldo': month_saldo,
                'css_class': 'table-success' if month_saldo > 0 else 'table-danger' if month_saldo < 0 else ''
            })
        
        context = {
            'year': year,
            'available_years': available_years,
            'monthly_data': monthly_data,
            'total_ventas': total_ventas,
            'total_compras': total_compras,
            'total_saldo': total_saldo,
            'css_class_total': 'text-success' if total_saldo > 0 else 'text-danger' if total_saldo < 0 else ''
        }
        
        return render(request, self.template_name, context)
    
################################TIPO DE COMPRA



class TipoCompraListView(LoginRequiredMixin, ListView):
    model = TipoCompra
    template_name = 'compras/tipocompra_lista.html'
    context_object_name = 'tipos_compra'
    paginate_by = 10
    
    def get_queryset(self):
        return TipoCompra.objects.all().order_by('categoria', 'nombre')

class TipoCompraCreateView(LoginRequiredMixin, CreateView):
    model = TipoCompra
    form_class = TipoCompraForm
    template_name = 'compras/tipocompra_crear.html'
    success_url = reverse_lazy('compras:tipodecompralista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de compra creado exitosamente.')
        return super().form_valid(form)

class TipoCompraUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoCompra
    form_class = TipoCompraForm
    template_name = 'compras/tipodecompra_editar.html'
    success_url = reverse_lazy('compras:tipodecompralista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de compra actualizado exitosamente.')
        return super().form_valid(form)

class TipoCompraDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoCompra
    template_name = 'compras/tipodecompra_eliminar.html'
    success_url = reverse_lazy('compras:tipodecompralista')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo de compra eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
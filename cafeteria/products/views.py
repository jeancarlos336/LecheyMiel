from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Producto, Categoria, AreaPreparacion,Stock, MovimientoStock
from .forms import ProductoForm, CategoriaForm, AreaPreparacionForm,StockForm, AgregarStockForm, MovimientoStockForm
from users.models import Rol
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse
from django.db import models



class EsAdministrador(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.rol and self.request.user.rol.nombre == Rol.ADMINISTRADOR

# Vistas para Productos
class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'products/producto_list.html'
    context_object_name = 'productos'
    
    def get_queryset(self):
        return Producto.objects.all().select_related('categoria')

class ProductoCreateView(LoginRequiredMixin, EsAdministrador, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'products/producto_form.html'
    success_url = reverse_lazy('products:producto_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Producto creado exitosamente.")
        return super().form_valid(form)

class ProductoUpdateView(LoginRequiredMixin, EsAdministrador, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'products/producto_form.html'
    success_url = reverse_lazy('products:producto_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Producto actualizado exitosamente.")
        return super().form_valid(form)


class ProductoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle para un Producto específico.
    Requiere autenticación.
    """
    model = Producto
    template_name = 'products/producto_detail.html'
    context_object_name = 'producto'

    def get_context_data(self, **kwargs):
        """
        Agrega información adicional al contexto si es necesario.
        """
        context = super().get_context_data(**kwargs)
        # Puedes agregar información adicional si lo requieres
        return context

class ProductoDeleteView(LoginRequiredMixin, EsAdministrador, DeleteView):
    model = Producto
    template_name = 'products/producto_confirm_delete.html'
    success_url = reverse_lazy('products:producto_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Producto eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para Categorías
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'products/categoria_list.html'
    context_object_name = 'categorias'

class CategoriaCreateView(LoginRequiredMixin, EsAdministrador, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'products/categoria_form.html'
    success_url = reverse_lazy('products:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría creada exitosamente.")
        return super().form_valid(form)

class CategoriaUpdateView(LoginRequiredMixin, EsAdministrador, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'products/categoria_form.html'
    success_url = reverse_lazy('products:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada exitosamente.")
        return super().form_valid(form)

class CategoriaDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle para una Categoría específica.
    Requiere autenticación.
    """
    model = Categoria
    template_name = 'products/categoria_detail.html'
    context_object_name = 'categoria'

    def get_context_data(self, **kwargs):
        """
        Incluye los productos de la categoría en el contexto.
        """
        context = super().get_context_data(**kwargs)
        context['productos'] = self.object.producto_set.select_related('categoria')
        return context   
    
class CategoriaDeleteView(LoginRequiredMixin, EsAdministrador, DeleteView):
    model = Categoria
    template_name = 'products/categoria_confirm_delete.html'
    success_url = reverse_lazy('products:categoria_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Categoría eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para Áreas de Preparación
class AreaPreparacionListView(LoginRequiredMixin, ListView):
    model = AreaPreparacion
    template_name = 'products/area_preparacion_list.html'
    context_object_name = 'areas'

class AreaPreparacionCreateView(LoginRequiredMixin, EsAdministrador, CreateView):
    model = AreaPreparacion
    form_class = AreaPreparacionForm
    template_name = 'products/area_preparacion_form.html'
    success_url = reverse_lazy('products:area_preparacion_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Área de preparación creada exitosamente.")
        return super().form_valid(form)

class AreaPreparacionUpdateView(LoginRequiredMixin, EsAdministrador, UpdateView):
    model = AreaPreparacion
    form_class = AreaPreparacionForm
    template_name = 'products/area_preparacion_form.html'
    success_url = reverse_lazy('products:area_preparacion_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Área de preparación actualizada exitosamente.")
        return super().form_valid(form)

class AreaPreparacionDeleteView(LoginRequiredMixin, EsAdministrador, DeleteView):
    model = AreaPreparacion
    template_name = 'products/area_preparacion_confirm_delete.html'
    success_url = reverse_lazy('products:area_preparacion_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Área de preparación eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)
    
class AreaPreparacionDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle para un Área de Preparación específica.
    Requiere autenticación.
    """
    model = AreaPreparacion
    template_name = 'products/area_preparacion_detail.html'
    context_object_name = 'area'

    def get_context_data(self, **kwargs):
        """
        Incluye las categorías del área de preparación en el contexto.
        """
        context = super().get_context_data(**kwargs)
        context['categorias'] = self.object.categoria_set.all()
        return context
    
################stock


@login_required
def stock_list(request):
    """Lista todos los productos y su stock"""
    search_query = request.GET.get('search', '')
    filter_stock = request.GET.get('filter', 'todos')
    
    stocks = Stock.objects.select_related('producto').all()
    
    # Filtrar por búsqueda
    if search_query:
        stocks = stocks.filter(
            Q(producto__nombre__icontains=search_query) |
            Q(producto__categoria__nombre__icontains=search_query)
        )
    
    if filter_stock == 'sin_stock':
        stocks = stocks.filter(cantidad_actual=0)
    elif filter_stock == 'stock_bajo':
        stocks = stocks.filter(
            cantidad_actual__isnull=False,
            stock_minimo__isnull=False,
            cantidad_actual__lte=F('stock_minimo')
        )
    elif filter_stock == 'stock_ok':
        stocks = stocks.filter(
            cantidad_actual__isnull=False,
            stock_minimo__isnull=False,
            cantidad_actual__gt=F('stock_minimo')
        )
    
    # Paginación
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Productos sin stock creado
    productos_sin_stock = Producto.objects.filter(stock__isnull=True).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_stock': filter_stock,
        'productos_sin_stock': productos_sin_stock,
    }
    return render(request, 'products/stock_list.html', context)

@login_required
def stock_edit(request, producto_id):
    """Editar stock de un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Crear stock si no existe
    stock, created = Stock.objects.get_or_create(
        producto=producto,
        defaults={'cantidad_actual': 0, 'stock_minimo': 5}
    )
    
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, f'Stock de {producto.nombre} actualizado correctamente.')
            return redirect('products:stock_list')
    else:
        form = StockForm(instance=stock)
    
    context = {
        'form': form,
        'producto': producto,
        'stock': stock,
    }
    return render(request, 'products/stock_edit.html', context)

@login_required
def stock_add(request, producto_id):
    """Agregar stock a un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Crear stock si no existe
    stock, created = Stock.objects.get_or_create(
        producto=producto,
        defaults={'cantidad_actual': 0, 'stock_minimo': 5}
    )
    
    if request.method == 'POST':
        form = AgregarStockForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            motivo = form.cleaned_data['motivo'] or 'Entrada manual de stock'
            
            stock.agregar_stock(cantidad, motivo)
            messages.success(request, f'Se agregaron {cantidad} unidades al stock de {producto.nombre}.')
            return redirect('products:stock_list')
    else:
        form = AgregarStockForm()
    
    context = {
        'form': form,
        'producto': producto,
        'stock': stock,
    }
    return render(request, 'products/stock_add.html', context)

@login_required
def stock_movimientos(request, producto_id):
    """Ver movimientos de stock de un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    movimientos = MovimientoStock.objects.filter(producto=producto).order_by('-fecha')
    
    # Paginación
    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'producto': producto,
        'page_obj': page_obj,
    }
    return render(request, 'products/stock_movimientos.html', context)

@login_required
def stock_alertas(request):
    """Mostrar productos con stock bajo o sin stock"""
    stocks_sin_stock = Stock.objects.filter(cantidad_actual=0).select_related('producto')
    stocks_bajo = Stock.objects.filter(
        cantidad_actual__gt=0,
        cantidad_actual__lte=models.F('stock_minimo')
    ).select_related('producto')
    
    context = {
        'stocks_sin_stock': stocks_sin_stock,
        'stocks_bajo': stocks_bajo,
    }
    return render(request, 'products/stock_alertas.html', context)

@login_required
def crear_stock_productos(request):
    """Crear registros de stock para productos que no los tienen"""
    if request.method == 'POST':
        productos_sin_stock = Producto.objects.filter(stock__isnull=True)
        count = 0
        
        for producto in productos_sin_stock:
            Stock.objects.create(
                producto=producto,
                cantidad_actual=0,
                stock_minimo=5
            )
            count += 1
        
        messages.success(request, f'Se crearon {count} registros de stock.')
        return redirect('products:stock_list')
    
    productos_sin_stock = Producto.objects.filter(stock__isnull=True).count()
    
    context = {
        'productos_sin_stock': productos_sin_stock,
    }
    return render(request, 'products/crear_stock.html', context)


@login_required
def stock_delete(request, producto_id):
    """Eliminar stock de un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    try:
        stock = Stock.objects.get(producto=producto)
    except Stock.DoesNotExist:
        messages.error(request, f'El producto {producto.nombre} no tiene stock registrado.')
        return redirect('products:stock_list')
    
    if request.method == 'POST':
        confirmar = request.POST.get('confirmar')
        if confirmar:
            # Opcional: Crear un registro de movimiento antes de eliminar
            MovimientoStock.objects.create(
                producto=producto,
                tipo='ajuste',
                cantidad=stock.cantidad_actual,
                motivo=f'Eliminación de stock - Cantidad eliminada: {stock.cantidad_actual}',
                usuario=request.user if hasattr(request.user, 'usuario') else None
            )
            
            # Eliminar el stock
            stock.delete()
            
            messages.success(
                request, 
                f'Stock de {producto.nombre} eliminado correctamente.'
            )
            return redirect('products:stock_list')
        else:
            messages.error(request, 'Debe confirmar la eliminación del stock.')
    
    context = {
        'producto': producto,
        'stock': stock,
    }
    return render(request, 'products/stock_eliminar.html', context)
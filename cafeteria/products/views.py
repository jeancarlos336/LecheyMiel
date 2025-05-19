from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Producto, Categoria, AreaPreparacion
from .forms import ProductoForm, CategoriaForm, AreaPreparacionForm
from users.models import Rol

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
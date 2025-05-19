from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # URLs para Productos
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_confirm_delete'),
    
    # URLs para Categorías
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_confirm_delete'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='Categoria_DetailView'),
    
    # URLs para Áreas de Preparación
    path('areas-preparacion/', views.AreaPreparacionListView.as_view(), name='area_preparacion_list'),
    path('areas-preparacion/crear/', views.AreaPreparacionCreateView.as_view(), name='area_preparacion_create'),
    path('areas-preparacion/<int:pk>/editar/', views.AreaPreparacionUpdateView.as_view(), name='area_preparacion_update'),
    path('areas-preparacion/<int:pk>/eliminar/', views.AreaPreparacionDeleteView.as_view(), name='area_preparacion_confirm_delete'),
    path('areas-preparacion/<int:pk>/', views.AreaPreparacionDetailView.as_view(), name='Area_Preparacion_DetailView'),
]
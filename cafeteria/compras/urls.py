# compras/urls.py
from django.urls import path
from . import views
from .views import BalanceAnualView


app_name = 'compras'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='compras_dashboard'),
    
    # Proveedores
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/', views.ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),
    
    # Compras
    path('compras/', views.CompraListView.as_view(), name='compra_list'),
    path('compras/nueva/', views.CompraCreateView.as_view(), name='compra_create'),
    path('compras/<int:pk>/', views.CompraDetailView.as_view(), name='compra_detail'),
    path('compras/<int:pk>/editar/', views.CompraUpdateView.as_view(), name='compra_update'),
    path('compras/<int:pk>/eliminar/', views.CompraDeleteView.as_view(), name='compra_delete'),
    
    
    #TIPO DE COMPRAS
    path('tipodecompra', views.TipoCompraListView.as_view(), name='tipodecompralista'),
    path('crear/', views.TipoCompraCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', views.TipoCompraUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', views.TipoCompraDeleteView.as_view(), name='eliminar'),
    
    
    #reportes
    path('reportes/balance-anual/', BalanceAnualView.as_view(), name='balance_anual'),
    path('informe/', views.informe_compras, name='informe_compras'),
]
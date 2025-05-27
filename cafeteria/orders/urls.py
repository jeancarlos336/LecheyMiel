from django.urls import path
from . import views
from .views import (
    VentaExpressView, 
    CrearPedidoExpressView,
    ReciboVentaExpressView,
    BuscarProductoExpressView,
    GetTodasCategoriasView
)

app_name = 'orders'

urlpatterns = [
    # Rutas para Pedidos
    path('tomar-pedido/<int:mesa_id>/', views.tomar_pedido, name='tomar_pedido'),
    path('pedidos/', views.lista_pedidos_pendientes, name='lista_pedidos_pendientes'),
    path('detalle-pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    

    path('pedido/<int:pedido_id>/procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('pedido/<int:pedido_id>/completar-pago/', views.completar_pago, name='completar_pago'),
    path('pago/<int:pago_id>/recibo/', views.imprimir_recibo, name='imprimir_recibo'), 
    path('pedido/<int:pedido_id>/recibo/', views.imprimir_recibo_pedido, name='imprimir_recibo_pedido'), 
    path('pagos-pendientes/', views.listar_pagos_pendientes, name='pagos_pendientes'),
    path('pagos-pendientes/<int:pago_pendiente_id>/marcar-pagado/', views.marcar_pago_como_pagado, name='marcar_pago_pagado'),
    path('pagos-pendientes/historial/', views.historial_pagos_pendientes, name='historial_pagos_pendientes'),       
    
    path('seleccionar-tipo-orden/', views.seleccionar_tipo_orden, name='seleccionar_tipo_orden'),
    path('crear-pedido-para-llevar/<int:tipo_orden_id>/', views.crear_pedido_para_llevar, name='crear_pedido_para_llevar'),
    path('tomar-pedido-para-llevar/<int:tipo_orden_id>/<int:pedido_id>/', views.tomar_pedido_para_llevar, name='tomar_pedido_para_llevar'),
    

    
    path('todos-pedidos/', views.todos_los_pedidos, name='todos_los_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),
    
    path('seleccionar-mesa/', views.seleccionar_mesa, name='seleccionar_mesa'),
    
    # Rutas para Mesas
    path('mesas/', views.lista_mesas, name='lista_mesas'), 
    path('mesas/<int:mesa_id>/', views.detalle_mesa, name='detalle_mesa'),
    path('mesas/crear/', views.crear_mesa, name='crear_mesa'),  
    path('mesas/editar/<int:mesa_id>/', views.editar_mesa, name='editar_mesa'),
    path('mesas/eliminar/<int:mesa_id>/', views.eliminar_mesa, name='eliminar_mesa'),
    path('mesas/cambiar_estado/<int:mesa_id>/', views.cambiar_estado_mesa, name='cambiar_estado_mesa'),
    
    
    path('preparacion/', views.pedidos_preparacion, name='pedidos_preparacion'),
    path('actualizar-estado/', views.actualizar_estado_item, name='actualizar_estado_item'),
    
    
    #informes
    path('informe-ventas/', views.informe_ventas, name='informe_ventas'),
    
    
    path('venta-express/', VentaExpressView.as_view(), name='venta_express'), 
    path('venta-express/crear-pedido/', CrearPedidoExpressView.as_view(), name='crear_pedido_express'),
    path('venta-express/recibo/<int:pedido_id>/', ReciboVentaExpressView.as_view(), name='recibo_venta_express'),
    path('buscar-producto-express/', BuscarProductoExpressView.as_view(), name='buscar_producto_express'),
    path('get-todas-categorias/', GetTodasCategoriasView.as_view(), name='get_todas_categorias'),
    
    path('pedido/<int:pedido_id>/recibo-cocina/', views.recibo_cocina,name='recibo_cocina'),   
    path('pedido/<int:pedido_id>/imprimir-cocina/', views.imprimir_recibo_cocina,name='imprimir_recibo_cocina'),

]

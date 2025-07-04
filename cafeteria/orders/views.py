from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import PedidoForm, DetallePedidoForm,SeleccionMesaForm,MesaForm
from products.forms import CategoriaForm,ProductoForm
from orders.models import Pedido,Mesa,DetallePedido,Pago,PagoPendiente,TipoOrden
from products.models import Producto,Categoria,AreaPreparacion
from users.models import Usuario,Rol
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView,View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from datetime import datetime,date,timedelta
from django.db.models import Q,Sum,Count
import json
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import socket
import logging
from django.urls import reverse
from django.db.models.functions import TruncMonth
import calendar

#trabajo con las mesas
@login_required
def lista_mesas(request):
    """Vista para mostrar la lista de todas las mesas"""
    mesas = Mesa.objects.all().order_by('numero')
    
    # Contadores para el resumen
    disponibles = mesas.filter(estado='disponible').count()
    ocupadas = mesas.filter(estado='ocupada').count()
    reservadas = mesas.filter(estado='reservada').count()
    
    context = {
        'mesas': mesas,
        'disponibles': disponibles,
        'ocupadas': ocupadas,
        'reservadas': reservadas,
        'total': mesas.count()
    }
    return render(request, 'orders/mesas/lista_mesas.html', context)

@login_required
def detalle_mesa(request, mesa_id):
    """Vista para mostrar los detalles de una mesa específica"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    return render(request, 'orders/mesas/detalle_mesa.html', {'mesa': mesa})

@login_required
def crear_mesa(request):
    """Vista para crear una nueva mesa"""
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mesa creada correctamente')
            return redirect('orders:lista_mesas')
    else:
        form = MesaForm()
    
    return render(request, 'orders/mesas/form_mesa.html', {'form': form, 'accion': 'Crear'})

@login_required
def editar_mesa(request, mesa_id):
    """Vista para editar una mesa existente"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Mesa {mesa.numero} actualizada correctamente')
            return redirect('orders:lista_mesas')
    else:
        form = MesaForm(instance=mesa)
    
    return render(request, 'orders/mesas/form_mesa.html', {'form': form, 'mesa': mesa, 'accion': 'Editar'})

@login_required
def eliminar_mesa(request, mesa_id):
    """Vista para eliminar una mesa"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        mesa_num = mesa.numero
        mesa.delete()
        messages.success(request, f'Mesa {mesa_num} eliminada correctamente')
        return redirect('orders:lista_mesas')
    
    return render(request, 'orders/mesas/confirmar_eliminar_mesa.html', {'mesa': mesa})

@login_required
def cambiar_estado_mesa(request, mesa_id):
    """Vista para cambiar rápidamente el estado de una mesa"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in [choice[0] for choice in Mesa.ESTADO_CHOICES]:
            mesa.estado = nuevo_estado
            mesa.save()
            messages.success(request, f'Estado de la mesa {mesa.numero} actualizado a {dict(Mesa.ESTADO_CHOICES)[nuevo_estado]}')
        else:
            messages.error(request, 'Estado no válido')
        
        return redirect('orders:lista_mesas')
    
    return render(request, 'orders/mesas/cambiar_estado_mesa.html', {'mesa': mesa})

#pedidos
@login_required
def tomar_pedido(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    # Obtener el tipo de orden LOCAL
    try:
        tipo_orden_local = TipoOrden.objects.get(codigo='LOCAL')
    except TipoOrden.DoesNotExist:
        messages.error(request, "Error: No existe el tipo de orden LOCAL")
        return redirect('orders:seleccionar_mesa')
   
    # Permitir acceso si la mesa está disponible O si ya tiene un pedido pendiente/en preparación
    pedido_existente = Pedido.objects.filter(
        mesa=mesa,
        estado__in=['pendiente', 'en_preparacion']
    ).first()
    
    # Solo verificar disponibilidad si no hay un pedido en curso
    if not pedido_existente and not mesa.esta_disponible and mesa.estado != 'reservada':
        messages.error(request, f"La Mesa {mesa.numero} no está disponible actualmente")
        return redirect('orders:seleccionar_mesa')
    
    try:
        mesero = Usuario.objects.get(username=request.user.username)
    except Usuario.DoesNotExist:
        messages.error(request, "No tienes permisos para tomar pedidos.")
        return redirect('home')

    # Obtener categorías y productos disponibles
    categorias = Categoria.objects.all()
    productos_por_categoria = {
        categoria: Producto.objects.filter(categoria=categoria, esta_disponible=True)
        for categoria in categorias
    }

    if request.method == 'POST':
        with transaction.atomic():
            # Si no hay pedido existente, crear uno nuevo
            if not pedido_existente:
                # Cambiar estado de la mesa a OCUPADA
                mesa.estado = 'ocupada'
                mesa.save()
                
                pedido = Pedido.objects.create(
                    mesa=mesa,
                    mesero=mesero,
                    tipo_orden=tipo_orden_local,
                    estado='pendiente',
                    monto_total=0,
                    estado_pago='pendiente',
                    numero_comensales=request.POST.get('numero_comensales', 1)
                )
                pedido_existente = pedido

            action = request.POST.get('action')
            
            if action == 'add_producto':
                # Procesar detalle del pedido
                producto_id = request.POST.get('producto_id')
                cantidad = int(request.POST.get('cantidad', 1))
                notas = request.POST.get('notas', '')
                producto = get_object_or_404(Producto, id=producto_id)

                # VERIFICAR STOCK ANTES DE PROCEDER
                try:
                    stock_producto = getattr(producto, 'stock', None)
                    if stock_producto and not stock_producto.puede_vender(cantidad):
                        error_msg = f"Stock insuficiente para {producto.nombre}. Stock disponible: {stock_producto.cantidad_actual}"
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': error_msg
                            }, status=400)
                        
                        messages.error(request, error_msg)
                        return redirect('orders:tomar_pedido', mesa_id=mesa.id)

                    # Verificar si el producto ya existe en el pedido
                    detalle_existente = DetallePedido.objects.filter(
                        pedido=pedido_existente,
                        producto=producto,
                        notas=notas,
                        estado='pendiente'
                    ).first()

                    if detalle_existente:
                        # Verificar stock para la nueva cantidad total
                        nueva_cantidad_total = detalle_existente.cantidad + cantidad
                        if stock_producto and not stock_producto.puede_vender(cantidad):
                            error_msg = f"Stock insuficiente para {producto.nombre}. Stock disponible: {stock_producto.cantidad_actual}"
                            
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'success': False,
                                    'error': error_msg
                                }, status=400)
                            
                            messages.error(request, error_msg)
                            return redirect('orders:tomar_pedido', mesa_id=mesa.id)
                        
                        # Si ya existe, actualizar la cantidad
                        detalle_existente.cantidad += cantidad
                        detalle_existente.save()
                        nuevo_detalle = detalle_existente
                    else:
                        # Si no existe, crear nuevo detalle
                        nuevo_detalle = DetallePedido.objects.create(
                            pedido=pedido_existente,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=producto.precio,
                            notas=notas,
                            estado='pendiente'
                        )

                    # NUEVA LÓGICA: Si el producto NO es de cocina, marcarlo automáticamente como entregado
                    if producto.categoria.area_preparacion.nombre != AreaPreparacion.COCINA:
                        nuevo_detalle.estado = 'entregado'
                        nuevo_detalle.hora_listo = timezone.now()
                        nuevo_detalle.hora_entrega = timezone.now()
                        nuevo_detalle.save()

                    pedido_existente.calcular_total()
                    
                    mensaje_estado = ""
                    if producto.categoria.area_preparacion.nombre == AreaPreparacion.COCINA:
                        mensaje_estado = "agregado al pedido (requiere preparación en cocina)"
                    else:
                        mensaje_estado = "agregado y marcado como entregado automáticamente"
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Producto {producto.nombre} {mensaje_estado}.',
                            'es_cocina': producto.categoria.area_preparacion.nombre == AreaPreparacion.COCINA
                        })
                    messages.success(request, f'Producto {producto.nombre} {mensaje_estado}.')
                    return redirect('orders:tomar_pedido', mesa_id=mesa.id)

                except ValueError as e:
                    # Capturar cualquier error de stock que pueda escapar
                    error_msg = str(e)
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        }, status=400)
                    
                    messages.error(request, error_msg)
                    return redirect('orders:tomar_pedido', mesa_id=mesa.id)
                
                except Exception as e:
                    # Capturar cualquier otro error inesperado
                    error_msg = f"Error al agregar el producto: {str(e)}"
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        }, status=500)
                    
                    messages.error(request, error_msg)
                    return redirect('orders:tomar_pedido', mesa_id=mesa.id)
                    
            elif action == 'remove_producto':
                detalle_id = request.POST.get('detalle_id')
                try:
                    detalle = DetallePedido.objects.get(
                        id=detalle_id,
                        pedido=pedido_existente
                    )
                    producto_nombre = detalle.producto.nombre
                    detalle.delete()
                    pedido_existente.calcular_total()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Producto {producto_nombre} eliminado del pedido.'
                        })
                    messages.success(request, f'Producto {producto_nombre} eliminado del pedido.')
                except DetallePedido.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'No se encontró el detalle del pedido'
                        }, status=404)
                    messages.error(request, 'No se encontró el detalle del pedido')
                
                return redirect('orders:tomar_pedido', mesa_id=mesa.id)
            
            elif 'action' in request.POST and request.POST['action'] == 'actualizar_cliente':
                if pedido_existente:
                    pedido_existente.nombre_cliente = request.POST.get('nombre_cliente', '')
                    pedido_existente.save()
                    return HttpResponse(status=200)
            
            elif action == 'update_note':
                detalle_id = request.POST.get('detalle_id')
                notas = request.POST.get('notas', '')
                try:
                    detalle = DetallePedido.objects.get(
                        id=detalle_id,
                        pedido=pedido_existente
                    )
                    detalle.notas = notas
                    detalle.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'Nota actualizada correctamente.'
                        })
                    messages.success(request, 'Nota actualizada correctamente.')
                except DetallePedido.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'No se encontró el detalle del pedido'
                        }, status=404)
                    messages.error(request, 'No se encontró el detalle del pedido')
                
                return redirect('orders:tomar_pedido', mesa_id=mesa.id)
            
            elif action == 'update_cantidad':
                detalle_id = request.POST.get('detalle_id')
                cantidad = int(request.POST.get('cantidad', 1))
                try:
                    detalle = DetallePedido.objects.get(
                        id=detalle_id,
                        pedido=pedido_existente
                    )
                    
                    # Verificar stock antes de actualizar cantidad
                    producto = detalle.producto
                    stock_producto = getattr(producto, 'stock', None)
                    
                    if stock_producto:
                        cantidad_actual = detalle.cantidad
                        diferencia = cantidad - cantidad_actual
                        
                        if diferencia > 0:  # Aumentar cantidad
                            if not stock_producto.puede_vender(diferencia):
                                return JsonResponse({
                                    'success': False,
                                    'error': f'Stock insuficiente para {producto.nombre}. Stock disponible: {stock_producto.cantidad_actual}'
                                }, status=400)
                    
                    detalle.cantidad = cantidad
                    detalle.save()
                    pedido_existente.calcular_total()
                    
                    return JsonResponse({
                        'success': True,
                        'subtotal': detalle.subtotal,
                        'total': pedido_existente.monto_total
                    })
                    
                except DetallePedido.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se encontró el detalle del pedido'
                    }, status=404)
                except ValueError as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=400)

    # Manejar parámetro de categoría activa
    categoria_activa = request.GET.get('categoria')
    if not categoria_activa and categorias.exists():
        categoria_activa = categorias.first().id

    # Recalcular total por si hubo cambios
    if pedido_existente:
        pedido_existente.calcular_total()
        total_pedido = pedido_existente.monto_total
    else:
        total_pedido = 0

    context = {
        'mesa': mesa,
        'pedido_existente': pedido_existente,
        'categorias': categorias,
        'productos_por_categoria': productos_por_categoria,
        'total_pedido': total_pedido,
        'tipo_orden': tipo_orden_local,
        'categoria_activa': int(categoria_activa) if categoria_activa else None
    }
    
    return render(request, 'orders/pedidos/tomar_pedido.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    """
    View to show and modify order details
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        # Handle actions like removing items or changing quantities
        action = request.POST.get('action')
        if action == 'eliminar_item':
            detalle_id = request.POST.get('detalle_id')
            detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
            detalle.delete()

            # Recalculate total
            pedido.monto_total = sum(
                detalle.cantidad * detalle.precio_unitario 
                for detalle in pedido.detalles.all()
            )
            pedido.save()

    return render(request, 'orders/detalle_pedido.html', {'pedido': pedido})

@login_required
def seleccionar_mesa(request):
    mesas = Mesa.objects.all().order_by('numero')
    
    # Configuración automática de posiciones basada en una cuadrícula
    mesas_por_fila = 5  # Número de mesas por fila
    espaciado_x = 15    # Espacio horizontal entre mesas (%)
    espaciado_y = 15    # Espacio vertical entre mesas (%)
    inicio_x = 10       # Margen izquierdo inicial (%)
    inicio_y = 20       # Margen superior inicial (%)
    
    mesa_positions = {}
    for i, mesa in enumerate(mesas):
        fila = i // mesas_por_fila
        columna = i % mesas_por_fila
        mesa_positions[mesa.numero] = {
            'x': inicio_x + columna * espaciado_x,
            'y': inicio_y + fila * espaciado_y
        }
    
    context = {
        'mesas': mesas,
        'mesa_positions': mesa_positions
    }
    
    return render(request, 'orders/pedidos/seleccionar_mesa.html', context)

@login_required
def cambiar_estado_pedido(request, pedido_id):
    """
    View to change order or order detail status
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        detalle_id = request.POST.get('detalle_id')
        
        if detalle_id:
            # Change status of a specific order detail
            detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
            detalle.estado = nuevo_estado
            detalle.save()
        else:
            # Change status of entire order
            pedido.estado = nuevo_estado
            pedido.save()
            
            # Optionally update all order details
            if nuevo_estado:
                pedido.detalles.update(estado=nuevo_estado)
        
        return redirect('lista_pedidos')
    
    return render(request, 'orders/cambiar_estado_pedido.html', {'pedido': pedido})

@login_required
def lista_pedidos_pendientes(request):
       
    query = request.GET.get('q', '')    
    pedidos = Pedido.objects.filter(estado_pago='pendiente').order_by('-fecha_creacion')
    
    if query:
        pedidos = pedidos.filter(
            Q(id__icontains=query) |
            Q(mesa__numero__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(numero_orden__icontains=query)
        )
        
    # Preparar detalles por área para cada pedido
    for pedido in pedidos:
        pedido.detalles_por_area = {}
        for detalle in pedido.detalles.all():
            area = detalle.area_preparacion
            if area not in pedido.detalles_por_area:
                pedido.detalles_por_area[area] = []
            pedido.detalles_por_area[area].append(detalle)
        
        # Verificar si todos los productos están listos para cerrar el pedido
        pedido.puede_cerrarse = True  # Comenzamos asumiendo que se puede cerrar
        for detalle in pedido.detalles.all():
            # Si hay algún producto pendiente o en preparación, no se puede cerrar
            if detalle.estado in ['pendiente', 'en_preparacion']:
                pedido.puede_cerrarse = False
                break
    
    context = {
        'pedidos': pedidos
    }
    return render(request, 'orders/pedidos/lista_pedidos_pendientes.html', context)



@login_required
def todos_los_pedidos(request):
    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    mesa_filtro = request.GET.get('mesa', '')
    
    # Comenzar con todos los pedidos
    pedidos = Pedido.objects.all()
    
    # Aplicar filtro de búsqueda general
    if query:
        pedidos = pedidos.filter(
            Q(id__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(mesa__numero__icontains=query)
        )
    
    
    # Filtro por mesa
    if mesa_filtro:
        pedidos = pedidos.filter(mesa__numero=mesa_filtro)
    
    # Filtros de fecha
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            pedidos = pedidos.filter(fecha_creacion__date__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            pedidos = pedidos.filter(fecha_creacion__date__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Ordenar de más reciente a más antiguo
    pedidos = pedidos.order_by('-fecha_creacion')
    
    
    # Obtener mesas únicas para el filtro
    mesas_disponibles = Pedido.objects.values_list('mesa__numero', flat=True).distinct().order_by('mesa__numero')
    
    context = {
        'pedidos': pedidos,
        'query': query,        
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,        
        'mesas_disponibles': mesas_disponibles,
        'total_resultados': pedidos.count(),
    }
    return render(request, 'orders/pedidos/todos_pedidos.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'orders/pedidos/detalle_pedido.html', {'pedido': pedido})


@login_required
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Si el método es POST, procesar la eliminación
    if request.method == 'POST':
        # Solo permitir eliminar pedidos pendientes o cancelados
        if pedido.estado_pago in ['pendiente', 'cancelado']:
            # Guardar información para el mensaje
            if pedido.mesa:
                pedido_info = f"Pedido #{pedido.id} de la Mesa {pedido.mesa.numero}"
                
                # Liberar la mesa marcándola como disponible
                mesa = pedido.mesa
                mesa.estado = 'disponible'
                mesa.save()
            else:
                # Para pedidos sin mesa (para llevar, a domicilio, etc.)
                tipo_orden_nombre = pedido.tipo_orden.nombre
                cliente_info = pedido.nombre_cliente or pedido.numero_orden or "Sin información"
                pedido_info = f"Pedido #{pedido.id} - {tipo_orden_nombre} ({cliente_info})"
            
            # Eliminar el pedido
            pedido.delete()
            
            # Añadir mensaje de éxito
            messages.success(request, f"{pedido_info} ha sido eliminado correctamente.")
            return redirect('orders:todos_los_pedidos')
        else:
            # Añadir mensaje de error
            messages.error(request, f"No se puede eliminar el Pedido #{pedido.id} porque su estado de pago es '{pedido.get_estado_pago_display()}'.")
            return render(request, 'orders/pedidos/error_eliminar_pedido.html', {'pedido': pedido})
    
    # Si el método es GET, mostrar página de confirmación
    return render(request, 'orders/pedidos/confirmar_eliminar_pedido.html', {'pedido': pedido})

@login_required
def imprimir_recibo(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    
    # Verificar que el pago esté completado
    if pago.pedido.estado_pago != 'pagado':
        messages.error(request, f"No se puede imprimir el recibo porque el pedido tiene estado {pago.pedido.estado_pago}. Solo se pueden imprimir recibos de pagos completados.")
        # Redirigir a una página de error o a la lista de pagos
        return redirect('orders:seleccionar_tipo_orden')
    
    # Si el pago está completado, continuar con la impresión
    # Filtrar solo los detalles activos
    detalles_activos = pago.pedido.detalles.exclude(estado='cancelado')
   
    # Calcular el total correcto basado solo en detalles activos
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    cambio_correcto = pago.monto_recibido - total_correcto if pago.monto_recibido else 0
   
    return render(request, 'orders/pedidos/imprimir_recibo.html', {
        'pago': pago,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto,
        'cambio_correcto': cambio_correcto
    })
    

@login_required
def imprimir_recibo_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    pagos = Pago.objects.filter(pedido=pedido)

    if not pagos.exists():
        messages.error(request, f"No se puede imprimir el recibo para el Pedido #{pedido.id} porque no tiene un pago asociado.")
        return redirect('orders:detalle_pedido', pedido_id=pedido.id)

    if pagos.count() > 1:
        messages.error(request, f"Hay múltiples pagos asociados al Pedido #{pedido.id}. No se puede generar el recibo hasta resolver esta inconsistencia.")
        return redirect('orders:detalle_pedido', pedido_id=pedido.id)

    pago = pagos.first()

    if pedido.estado_pago != 'pagado':
        messages.error(request, f"No se puede imprimir el recibo para el Pedido #{pedido.id} Solo se pueden imprimir recibos de pagos completados.")
        return redirect('orders:detalle_pedido', pedido_id=pedido.id)

    detalles_activos = pedido.detalles.exclude(estado='cancelado')
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    cambio_correcto = pago.monto_recibido - total_correcto if pago.monto_recibido else 0

    return render(request, 'orders/pedidos/imprimir_recibo.html', {
        'pago': pago,
        'pedido': pedido,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto,
        'cambio_correcto': cambio_correcto
    })
    
@login_required
def boleta(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Filtrar solo los detalles activos
    detalles_activos = pedido.detalles.exclude(estado='cancelado')
    
    # Calcular el total correcto basado solo en detalles activos
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    
    return render(request, 'orders/pedidos/boleta.html', {
        'pedido': pedido,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto
    })
    
@login_required
def pedidos_preparacion(request):
    # Determinar el área del usuario actual
    user = request.user
    
    if not hasattr(user, 'rol'):
        messages.error(request, "Tu usuario no tiene un rol asignado.")
        return redirect('dashboard')
    
    try:
        # Permitir acceso a cocina, bar, barra o administrador
        if user.rol.nombre == Rol.COCINA:
            area_nombre = AreaPreparacion.COCINA
            template = 'orders/pedidos/pedidos_cocina.html'
        elif user.rol.nombre == Rol.BAR:
            area_nombre = AreaPreparacion.BAR
            template = 'orders/pedidos/pedidos_bar.html'
        elif user.rol.nombre == Rol.BARRA:
            area_nombre = AreaPreparacion.BARRA
            template = 'orders/pedidos/pedidos_barra.html'
        elif user.rol.nombre == Rol.ADMINISTRADOR:
            # Para administrador, podemos mostrar todas las áreas o elegir una por defecto
            area_nombre = request.GET.get('area', AreaPreparacion.COCINA)
            
            # Validar que el área solicitada sea válida
            if area_nombre not in [AreaPreparacion.COCINA, AreaPreparacion.BAR, AreaPreparacion.BARRA]:
                area_nombre = AreaPreparacion.COCINA
            
            # Elegir la plantilla correspondiente
            if area_nombre == AreaPreparacion.COCINA:
                template = 'orders/pedidos/pedidos_cocina.html'
            elif area_nombre == AreaPreparacion.BAR:
                template = 'orders/pedidos/pedidos_bar.html'
            else:
                template = 'orders/pedidos/pedidos_barra.html'
        else:
            # Cualquier otro rol no tiene permiso
            messages.error(request, "No tienes autorización para acceder a esta sección.")
            return redirect('dashboard')
        
        # LÓGICA DIFERENTE según el área
        if area_nombre == AreaPreparacion.COCINA:
            # COCINA: Mostrar solo productos pendientes y en preparación (flujo normal)
            estados_a_mostrar = ['pendiente', 'en_preparacion']
        else:
            # BAR Y BARRA: Mostrar solo productos pendientes y en preparación 
            # (los productos se entregan automáticamente, pero pueden verse mientras se preparan)
            estados_a_mostrar = ['pendiente', 'en_preparacion']
        
        # Obtener pedidos con items en los estados correspondientes para esta área
        pedidos = Pedido.objects.filter(
            Q(detalles__producto__categoria__area_preparacion__nombre=area_nombre) &
            Q(detalles__estado__in=estados_a_mostrar)
        ).distinct().order_by('fecha_creacion')
        
        # Organizar los detalles por pedido y área
        pedidos_con_detalles = []
        for pedido in pedidos:
            detalles = pedido.detalles.filter(
                producto__categoria__area_preparacion__nombre=area_nombre,
                estado__in=estados_a_mostrar
            ).order_by('estado', 'hora_solicitud')
            
            if detalles.exists():
                pedidos_con_detalles.append({
                    'pedido': pedido,
                    'detalles': detalles
                })
        
        context = {
            'pedidos': pedidos_con_detalles,
            'area': AreaPreparacion.objects.get(nombre=area_nombre),
            'es_cocina': area_nombre == AreaPreparacion.COCINA
        }
        
        # Si es administrador, agregar opciones para cambiar de área
        if user.rol.nombre == Rol.ADMINISTRADOR:
            context['es_admin'] = True
            context['area_actual'] = area_nombre
        
        return render(request, template, context)
    
    except AreaPreparacion.DoesNotExist:
        messages.error(request, "El área de preparación no existe.")
        return redirect('dashboard')

@require_POST
@login_required
def actualizar_estado_item(request):
    try:
        # Manejar tanto JSON como form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        item_id = data.get('item_id')
        nuevo_estado = data.get('estado')
        
        if not item_id or not nuevo_estado:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        item = DetallePedido.objects.get(pk=item_id)
        
        # Verificar permisos
        user = request.user
        area_item = item.producto.categoria.area_preparacion
        
        # SOLO permitir que cada área modifique sus propios productos
        if (user.rol.nombre == Rol.COCINA and area_item.nombre != AreaPreparacion.COCINA) or \
           (user.rol.nombre == Rol.BAR and area_item.nombre != AreaPreparacion.BAR) or \
           (user.rol.nombre == Rol.BARRA and area_item.nombre != AreaPreparacion.BARRA):
            return JsonResponse({'error': 'No tienes permiso para modificar este ítem'}, status=403)
        
        # LÓGICA PRINCIPAL: Solo cocina requiere validación manual
        if area_item.nombre == AreaPreparacion.COCINA:
            # COCINA: Proceso manual completo
            item.estado = nuevo_estado
            item.preparado_por = user
            
            # Actualizar timestamps según el estado
            if nuevo_estado == 'en_preparacion':
                item.hora_preparacion = timezone.now()
            elif nuevo_estado == 'listo':
                item.hora_listo = timezone.now()
            elif nuevo_estado == 'entregado':
                item.hora_entrega = timezone.now()
                
        else:
            # BAR Y BARRA: Solo pueden cambiar a "en_preparacion", luego se entrega automáticamente
            if nuevo_estado == 'en_preparacion':
                item.estado = 'en_preparacion'
                item.hora_preparacion = timezone.now()
                item.preparado_por = user
            elif nuevo_estado == 'listo':
                # Cuando marcan como listo, automáticamente se marca como entregado
                item.estado = 'entregado'
                item.hora_listo = timezone.now()
                item.hora_entrega = timezone.now()
                item.preparado_por = user
            elif nuevo_estado == 'cancelado':
                item.estado = 'cancelado'
                item.preparado_por = user
            else:
                # No permitir otros estados para bar/barra
                return JsonResponse({'error': 'Estado no válido para esta área'}, status=400)
        
        item.save()
        
        # Verificar si todo el pedido está listo/entregado para actualizar estado del pedido
        pedido = item.pedido
        todos_listos_o_entregados = all(
            detalle.estado in ['listo', 'entregado', 'cancelado'] 
            for detalle in pedido.detalles.all()
        )
        
        if todos_listos_o_entregados and pedido.estado != 'listo':
            pedido.estado = 'listo'
            pedido.save()
        
        return JsonResponse({
            'success': True,
            'nuevo_estado': item.get_estado_display(),
            'estado_real': item.estado,
            'area': area_item.nombre,
            'es_automatico': area_item.nombre != AreaPreparacion.COCINA
        })
        
    except DetallePedido.DoesNotExist:
        return JsonResponse({'error': 'Ítem no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def auto_entregar_productos_no_cocina(pedido):
    """
    Marca automáticamente como entregados los productos que no son de cocina
    """
    detalles_no_cocina = pedido.detalles.filter(
        ~Q(producto__categoria__area_preparacion__nombre=AreaPreparacion.COCINA),
        estado='pendiente'
    )
    
    for detalle in detalles_no_cocina:
        detalle.estado = 'entregado'
        detalle.hora_listo = timezone.now()
        detalle.hora_entrega = timezone.now()
        # No asignar preparado_por ya que es automático
        detalle.save()
        
        
#informes
def informe_ventas(request):
    # Valores predeterminados
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    metodo_pago = request.GET.get('metodo_pago', '')
    
    # Preparar consulta base
    pagos = Pago.objects.all()
    
    # Aplicar filtros si están presentes
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            pagos = pagos.filter(fecha__gte=fecha_inicio_obj)
        except ValueError:
            fecha_inicio = ''
    
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
            pagos = pagos.filter(fecha__lt=fecha_fin_obj)
        except ValueError:
            fecha_fin = ''
    
    if metodo_pago:
        pagos = pagos.filter(metodo=metodo_pago)
    
    # Calcular totales
    total_ventas = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Agrupar por método de pago
    resumen_por_metodo = {}
    for metodo, nombre in Pago.METODOS_PAGO:
        monto = pagos.filter(metodo=metodo).aggregate(total=Sum('monto'))['total'] or 0
        resumen_por_metodo[nombre] = monto
    
    # Obtener pagos para mostrar en la tabla
    lista_pagos = pagos.select_related('pedido').order_by('-pedido_id')
    
    context = {
        'pagos': lista_pagos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'metodo_pago': metodo_pago,
        'total_ventas': total_ventas,
        'resumen_por_metodo': resumen_por_metodo,
        'metodos_pago': Pago.METODOS_PAGO,
    }
    
    return render(request, 'orders/pedidos/informe_ventas.html', context)

#----------------------------

@login_required
def completar_pago(request, pedido_id):
    """
    Procesa el pago y actualiza el estado del pedido
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)    
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        imprimir_recibo = request.POST.get('imprimir_recibo') == 'on'
        
        # Usar monto_total en lugar de total
        pago = Pago(
            pedido=pedido,
            monto=pedido.monto_total,
            metodo=metodo_pago
        )
        
        if metodo_pago == 'efectivo':
            monto_recibido = float(request.POST.get('monto_recibido', 0))
            cambio = monto_recibido - float(pedido.monto_total)
            
            pago.monto_recibido = monto_recibido
            pago.cambio = cambio
            pago.notas = f"Pago en efectivo. Monto recibido: ${monto_recibido}, Cambio: ${cambio}"
        elif metodo_pago == 'tarjeta':
            # Simplemente registrar que se pagó con tarjeta usando POS externo
            pago.notas = "Pago con tarjeta usando terminal POS externa"
        elif metodo_pago == 'pendiente':
            # Guardar el pago básico primero
            pago.notas = "Pago pendiente"
            pago.save()
            
            # Crear registro en PagoPendiente
            cliente_nombre = request.POST.get('cliente_nombre', '')
            fecha_promesa = request.POST.get('fecha_promesa', '')
            notas_adicionales = request.POST.get('notas_adicionales', '')
            
            PagoPendiente.objects.create(
                pago=pago,
                cliente_nombre=cliente_nombre,
                fecha_promesa=fecha_promesa,
                notas_adicionales=notas_adicionales
            )
            
            # No necesitamos continuar con el save de pago aquí ya que ya lo hemos guardado
            # Actualizar estado del pedido
            
            pedido.estado_pago = 'impago'
            pedido.estado = 'completado'
            pedido.save()
            
            # Liberar la mesa marcándola como disponible
            mesa = pedido.mesa
            if mesa and pedido.tipo_orden.codigo == 'LOCAL':
                mesa.estado = 'disponible'
                mesa.save()
                messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente. '
                                    f'La mesa {mesa.numero} está disponible.')
            else:
                messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente.')
        
            if imprimir_recibo:
                return redirect('orders:imprimir_recibo', pago_id=pago.id)
            
            return redirect('orders:todos_los_pedidos')
        
        # Si no es pendiente, seguimos con el flujo normal para efectivo y tarjeta
        pedido.estado = 'completado'
        pago.save()
        
        # Actualizar estado del pedido
        pedido.estado_pago = 'pagado'
        pedido.save()
        
        # Liberar la mesa marcándola como disponible
        mesa = pedido.mesa    
        if mesa and pedido.tipo_orden.codigo == 'LOCAL':    
            mesa.estado = 'disponible'
            mesa.save()
            messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente. '
                                f'La mesa {mesa.numero} está disponible.')
        else:
            messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente.')
        
        # Siempre imprimir recibo si está marcado
        if imprimir_recibo:
            return redirect('orders:imprimir_recibo', pago_id=pago.id)
        
        return redirect('orders:todos_los_pedidos')
    
    # Si no es POST, redirigir a la página de procesar pago
    return redirect('orders:procesar_pago', pedido_id=pedido.id)

@login_required
def listar_pagos_pendientes(request):
    """
    Muestra todos los pagos pendientes con paginación y búsqueda por cliente
    """
    # Obtener el parámetro de búsqueda
    cliente_busqueda = request.GET.get('cliente', '')
    
    # Filtrar solo los pagos pendientes que no han sido pagados
    pagos_pendientes = PagoPendiente.objects.filter(esta_pagado=False)
    
    # Aplicar filtro por cliente si se ha proporcionado una búsqueda
    if cliente_busqueda:
        pagos_pendientes = pagos_pendientes.filter(cliente_nombre__icontains=cliente_busqueda)
    
    # Ordenar por fecha de promesa
    pagos_pendientes = pagos_pendientes.order_by('cliente_nombre')
    
    # Calcular el total pendiente de los pagos filtrados
    total_pendiente = pagos_pendientes.aggregate(total=Sum('pago__monto'))['total'] or 0
    
    # Configurar la paginación
    paginator = Paginator(pagos_pendientes, 10)  # 10 pagos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'orders/pedidos/pagos_pendientes.html', {
        'pagos_pendientes': page_obj,
        'total_pendiente': total_pendiente,
        'cliente_busqueda': cliente_busqueda,
        'paginator': paginator,
        'page_obj': page_obj,
    })
    
@login_required
def marcar_pago_como_pagado(request, pago_pendiente_id):
    """
    Marca un pago pendiente como pagado
    """
    pago_pendiente = get_object_or_404(PagoPendiente, id=pago_pendiente_id)
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        
        # Actualizar el registro de pago pendiente
        pago_pendiente.esta_pagado = True
        pago_pendiente.fecha_pago_real = timezone.now().date()
        pago_pendiente.save()
        
        # Actualizar el pago original
        pago = pago_pendiente.pago
        pago.metodo = metodo_pago  # Actualizar al método real con el que se pagó
        pago.notas += f" | Pagado el {pago_pendiente.fecha_pago_real} con {metodo_pago}"
        pago.save()
        
        # Actualizar el pedido
        pedido = pago.pedido
        pedido.estado_pago = 'pagado'
        pedido.save()
        
        messages.success(request, f'El pago pendiente de {pago_pendiente.cliente_nombre} '
                                   f'por ${pago.monto} ha sido marcado como pagado.')
        
        return redirect('orders:pagos_pendientes')
    
    return render(request, 'orders/pedidos/marcar_pago_pendiente.html', {
        'pago_pendiente': pago_pendiente
    })

@login_required
def historial_pagos_pendientes(request):
    """
    Muestra el historial de pagos pendientes ya pagados
    """
    pagos_completados = PagoPendiente.objects.filter(esta_pagado=True).order_by('-fecha_pago_real')
    
    return render(request, 'orders/pedidos/historial_pagos_pendientes.html', {
        'pagos_completados': pagos_completados
    })

@login_required
def procesar_pago(request, pedido_id):
    """
    Muestra la página para procesar el pago
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
   
    
    # Modificación para usar tu propiedad items_activos
    items_activos = pedido.items_activos
    total_activo = sum(detalle.subtotal for detalle in items_activos)
        
    return render(request, 'orders/pedidos/procesar_pago.html', {
        'pedido': pedido,
        'items_activos': items_activos,
        'total_activo': total_activo
    })
    

#----------------------------
# Nuevas vistas para implementar el flujo de pedidos

@login_required
def seleccionar_tipo_orden(request):
    """
    Vista para seleccionar el tipo de orden
    """
    # Obtener tipos de orden activos
    tipos_orden = TipoOrden.objects.filter(activo=True)
    
    # Separar tipos de orden por si requieren mesa o no
    tipos_con_mesa = tipos_orden.filter(requiere_mesa=True)
    tipos_sin_mesa = tipos_orden.filter(requiere_mesa=False)
    
    context = {
        'tipos_con_mesa': tipos_con_mesa,
        'tipos_sin_mesa': tipos_sin_mesa
    }
    
    return render(request, 'orders/pedidos/seleccionar_tipo_orden.html', context)

###################
@login_required
def crear_pedido_para_llevar(request, tipo_orden_id):
    """
    Vista para crear y gestionar pedidos para llevar
    """
    tipo_orden = get_object_or_404(TipoOrden, id=tipo_orden_id)
    
    # Verificar que el tipo de orden no requiera mesa
    if tipo_orden.requiere_mesa:
        messages.error(request, f"El tipo de orden '{tipo_orden.nombre}' requiere seleccionar una mesa.")
        return redirect('orders:seleccionar_tipo_orden')
    
    try:
        mesero = Usuario.objects.get(username=request.user.username)
    except Usuario.DoesNotExist:
        messages.error(request, "No tienes permisos para tomar pedidos.")
        return redirect('home')
    
    # Procesar acción de creación de pedido
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_pedido':
            nombre_cliente = request.POST.get('nombre_cliente', '').strip()
            
            if not nombre_cliente:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': "El nombre del cliente es obligatorio."
                    }, status=400)
                messages.error(request, "El nombre del cliente es obligatorio.")
                return redirect('orders:crear_pedido_para_llevar', tipo_orden_id=tipo_orden.id)
            
            # Crear nuevo pedido para llevar
            try:
                with transaction.atomic():
                    pedido = Pedido.objects.create(
                        tipo_orden=tipo_orden,
                        mesero=mesero,
                        mesa=None,  # Sin mesa para pedidos para llevar
                        estado='pendiente',
                        monto_total=0,
                        estado_pago='pendiente',
                        nombre_cliente=nombre_cliente
                    )
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'pedido_id': pedido.id,
                            'numero_orden': pedido.numero_orden,
                            'redirect_url': reverse('orders:tomar_pedido_para_llevar', 
                                                 kwargs={'tipo_orden_id': tipo_orden.id, 'pedido_id': pedido.id})
                        })
                    
                    messages.success(request, f"Pedido para llevar creado correctamente. Número de orden: {pedido.numero_orden}")
                    return redirect('orders:tomar_pedido_para_llevar', tipo_orden_id=tipo_orden.id, pedido_id=pedido.id)
                    
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f"Error al crear el pedido: {str(e)}"
                    }, status=500)
                messages.error(request, f"Error al crear el pedido: {str(e)}")
                return redirect('orders:crear_pedido_para_llevar', tipo_orden_id=tipo_orden.id)
    
    # Generar un número de orden temporal para mostrar (no se guardará hasta crear el pedido)
    ultimo_numero = Pedido.objects.filter(
        tipo_orden=tipo_orden, 
        fecha_creacion__date=timezone.now().date()
    ).count() + 1
    
    fecha_str = timezone.now().strftime('%Y%m%d')
    numero_orden_temp = f"{tipo_orden.codigo}-{fecha_str}-{ultimo_numero:03d}"
    
    # Obtener categorías y productos
    categorias = Categoria.objects.all()
    
    context = {
        'tipo_orden': tipo_orden,
        'numero_orden': numero_orden_temp,
        'categorias': categorias,
        'productos_por_categoria': {
            categoria: Producto.objects.filter(categoria=categoria, esta_disponible=True)
            for categoria in categorias
        },
        'categoria_activa': categorias.first().id if categorias.exists() else None,
        'es_creacion': True
    }
    
    return render(request, 'orders/pedidos/tomar_pedido_para_llevar.html', context)

@login_required
def tomar_pedido_para_llevar(request, tipo_orden_id, pedido_id):
    """
    Vista para tomar pedidos para llevar una vez creado el pedido
    """
    tipo_orden = get_object_or_404(TipoOrden, id=tipo_orden_id)
    pedido = get_object_or_404(Pedido, id=pedido_id, tipo_orden=tipo_orden)
    
    # Verificar que el pedido no tenga mesa asignada
    if pedido.mesa:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': "Este no es un pedido para llevar."
            }, status=400)
        messages.error(request, "Este no es un pedido para llevar.")
        return redirect('orders:seleccionar_tipo_orden')
    
    # Obtener categorías y productos disponibles
    categorias = Categoria.objects.all()
    productos_por_categoria = {
        categoria: Producto.objects.filter(categoria=categoria, esta_disponible=True)
        for categoria in categorias
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            with transaction.atomic():
                if action == 'add_producto':
                    # Procesar detalle del pedido
                    producto_id = request.POST.get('producto_id')
                    cantidad = int(request.POST.get('cantidad', 1))
                    notas = request.POST.get('notas', '').strip()
                    
                    if not producto_id:
                        raise ValueError("ID de producto requerido")
                    
                    if cantidad <= 0:
                        raise ValueError("La cantidad debe ser mayor a 0")
                    
                    producto = get_object_or_404(Producto, id=producto_id)

                    # Verificar si el producto ya existe en el pedido con las mismas notas
                    detalle_existente = DetallePedido.objects.filter(
                        pedido=pedido,
                        producto=producto,
                        notas=notas,
                        estado='pendiente'
                    ).first()

                    if detalle_existente:
                        # Si ya existe, actualizar la cantidad
                        detalle_existente.cantidad += cantidad
                        detalle_existente.save()
                        nuevo_detalle = detalle_existente
                        message = f'Cantidad de {producto.nombre} actualizada (+{cantidad})'
                    else:
                        # Si no existe, crear nuevo detalle
                        nuevo_detalle = DetallePedido.objects.create(
                            pedido=pedido,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=producto.precio,
                            notas=notas,
                            estado='pendiente'
                        )
                        message = f'Producto {producto.nombre} agregado al pedido'

                    # NUEVA LÓGICA: Si el producto NO es de cocina, marcarlo automáticamente como entregado
                    if producto.categoria.area_preparacion.nombre != AreaPreparacion.COCINA:
                        nuevo_detalle.estado = 'entregado'
                        nuevo_detalle.hora_listo = timezone.now()
                        nuevo_detalle.hora_entrega = timezone.now()
                        nuevo_detalle.save()

                    pedido.calcular_total()
                    
                    # Actualizar mensaje según el área de preparación
                    mensaje_estado = ""
                    if producto.categoria.area_preparacion.nombre == AreaPreparacion.COCINA:
                        mensaje_estado = "agregado al pedido (requiere preparación en cocina)"
                    else:
                        mensaje_estado = "agregado y marcado como entregado automáticamente"
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Producto {producto.nombre} {mensaje_estado}.',
                            'total': float(pedido.monto_total),
                            'detalle_id': nuevo_detalle.id,
                            'cantidad_total': nuevo_detalle.cantidad,
                            'es_cocina': producto.categoria.area_preparacion.nombre == AreaPreparacion.COCINA
                        })
                    
                    messages.success(request, f'Producto {producto.nombre} {mensaje_estado}.')
                    
                elif action == 'remove_producto':
                    detalle_id = request.POST.get('detalle_id')
                    
                    if not detalle_id:
                        raise ValueError("ID de detalle requerido")
                    
                    detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
                    producto_nombre = detalle.producto.nombre
                    detalle.delete()
                    pedido.calcular_total()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Producto {producto_nombre} eliminado del pedido',
                            'total': float(pedido.monto_total)
                        })
                    
                    messages.success(request, f'Producto {producto_nombre} eliminado del pedido.')
                
                # NUEVO: Manejo para incrementar cantidad
                elif action == 'increment_cantidad':
                    detalle_id = request.POST.get('detalle_id')
                    
                    if not detalle_id:
                        raise ValueError("ID de detalle requerido")
                    
                    detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
                    detalle.cantidad += 1
                    detalle.save()
                    pedido.calcular_total()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'nueva_cantidad': detalle.cantidad,
                            'nuevo_subtotal': float(detalle.subtotal),
                            'total': float(pedido.monto_total),
                            'message': 'Cantidad incrementada correctamente'
                        })
                    
                    messages.success(request, 'Cantidad incrementada correctamente.')
                
                # NUEVO: Manejo para decrementar cantidad
                elif action == 'decrement_cantidad':
                    detalle_id = request.POST.get('detalle_id')
                    
                    if not detalle_id:
                        raise ValueError("ID de detalle requerido")
                    
                    detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
                    
                    if detalle.cantidad > 1:
                        detalle.cantidad -= 1
                        detalle.save()
                        pedido.calcular_total()
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'nueva_cantidad': detalle.cantidad,
                                'nuevo_subtotal': float(detalle.subtotal),
                                'total': float(pedido.monto_total),
                                'message': 'Cantidad decrementada correctamente'
                            })
                        
                        messages.success(request, 'Cantidad decrementada correctamente.')
                    else:
                        # Si la cantidad es 1, eliminar el producto completamente
                        producto_nombre = detalle.producto.nombre
                        detalle.delete()
                        pedido.calcular_total()
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'nueva_cantidad': 0,
                                'nuevo_subtotal': 0,
                                'total': float(pedido.monto_total),
                                'message': f'Producto {producto_nombre} eliminado del pedido'
                            })
                        
                        messages.success(request, f'Producto {producto_nombre} eliminado del pedido.')
                    
                elif action == 'update_nota':
                    detalle_id = request.POST.get('detalle_id')
                    nota = request.POST.get('nota', '').strip()
                    
                    if not detalle_id:
                        raise ValueError("ID de detalle requerido")
                    
                    detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
                    detalle.notas = nota
                    detalle.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'Nota actualizada correctamente.'
                        })
                    
                    messages.success(request, 'Nota actualizada correctamente.')
                    
                elif action == 'update_cantidad':
                    detalle_id = request.POST.get('detalle_id')
                    cantidad = int(request.POST.get('cantidad', 1))
                    
                    if not detalle_id:
                        raise ValueError("ID de detalle requerido")
                    
                    if cantidad <= 0:
                        raise ValueError("La cantidad debe ser mayor a 0")
                    
                    detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
                    cantidad_anterior = detalle.cantidad
                    detalle.cantidad = cantidad
                    detalle.save()
                    pedido.calcular_total()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'subtotal': float(detalle.subtotal),
                            'total': float(pedido.monto_total),
                            'cantidad_anterior': cantidad_anterior,
                            'message': 'Cantidad actualizada correctamente'
                        })
                    
                    messages.success(request, 'Cantidad actualizada correctamente.')
                    
                else:
                    raise ValueError(f"Acción no válida: {action}")
                    
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Error interno del servidor: {str(e)}'
                }, status=500)
            messages.error(request, f'Error: {str(e)}')

    # Manejar parámetro de categoría activa
    categoria_activa = request.GET.get('categoria')
    if not categoria_activa and categorias.exists():
        categoria_activa = categorias.first().id

    # Recalcular total
    pedido.calcular_total()
    
    context = {
        'tipo_orden': tipo_orden,
        'pedido_existente': pedido,
        'categorias': categorias,
        'productos_por_categoria': productos_por_categoria,
        'total_pedido': pedido.monto_total,
        'categoria_activa': int(categoria_activa) if categoria_activa else None,
        'es_creacion': False
    }
    
    return render(request, 'orders/pedidos/tomar_pedido_para_llevar.html', context)
#####################

#VENTA EXPRESS
class VentaExpressView(LoginRequiredMixin, View):
    """Vista para la venta express"""
    template_name = 'orders/pedidos/venta_express.html'
    
    def get(self, request):
        # Obtener TODAS las áreas de preparación disponibles
        areas_preparacion = AreaPreparacion.objects.all()
        
        # Obtener TODAS las categorías (no solo Barra y Bar)
        categorias = Categoria.objects.filter(area_preparacion__in=areas_preparacion).order_by('nombre')
        
        # Obtener productos de estas categorías que estén disponibles
        productos = Producto.objects.filter(
            categoria__in=categorias,
            esta_disponible=True
        ).select_related('categoria').order_by('categoria__nombre', 'nombre')
        
        # Obtener el tipo de orden para venta express
        tipo_orden_express = TipoOrden.objects.get(codigo='EXPRESS')
        
        # Fecha actual para mostrar en la interfaz
        today = date.today()
        
        context = {
            'categorias': categorias,
            'productos': productos,
            'tipo_orden': tipo_orden_express,
            'today': today,
        }
        
        return render(request, self.template_name, context)


class BuscarProductoExpressView(LoginRequiredMixin, View):
    """Vista para buscar productos en venta express mediante AJAX"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        categoria_id = request.GET.get('categoria', '')
        
        # Base query - productos disponibles
        productos = Producto.objects.filter(esta_disponible=True)
        
        # Filtrar por categoría si se especifica
        if categoria_id and categoria_id != 'todas':
            productos = productos.filter(categoria_id=categoria_id)
        
        # Filtrar por término de búsqueda
        if query:
            productos = productos.filter(
                Q(nombre__icontains=query) | 
                Q(descripcion__icontains=query)
            )
        
        # Obtener datos necesarios incluyendo información de stock
        productos_data = []
        for producto in productos[:20]:  # Limitar a 20 resultados para mejor rendimiento
            stock_producto = getattr(producto, 'stock', None)
            stock_disponible = stock_producto.cantidad_actual if stock_producto else 0
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'categoria_id': producto.categoria_id,
                'categoria__nombre': producto.categoria.nombre,
                'stock_disponible': stock_disponible,
                'tiene_stock': stock_disponible > 0 if stock_producto else True
            })
        
        return JsonResponse({
            'productos': productos_data
        })

class CrearPedidoExpressView(LoginRequiredMixin, View):
    """Vista para procesar la creación de un pedido express"""
    
    def post(self, request):
        try:
            # Obtener datos del formulario
            tipo_orden_id = request.POST.get('tipo_orden')
            estado_pago = request.POST.get('estado_pago', 'pendiente')
            nombre_cliente = request.POST.get('nombre_cliente', '')
            
            # Lista de productos del carrito (formato: id_producto:cantidad)
            items_carrito = request.POST.getlist('items_carrito')
            
            # DEBUG: Agregar logging para ver qué se está recibiendo
            print(f"DEBUG: items_carrito recibidos: {items_carrito}")
            
            # VALIDAR STOCK ANTES DE CREAR EL PEDIDO
            productos_sin_stock = []
            items_validados = []
            
            for item in items_carrito:
                try:
                    # Validar formato del item
                    if ':' not in item:
                        print(f"DEBUG: Item mal formateado: {item}")
                        continue
                        
                    producto_id, cantidad = item.split(':')
                    producto_id = int(producto_id.strip())
                    cantidad = int(cantidad.strip())
                    
                    # Verificar que el producto existe
                    try:
                        producto = Producto.objects.get(id=producto_id)
                    except Producto.DoesNotExist:
                        print(f"DEBUG: Producto no encontrado: {producto_id}")
                        continue
                    
                    print(f"DEBUG: Procesando producto: {producto.nombre}, cantidad: {cantidad}")
                    
                    # Verificar stock solo si el producto tiene control de stock
                    stock_producto = getattr(producto, 'stock', None)
                    
                    if stock_producto:
                        # Producto con control de stock
                        print(f"DEBUG: Stock disponible para {producto.nombre}: {stock_producto.cantidad_actual}")
                        
                        if stock_producto.cantidad_actual < cantidad:
                            productos_sin_stock.append({
                                'nombre': producto.nombre,
                                'solicitado': cantidad,
                                'disponible': stock_producto.cantidad_actual
                            })
                            print(f"DEBUG: Stock insuficiente para {producto.nombre}")
                        else:
                            items_validados.append({
                                'producto': producto,
                                'cantidad': cantidad
                            })
                            print(f"DEBUG: Stock suficiente para {producto.nombre}")
                    else:
                        # Producto sin control de stock - siempre válido
                        items_validados.append({
                            'producto': producto,
                            'cantidad': cantidad
                        })
                        print(f"DEBUG: Producto sin control de stock: {producto.nombre}")
                        
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error al procesar item {item}: {e}")
                    continue
            
            print(f"DEBUG: Items validados: {len(items_validados)}")
            print(f"DEBUG: Productos sin stock: {len(productos_sin_stock)}")
            
            # Si hay productos sin stock, devolver error
            if productos_sin_stock:
                error_messages = []
                for item in productos_sin_stock:
                    error_messages.append(
                        f"{item['nombre']}: solicitado {item['solicitado']}, disponible {item['disponible']}"
                    )
                
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Stock insuficiente',
                        'detalles': error_messages
                    }, status=400)
                
                # Si es una petición normal, mostrar mensaje y redirigir
                messages.error(request, f"Stock insuficiente para: {', '.join(error_messages)}")
                return redirect('orders:venta_express')
            
            # Si no hay items válidos, mostrar error
            if not items_validados:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'No hay productos válidos en el carrito'
                    }, status=400)
                
                messages.error(request, "No hay productos válidos en el carrito")
                return redirect('orders:venta_express')
            
            # Crear el pedido dentro de una transacción
            with transaction.atomic():
                tipo_orden = get_object_or_404(TipoOrden, id=tipo_orden_id)
                
                pedido = Pedido(
                    tipo_orden=tipo_orden,
                    mesero=request.user,
                    estado='pendiente',
                    monto_total=0,
                    estado_pago=estado_pago,
                    nombre_cliente=nombre_cliente
                )
                pedido.save()  # Guardar para generar número automático
                
                print(f"DEBUG: Pedido creado con ID: {pedido.id}")
                
                # Crear detalles del pedido
                detalles = []
                for item in items_validados:
                    try:
                        producto = item['producto']
                        cantidad = item['cantidad']
                        
                        print(f"DEBUG: Creando detalle para {producto.nombre}")
                        
                        # Determinar el estado inicial del detalle del pedido
                        estado_detalle = 'listo'
                        
                        detalle = DetallePedido.objects.create(
                            pedido=pedido,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=producto.precio,
                            estado=estado_detalle
                        )
                        detalles.append(detalle)
                        
                        # Actualizar stock si el producto tiene control de stock
                        stock_producto = getattr(producto, 'stock', None)
                        if stock_producto:
                            stock_producto.cantidad_actual -= cantidad
                            stock_producto.save()
                            print(f"DEBUG: Stock actualizado para {producto.nombre}. Nuevo stock: {stock_producto.cantidad_actual}")
                        
                    except Exception as e:
                        print(f"DEBUG: Error al procesar item {producto.nombre}: {e}")
                        raise Exception(f"Error al procesar {producto.nombre}: {str(e)}")
                
                # Calcular el total del pedido
                pedido.calcular_total()
                
                print(f"DEBUG: Total del pedido: {pedido.monto_total}")
                
                # Procesar según el estado de pago
                if estado_pago == 'pagado':
                    metodo_pago = request.POST.get('metodo_pago', 'efectivo')
                    monto_recibido = request.POST.get('monto_recibido', None)
                    
                    pago = Pago(
                        pedido=pedido,
                        monto=pedido.monto_total,
                        metodo=metodo_pago,
                        fecha=timezone.now()
                    )
                    
                    if metodo_pago == 'efectivo' and monto_recibido:
                        monto_recibido = Decimal(monto_recibido)
                        pago.monto_recibido = monto_recibido
                        pago.cambio = monto_recibido - pedido.monto_total if monto_recibido > pedido.monto_total else 0
                    
                    pago.save()
                    
                    # Actualizar el pedido para reflejar quién lo cobró
                    pedido.cajero = request.user
                    pedido.estado = 'completado'
                    pedido.save()
                    
                elif estado_pago == 'pendiente':
                    # Crear registro de pago pendiente
                    metodo_pago = 'pendiente'
                    cliente_nombre = request.POST.get('nombre_cliente', '')
                    FECHA_PROMESA_DEFAULT = '2060-12-31'
                    fecha_promesa = request.POST.get('fecha_promesa', FECHA_PROMESA_DEFAULT)
                    notas_adicionales = request.POST.get('notas_adicionales', 'compromiso de pago')
                    
                    # Crear el pago básico
                    pago = Pago(
                        pedido=pedido,
                        monto=pedido.monto_total,
                        metodo=metodo_pago,
                        notas="Pago pendiente",
                        fecha=timezone.now()
                    )
                    pago.save()
                    
                    # Crear registro en PagoPendiente
                    PagoPendiente.objects.create(
                        pago=pago,
                        cliente_nombre=cliente_nombre,
                        fecha_promesa=fecha_promesa,
                        notas_adicionales=notas_adicionales
                    )
                    
                    # Actualizar estado del pedido
                    pedido.estado_pago = 'impago'
                    pedido.estado = 'completado'
                    pedido.save()
                
                print(f"DEBUG: Pedido completado exitosamente")
                
                # Si es una petición AJAX, devolver éxito
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'pedido_id': pedido.id,
                        'redirect_url': reverse('orders:recibo_venta_express', kwargs={'pedido_id': pedido.id})
                    })
                
                # Redireccionar a la vista de recibo
                return redirect('orders:recibo_venta_express', pedido_id=pedido.id)
                
        except Exception as e:
            # Manejar cualquier error inesperado
            error_msg = f"Error al crear el pedido: {str(e)}"
            print(f"DEBUG: Error inesperado: {error_msg}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)
            
            messages.error(request, error_msg)
            return redirect('orders:venta_express')


# VISTA ADICIONAL: Para verificar stock en tiempo real via AJAX
class VerificarStockExpressView(LoginRequiredMixin, View):
    """Vista para verificar stock de productos en tiempo real"""
    
    def post(self, request):
        try:
            items_carrito = request.POST.getlist('items_carrito')
            
            productos_sin_stock = []
            stock_info = []
            
            for item in items_carrito:
                try:
                    producto_id, cantidad = item.split(':')
                    producto = Producto.objects.get(id=producto_id)
                    cantidad = int(cantidad)
                    
                    stock_producto = getattr(producto, 'stock', None)
                    if stock_producto:
                        stock_disponible = stock_producto.cantidad_actual
                        tiene_stock = stock_producto.puede_vender(cantidad)
                        
                        stock_info.append({
                            'producto_id': producto.id,
                            'nombre': producto.nombre,
                            'cantidad_solicitada': cantidad,
                            'stock_disponible': stock_disponible,
                            'tiene_stock': tiene_stock
                        })
                        
                        if not tiene_stock:
                            productos_sin_stock.append({
                                'nombre': producto.nombre,
                                'solicitado': cantidad,
                                'disponible': stock_disponible
                            })
                    else:
                        # Producto sin control de stock
                        stock_info.append({
                            'producto_id': producto.id,
                            'nombre': producto.nombre,
                            'cantidad_solicitada': cantidad,
                            'stock_disponible': 'Sin control',
                            'tiene_stock': True
                        })
                        
                except (ValueError, Producto.DoesNotExist):
                    continue
            
            return JsonResponse({
                'success': True,
                'tiene_stock_suficiente': len(productos_sin_stock) == 0,
                'productos_sin_stock': productos_sin_stock,
                'stock_info': stock_info
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


    
class ReciboVentaExpressView(LoginRequiredMixin, View):
    """Vista para mostrar el recibo de una venta express"""
    template_name = 'orders/pedidos/recibo_venta_express.html'
    
    def get(self, request, pedido_id):
        pedido = get_object_or_404(Pedido, id=pedido_id)
        return render(request, self.template_name, {
            'pedido': pedido,
            'detalles': pedido.items_activos,
            'pagos': pedido.pagos.all()
        })

class GetTodasCategoriasView(LoginRequiredMixin, View):
    """Vista para obtener todas las categorías disponibles"""
    
    def get(self, request):
        # Obtener todas las categorías, no solo las de Bar y Barra
        categorias = Categoria.objects.all().order_by('nombre')
        categorias_data = categorias.values('id', 'nombre', 'area_preparacion__nombre')
        
        return JsonResponse({
            'categorias': list(categorias_data)
        })



######################################################
#Recivo cocina
@login_required
def recibo_cocina(request, pedido_id):
    """
    Vista para mostrar el recibo de cocina de un pedido específico
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Items de cocina (prioritarios) - solo los que no están entregados
    items_cocina = pedido.items_activos.filter(
        producto__categoria__area_preparacion__nombre='cocina'
    ).exclude(estado='entregado')
    
    # Items de otras áreas (bar, barra, etc.) - solo los que no están entregados
    items_otras_areas = pedido.items_activos.exclude(
        producto__categoria__area_preparacion__nombre='cocina'
    ).exclude(estado='entregado')
    
    context = {
        'pedido': pedido,
        'items_cocina': items_cocina,
        'items_otras_areas': items_otras_areas,
        'fecha_impresion': timezone.now(),
    }
    
    return render(request, 'orders/pedidos/recibo_cocina.html', context)

@login_required
def imprimir_recibo_cocina(request, pedido_id):
    """
    Vista para imprimir directamente el recibo (abre en nueva ventana)
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Items de cocina (prioritarios) - solo los que no están entregados
    items_cocina = pedido.items_activos.filter(
        producto__categoria__area_preparacion__nombre='cocina'
    ).exclude(estado='entregado')
    
    # Items de otras áreas (bar, barra, etc.) - solo los que no están entregados
    items_otras_areas = pedido.items_activos.exclude(
        producto__categoria__area_preparacion__nombre='cocina'
    ).exclude(estado='listo')
    
    context = {
        'pedido': pedido,
        'items_cocina': items_cocina,
        'items_otras_areas': items_otras_areas,
        'fecha_impresion': timezone.now(),
        'para_impresion': True,  # Flag para saber que es para impresión
    }
    
    response = render(request, 'orders/pedidos/recibo_cocina.html', context)
    response['Content-Type'] = 'text/html; charset=utf-8'
    return response



@csrf_exempt
@require_POST
@login_required
def marcar_recibo_impreso(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.recibo_cocina_impreso = True
        pedido.save()
        return JsonResponse({'status': 'success'})
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado'}, status=404)
    
    

#impresora termica
# views.py - VERSIÓN OPTIMIZADA PARA XPRINTER XP-A160H


# Configurar logging
logger = logging.getLogger('printer')


@login_required
def imprimir_orden_mobile(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Usar la propiedad area_preparacion del detalle
    items_cocina = [item for item in pedido.items_activos 
                   if item.area_preparacion and item.area_preparacion.nombre.lower() == 'cocina']
    
    items_otras_areas = [item for item in pedido.items_activos 
                        if not item.area_preparacion or item.area_preparacion.nombre.lower() != 'cocina']
    
    context = {
        'pedido': pedido,
        'items_cocina': items_cocina,
        'items_otras_areas': items_otras_areas,
        'fecha_impresion': timezone.now(),
        'es_mobile': True,
    }
    
    return render(request, 'orders/pedidos/recibo_cocina_mobile.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def enviar_a_impresora_termica(request, pedido_id):
    """
    Envía la orden directamente a la impresora térmica Xprinter XP-A160H
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Generar contenido para impresora térmica (formato ESC/POS optimizado)
        contenido_impresion = generar_ticket_xprinter_a160h(pedido)
        
        # Enviar a impresora por red
        resultado = enviar_a_impresora_red(contenido_impresion)
        
        if resultado['success']:
            logger.info(f"Orden {pedido.id} impresa correctamente en XP-A160H")            
            return JsonResponse({
                'success': True, 
                'message': 'Orden enviada a impresora XP-A160H correctamente'
            })
        else:
            logger.error(f"Error al imprimir orden {pedido.id}: {resultado['error']}")          
            return JsonResponse({
                'success': False, 
                'message': f'Error al imprimir: {resultado["error"]}'
            })
            
    except Exception as e:
        logger.error(f"Excepción al imprimir orden {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })

def generar_ticket_xprinter_a160h(pedido):
    """
    Genera el contenido de impresión en formato ESC/POS optimizado para Xprinter XP-A160H
    """
    # Comandos ESC/POS específicos para XP-A160H
    ESC = chr(27)
    GS = chr(29)
    
    # Comandos básicos
    INIT = ESC + "@"                    # Inicializar impresora
    RESET = ESC + "c" + chr(0)          # Reset completo
    
    # Texto
    BOLD_ON = ESC + "E" + chr(1)        # Negrita ON (más compatible)
    BOLD_OFF = ESC + "E" + chr(0)       # Negrita OFF
    DOUBLE_HEIGHT = ESC + "!" + chr(16) # Altura doble
    DOUBLE_WIDTH = ESC + "!" + chr(32)  # Ancho doble
    DOUBLE_SIZE = ESC + "!" + chr(48)   # Tamaño doble (alto + ancho)
    NORMAL_SIZE = ESC + "!" + chr(0)    # Tamaño normal
    
    # Alineación
    CENTER = ESC + "a" + chr(1)         # Centrar
    LEFT = ESC + "a" + chr(0)           # Alinear izquierda
    RIGHT = ESC + "a" + chr(2)          # Alinear derecha
    
    # Corte de papel (específico para XP-A160H con auto-cut)
    FULL_CUT = GS + "V" + chr(65) + chr(0)      # Corte completo
    PARTIAL_CUT = GS + "V" + chr(66) + chr(0)   # Corte parcial
    
    # Avance de papel
    FEED_LINES = lambda n: ESC + "d" + chr(n)   # Avanzar n líneas
    
    # Caracteres especiales para separadores
    SEPARATOR_CHAR = "="
    DASH_CHAR = "-"
    
    detalles = pedido.detalles.all()  # <- Aquí quitamos cualquier exclude()
    # Items de cocina
    # Filtrar solo por área de preparación (sin excluir por estado)
    items_cocina = detalles.filter(
        producto__categoria__area_preparacion__nombre='cocina'
    )
    
    items_otras_areas = detalles.exclude(
        producto__categoria__area_preparacion__nombre='cocina'
    )
    
    # Construir el ticket optimizado para XP-A160H
    ticket = INIT + RESET  # Inicializar y resetear
    
    # ENCABEZADO
    ticket += CENTER + DOUBLE_SIZE + BOLD_ON
    ticket += "ORDEN DE COCINA\n"
    ticket += BOLD_OFF + NORMAL_SIZE
    ticket += SEPARATOR_CHAR * 32 + "\n"
    
    # INFORMACIÓN DEL PEDIDO
    ticket += DOUBLE_HEIGHT + BOLD_ON
    ticket += f"PEDIDO #{pedido.id}\n"
    ticket += BOLD_OFF + NORMAL_SIZE
    
    if pedido.mesa:
        ticket += DOUBLE_WIDTH + BOLD_ON
        ticket += f"MESA {pedido.mesa.numero}\n"
        ticket += BOLD_OFF + NORMAL_SIZE
    
    ticket += SEPARATOR_CHAR * 32 + "\n"
    ticket += LEFT  # Cambiar a alineación izquierda
    
    # INFORMACIÓN ADICIONAL
    ticket += f"Fecha: {pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n"
    ticket += f"Mesero: {pedido.mesero.get_full_name()}\n"
    if pedido.nombre_cliente:
        ticket += f"Cliente: {pedido.nombre_cliente}\n"
    
    ticket += SEPARATOR_CHAR * 32 + "\n"
    
    # SECCIÓN COCINA
    if items_cocina:
        ticket += CENTER + BOLD_ON + DOUBLE_HEIGHT
        ticket += "*** COCINA ***\n"
        ticket += BOLD_OFF + NORMAL_SIZE + LEFT
        ticket += SEPARATOR_CHAR * 32 + "\n"
        
        for item in items_cocina:
            # Cantidad y producto
            ticket += BOLD_ON + f"{item.cantidad}x "
            ticket += f"{item.producto.nombre.upper()}\n" + BOLD_OFF
            
            # Precio si está disponible
            #if hasattr(item, 'precio_unitario') and item.precio_unitario:
             #   ticket += f"    ${item.precio_unitario:.2f} c/u\n"
            
            # Notas
            if item.notas:
                ticket += f"    NOTAS: {item.notas}\n"
            
            ticket += DASH_CHAR * 32 + "\n"
    
    # SECCIÓN OTRAS ÁREAS
    if items_otras_areas:
        ticket += CENTER + BOLD_ON + DOUBLE_HEIGHT
        ticket += "*** OTRAS AREAS ***\n"
        ticket += BOLD_OFF + NORMAL_SIZE + LEFT
        ticket += SEPARATOR_CHAR * 32 + "\n"
        
        for item in items_otras_areas:
            area = item.producto.categoria.area_preparacion.nombre.upper() if item.producto.categoria.area_preparacion else "GENERAL"
            
            # Cantidad, producto y área
            ticket += BOLD_ON + f"{item.cantidad}x "
            ticket += f"{item.producto.nombre.upper()}\n" + BOLD_OFF
            ticket += f"    [{area}]\n"
            
            # Precio si está disponible
            #if hasattr(item, 'precio_unitario') and item.precio_unitario:
             #   ticket += f"    ${item.precio_unitario:.2f} c/u\n"
            
            # Notas
            if item.notas:
                ticket += f"    NOTAS: {item.notas}\n"
            
            ticket += DASH_CHAR * 32 + "\n"
   
    # TOTALES (si están disponibles)
    #if hasattr(pedido, 'monto_total') and pedido.monto_total:        
     #   ticket += SEPARATOR_CHAR * 32 + "\n"
      #  ticket += RIGHT + BOLD_ON + DOUBLE_HEIGHT
       # ticket += f"TOTAL: ${pedido.monto_total:.2f}\n"        
        #ticket += BOLD_OFF + NORMAL_SIZE + LEFT
    
    # PIE DE PÁGINA
    ticket += SEPARATOR_CHAR * 32 + "\n"
    ticket += CENTER
    ticket += f"Impreso: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    ticket += "Gracias por su pedido\n"
    
    # ESPACIADO FINAL Y CORTE
    ticket += FEED_LINES(3)  # Avanzar 3 líneas antes del corte
    ticket += PARTIAL_CUT    # Corte parcial (recomendado para XP-A160H)
    
    # Codificar en UTF-8 con manejo de errores
    try:
        return ticket.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback a codificación más básica si hay caracteres problemáticos
        return ticket.encode('latin-1', errors='replace')

def enviar_a_impresora_red(contenido):
    """
    Envía el contenido a la impresora térmica Xprinter XP-A160H por red
    Optimizado para XP-A160H con mejor manejo de errores
    """
    try:
        from django.conf import settings
        
        printer_ip = getattr(settings, 'PRINTER_IP', '10.201.71.207')
        printer_port = getattr(settings, 'PRINTER_PORT', 9100)
        timeout = getattr(settings, 'PRINTER_TIMEOUT', 15)  # Aumentado para XP-A160H
        
        logger.info(f"Conectando a impresora XP-A160H en {printer_ip}:{printer_port}")
        
        # Crear socket con configuración optimizada
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Conectar a la impresora
        sock.connect((printer_ip, printer_port))
        
        # Enviar datos en chunks para mejor compatibilidad
        chunk_size = 1024
        for i in range(0, len(contenido), chunk_size):
            chunk = contenido[i:i + chunk_size]
            sock.send(chunk)
            # Pequeña pausa para asegurar procesamiento
            import time
            time.sleep(0.01)
        
        # Cerrar conexión
        sock.close()
        
        logger.info("Impresión enviada exitosamente a XP-A160H")
        return {'success': True, 'message': 'Impresión exitosa en XP-A160H'}
        
    except socket.timeout:
        error_msg = 'Timeout - Impresora XP-A160H no responde'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    except socket.error as e:
        error_msg = f'Error de conexión con XP-A160H: {e}'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f'Error inesperado con XP-A160H: {e}'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

@login_required
def test_impresora_xprinter(request):
    """
    Vista para probar la conexión con la impresora Xprinter XP-A160H
    """
    if request.method == 'POST':
        # Generar contenido de prueba específico para XP-A160H
        ESC = chr(27)
        GS = chr(29)
        
        contenido_test = ESC + "@"  # Inicializar
        contenido_test += ESC + "a" + chr(1)  # Centrar
        contenido_test += ESC + "E" + chr(1)  # Negrita ON
        contenido_test += "XPRINTER XP-A160H\n"
        contenido_test += ESC + "E" + chr(0)  # Negrita OFF
        contenido_test += "=" * 32 + "\n"
        contenido_test += "TEST DE IMPRESORA\n"
        contenido_test += "=" * 32 + "\n"
        contenido_test += ESC + "a" + chr(0)  # Alinear izquierda
        contenido_test += f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        contenido_test += "Si ves esto, la\n"
        contenido_test += "impresora funciona!\n"
        contenido_test += "\n"
        contenido_test += "Velocidad: 160mm/s\n"
        contenido_test += "Papel: 80mm\n"
        contenido_test += "Protocolo: ESC/POS\n"
        contenido_test += "\n" * 3
        contenido_test += GS + "V" + chr(66) + chr(0)  # Corte parcial
        
        resultado = enviar_a_impresora_red(contenido_test.encode('utf-8'))
        return JsonResponse(resultado)
    
    return render(request, 'orders/test_impresora.html', {
        'printer_model': 'Xprinter XP-A160H',
        'printer_specs': {
            'speed': '160mm/s',
            'paper_width': '80mm',
            'commands': 'ESC/POS',
            'auto_cut': 'Sí'
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def configurar_impresora_xprinter(request):
    """
    Configuración avanzada para Xprinter XP-A160H
    """
    try:
        # Comandos de configuración específicos para XP-A160H
        ESC = chr(27)
        GS = chr(29)
        
        config_commands = ESC + "@"  # Reset
        config_commands += ESC + "c" + chr(0)  # Reset completo
        config_commands += GS + "f" + chr(0)  # Configurar fuente
        config_commands += ESC + "M" + chr(0)  # Seleccionar conjunto de caracteres
        config_commands += ESC + "R" + chr(0)  # Seleccionar página de códigos
        
        resultado = enviar_a_impresora_red(config_commands.encode('utf-8'))
        
        if resultado['success']:
            return JsonResponse({
                'success': True,
                'message': 'Impresora XP-A160H configurada correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Error al configurar: {resultado["error"]}'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error de configuración: {str(e)}'
        })

# Función auxiliar para generar códigos de barras (opcional)
def generar_codigo_barras_pedido(pedido_numero):
    """
    Genera código de barras para el número de pedido (opcional)
    """
    GS = chr(29)
    
    # Configurar código de barras CODE128
    barcode_commands = GS + "k" + chr(73)  # Seleccionar CODE128
    barcode_commands += chr(len(str(pedido_numero)))  # Longitud
    barcode_commands += str(pedido_numero)  # Datos
    
    return barcode_commands.encode('utf-8')

def detectar_impresora_red():
    """
    Función para detectar automáticamente la IP de la impresora XP-A160H en la red
    """
    import subprocess
    import ipaddress
    
    # Obtener IP de la red local
    try:
        # Escanear red local común
        network = ipaddress.IPv4Network('192.168.1.0/24', strict=False)
        
        for ip in network.hosts():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((str(ip), 9100))
                sock.close()
                
                if result == 0:
                    return str(ip)
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error detectando impresora: {e}")
        
    return None

######################################################################
#boleta de cliente
# Configurar logging
logger = logging.getLogger('printer')

@login_required
def boleta_mobile(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Filtrar solo los detalles activos
    detalles_activos = pedido.detalles.exclude(estado='cancelado')
    
    # Calcular el total correcto basado solo en detalles activos
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    
    context = {
        'pedido': pedido,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto,
        'fecha_impresion': timezone.now(),
        'es_mobile': True,
    }
    
    return render(request, 'orders/pedidos/boleta_mobile.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def enviar_boleta_a_impresora_termica(request, pedido_id):
    """
    Envía la boleta directamente a la impresora térmica Xprinter XP-A160H
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Generar contenido de boleta para impresora térmica (formato ESC/POS optimizado)
        contenido_impresion = generar_boleta_xprinter_a160h(pedido)
        
        # Enviar a impresora por red
        resultado = enviar_a_impresora_red(contenido_impresion)
        
        if resultado['success']:
            logger.info(f"Boleta del pedido {pedido.id} impresa correctamente en XP-A160H")            
            return JsonResponse({
                'success': True, 
                'message': 'Boleta enviada a impresora XP-A160H correctamente'
            })
        else:
            logger.error(f"Error al imprimir boleta del pedido {pedido.id}: {resultado['error']}")          
            return JsonResponse({
                'success': False, 
                'message': f'Error al imprimir: {resultado["error"]}'
            })
            
    except Exception as e:
        logger.error(f"Excepción al imprimir boleta del pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })

def generar_boleta_xprinter_a160h(pedido):
    """
    Genera el contenido de la boleta en formato ESC/POS optimizado para Xprinter XP-A160H
    """
    # Comandos ESC/POS específicos para XP-A160H
    ESC = chr(27)
    GS = chr(29)
    
    # Comandos básicos
    INIT = ESC + "@"                    # Inicializar impresora
    RESET = ESC + "c" + chr(0)          # Reset completo
    
    # Texto
    BOLD_ON = ESC + "E" + chr(1)        # Negrita ON
    BOLD_OFF = ESC + "E" + chr(0)       # Negrita OFF
    DOUBLE_HEIGHT = ESC + "!" + chr(16) # Altura doble
    DOUBLE_WIDTH = ESC + "!" + chr(32)  # Ancho doble
    DOUBLE_SIZE = ESC + "!" + chr(48)   # Tamaño doble (alto + ancho)
    NORMAL_SIZE = ESC + "!" + chr(0)    # Tamaño normal
    
    # Alineación
    CENTER = ESC + "a" + chr(1)         # Centrar
    LEFT = ESC + "a" + chr(0)           # Alinear izquierda
    RIGHT = ESC + "a" + chr(2)          # Alinear derecha
    
    # Corte de papel
    FULL_CUT = GS + "V" + chr(65) + chr(0)      # Corte completo
    PARTIAL_CUT = GS + "V" + chr(66) + chr(0)   # Corte parcial
    
    # Avance de papel
    FEED_LINES = lambda n: ESC + "d" + chr(n)   # Avanzar n líneas
    
    # Caracteres especiales para separadores
    SEPARATOR_CHAR = "="
    DASH_CHAR = "-"
    
    # Filtrar solo los detalles activos
    detalles_activos = pedido.detalles.exclude(estado='cancelado')
    
    # Calcular el total correcto
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    
    # Construir la boleta optimizada para XP-A160H
    boleta = INIT + RESET  # Inicializar y resetear
    
    # ENCABEZADO
    boleta += CENTER + DOUBLE_SIZE + BOLD_ON
    boleta += "CAFETERIA LECHE Y MIEL\n"
    boleta += BOLD_OFF + NORMAL_SIZE
    boleta += "Colin s/n\n"
    boleta += SEPARATOR_CHAR * 32 + "\n"
    
    # TÍTULO BOLETA
    boleta += BOLD_ON + DOUBLE_HEIGHT
    boleta += "BOLETA DE PEDIDO\n"
    boleta += BOLD_OFF + NORMAL_SIZE
    boleta += f"{pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n"
    boleta += SEPARATOR_CHAR * 32 + "\n"
    
    # INFORMACIÓN DEL PEDIDO
    boleta += LEFT  # Cambiar a alineación izquierda
    boleta += BOLD_ON + f"Pedido #: {pedido.id}\n" + BOLD_OFF
    
    if pedido.mesa:
        boleta += BOLD_ON + f"Mesa: {pedido.mesa.numero}\n" + BOLD_OFF
    else:
        boleta += BOLD_ON + f"{pedido.tipo_orden.nombre}"
        if pedido.numero_orden:
            boleta += f" - {pedido.numero_orden}"
        boleta += "\n" + BOLD_OFF
        
        if pedido.nombre_cliente:
            boleta += BOLD_ON + f"Cliente: {pedido.nombre_cliente}\n" + BOLD_OFF
    
    boleta += SEPARATOR_CHAR * 32 + "\n"
    
    # ENCABEZADOS DE TABLA
    boleta += BOLD_ON
    boleta += f"{'Producto':<20} {'Cant':<4} {'Total':<8}\n"
    boleta += BOLD_OFF
    boleta += DASH_CHAR * 32 + "\n"
    
    # DETALLES DE PRODUCTOS
    for detalle in detalles_activos:
        # Truncar nombre del producto si es muy largo
        nombre_producto = detalle.producto.nombre
        if len(nombre_producto) > 18:
            nombre_producto = nombre_producto[:15] + "..."
        
        # Formatear subtotal
        subtotal_str = f"${detalle.subtotal:,.0f}".replace(',', '.')
        
        # Línea del producto
        boleta += f"{nombre_producto:<20} {detalle.cantidad:<4} {subtotal_str:<8}\n"
    
    boleta += DASH_CHAR * 32 + "\n"
    
    # TOTAL
    boleta += RIGHT + BOLD_ON + DOUBLE_HEIGHT
    boleta += f"TOTAL: ${total_correcto:,.0f}".replace(',', '.') + "\n"
    boleta += BOLD_OFF + NORMAL_SIZE
    
    # ESTADO
    boleta += CENTER + BOLD_ON
    boleta += "ESTADO: PENDIENTE DE PAGO\n"
    boleta += BOLD_OFF
    
    boleta += SEPARATOR_CHAR * 32 + "\n"
    
    # PIE DE PÁGINA
    boleta += LEFT
    boleta += f"Atendido: {pedido.mesero.get_full_name()[:20]}\n"
    boleta += CENTER + BOLD_ON
    boleta += "¡Gracias por su preferencia!\n"
    boleta += BOLD_OFF
    boleta += f"Boleta generada: {pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n"
    boleta += "\n"
    boleta += "Esta es una boleta pre-pago.\n"
    boleta += "No valida como comprobante fiscal.\n"
    
    # ESPACIADO FINAL Y CORTE
    boleta += FEED_LINES(3)  # Avanzar 3 líneas antes del corte
    boleta += PARTIAL_CUT    # Corte parcial
    
    # Codificar en UTF-8 con manejo de errores
    try:
        return boleta.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback a codificación más básica si hay caracteres problemáticos
        return boleta.encode('latin-1', errors='replace')
    
    
##############ELIMINA VENTA COMPLETA############################
@login_required
@require_http_methods(["POST"])
def eliminar_venta_completa(request, pedido_id):
    """
    Elimina completamente una venta y todos sus registros relacionados
    de todas las tablas: Pedido, DetallePedido, Pago y PagoPendiente
    """
    try:
        # Obtener el pedido o devolver 404 si no existe
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Usar una transacción para asegurar que todo se elimine correctamente
        # o nada se elimine si hay algún error
        with transaction.atomic():
            # 1. Eliminar PagoPendiente si existe
            pagos_pendientes_eliminados = 0
            for pago in pedido.pagos.all():
                if hasattr(pago, 'pendiente_info'):
                    pago.pendiente_info.delete()
                    pagos_pendientes_eliminados += 1
            
            # 2. Eliminar todos los Pagos relacionados
            pagos_eliminados = pedido.pagos.count()
            pedido.pagos.all().delete()
            
            # 3. RESTAURAR STOCK: Eliminar todos los DetallePedido UNO POR UNO
            # para que se ejecute el método delete() personalizado
            detalles_eliminados = 0
            stock_restaurado = []
            
            for detalle in pedido.detalles.all():
                # Guardar info del stock que se va a restaurar
                if detalle.estado != 'cancelado':
                    stock_restaurado.append({
                        'producto': detalle.producto.nombre,
                        'cantidad': detalle.cantidad
                    })
                
                # Eliminar individualmente para activar el método delete() personalizado
                detalle.delete()  # Esto ejecutará nuestro método delete() que restaura el stock
                detalles_eliminados += 1
            
            # 4. Liberar la mesa si existe (cambiar estado a Disponible)
            mesa_liberada = None
            if pedido.mesa:
                mesa_liberada = pedido.mesa
                mesa_liberada.estado = 'disponible'  # Ajusta según tu modelo de Mesa
                mesa_liberada.save()
            
            # 5. Finalmente eliminar el Pedido
            pedido_info = {
                'id': pedido.id,
                'numero_orden': pedido.numero_orden,
                'mesa': pedido.mesa.numero if pedido.mesa else 'Para llevar',
                'cliente': pedido.nombre_cliente or 'Sin nombre',
                'monto_total': pedido.monto_total,
                'mesa_liberada': mesa_liberada.numero if mesa_liberada else None,
                'stock_restaurado': stock_restaurado
            }
            pedido.delete()
        
        # Mensaje de éxito con detalles
        mensaje_mesa = f"\n- Mesa {pedido_info['mesa_liberada']} liberada y disponible" if pedido_info['mesa_liberada'] else ""
        
        # Mensaje de stock restaurado
        mensaje_stock = ""
        if stock_restaurado:
            mensaje_stock = "\n- Stock restaurado:"
            for item in stock_restaurado:
                mensaje_stock += f"\n  • {item['producto']}: +{item['cantidad']} unidades"
        
        mensaje = f"""
        Venta eliminada completamente:
        - Pedido #{pedido_info['id']} ({pedido_info['numero_orden'] or 'Sin número'})
        - Mesa: {pedido_info['mesa']}
        - Cliente: {pedido_info['cliente']}
        - Monto: ${pedido_info['monto_total']}
        - Detalles eliminados: {detalles_eliminados}
        - Pagos eliminados: {pagos_eliminados}
        - Pagos pendientes eliminados: {pagos_pendientes_eliminados}{mensaje_mesa}{mensaje_stock}
        """
        
        messages.success(request, mensaje)
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Venta eliminada completamente',
                'pedido_info': pedido_info,
                'detalles_eliminados': detalles_eliminados,
                'pagos_eliminados': pagos_eliminados,
                'pagos_pendientes_eliminados': pagos_pendientes_eliminados,
                'mesa_liberada': pedido_info['mesa_liberada'],
                'stock_restaurado': stock_restaurado
            })
        
        # Redireccionar a la lista de pedidos
        return redirect('orders:todos_los_pedidos')  # Ajusta la URL según tu configuración
        
    except Exception as e:
        # En caso de error, hacer rollback automático y mostrar mensaje
        error_msg = f"Error al eliminar la venta: {str(e)}"
        messages.error(request, error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
        
        return redirect('orders:todos_los_pedidos')

@login_required
def confirmar_eliminar_venta(request, pedido_id):
    """
    Vista para mostrar la página de confirmación antes de eliminar
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Obtener información para mostrar en la confirmación
    context = {
        'pedido': pedido,
        'detalles_count': pedido.detalles.count(),
        'pagos_count': pedido.pagos.count(),
        'pagos_pendientes_count': sum(1 for pago in pedido.pagos.all() if hasattr(pago, 'pendiente_info')),
        'total_registros': pedido.detalles.count() + pedido.pagos.count() + 1  # +1 por el pedido mismo
    }
    
    return render(request, 'orders/pedidos/confirmar_eliminar_venta.html', context)




#####################RANKING DE VENTAS PRODUTUCTOS


def ranking_productos_view(request):
    """Vista principal para mostrar el formulario de selección de fechas"""
    return render(request, 'orders/pedidos/ranking_productos.html')

def ranking_productos_data(request):
    """API endpoint que devuelve los datos del ranking - VERSION CORREGIDA"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        # PASO 1: Convertir strings a fechas
        print(f"DEBUG - Fechas recibidas: {fecha_inicio} - {fecha_fin}")
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        print(f"DEBUG - Fechas convertidas: {fecha_inicio} - {fecha_fin}")
        
        # PASO 2: Verificar que existen datos
        total_detalles = DetallePedido.objects.count()
        print(f"DEBUG - Total DetallePedido en BD: {total_detalles}")
        
        if total_detalles == 0:
            return JsonResponse({
                'error': 'No hay datos de DetallePedido en la base de datos',
                'debug': 'La tabla DetallePedido está vacía'
            }, status=200)
        
        # PASO 3: Verificar filtro de fechas (corregido para timezone)
        detalles_en_rango = DetallePedido.objects.filter(
            pedido__fecha_creacion__date__range=[fecha_inicio, fecha_fin]
        ).count()
        print(f"DEBUG - DetallePedido en rango de fechas: {detalles_en_rango}")
        
        # PASO 4: Verificar filtro con estados CORREGIDOS
        detalles_con_estado = DetallePedido.objects.filter(
            pedido__fecha_creacion__date__range=[fecha_inicio, fecha_fin],
            pedido__estado__in=['completado'],  # ✅ Cambiado de 'entregado' a 'completado'
            estado__in=['Entregado', 'entregado', 'listo']  # ✅ Incluye ambas variantes
        ).count()
        print(f"DEBUG - DetallePedido con estados válidos: {detalles_con_estado}")
        
        if detalles_con_estado == 0:
            return JsonResponse({
                'ranking': [],
                'totales': {
                    'total_productos_vendidos': 0,
                    'valor_total_ventas': 0,
                    'numero_productos_diferentes': 0
                },
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
                'debug': f'No hay datos con estados válidos. Total en rango: {detalles_en_rango}'
            })
        
        # PASO 5: Verificar la consulta básica sin aggregation
        print("DEBUG - Ejecutando consulta básica...")
        queryset_basico = DetallePedido.objects.filter(
            pedido__fecha_creacion__date__range=[fecha_inicio, fecha_fin],
            pedido__estado__in=['completado'],  # ✅ Corregido
            estado__in=['Entregado', 'entregado', 'listo']  # ✅ Corregido
        ).select_related('producto', 'producto__categoria', 'pedido')
        
        # Verificar un registro
        primer_detalle = queryset_basico.first()
        if primer_detalle:
            print(f"DEBUG - Primer detalle encontrado: {primer_detalle.id}")
            print(f"DEBUG - Producto: {primer_detalle.producto.nombre if primer_detalle.producto else 'None'}")
            print(f"DEBUG - Cantidad: {primer_detalle.cantidad}")
            print(f"DEBUG - Subtotal: {primer_detalle.subtotal}")
            print(f"DEBUG - Estado pedido: {primer_detalle.pedido.estado}")
            print(f"DEBUG - Estado detalle: {primer_detalle.estado}")
        
        # PASO 6: Ejecutar la consulta con aggregation
        print("DEBUG - Ejecutando consulta con aggregation...")
        
        # ✅ Usar F() para el cálculo del subtotal en la BD
        from django.db.models import F
        
        ranking = queryset_basico.values(
            'producto__id',
            'producto__nombre',
            'producto__precio',
            'producto__categoria__nombre'
        ).annotate(
            total_vendido=Sum('cantidad'),
            valor_total=Sum(F('cantidad') * F('precio_unitario')),  # ✅ Cálculo en BD
            numero_pedidos=Count('pedido', distinct=True)
        ).order_by('-total_vendido')[:20]
        
        print(f"DEBUG - Número de productos en ranking: {len(ranking)}")
        
        # PASO 7: Procesar los resultados
        ranking_list = []
        for i, item in enumerate(ranking):
            try:
                print(f"DEBUG - Procesando item {i+1}: {item}")
                
                producto_data = {
                    'producto__id': item['producto__id'],
                    'producto__nombre': item['producto__nombre'] or 'Sin nombre',
                    'producto__precio': float(item['producto__precio']) if item['producto__precio'] is not None else 0,
                    'producto__categoria__nombre': item['producto__categoria__nombre'] or 'Sin categoría',
                    'total_vendido': item['total_vendido'] or 0,
                    'valor_total': float(item['valor_total']) if item['valor_total'] is not None else 0,
                    'numero_pedidos': item['numero_pedidos'] or 0
                }
                ranking_list.append(producto_data)
                
            except Exception as e:
                print(f"DEBUG - Error procesando item {i+1}: {str(e)}")
                print(f"DEBUG - Datos del item problemático: {item}")
                continue
        
        # Calcular totales generales
        totales = {
            'total_productos_vendidos': sum(item['total_vendido'] for item in ranking_list),
            'valor_total_ventas': sum(item['valor_total'] for item in ranking_list),
            'numero_productos_diferentes': len(ranking_list)
        }
        
        print(f"DEBUG - Totales calculados: {totales}")
        
        return JsonResponse({
            'ranking': ranking_list,
            'totales': totales,
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'debug': f'Consulta exitosa. Procesados {len(ranking_list)} productos'
        })
        
    except ValueError as e:
        print(f"DEBUG - Error de formato de fecha: {str(e)}")
        return JsonResponse({'error': f'Formato de fecha inválido: {str(e)}'}, status=400)
    except Exception as e:
        print(f"DEBUG - Error general: {str(e)}")
        print(f"DEBUG - Tipo de error: {type(e).__name__}")
        import traceback
        print(f"DEBUG - Traceback completo: {traceback.format_exc()}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}',
            'error_type': type(e).__name__,
            'debug': 'Ver logs del servidor para más detalles'
        }, status=500)
        
        
##########INFORMES DE PAGOS



def informe_pagos(request):
    desde = hasta = None
    resumen_mensual = []

    if request.method == 'GET':
        desde = request.GET.get('desde')
        hasta = request.GET.get('hasta')

        if desde and hasta:
            try:
                desde_dt = datetime.strptime(desde, "%Y-%m-%d")
                hasta_dt = datetime.strptime(hasta, "%Y-%m-%d")

                pagos = Pago.objects.filter(fecha__date__gte=desde_dt, fecha__date__lte=hasta_dt)

                # Agrupar por mes
                pagos_por_mes = (
                    pagos
                    .annotate(mes=TruncMonth('fecha'))
                    .values('mes')
                    .annotate(
                        total_venta=Sum('total_venta'),
                        total_costo=Sum('costo_total'),
                        total_ganancia=Sum('ganancia')
                    )
                    .order_by('mes')
                )

                # Convertir a lista legible
                for item in pagos_por_mes:
                    resumen_mensual.append({
                        'mes': item['mes'].strftime('%B %Y'),  # Ej: "Julio 2025"
                        'total_venta': item['total_venta'] or 0,
                        'total_costo': item['total_costo'] or 0,
                        'total_ganancia': item['total_ganancia'] or 0,
                    })
            except Exception as e:
                print(f"Error: {e}")

    return render(request, 'orders/pedidos/informe_pagos.html', {
        'resumen_mensual': resumen_mensual,
        'desde': desde,
        'hasta': hasta
    })

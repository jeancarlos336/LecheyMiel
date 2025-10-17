document.addEventListener('DOMContentLoaded', function() {
    // Debug inicial
    console.log("🟡 preparacion.js cargado. Ruta:", window.location.pathname);

    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Filtrar por estado
    document.getElementById('btn-pendientes')?.addEventListener('click', function(e) {
        e.preventDefault();
        togglePedidosFilter('pendientes');
    });

    document.getElementById('btn-en-proceso')?.addEventListener('click', function(e) {
        e.preventDefault();
        togglePedidosFilter('en_preparacion');
    });

    document.getElementById('btn-listo')?.addEventListener('click', function(e) {
        e.preventDefault();
        togglePedidosFilter('listo');
    });

    // Actualizar estado del ítem
    document.querySelectorAll('.btn-cambiar-estado').forEach(btn => {
        btn.addEventListener('click', cambiarEstadoItem);
    });

    // Temporizadores para pedidos
    actualizarTemporizadores();
    setInterval(actualizarTemporizadores, 1000);

    // 🚀 SISTEMA DE ACTUALIZACIÓN AUTOMÁTICA SOLO PARA /preparacion/
    configurarActualizacionAutomatica();
});

// ✅ FUNCIÓN PRINCIPAL PARA LA ACTUALIZACIÓN AUTOMÁTICA (SOLO PREPARACIÓN)
function configurarActualizacionAutomatica() {
    try {
        const path = window.location.pathname.toLowerCase();
        console.log("🔍 Verificando actualización automática para:", path);

        // 🎯 VERIFICACIÓN ESPECÍFICA: SOLO activar en /pedidos/preparacion/
        const esRutaPreparacion = path === '/pedidos/preparacion/' || 
                                 path === '/pedidos/preparacion' ||
                                 path.endsWith('/preparacion/') ||
                                 path.endsWith('/preparacion');
        
        if (!esRutaPreparacion) {
            console.log("🚫 ACTUALIZACIÓN AUTOMÁTICA DESACTIVADA - No es ruta de preparación");
            console.log("   - Ruta actual:", path);
            console.log("   - Ruta requerida: /pedidos/preparacion/");
            
            // Cancelar cualquier timeout existente
            if (window.pageRefreshTimeout) {
                clearTimeout(window.pageRefreshTimeout);
                window.pageRefreshTimeout = null;
            }
            
            return;
        }

        // ✅ VERIFICACIÓN ADICIONAL: Asegurar que no hay banderas de protección activas
        const tieneProteccionActiva = window.isVentaExpress === true || 
                                     window.isTomarPedido === true || 
                                     window.isCrearPedidoParaLlevar === true || 
                                     window.preventRefresh === true;

        if (tieneProteccionActiva) {
            console.log("🚫 ACTUALIZACIÓN AUTOMÁTICA DESACTIVADA - Protección activa");
            console.log("   - Protección activa:", tieneProteccionActiva);
            
            // Cancelar cualquier timeout existente
            if (window.pageRefreshTimeout) {
                clearTimeout(window.pageRefreshTimeout);
                window.pageRefreshTimeout = null;
            }
            
            window.isPageProtected = true;
            return;
        }

        // ✅ CONFIGURAR ACTUALIZACIÓN SOLO PARA /pedidos/preparacion/
        const TIEMPO_REFRESH = 30000; // 30 segundos
        console.log(`🔄 Configurando actualización automática para /pedidos/preparacion/ (${TIEMPO_REFRESH/1000} segundos)`);
        
        // Cancelar timeout previo si existe
        if (window.pageRefreshTimeout) {
            clearTimeout(window.pageRefreshTimeout);
            console.log("   ⚠️ Timeout anterior cancelado");
        }
        
        // ⏰ Mostrar cuenta regresiva en consola cada 10 segundos
        const tiempoInicio = Date.now();
        window.pageRefreshTimeout = setTimeout(() => {
            // Verificación final antes de recargar
            const pathActual = window.location.pathname.toLowerCase();
            const sigueEnPreparacion = pathActual === '/pedidos/preparacion/' || 
                                      pathActual === '/pedidos/preparacion' ||
                                      pathActual.endsWith('/preparacion/') ||
                                      pathActual.endsWith('/preparacion');
            
            if (!sigueEnPreparacion) {
                console.log("🛡️ Recarga cancelada - Ya no está en /pedidos/preparacion/");
                return;
            }
            
            if (window.isPageProtected) {
                console.log("🛡️ Recarga cancelada por protección de última hora");
                return;
            }
            
            console.log("🔄 Ejecutando recarga automática en /pedidos/preparacion/...");
            window.location.reload();
        }, TIEMPO_REFRESH);

        console.log("✅ Actualización automática configurada correctamente");
        console.log(`   ⏰ Próxima recarga en ${TIEMPO_REFRESH/1000} segundos`);
        console.log(`   🆔 Timeout ID: ${window.pageRefreshTimeout}`);
        
        // Contador visual en consola
        const intervalo = setInterval(() => {
            const transcurrido = Math.floor((Date.now() - tiempoInicio) / 1000);
            const restante = Math.floor(TIEMPO_REFRESH/1000) - transcurrido;
            
            if (restante <= 0 || !window.pageRefreshTimeout) {
                clearInterval(intervalo);
                return;
            }
            
            if (restante % 10 === 0) {
                console.log(`⏰ Auto-refresh en ${restante} segundos...`);
            }
        }, 1000);

    } catch (error) {
        console.error("❌ Error al configurar actualización automática:", error);
    }
}

// ✅ FUNCIÓN PARA CANCELAR MANUALMENTE LA ACTUALIZACIÓN
function cancelarActualizacionAutomatica(motivo = "Manual") {
    if (window.pageRefreshTimeout) {
        clearTimeout(window.pageRefreshTimeout);
        window.pageRefreshTimeout = null;
        console.log(`🛑 Actualización automática cancelada: ${motivo}`);
    }
    window.isPageProtected = true;
}

// ✅ FUNCIÓN PARA REACTIVAR LA ACTUALIZACIÓN (si es necesario)
function reactivarActualizacionAutomatica() {
    window.isPageProtected = false;
    configurarActualizacionAutomatica();
    console.log("🔄 Actualización automática reactivada");
}

// Funciones auxiliares
function togglePedidosFilter(estado) {
    const cards = document.querySelectorAll('.pedido-card');
    const botones = document.querySelectorAll('.btn-group a');

    botones.forEach(btn => btn.classList.remove('active'));
    
    cards.forEach(card => {
        // Solo mostrar tarjetas que están visibles (no ocultas por completado)
        if (card.style.display === 'none' && card.dataset.completado === 'true') {
            return; // Mantener ocultas las tarjetas completadas
        }
        
        if (estado === 'pendientes') {
            card.style.display = '';
        } else {
            card.style.display = card.dataset.estado === estado ? '' : 'none';
        }
    });

    document.getElementById(`btn-${estado.replace('_', '-')}`)?.classList.add('active');
}

// 🌟 FUNCIÓN MEJORADA: cambiarEstadoItem CON PRESERVACIÓN DEL TIMEOUT
async function cambiarEstadoItem(e) {
    e.preventDefault();
    
    // 🔒 NO cancelar el timeout - solo informar que estamos actualizando
    console.log("📝 Actualizando estado de ítem (timeout preservado)...");
    
    const btn = e.currentTarget;
    const itemId = btn.dataset.itemId;
    const nuevoEstado = btn.dataset.estado;
    const itemRow = btn.closest('.item-row');
    
    try {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            mostrarNotificacion('error', 'Error de autenticación');
            return;
        }

        const response = await fetch('/pedidos/actualizar-estado/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                item_id: itemId,
                estado: nuevoEstado
            })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP! estado: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Actualizar la interfaz del ítem individual
            const badge = itemRow.querySelector('.estado-badge');
            
            // Resetear clases del badge
            badge.className = 'badge estado-badge';
            
            // 🔥 IMPORTANTE: Usar el estado_real que devuelve el backend (no el que enviamos)
            const estadoReal = data.estado_real || nuevoEstado;
            
            // Añadir clase según el estado REAL (el que está en la BD)
            const clasesEstado = {
                'pendiente': 'bg-secondary',
                'en_preparacion': 'bg-warning',
                'listo': 'bg-success',
                'entregado': 'bg-primary',
                'cancelado': 'bg-danger'
            };
            badge.classList.add(clasesEstado[estadoReal] || 'bg-secondary');
            badge.textContent = data.nuevo_estado;
            
            // 🎯 Actualizar el data-estado del row para que la verificación funcione
            itemRow.dataset.estado = estadoReal;

            console.log(`📝 Estado actualizado - Solicitado: ${nuevoEstado}, Real: ${estadoReal}, Display: ${data.nuevo_estado}`);

            // Actualizar botones del ítem basado en el estado REAL
            const btns = itemRow.querySelectorAll('.btn-cambiar-estado');
            btns.forEach(btn => {
                btn.disabled = false;
                
                // Deshabilitar según el estado real
                if (estadoReal === 'en_preparacion' && btn.dataset.estado === 'en_preparacion') {
                    btn.disabled = true;
                } else if (estadoReal === 'listo' || estadoReal === 'entregado') {
                    // Si está listo o entregado, deshabilitar todos los botones
                    btn.disabled = true;
                } else if (estadoReal === 'cancelado') {
                    btn.disabled = true;
                }
            });

            // Mostrar notificación diferente si fue auto-entregado
            if (data.es_automatico && estadoReal === 'entregado') {
                mostrarNotificacion('success', `✅ ${data.area}: Producto marcado como entregado automáticamente`);
            } else {
                mostrarNotificacion('success', 'Estado actualizado correctamente');
            }
            
            // ✨ NUEVA LÓGICA: Verificar si todos los ítems del pedido están listos/entregados
            verificarYOcultarPedidoCompleto(itemRow);
            
            // 🔄 Reactivar actualización automática después de 3 segundos
            setTimeout(() => {
                const pathActual = window.location.pathname.toLowerCase();
                const sigueEnPreparacion = pathActual === '/pedidos/preparacion/' || 
                                          pathActual === '/pedidos/preparacion' ||
                                          pathActual.endsWith('/preparacion/') ||
                                          pathActual.endsWith('/preparacion');
                
                if (!window.isPageProtected && sigueEnPreparacion) {
                    reactivarActualizacionAutomatica();
                }
            }, 3000);
            
        } else {
            mostrarNotificacion('error', data.error || 'Error al actualizar el estado');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('error', 'Error de conexión');
    }
}

// 🌟 NUEVA FUNCIÓN: Verificar si todos los ítems están listos y ocultar el pedido
function verificarYOcultarPedidoCompleto(itemRow) {
    try {
        // Obtener la tarjeta del pedido completo
        const pedidoCard = itemRow.closest('.pedido-card');
        
        if (!pedidoCard) {
            console.warn("⚠️ No se encontró la tarjeta del pedido");
            return;
        }
        
        // Obtener todos los ítems del pedido
        const todosLosItems = pedidoCard.querySelectorAll('.item-row');
        
        if (todosLosItems.length === 0) {
            console.warn("⚠️ No se encontraron ítems en el pedido");
            return;
        }
        
        // 🔍 DEBUG: Mostrar información detallada de cada ítem
        console.log("🔍 Verificando estados de ítems:");
        Array.from(todosLosItems).forEach((row, index) => {
            const badge = row.querySelector('.estado-badge');
            const botonesEstado = row.querySelectorAll('.btn-cambiar-estado');
            
            console.log(`\n   📦 Item ${index + 1}:`);
            console.log(`      - Badge texto: "${badge?.textContent || 'SIN BADGE'}"`);
            console.log(`      - Badge clases: ${badge?.className || 'N/A'}`);
            console.log(`      - HTML completo:`, row.outerHTML.substring(0, 200) + '...');
            
            // Verificar botones deshabilitados (indica estado listo)
            botonesEstado.forEach(btn => {
                console.log(`      - Botón ${btn.dataset.estado}: ${btn.disabled ? 'DESHABILITADO' : 'habilitado'}`);
            });
        });
        
        // ESTRATEGIA DE VERIFICACIÓN MÚLTIPLE:
        const todosListos = Array.from(todosLosItems).every(row => {
            const badge = row.querySelector('.estado-badge');
            if (!badge) {
                console.log("   ❌ Badge no encontrado en un ítem");
                return false;
            }
            
            // 1. Verificar por data-estado del row (MÉTODO MÁS CONFIABLE)
            const estadoData = row.dataset.estado;
            const porDataAttr = estadoData === 'listo' || estadoData === 'entregado' || estadoData === 'cancelado';
            
            // 2. Verificar por texto del badge
            const textoEstado = badge.textContent.trim().toLowerCase();
            const porTexto = textoEstado.includes('listo') || 
                            textoEstado.includes('entregado') || 
                            textoEstado.includes('cancelado');
            
            // 3. Verificar por clases CSS
            const porClase = badge.classList.contains('bg-success') || 
                           badge.classList.contains('bg-primary') || 
                           badge.classList.contains('bg-danger');
            
            // 4. Verificar por botones deshabilitados (todos deshabilitados = completado)
            const botones = row.querySelectorAll('.btn-cambiar-estado:not([data-estado="cancelado"])');
            const botonesAccionDeshabilitados = Array.from(botones).every(btn => btn.disabled);
            
            const resultado = porDataAttr || porTexto || porClase || botonesAccionDeshabilitados;
            
            console.log(`\n   ✓ Validación para item (ID: ${row.dataset.itemId || 'N/A'}):`);
            console.log(`      - Estado data-attr: "${estadoData}" → ${porDataAttr}`);
            console.log(`      - Por texto: "${textoEstado}" → ${porTexto}`);
            console.log(`      - Por clase CSS → ${porClase}`);
            console.log(`      - Por botones deshabilitados → ${botonesAccionDeshabilitados}`);
            console.log(`      - 🎯 RESULTADO FINAL: ${resultado ? '✅ COMPLETADO' : '⏳ PENDIENTE'}`);
            
            return resultado;
        });
        
        console.log(`\n📊 RESULTADO FINAL DEL PEDIDO: ${todosListos ? '✅ COMPLETO' : '⏳ PENDIENTE'}`);
        console.log(`   - Total ítems: ${todosLosItems.length}`);
        
        // Si todos están listos, ocultar la tarjeta con animación
        if (todosListos) {
            console.log("\n✨ ¡Pedido completado! Iniciando proceso de ocultamiento...");
            
            // Marcar como completado para el filtro
            pedidoCard.dataset.completado = 'true';
            
            // Agregar clase de animación
            pedidoCard.style.transition = 'all 0.5s ease-out';
            pedidoCard.style.opacity = '0';
            pedidoCard.style.transform = 'scale(0.95)';
            
            // Mostrar notificación
            mostrarNotificacion('success', '🎉 ¡Pedido completado y listo para entregar!');
            
            // Ocultar después de la animación
            setTimeout(() => {
                pedidoCard.style.display = 'none';
                console.log("✅ Tarjeta del pedido ocultada exitosamente");
                
                // Verificar si quedan pedidos visibles
                verificarPedidosVisibles();
            }, 500);
        } else {
            console.log("\n⏸️ Pedido aún tiene ítems pendientes, no se ocultará");
        }
    } catch (error) {
        console.error("❌ Error al verificar pedido completo:", error);
        console.error("Stack trace:", error.stack);
    }
}

// 🌟 NUEVA FUNCIÓN: Verificar si quedan pedidos visibles
function verificarPedidosVisibles() {
    const todasLasTarjetas = document.querySelectorAll('.pedido-card');
    const tarjetasVisibles = Array.from(todasLasTarjetas).filter(card => {
        return card.style.display !== 'none';
    });
    
    console.log(`📋 Pedidos visibles: ${tarjetasVisibles.length} de ${todasLasTarjetas.length}`);
    
    if (tarjetasVisibles.length === 0) {
        // Opcional: Mostrar mensaje de "No hay pedidos pendientes"
        mostrarMensajeSinPedidos();
    }
}

// 🌟 NUEVA FUNCIÓN: Mostrar mensaje cuando no hay pedidos
function mostrarMensajeSinPedidos() {
    const contenedor = document.querySelector('.main-content') || document.querySelector('.container');
    
    if (!contenedor) return;
    
    // Verificar si ya existe el mensaje
    if (document.getElementById('mensaje-sin-pedidos')) return;
    
    const mensaje = document.createElement('div');
    mensaje.id = 'mensaje-sin-pedidos';
    mensaje.className = 'alert alert-info text-center mt-4';
    mensaje.innerHTML = `
        <h4>🎉 ¡Excelente trabajo!</h4>
        <p class="mb-0">No hay pedidos pendientes en este momento.</p>
    `;
    
    contenedor.appendChild(mensaje);
    
    console.log("📢 Mensaje de 'sin pedidos' mostrado");
}

function getCSRFToken() {
    // Buscar en meta tag
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) return csrfMeta.content;
    
    // Buscar en input hidden
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) return csrfInput.value;
    
    // Buscar en cookies (último recurso)
    const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (cookieMatch) return cookieMatch[1];
    
    console.error('CSRF token no encontrado');
    return null;
}

function getEstadoClass(estado) {
    const clases = {
        'pendiente': 'bg-secondary',
        'en_preparacion': 'bg-warning',
        'listo': 'bg-success',
        'entregado': 'bg-primary',
        'cancelado': 'bg-danger'
    };
    return clases[estado] || 'bg-secondary';
}

function actualizarBotonesEstado(itemRow, nuevoEstado) {
    const btns = itemRow.querySelectorAll('.btn-cambiar-estado');
    
    btns.forEach(btn => {
        btn.disabled = false;
        
        if (nuevoEstado === 'en_preparacion') {
            if (btn.dataset.estado === 'en_preparacion') btn.disabled = true;
        } else if (nuevoEstado === 'listo') {
            if (btn.dataset.estado !== 'entregado') btn.disabled = true;
        } else if (nuevoEstado === 'cancelado') {
            btn.disabled = true;
        }
    });
}

function actualizarTemporizadores() {
    const ahora = new Date();

    document.querySelectorAll('.timer-cell').forEach(cell => {
        const startTimeStr = cell.dataset.startTime;
        if (!startTimeStr) return;

        const startTime = new Date(startTimeStr);
        const diffMs = ahora - startTime;
        const diffMin = Math.floor(diffMs / 60000);
        const diffSeg = Math.floor((diffMs % 60000) / 1000);

        const texto = `${diffMin}m ${diffSeg}s`;
        cell.textContent = texto;

        // ⚠️ Cambia estilo si supera 30 minutos
        if (diffMin >= 30) {
            cell.classList.add('text-danger', 'fw-bold');
        } else {
            cell.classList.remove('text-danger', 'fw-bold');
        }
    });
}

function mostrarNotificacion(tipo, mensaje) {
    // Usar Toastr si está disponible, si no, alert nativo
    if (typeof toastr !== 'undefined') {
        toastr[tipo](mensaje);
    } else {
        alert(mensaje);
    }
}

// 🚀 FUNCIONES GLOBALES DISPONIBLES PARA USO MANUAL
window.cancelarActualizacionAutomatica = cancelarActualizacionAutomatica;
window.reactivarActualizacionAutomatica = reactivarActualizacionAutomatica;
window.verificarYOcultarPedidoCompleto = verificarYOcultarPedidoCompleto;
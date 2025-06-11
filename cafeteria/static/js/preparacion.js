document.addEventListener('DOMContentLoaded', function() {
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

    // Actualización automática de la página (excepto en páginas protegidas)
    try {
        const path = window.location.pathname.toLowerCase();

        const rutasProtegidas = [
            '/venta-express',
            '/pedidos/tomar-pedido',
            '/pedidos/crear-pedido-para-llevar'
        ];

        const esRutaProtegida = rutasProtegidas.some(ruta => path.startsWith(ruta));

        if (!esRutaProtegida) {
            console.log("🔄 La página se actualizará automáticamente en 30 segundos");
            setTimeout(() => {
                window.location.reload();
            }, 45000);
        } else {
            console.log("🔒 Actualización automática desactivada para:", path);
        }
    } catch (error) {
        console.error("❌ Error al verificar la ruta protegida:", error);
    }
});

// Funciones auxiliares
function togglePedidosFilter(estado) {
    const cards = document.querySelectorAll('.pedido-card');
    const botones = document.querySelectorAll('.btn-group a');

    botones.forEach(btn => btn.classList.remove('active'));
    
    cards.forEach(card => {
        if (estado === 'pendientes') {
            card.style.display = '';
        } else {
            card.style.display = card.dataset.estado === estado ? '' : 'none';
        }
    });

    document.getElementById(`btn-${estado.replace('_', '-')}`)?.classList.add('active');
}

// Reemplaza la función cambiarEstadoItem con esta versión corregida
async function cambiarEstadoItem(e) {
    e.preventDefault();
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
            // Actualizar la interfaz manualmente
            const badge = itemRow.querySelector('.estado-badge');
            
            // Resetear clases del badge
            badge.className = 'badge estado-badge';
            
            // Añadir clase según el estado
            const clasesEstado = {
                'pendiente': 'bg-secondary',
                'en_preparacion': 'bg-warning',
                'listo': 'bg-success',
                'entregado': 'bg-primary',
                'cancelado': 'bg-danger'
            };
            badge.classList.add(clasesEstado[nuevoEstado] || 'bg-secondary');
            badge.textContent = data.nuevo_estado;

            // Actualizar botones
            const btns = itemRow.querySelectorAll('.btn-cambiar-estado');
            btns.forEach(btn => {
                btn.disabled = false;
                if (nuevoEstado === 'en_preparacion' && btn.dataset.estado === 'en_preparacion') {
                    btn.disabled = true;
                } else if (nuevoEstado === 'listo') {
                    btn.disabled = true;
                } else if (nuevoEstado === 'cancelado') {
                    btn.disabled = true;
                }
            });

            mostrarNotificacion('success', 'Estado actualizado correctamente');
        } else {
            mostrarNotificacion('error', data.error || 'Error al actualizar el estado');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('error', 'Error de conexión');
    }
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
    document.querySelectorAll('.timer-cell').forEach(timer => {
        const startTime = new Date(timer.dataset.startTime);
        const now = new Date();
        const diff = Math.floor((now - startTime) / 1000); // diferencia en segundos
        
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const seconds = diff % 60;
        
        timer.textContent = 
            (hours > 0 ? hours + 'h ' : '') + 
            (minutes > 0 ? minutes + 'm ' : '') + 
            seconds + 's';
        
        // Marcar como urgente si lleva más de 15 minutos (900 segundos)
        if (diff > 900) {
            const card = timer.closest('.pedido-card');
            if (card) {
                card.classList.add('urgent');
                card.style.borderLeft = '4px solid #dc3545';
            }
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



function actualizarTemporizadores() {
    const ahora = new Date();

    document.querySelectorAll('.timer-cell').forEach(cell => {
        const startTimeStr = cell.dataset.startTime;
        if (!startTimeStr) return; // Previene errores si falta el dato

        const startTime = new Date(startTimeStr);
        const diffMs = ahora - startTime;
        const diffMin = Math.floor(diffMs / 60000); // Diferencia en minutos
        const diffSeg = Math.floor((diffMs % 60000) / 1000); // Segundos restantes

        const texto = `${diffMin}m ${diffSeg}s`;
        cell.textContent = texto;

        // ⚠️ Cambia estilo si supera 30 minutos
        if (diffMin >= 30) {
            cell.classList.add('text-danger', 'fw-bold'); // resalta en rojo y negrita
        } else {
            cell.classList.remove('text-danger', 'fw-bold');
        }
    });
}

actualizarTemporizadores(); // Ejecutar una vez al cargar
setInterval(actualizarTemporizadores, 1000); // Luego cada segundo


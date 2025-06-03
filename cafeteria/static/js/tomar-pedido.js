/**
 * Tomar Pedido - JavaScript optimizado
 * Funcionalidades principales para la gestión de pedidos
 */

// =============================================
// CONFIGURACIÓN Y SEGURIDAD
// =============================================

// Inicialización de medidas de seguridad
(function initSecurity() {
    console.log("🔒 Tomar Pedido - Inicializando medidas de seguridad");
    
    // Configurar flags de seguridad
    window.disableActivityUpdates = true;
    window.isTomarPedido = true;
    window.preventRefresh = true;
    
    // Limpiar timeout de actividad existente
    if (window.activityTimeout) {
        clearTimeout(window.activityTimeout);
        console.log("🛑 Timeout de actividad limpiado");
    }
    
    // Bloquear función de actualización de actividad
    if (typeof window.updateUserActivity === 'function') {
        window.originalUpdateUserActivity = window.updateUserActivity;
        window.updateUserActivity = function() {
            console.log("🛑 Bloqueado intento de actualización en Tomar Pedido");
            return Promise.resolve();
        };
    }
    
    // Remover event listeners de actividad
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    activityEvents.forEach(event => {
        if (window.handleUserActivity) {
            document.removeEventListener(event, window.handleUserActivity);
        }
    });
})();

// =============================================
// VARIABLES GLOBALES
// =============================================

let currentProductId = null;
let currentProductName = '';
let searchTimeout = null;

// =============================================
// UTILIDADES
// =============================================

/**
 * Obtiene el token CSRF del formulario
 */
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

/**
 * Maneja errores de fetch con SweetAlert
 */
function handleFetchError(error, defaultMessage = 'Ocurrió un error inesperado') {
    console.error('Error:', error);
    Swal.fire('Error', defaultMessage, 'error');
}

/**
 * Muestra notificación toast
 */
function showToast(icon, title, timer = 2000) {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: timer,
        timerProgressBar: true
    });
    
    Toast.fire({ icon, title });
}

/**
 * Añade clase de animación temporal
 */
function addTempClass(element, className, duration = 300) {
    if (element) {
        element.classList.add(className);
        setTimeout(() => element.classList.remove(className), duration);
    }
}

// =============================================
// GESTIÓN DE CATEGORÍAS
// =============================================

/**
 * Activa una categoría específica
 */
function activateCategory(categoriaId) {
    // Ocultar todos los productos
    document.querySelectorAll('.categoria-productos').forEach(el => {
        el.style.display = 'none';
    });

    // Desactivar todos los botones
    document.querySelectorAll('.categoria-btn').forEach(el => {
        el.classList.remove('active');
    });

    // Mostrar productos de la categoría seleccionada
    const productos = document.getElementById(`categoria-${categoriaId}`);
    if (productos) {
        productos.style.display = 'block';
        localStorage.setItem('categoriaActiva', categoriaId);
        
        // Actualizar título
        updateCategoryTitle(categoriaId);
    }

    // Activar botón actual
    const currentBtn = document.querySelector(`.categoria-btn[data-categoria="${categoriaId}"]`);
    if (currentBtn) {
        currentBtn.classList.add('active');
    }
}

/**
 * Actualiza el título de la categoría
 */
function updateCategoryTitle(categoriaId) {
    const categoryTitle = document.getElementById('category-title');
    const activeBtn = document.querySelector(`.categoria-btn[data-categoria="${categoriaId}"]`);
    
    if (categoryTitle && activeBtn) {
        categoryTitle.textContent = categoriaId === 'all' 
            ? 'Todos los productos' 
            : activeBtn.textContent.trim();
    }
}

// =============================================
// BÚSQUEDA DE PRODUCTOS
// =============================================

/**
 * Realiza búsqueda de productos con filtrado
 */
function searchProducts(query) {
    const normalizedQuery = query.toLowerCase().trim();
    const allProducts = document.querySelectorAll('.producto-item');
    
    if (normalizedQuery === '') {
        allProducts.forEach(product => {
            product.style.display = 'flex';
        });
        return;
    }
    
    let hasResults = false;
    allProducts.forEach(product => {
        const productName = product.dataset.nombre;
        if (productName && productName.includes(normalizedQuery)) {
            product.style.display = 'flex';
            hasResults = true;
        } else {
            product.style.display = 'none';
        }
    });
    
    if (!hasResults) {
        showToast('info', 'No se encontraron productos', 1500);
    }
}

// =============================================
// GESTIÓN DE MODAL DE NOTAS
// =============================================

/**
 * Abre el modal para agregar notas a productos
 */
function openNoteModal(productId, productName) {
    currentProductId = productId;
    currentProductName = productName;
        
    const modal = document.getElementById('noteModal');
    const title = document.getElementById('noteModalTitle');
    const input = document.getElementById('noteInput');
    
    if (!modal || !title || !input) {
        console.error('Elementos del modal no encontrados');
        return;
    }
        
    title.textContent = `Agregar nota - ${productName}`;
    input.value = '';
    input.focus();
    modal.style.display = 'block';
}

/**
 * Cierra el modal de notas
 */
function closeNoteModal() {
    const modal = document.getElementById('noteModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentProductId = null;
    currentProductName = '';
    
    // Restaurar botón de confirmación
    const confirmBtn = document.querySelector('.btn-confirm');
    if (confirmBtn) {
        confirmBtn.textContent = 'Agregar';
        confirmBtn.onclick = confirmNote;
    }
}

/**
 * Confirma y guarda la nota del producto
 */
function confirmNote() {
    const noteInput = document.getElementById('noteInput');
    if (!noteInput) {
        console.error('Input de nota no encontrado');
        return;
    }
    
    const note = noteInput.value.trim();
        
    if (currentProductId) {
        const notasInput = document.getElementById(`notas-${currentProductId}`);
        if (notasInput) {
            notasInput.value = note;
        }
            
        if (note) {
            showToast('success', `Nota agregada a ${currentProductName}`, 1500);
        }
    }
        
    closeNoteModal();
}

/**
 * Edita nota existente en el carrito
 */
function editNote(detalleId, currentNote, productName) {
    const modal = document.getElementById('noteModal');
    const title = document.getElementById('noteModalTitle');
    const input = document.getElementById('noteInput');
    
    title.textContent = `Nota para ${productName}`;
    input.value = currentNote === '[Agregar nota]' ? '' : currentNote;
    input.focus();
    modal.style.display = 'block';
    
    const confirmBtn = document.querySelector('.btn-confirm');
    confirmBtn.textContent = currentNote ? 'Actualizar' : 'Agregar';
    confirmBtn.onclick = function() {
        updateNote(detalleId);
    };
}

/**
 * Actualiza nota existente vía AJAX
 */
function updateNote(detalleId) {
    const noteInput = document.getElementById('noteInput');
    const note = noteInput.value.trim();
    const csrfToken = getCsrfToken();
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 'all';
    
    const formData = new URLSearchParams({
        action: 'update_note',
        detalle_id: detalleId,
        notas: note,
        categoria_activa: categoriaActiva
    });
    
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al actualizar la nota');
    })
    .finally(() => {
        closeNoteModal();
    });
}

// =============================================
// GESTIÓN DE CANTIDADES Y CARRITO
// =============================================

/**
 * Actualiza la cantidad de un producto en el carrito
 */
function updateCantidad(detalleId, action) {
    const cantidadElement = document.querySelector(`.quantity-value[data-detalle-id="${detalleId}"]`);
    if (!cantidadElement) return;

    let cantidad = parseInt(cantidadElement.textContent);
    if (isNaN(cantidad)) return;

    // Calcular nueva cantidad
    if (action === 'incrementar') {
        cantidad += 1;
    } else if (action === 'decrementar' && cantidad > 1) {
        cantidad -= 1;
    } else {
        return;
    }

    // Actualización optimista
    cantidadElement.textContent = cantidad;
    addTempClass(cantidadElement, 'pulse');

    const csrfToken = getCsrfToken();
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 'all';

    const formData = new URLSearchParams({
        action: 'update_cantidad',
        detalle_id: detalleId,
        cantidad: cantidad,
        categoria_activa: categoriaActiva
    });

    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: formData.toString()
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.success) {
            updateCartTotals(detalleId, data);
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al actualizar la cantidad');
        // Revertir cambio en caso de error
        setTimeout(() => window.location.reload(), 1000);
    });
}

/**
 * Actualiza los totales del carrito después de cambios
 */
function updateCartTotals(detalleId, data) {
    // Actualizar subtotal
    const subtotalElement = document.querySelector(`.cart-item-price[data-detalle-id="${detalleId}"]`);
    if (subtotalElement && data.subtotal) {
        subtotalElement.textContent = `$${parseFloat(data.subtotal).toFixed(0)}`;
        addTempClass(subtotalElement, 'pulse');
    }

    // Actualizar total
    const totalElement = document.querySelector('.total-amount');
    if (totalElement && data.total) {
        totalElement.textContent = `$${parseFloat(data.total).toFixed(0)}`;
        addTempClass(totalElement, 'pulse');
    }
}

/**
 * Elimina un producto del carrito
 */
function removeProduct(detalleId) {
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 'all';
    const csrfToken = getCsrfToken();
    
    const formData = new URLSearchParams({
        action: 'remove_producto',
        detalle_id: detalleId,
        categoria_activa: categoriaActiva
    });
    
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            window.location.reload();
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al eliminar el producto');
    });
}


// =============================================
// GESTIÓN DE CLIENTE
// =============================================

/**
 * Guarda el nombre del cliente
 */
function saveClientName() {
    const nombreCliente = document.getElementById('nombre_cliente').value.trim();
    const csrfToken = getCsrfToken();
    
    const formData = new URLSearchParams({
        action: 'actualizar_cliente',
        nombre_cliente: nombreCliente
    });
    
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.ok) {
            showToast('success', 'Nombre del cliente guardado', 1500);
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al guardar el nombre');
    });
}

// =============================================
// EVENT LISTENERS E INICIALIZACIÓN
// =============================================

/**
 * Inicializa todos los event listeners cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Tomar Pedido - Inicializando interfaz");
    
    // ==========================================
    // GESTIÓN DE CATEGORÍAS
    // ==========================================
    
    // Event listeners para botones de categoría
    const categoriaBtns = document.querySelectorAll('.categoria-btn');
    categoriaBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const categoriaId = this.dataset.categoria;
            if (categoriaId) {
                activateCategory(categoriaId);
            }
        });
    });

    // Mostrar categoría guardada o todas por defecto
    const categoriaGuardada = localStorage.getItem('categoriaActiva') || 'all';
    activateCategory(categoriaGuardada);
    
    // ==========================================
    // BÚSQUEDA DE PRODUCTOS
    // ==========================================
    
    // Event listener para búsqueda con debounce
    const searchInput = document.getElementById('producto-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchProducts(this.value);
            }, 300);
        });
    }
    
    // ==========================================
    // EVENT DELEGATION PRINCIPAL
    // ==========================================
    
    // Delegación de eventos para botones dinámicos
    document.addEventListener('click', function(e) {
        // Incrementar cantidad
        if (e.target.closest('.incrementar')) {
            const detalleId = e.target.closest('.incrementar').dataset.detalleId;
            if (detalleId) {
                updateCantidad(detalleId, 'incrementar');
            }
        }
        
        // Decrementar cantidad
        if (e.target.closest('.decrementar')) {
            const detalleId = e.target.closest('.decrementar').dataset.detalleId;
            if (detalleId) {
                updateCantidad(detalleId, 'decrementar');
            }
        }
        
        // Eliminar producto con confirmación
        if (e.target.closest('.remove-btn')) {
            e.preventDefault();
            const detalleId = e.target.closest('.remove-btn').dataset.detalleId;
            
            if (detalleId) {
                Swal.fire({
                    title: '¿Eliminar producto?',
                    text: "¿Estás seguro de que quieres eliminar este producto del carrito?",
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#dc3545',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, eliminar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        removeProduct(detalleId);
                    }
                });
            }
        }
        
        // Cerrar modal al hacer clic fuera
        const modal = document.getElementById('noteModal');
        if (e.target === modal) {
            closeNoteModal();
        }
        
        // Guardar nombre del cliente
        if (e.target.id === 'guardar-cliente') {
            saveClientName();
        }
    });
    
    // ==========================================
    // FEEDBACK VISUAL PARA BOTONES
    // ==========================================
    
    // Animación para botones de agregar producto
    document.querySelectorAll('.add-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const originalHTML = this.innerHTML;
            const originalBgColor = this.style.backgroundColor;
            
            // Cambiar a estado de éxito
            this.innerHTML = '<i class="fas fa-check"></i>';
            this.style.backgroundColor = '#28a745';
            
            setTimeout(() => {
                this.innerHTML = originalHTML;
                this.style.backgroundColor = originalBgColor;
            }, 1000);
            
            showToast('success', 'Producto agregado');
        });
    });
    
    // ==========================================
    // EVENTOS DE TECLADO
    // ==========================================
    
    document.addEventListener('keydown', function(e) {
        // Cerrar modal con ESC
        if (e.key === 'Escape') {
            closeNoteModal();
        }
    });
    
    // Confirmar nota con Enter en el input
    const noteInput = document.getElementById('noteInput');
    if (noteInput) {
        noteInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                confirmNote();
            }
        });
    }
    
    console.log("✅ Tomar Pedido - Interfaz inicializada correctamente");
});

// =============================================
// FUNCIONES GLOBALES EXPUESTAS
// =============================================

// Exponer funciones principales al scope global para uso en templates
window.TomarPedido = {
    openNoteModal,
    closeNoteModal,
    confirmNote,
    editNote,
    updateNote,
    activateCategory,
    searchProducts,
    updateCantidad,
    removeProduct,
    saveClientName,
    showToast
};

console.log("📦 Tomar Pedido JS - Módulo cargado completamente");
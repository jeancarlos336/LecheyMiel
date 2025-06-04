/**
 * Tomar Pedido Para Llevar - JavaScript optimizado
 * Funcionalidades principales para la gestión de pedidos para llevar
 */

// =============================================
// CONFIGURACIÓN Y SEGURIDAD
// =============================================

// Inicialización de medidas de seguridad
(function initSecurity() {
    console.log("🔒 Crear Pedido Para Llevar - Inicializando medidas de seguridad");
    
    // Configurar flags de seguridad
    window.disableActivityUpdates = true;
    window.isCrearPedidoParaLlevar = true;
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
            console.log("🛑 Bloqueado intento de actualización en Crear Pedido Para Llevar");
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
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
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
    const categoriaProductos = document.querySelectorAll('.categoria-productos');
    categoriaProductos.forEach(el => {
        el.style.display = 'none';
    });

    // Desactivar todos los botones
    const categoriaBtns = document.querySelectorAll('.categoria-btn');
    categoriaBtns.forEach(el => {
        el.classList.remove('active');
    });

    // Mostrar productos de la categoría seleccionada
    const productos = document.getElementById(`categoria-${categoriaId}`);
    if (productos) {
        productos.style.display = 'block';
        localStorage.setItem('categoriaActiva', categoriaId);
        
        // Actualizar título de categoría
        updateCategoryTitle(categoriaId);
        
        // Scroll suave hasta la sección de productos
        setTimeout(() => {
            productos.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    // Activar botón actual
    const activeBtn = document.querySelector(`.categoria-btn[data-categoria="${categoriaId}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        
        // Asegurar que el botón activo sea visible en móviles
        if (window.innerWidth < 768) {
            activeBtn.scrollIntoView({ behavior: 'smooth', inline: 'center' });
        }
    }
}

/**
 * Actualiza el título de la categoría
 */
function updateCategoryTitle(categoriaId) {
    const categoryTitle = document.getElementById('category-title');
    const activeBtn = document.querySelector(`.categoria-btn[data-categoria="${categoriaId}"]`);
    
    if (categoryTitle && activeBtn) {
        categoryTitle.textContent = activeBtn.title || activeBtn.textContent.trim();
    }
}

// =============================================
// BÚSQUEDA DE PRODUCTOS
// =============================================
function searchProducts(query) {
    const normalizedQuery = query.toLowerCase().trim();
    const isMobile = window.innerWidth < 768;
    
    // Obtener solo los productos visibles actualmente (para evitar duplicados)
    const activeCategory = localStorage.getItem('categoriaActiva') || 'todas';
    const currentContainer = document.getElementById(`categoria-${activeCategory}`);
    const visibleProducts = currentContainer ? currentContainer.querySelectorAll('.producto-item') : [];
    
    if (normalizedQuery === '') {
        // Restaurar visualización original
        document.querySelectorAll('.categoria-productos').forEach(cat => {
            cat.style.display = 'none';
        });
        
        // Mostrar solo la categoría activa
        if (currentContainer) {
            currentContainer.style.display = 'block';
        }
        
        // Restaurar estilo de productos
        visibleProducts.forEach(product => {
            product.style.display = 'flex';
            product.style.flexDirection = isMobile ? 'column' : 'row';
            product.style.alignItems = isMobile ? 'stretch' : 'center';
        });
        return;
    }
    
    // Ocultar todos los contenedores de categoría
    document.querySelectorAll('.categoria-productos').forEach(cat => {
        cat.style.display = 'none';
    });
    
    // Crear o mostrar contenedor de búsqueda
    let searchContainer = document.getElementById('search-results-container');
    if (!searchContainer) {
        searchContainer = document.createElement('div');
        searchContainer.id = 'search-results-container';
        searchContainer.className = 'categoria-productos';
        document.querySelector('.products-section').appendChild(searchContainer);
    } else {
        searchContainer.innerHTML = ''; // Limpiar resultados anteriores
    }
    searchContainer.style.display = 'block';
    
    // Mostrar solo los productos que coincidan en el contenedor de búsqueda
    let hasResults = false;
    visibleProducts.forEach(product => {
        const productName = product.dataset.nombre;
        if (productName && productName.includes(normalizedQuery)) {
            const productClone = product.cloneNode(true);
            productClone.style.display = 'flex';
            productClone.style.flexDirection = isMobile ? 'column' : 'row';
            productClone.style.alignItems = isMobile ? 'stretch' : 'center';
            searchContainer.appendChild(productClone);
            hasResults = true;
        }
    });
    
    // Mostrar mensaje si no hay resultados
    if (!hasResults) {
        searchContainer.innerHTML = '<p class="no-results">No se encontraron productos</p>';
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

function editNote(detalleId, currentNote, productName) {
    const modal = document.getElementById('noteModal');
    const title = document.getElementById('noteModalTitle');
    const input = document.getElementById('noteInput');
    
    if (!modal || !title || !input) {
        console.error('Elementos del modal no encontrados');
        return;
    }
    
    title.textContent = `Nota para ${productName}`;
    
    // Limpiar el valor anterior y establecer el actual
    const cleanNote = currentNote === '[Agregar nota]' || !currentNote ? '' : currentNote;
    input.value = cleanNote;
    input.focus();
    
    modal.style.display = 'block';
    
    const confirmBtn = document.querySelector('.btn-confirm');
    if (confirmBtn) {
        confirmBtn.textContent = cleanNote ? 'Actualizar' : 'Agregar';
        
        // Crear nueva función para evitar referencias stale
        confirmBtn.onclick = function() {
            updateNoteImproved(detalleId, productName);
        };
    }
}


/**
 * Actualiza nota existente vía AJAX - VERSIÓN CORREGIDA
 */
function updateNote(detalleId) {
    const noteInput = document.getElementById('noteInput');
    const note = noteInput.value.trim();
    const csrfToken = getCsrfToken();
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 
                        document.querySelector('.categoria-btn.active')?.dataset.categoria;

    const formData = new URLSearchParams({
        action: 'update_nota',
        detalle_id: detalleId,
        nota: note,
        categoria_activa: categoriaActiva
    });

    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            throw new Error('Respuesta no es JSON');
        }
    })
    .then(data => {
        if (data && data.success) {
            // *** AQUÍ ESTÁ LA CORRECCIÓN PRINCIPAL ***
            // Actualizar la nota en el DOM inmediatamente
            const noteElement = document.querySelector(`.cart-item-note[onclick*="${detalleId}"]`);
            if (noteElement) {
                if (note.trim() === '') {
                    // Si la nota está vacía, mostrar el placeholder
                    noteElement.innerHTML = '<i class="fas fa-sticky-note me-1"></i><span style="color:#999">[Agregar nota]</span>';
                } else {
                    // Si hay nota, mostrarla
                    noteElement.innerHTML = `<i class="fas fa-sticky-note me-1"></i>${note}`;
                }
                
                // Efecto visual para indicar que se actualizó
                noteElement.style.backgroundColor = '#d4edda';
                setTimeout(() => {
                    noteElement.style.backgroundColor = '';
                }, 1000);
            }
            
            // Actualizar el onclick para reflejar la nueva nota
            if (noteElement) {
                const productName = noteElement.closest('.cart-item').querySelector('.cart-item-name').textContent;
                noteElement.setAttribute('onclick', `editNote(${detalleId}, '${note.replace(/'/g, "\\'")}', '${productName.replace(/'/g, "\\'")}' )`);
            }

            // Mostrar notificación de éxito
            Swal.fire({
                position: 'top-end',
                icon: 'success',
                title: note.trim() === '' ? 'Nota eliminada' : 'Nota guardada',
                showConfirmButton: false,
                timer: 1500
            });
        } else if (data && data.error) {
            Swal.fire('Error', data.error, 'error');
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al actualizar la nota');
    })
    .finally(() => {
        closeNoteModal();
    });
}

/**
 * Función auxiliar para actualizar notas en el DOM
 */
function updateNoteInDOM(detalleId, newNote) {
    const noteElement = document.querySelector(`.cart-item-note[onclick*="${detalleId}"]`);
    if (!noteElement) return;
    
    if (newNote.trim() === '') {
        noteElement.innerHTML = '<i class="fas fa-sticky-note me-1"></i><span style="color:#999">[Agregar nota]</span>';
    } else {
        noteElement.innerHTML = `<i class="fas fa-sticky-note me-1"></i>${newNote}`;
    }
    
    // Actualizar el onclick para reflejar la nueva nota
    const productName = noteElement.closest('.cart-item').querySelector('.cart-item-name').textContent;
    noteElement.setAttribute('onclick', `editNote(${detalleId}, '${newNote.replace(/'/g, "\\'")}', '${productName.replace(/'/g, "\\'")}' )`);
    
    // Efecto visual
    noteElement.style.backgroundColor = '#d4edda';
    setTimeout(() => {
        noteElement.style.backgroundColor = '';
    }, 1000);
}

/**
 * Versión mejorada de updateNote con mejor manejo de DOM
 */
function updateNoteImproved(detalleId, productName) {
    const noteInput = document.getElementById('noteInput');
    const note = noteInput.value.trim();
    const csrfToken = getCsrfToken();
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 
                        document.querySelector('.categoria-btn.active')?.dataset.categoria;

    // Mostrar indicador de carga
    const loadingToast = Swal.fire({
        title: 'Guardando nota...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    const formData = new URLSearchParams({
        action: 'update_nota',
        detalle_id: detalleId,
        nota: note,
        categoria_activa: categoriaActiva
    });

    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            throw new Error('Respuesta no es JSON');
        }
    })
    .then(data => {
        loadingToast.close();
        
        if (data && data.success) {
            // Actualizar inmediatamente en el DOM
            updateNoteInDOMImproved(detalleId, note, productName);
            
            // Mostrar éxito
            Swal.fire({
                position: 'top-end',
                icon: 'success',
                title: note === '' ? 'Nota eliminada' : 'Nota guardada',
                showConfirmButton: false,
                timer: 1500
            });
            
        } else if (data && data.error) {
            Swal.fire('Error', data.error, 'error');
        }
    })
    .catch(error => {
        loadingToast.close();
        console.error('Error updating note:', error);
        Swal.fire('Error', 'No se pudo actualizar la nota. Inténtalo de nuevo.', 'error');
    })
    .finally(() => {
        closeNoteModal();
    });
}

/**
 * Función mejorada para actualizar notas en el DOM
 */
function updateNoteInDOMImproved(detalleId, newNote, productName) {
    // Buscar el elemento de nota usando múltiples selectores para mayor robustez
    let noteElement = document.querySelector(`[data-detalle-id="${detalleId}"].cart-item-note`);
    
    if (!noteElement) {
        // Fallback: buscar por onclick que contenga el detalleId  
        noteElement = document.querySelector(`.cart-item-note[onclick*="${detalleId}"]`);
    }
    
    if (!noteElement) {
        console.warn(`No se encontró el elemento de nota para detalle ${detalleId}`);
        return;
    }
    
    // Actualizar el contenido
    const iconHTML = '<i class="fas fa-sticky-note me-1"></i>';
    if (newNote.trim() === '') {
        noteElement.innerHTML = iconHTML + '<span style="color:#999">[Agregar nota]</span>';
    } else {
        noteElement.innerHTML = iconHTML + newNote;
    }
    
    // Actualizar el onclick para la próxima edición
    const escapedNote = newNote.replace(/'/g, "\\'");
    const escapedProductName = productName.replace(/'/g, "\\'");
    noteElement.setAttribute('onclick', `editNote(${detalleId}, '${escapedNote}', '${escapedProductName}')`);
    
    // Efecto visual mejorado
    noteElement.style.transition = 'background-color 0.3s ease';
    noteElement.style.backgroundColor = '#d4edda';
    noteElement.style.borderRadius = '4px';
    noteElement.style.padding = '2px 4px';
    
    setTimeout(() => {
        noteElement.style.backgroundColor = '';
        noteElement.style.padding = '';
    }, 1500);
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

    const csrfToken = getCsrfToken();
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 
                        document.querySelector('.categoria-btn.active')?.dataset.categoria;

    const formData = new URLSearchParams({
        action: action === 'incrementar' ? 'increment_cantidad' : 'decrement_cantidad',
        detalle_id: detalleId,
        categoria_activa: categoriaActiva
    });

    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            throw new Error('Respuesta no es JSON');
        }
    })
    .then(data => {
        if (data && data.success) {
            // Actualizar cantidad
            cantidadElement.textContent = data.nueva_cantidad;
            addTempClass(cantidadElement, 'pulse');

            // Actualizar subtotal del producto
            const subtotalSpan = document.querySelector(`.cart-item-price[data-detalle-id="${detalleId}"]`);
            if (subtotalSpan) {
                subtotalSpan.textContent = `$${data.nuevo_subtotal.toFixed(0)}`;
                addTempClass(subtotalSpan, 'pulse');
            }

            // Actualizar total general
            const totalElement = document.querySelector('.total-amount');
            if (totalElement) {
                totalElement.textContent = `$${data.total.toFixed(0)}`;
                addTempClass(totalElement, 'pulse');
            }

            // Si la cantidad llega a 0, eliminar el item
            if (data.nueva_cantidad === 0) {
                const cartItem = cantidadElement.closest('.cart-item');
                if (cartItem) {
                    cartItem.remove();
                }
            }
        } else if (data && data.error) {
            Swal.fire('Error', data.error, 'error');
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al actualizar la cantidad');
    });
}

/**
 * Elimina un producto del carrito
 */
function removeProduct(detalleId) {
    const categoriaActiva = localStorage.getItem('categoriaActiva') || 
                        document.querySelector('.categoria-btn.active')?.dataset.categoria;
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
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            throw new Error('Respuesta no es JSON');
        }
    })
    .then(data => {
        if (data && data.success) {
            // Eliminar elemento del DOM
            const cartItem = document.querySelector(`[data-detalle-id="${detalleId}"]`).closest('.cart-item');
            if (cartItem) {
                cartItem.remove();
            }
            
            // Actualizar total
            const totalElement = document.querySelector('.total-amount');
            if (totalElement) {
                totalElement.textContent = `$${data.total.toFixed(0)}`;
            }
            
            Swal.fire('Eliminado', data.message, 'success');
        } else if (data && data.error) {
            Swal.fire('Error', data.error, 'error');
        }
    })
    .catch(error => {
        handleFetchError(error, 'Error al eliminar el producto');
    });
}

// =============================================
// EVENT LISTENERS E INICIALIZACIÓN
// =============================================

/**
 * Inicializa todos los event listeners cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Crear Pedido Para Llevar - Inicializando interfaz");
    
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

    // Al cargar la página, verificar si hay una categoría activa en localStorage
    const categoriaActiva = localStorage.getItem('categoriaActiva');
    if (categoriaActiva) {
        activateCategory(categoriaActiva);
    }

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
        
        // Manejar la tecla Escape para limpiar búsqueda
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                searchProducts('');
            }
        });
    }
    
    // ==========================================
    // EVENT DELEGATION PRINCIPAL
    // ==========================================
    
    // Manejo unificado de todos los botones del pedido
    document.addEventListener('click', function(e) {
        // Botón eliminar producto
        const eliminarBtn = e.target.closest('.remove-btn');
        if (eliminarBtn) {
            e.preventDefault();
            const detalleId = eliminarBtn.dataset.detalleId;

            Swal.fire({
                title: '¿Eliminar producto?',
                text: "Esta acción no se puede deshacer",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    removeProduct(detalleId);
                }
            });
            return;
        }

        // Botones de incrementar/decrementar cantidad
        const incrementarBtn = e.target.closest('.incrementar');
        if (incrementarBtn) {
            e.preventDefault();
            const detalleId = incrementarBtn.dataset.detalleId;
            if (detalleId) {
                updateCantidad(detalleId, 'incrementar');
            }
            return;
        }

        const decrementarBtn = e.target.closest('.decrementar');
        if (decrementarBtn) {
            e.preventDefault();
            const detalleId = decrementarBtn.dataset.detalleId;
            if (detalleId) {
                updateCantidad(detalleId, 'decrementar');
            }
            return;
        }
        
        // Cerrar modal al hacer clic fuera
        const modal = document.getElementById('noteModal');
        if (e.target === modal) {
            closeNoteModal();
        }
    });

    // ==========================================
    // FEEDBACK VISUAL PARA BOTONES
    // ==========================================
    
    // Feedback al agregar productos
    document.querySelectorAll('.add-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const productoNombre = this.dataset.producto;
            
            // Feedback visual
            const originalHTML = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i>';
            this.classList.remove('btn-success');
            this.classList.add('btn-primary');
            
            setTimeout(() => {
                this.innerHTML = originalHTML;
                this.classList.remove('btn-primary');
                this.classList.add('btn-success');
            }, 1500);
            
            // Notificación toast
            showToast('success', `${productoNombre} agregado`);
        });
    });
    
    // ==========================================
    // EVENTOS DE TECLADO
    // ==========================================
    
    // Manejo especial para Enter en campos de nota (usando delegación de eventos)
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.target.classList.contains('nota-input')) {
            e.preventDefault();
            const detalleId = e.target.dataset.detalleId;
            const guardarBtn = document.querySelector(`.guardar-nota[data-detalle-id="${detalleId}"]`);
            
            if (guardarBtn) {
                guardarBtn.click();
            }
        }
    });

    document.addEventListener('keydown', function(e) {
        // Cerrar modal con ESC
        if (e.key === 'Escape') {
            closeNoteModal();
        }
    });
    
    // Confirmar nota con Enter en el input del modal
    const noteInput = document.getElementById('noteInput');
    if (noteInput) {
        noteInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                confirmNote();
            }
        });
    }
    
    // ==========================================
    // EXPERIENCIA MÓVIL
    // ==========================================
    
    // Mejorar experiencia móvil: hacer scroll horizontal en categorías
    const categoriasWrapper = document.querySelector('.categories-wrapper');
    if (categoriasWrapper && window.innerWidth < 768) {
        const activeBtn = document.querySelector('.categoria-btn.active');
        if (activeBtn) {
            setTimeout(() => {
                activeBtn.scrollIntoView({ behavior: 'smooth', inline: 'center' });
            }, 300);
        }
    }
    
    console.log("✅ Crear Pedido Para Llevar - Interfaz inicializada correctamente");
});

// =============================================
// FUNCIONES GLOBALES EXPUESTAS
// =============================================

// Exponer funciones principales al scope global para uso en templates
window.PedidoParaLlevar = {
    ...window.PedidoParaLlevar,
    openNoteModal,
    closeNoteModal,
    confirmNote,
    activateCategory,
    searchProducts,
    updateCantidad,
    removeProduct,
    showToast,
    editNote: editNote,
    updateNote: updateNoteImproved,
    updateNoteInDOM: updateNoteInDOMImproved
};

console.log("📦 Pedido Para Llevar JS - Módulo cargado completamente");


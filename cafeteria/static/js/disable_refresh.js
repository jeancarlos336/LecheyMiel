// disable_refresh.js - Anti-refresh para venta express
(function() {
    console.log("🔨 Inicializando mecanismo anti-refresh avanzado");
    
    // 1. Variable para rastrear si ya se instaló
    if (window.__antiRefreshInstalled) {
        console.log("Anti-refresh ya instalado, omitiendo");
        return;
    }
    window.__antiRefreshInstalled = true;
    
    // 2. Sobrescribir fetch para bloquear actualizaciones de actividad
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (typeof url === 'string' && url.includes('update_activity')) {
            console.warn("🚫 Bloqueada petición de update_activity:", url);
            return Promise.resolve(new Response(JSON.stringify({status: "blocked"}), {
                status: 200,
                headers: {'Content-Type': 'application/json'}
            }));
        }
        return originalFetch.apply(this, arguments);
    };
    
    // 3. Sobrescribir XMLHttpRequest para mayor seguridad
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (typeof url === 'string' && url.includes('update_activity')) {
            console.warn("🚫 Bloqueada petición XHR de update_activity:", url);
            // Redirigir a una URL ficticia para que falle silenciosamente
            arguments[1] = 'about:blank';
        }
        return originalXHROpen.apply(this, arguments);
    };
    
    // 4. Bloquear eventos que puedan disparar actualizaciones de actividad
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    
    // Función que evita que se propaguen eventos que podrían disparar actualizaciones
    function blockActivityEvents(e) {
        // Solo bloquear la propagación si parece un controlador de actividad
        const stack = new Error().stack || '';
        if (stack.includes('activity') || stack.includes('Activity')) {
            console.log("🛡️ Bloqueado evento que podría disparar actualización:", e.type);
            e.stopImmediatePropagation();
        }
    }
    
    // Añadir el bloqueador a todos los eventos relevantes
    events.forEach(eventType => {
        document.addEventListener(eventType, blockActivityEvents, true);
    });
    
    // 5. Desactivar todas las variables y funciones relacionadas con actividad
    window.disableActivityUpdates = true;
    window.activityUpdateDisabled = true;
    window.activityTimeout = null;
    
    // 6. Reemplazar funciones críticas
    window.updateUserActivity = function() {
        console.log("⛔ Función updateUserActivity neutralizada");
        return Promise.resolve({ok: true});
    };
    
    window.handleUserActivity = function() {
        return false;
    };
    
    // 7. Sobrescribir setTimeout para capturar intentos de programar actualizaciones
    const originalSetTimeout = window.setTimeout;
    window.setTimeout = function(callback, delay, ...args) {
        if (callback && typeof callback === 'function') {
            const callbackStr = callback.toString();
            if (
                callbackStr.includes('updateUserActivity') || 
                callbackStr.includes('activityTimeout') ||
                callbackStr.includes('activity')
            ) {
                console.log("⏱️ Bloqueado setTimeout relacionado con actividad");
                return 99999; // ID falso
            }
        }
        return originalSetTimeout.apply(this, arguments);
    };
    
    // 8. Monitor periódico para mantener las protecciones activas
    originalSetTimeout(function maintainProtection() {
        window.disableActivityUpdates = true;
        window.activityUpdateDisabled = true;
        if (window.activityTimeout) {
            clearTimeout(window.activityTimeout);
            window.activityTimeout = null;
        }
        originalSetTimeout(maintainProtection, 1000);
    }, 1000);
    
    // 9. Detener cualquier refresco automático
    if (window.stop) {
        // Acceder a window.stop de forma segura
        const originalStop = window.stop;
        originalSetTimeout(function() {
            // Si hay algún refresco programado, deténlo
            originalStop.call(window);
        }, 10000); // Justo antes de los 10s mencionados
    }
    
    console.log("✅ Sistema anti-refresh instalado exitosamente");
})();
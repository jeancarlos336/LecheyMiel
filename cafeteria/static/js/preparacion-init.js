// 🛡️ PROTECCIÓN PARA LA PÁGINA DE PREPARACIÓN
// Este script debe cargarse ANTES de preparacion.js y ANTES de los scripts de base.html

(function() {
    'use strict';
    
    const currentPath = window.location.pathname.toLowerCase();
    const esPreparacion = currentPath === '/pedidos/preparacion/' || 
                         currentPath === '/pedidos/preparacion' ||
                         currentPath.endsWith('/preparacion/') ||
                         currentPath.endsWith('/preparacion');
    
    if (esPreparacion) {
        console.log("🔐 Inicializando página de preparación - Desactivando interferencias");
        
        // Desactivar COMPLETAMENTE el sistema de actividad de base.html
        window.disableActivityUpdates = true;
        
        // Asegurar que NO se considere página protegida
        window.isVentaExpress = false;
        window.isTomarPedido = false;
        window.isCrearPedidoParaLlevar = false;
        window.preventRefresh = false;
        window.isPageProtected = false;
        
        console.log("✅ Página de preparación lista - Sistema de auto-refresh habilitado");
        console.log("   - disableActivityUpdates:", window.disableActivityUpdates);
        console.log("   - isPageProtected:", window.isPageProtected);
    }
})();
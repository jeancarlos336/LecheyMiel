from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Incluir URLs de cada aplicación
    path('usuarios/', include('users.urls')),
    path('productos/', include('products.urls')),
    path('pedidos/', include('orders.urls')),
    path('notificaciones/', include('notifications.urls')),
    path('audit/', include('audit.urls')),
    path('compras/', include('compras.urls')),
    path('', RedirectView.as_view(url='usuarios/login/', permanent=False)),
    

]

# Agregar URLs para servir archivos estáticos y media durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

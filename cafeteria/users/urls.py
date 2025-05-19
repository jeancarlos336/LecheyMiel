from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('update_activity/', views.update_activity, name='update_activity'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Perfil de usuario
    path('perfil/', views.perfil_view, name='perfil'),
    
    # CRUD de usuarios (solo para administradores)
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/crear/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<int:pk>/', views.UsuarioDetailView.as_view(), name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_confirm_delete'),
    
    #cambiar contraseña
    path('cambiar-contrasena/', views.CambiarContrasenaView.as_view(), name='cambiar_contrasena'),
]
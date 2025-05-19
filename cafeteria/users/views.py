from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Usuario, Rol
from .forms import UsuarioCreationForm, UsuarioUpdateForm, LoginForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

@require_POST
def update_activity(request):
    if request.user.is_authenticated:
        request.session['last_activity'] = timezone.now().isoformat()
    return HttpResponse(status=204)  # No content response

# Vistas para login y logout
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.esta_activo:
                login(request, user)
                messages.success(request, f"Bienvenido, {username}!")
                return redirect('users:dashboard')
            else:
                messages.error(request, "Usuario inactivo o credenciales incorrectas.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('users:login')

# Verificadores de permisos
class EsAdministrador(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.rol and self.request.user.rol.nombre == Rol.ADMINISTRADOR

# Vista para el panel de control
@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

# Vistas CRUD para usuarios
class UsuarioListView(LoginRequiredMixin, EsAdministrador, ListView):
    model = Usuario
    template_name = 'users/usuario_list.html'
    context_object_name = 'usuarios'
    
    def get_queryset(self):
        return Usuario.objects.all().order_by('username')

class UsuarioCreateView(LoginRequiredMixin, EsAdministrador, CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'users/usuario_form.html'
    success_url = reverse_lazy('users:usuario_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)

class UsuarioUpdateView(LoginRequiredMixin, EsAdministrador, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'users/usuario_form.html'
    success_url = reverse_lazy('users:usuario_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        password1 = form.cleaned_data.get("password1")
        password2 = form.cleaned_data.get("password2")
        
        if password1 and password1 == password2:
            self.object.set_password(password1)
            self.object.save()
        
        messages.success(self.request, "Usuario actualizado correctamente.")
        return response


class UsuarioDetailView(LoginRequiredMixin, EsAdministrador, DetailView):
    model = Usuario
    template_name = 'users/usuario_detail.html'
    context_object_name = 'usuario'

class UsuarioDeleteView(LoginRequiredMixin, EsAdministrador, DeleteView):
    model = Usuario
    template_name = 'users/usuario_confirm_delete.html'
    success_url = reverse_lazy('users:usuario_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Usuario eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

# Vistas de perfil para cualquier usuario
@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = UsuarioUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('users:perfil')
    else:
        form = UsuarioUpdateForm(instance=request.user)
    
    return render(request, 'users/perfil.html', {'form': form})


class CambiarContrasenaView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'users/cambiar_contrasena.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:perfil')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['old_password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
        form.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
        form.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Tu contraseña ha sido cambiada exitosamente.')
        return super().form_valid(form)
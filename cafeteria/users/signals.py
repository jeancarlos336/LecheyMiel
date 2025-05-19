from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def limpiar_cache_al_loguear(sender, request, user, **kwargs):
    try:
        print("🔍 Verificando caché antes de limpiar...")
        cache.set("test_cache", "ok", timeout=10)  # Prueba si la caché está operativa
        cache_value = cache.get("test_cache")

        if cache_value == "ok":
            print("✅ Caché operativa, procediendo a limpiar...")
            cache.clear()  # Borra la caché
            print(f"🚀 Caché limpiada al iniciar sesión: {user.username}")  
        else:
            print("⚠️ La caché no está funcionando correctamente.")

    except Exception as e:
        print(f"❌ Error al limpiar caché: {e}")

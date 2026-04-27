import logging
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def limpiar_cache_al_loguear(sender, request, user, **kwargs):
    logger.info(f"Inicio de sesión: {user.username}")
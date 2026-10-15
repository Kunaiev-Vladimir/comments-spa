"""
ASGI config for comments_spa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

from comments.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import os

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'comments_spa.settings'
)


django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    'http': django_asgi_app,

    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

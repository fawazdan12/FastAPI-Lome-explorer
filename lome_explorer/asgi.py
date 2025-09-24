import os
import django
from django.core.asgi import get_asgi_application

# Configurer Django AVANT d'importer quoi que ce soit d'autre
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lome_explorer.settings')
django.setup()

# MAINTENANT on peut importer les modules qui dépendent de Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Importer les WebSocket URLs après la configuration Django
try:
    from FastAPI.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
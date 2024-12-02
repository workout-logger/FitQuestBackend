import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from inventory.consumers import InventoryConsumer
from inventory.middleware import TokenAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')

# Define the ASGI application with protocol routing
application = ProtocolTypeRouter({
    # HTTP protocol
    "http": get_asgi_application(),

    # WebSocket protocol
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path("ws/inventory/", InventoryConsumer.as_asgi()),  # Adjust as per your WebSocket path
        ])
    ),
})
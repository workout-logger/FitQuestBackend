from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from .consumers import InventoryConsumer
from .middleware import TokenAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path("ws/inventory/", InventoryConsumer.as_asgi()),
        ])
    ),
})
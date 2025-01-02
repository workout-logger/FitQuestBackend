import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')

# Define the ASGI application with protocol routing
application = ProtocolTypeRouter({
    # HTTP protocol
    "http": get_asgi_application(),

    # WebSocket protocol
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # WebSocket paths defined below in a deferred manner
            []
        )
    ),
})

# Lazy load WebSocket routes
def add_websocket_routes():
    from inventory.consumers import InventoryConsumer
    from inventory.middleware import TokenAuthMiddleware
    import chat.routing

    application.application_mapping["websocket"] = TokenAuthMiddleware(
        URLRouter(
            [
                path("ws/inventory/", InventoryConsumer.as_asgi()),  # Adjust WebSocket path
            ] + chat.routing.websocket_urlpatterns  # Add chat WebSocket routes
        )
    )

# Call the function to load routes after initialization
add_websocket_routes()

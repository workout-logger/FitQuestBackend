from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication
from channels.middleware import BaseMiddleware
from asgiref.sync import sync_to_async


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        token_key = None

        # Extract token from query string (e.g., ws://.../?token=abc123)
        if "token=" in query_string:
            token_key = query_string.split("token=")[1]

        if token_key:
            # Validate the token
            try:
                user = await sync_to_async(self.get_user_from_token)(token_key)
                scope["user"] = user
            except:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    def get_user_from_token(self, token_key):
        auth = TokenAuthentication()
        token = auth.get_model().objects.get(key=token_key)
        return token.user

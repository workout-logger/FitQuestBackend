import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework import status


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        access_token = request.data.get("access_token")

        # Print the access token for debugging
        print("Access Token:", access_token)

        # Verify the token with Google
        response = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}')

        # Check if the token is valid
        if response.status_code == 200:
            print("Google token is valid:", response.json())
            return super().post(request, *args, **kwargs)
        else:
            print("Invalid Google token:", response.json())
            return Response({"error": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)

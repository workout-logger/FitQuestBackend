import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from dj_rest_auth.views import LoginView
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import CustomUser
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        access_token = request.data.get("access_token")

        # Debug: Print the access token
        print("Access Token:", access_token)

        # Verify the token with Google
        response = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}')

        if response.status_code == 200:
            google_data = response.json()
            print("Google token is valid:", google_data)

            email = google_data.get('email')

            if email:
                try:
                    # Check if the user already exists
                    user = User.objects.get(email=email)
                    print("User exists, logging in:", user.email)

                    # Proceed with login
                    response = super().post(request, *args, **kwargs)
                    response.data['is_new_user'] = False
                    return response

                except User.DoesNotExist:
                    # User does not exist, this is a signup
                    print("User does not exist, signing up:", email)

                    # Proceed with signup
                    response = super().post(request, *args, **kwargs)
                    response.data['is_new_user'] = True
                    return response
            else:
                return Response({"error": "Google token does not contain an email"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("Invalid Google token:", response.json())
            return Response({"error": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)


class EmailRegisterView(APIView):
    permission_classes = [AllowAny]

    """
    Handles user registration with email and password.
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()

        # Generate a token for the user
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "User registered successfully",
            "token": token.key  # Include the token in the response
        }, status=status.HTTP_201_CREATED)


class EmailLoginView(APIView):
    permission_classes = [AllowAny]
    """
    Handles user login with email and password.
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)

        if user is not None:
            from rest_framework.authtoken.models import Token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "message": "Login successful",
                "token": token.key
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def username_exists(request):
    username = request.query_params.get('username')

    if not username:
        return JsonResponse({"success": False, "error": "Username is required"}, status=400)

    try:
        # Check if a user with the given username exists
        User.objects.get(username=username)
        return JsonResponse({"success": True, "exists": True}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"success": True, "exists": False}, status=200)

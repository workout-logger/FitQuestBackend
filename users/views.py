import uuid

import requests
from allauth.socialaccount.models import SocialApp, SocialToken, SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from dj_rest_auth.views import LoginView
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from inventory.models import Inventory
from .models import CustomUser
from django.contrib.auth import authenticate, get_user_model
from django.utils.timezone import now as timezone_now
from rest_framework.authtoken.models import Token
User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any user (authenticated or not) to access this view
def guest_signup(request):
    """
    Endpoint for creating a guest user account.
    """
    try:
        # Generate unique guest email and username
        unique_id = uuid.uuid4().hex[:8]
        guest_email = f"guest_{unique_id}@example.com"
        guest_username = f"guest_{unique_id}"

        # Ensure uniqueness (though UUID reduces collision chances)
        if User.objects.filter(username=guest_username).exists():
            return Response(
                {"error": "Guest username collision. Please try again."},
                status=status.HTTP_409_CONFLICT,
            )

        # Create the guest user
        guest_user = User.objects.create_user(
            username=guest_username,
            email=guest_email,
            password=None  # Guests do not have a password
        )
        guest_user.is_active = True  # Ensure the user is active
        guest_user.coins = 200
        guest_user.save()

        # Optionally, flag the user as a guest by extending the User model or using a Profile model
        # For simplicity, we'll skip this step here

        # Generate a DRF Token for the guest user
        token, created = Token.objects.get_or_create(user=guest_user)
        Inventory.objects.get_or_create(user=guest_user)
        # Return the token to the client
        response_data = {
            "message": "Guest account created successfully",
            "token": token.key,
            "username": guest_username,
            "email": guest_email,
            "is_new_user": True
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        # Log the error for debugging
        print(f"Error creating guest user: {e}")
        return Response(
            {"error": "Failed to create guest account", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                    user = User.objects.get(email=email)
                    user.coins = 200
                    user.save()
                    Inventory.objects.get_or_create(user=user)
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
@permission_classes([AllowAny])
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_user_preferences(request):
    username = request.data.get('username')
    body_color = request.data.get('body_color_index')
    eye_color = request.data.get('eye_color_index')

    try:
        user = request.user

        # Validate body color
        body_color_value = int(body_color) + 1
        if body_color_value not in dict(CustomUser.BODY_COLOR_CHOICES):
            return Response({"error": "Invalid body color choice"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate eye color
        eye_color_value = int(eye_color) + 1
        if eye_color_value not in dict(CustomUser.EYE_COLOR_CHOICES):
            return Response({"error": "Invalid eye color choice"}, status=status.HTTP_400_BAD_REQUEST)

        # Update user preferences
        user.username = username
        user.body_color = body_color_value
        user.eye_color = eye_color_value
        user.save()

        # Reload user to confirm save
        user.refresh_from_db()
        print(f"Saved Body Color: {user.body_color}")
        print(f"Saved Eye Color: {user.eye_color}")

        return Response(
            {
                "message": "User preferences saved successfully",
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
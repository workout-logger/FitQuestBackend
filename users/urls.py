from django.urls import path, include

from users.views import GoogleLogin

urlpatterns = [

    path('google/', GoogleLogin.as_view(), name="google_login"),
]

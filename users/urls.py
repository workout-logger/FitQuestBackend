from django.urls import path, include

from users.views import GoogleLogin,EmailRegisterView,EmailLoginView

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name="google_login"),
    path('register/', EmailRegisterView.as_view(), name='email_register'),
    path('login/', EmailLoginView.as_view(), name='email_login'),
]

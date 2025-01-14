from django.urls import path, include

from users.views import GoogleLogin, EmailRegisterView, EmailLoginView, username_exists, save_user_preferences, \
    guest_signup

urlpatterns = [
    path('guest/', guest_signup, name='guest_signup'),
    path('google/', GoogleLogin.as_view(), name="google_login"),
    path('register/', EmailRegisterView.as_view(), name='email_register'),
    path('login/', EmailLoginView.as_view(), name='email_login'),
    path('username_exists/', username_exists, name='username_exists'),
    path('save_user_preferences/', save_user_preferences, name='save_user_preferences')
]

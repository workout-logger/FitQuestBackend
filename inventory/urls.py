# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('get_equipped_items/', views.get_equipped_items, name='get_equipped_items'),
    path('buy_chest/', views.buy_chest, name='buy_chest'),

]

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('get_equipped_items/', views.get_equipped_items, name='get_equipped_items'),
    path('buy_chest/', views.buy_chest, name='buy_chest'),
    path('marketplace/add_listing/', views.add_listing, name='add_listing'),
    path('marketplace/buy/', views.buy_from_listing, name='buy_from_listing'),
    path('marketplace/', views.show_listings, name='show_listings'),
]

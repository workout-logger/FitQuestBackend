from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('exercises_all', views.exercises_all, name='exercises_all'),
    path('muscles', views.muscles, name='muscles')
]
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('workouts/', views.workout_list, name='workout-list'),
    path('workouts/<int:pk>/', views.workout_detail, name='workout-detail'),
    path('workout_receiver/', views.workout_receiver, name='workout_receiver'),
    path('debug/', views.print_post_data, name='print_post_data'),
    path('sync_workouts/', views.sync_workouts, name='sync_workouts'),
    path('last_workout/', views.last_workout, name='last_workout'),
    path('past_workouts/', views.past_workouts, name='past_workouts'),
    path('week_workouts/', views.this_weeks_workouts, name='this_weeks_workouts'),
    path('workout/update_latest_muscle_groups/', views.update_latest_muscle_groups, name='update_latest_muscle_groups'),

]

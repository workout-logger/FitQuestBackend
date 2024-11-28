# serializers.py
from rest_framework import serializers
from .models import Workout

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'user', 'duration', 'exercises_done', 'workout_date']
        read_only_fields = ['id']

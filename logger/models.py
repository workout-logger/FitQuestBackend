from django.db import models
from django.conf import settings
from django.db.models import JSONField
from exercises.models import Exercise
from exercises.models import MuscleGroup
class Workout(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workouts')
    duration = models.DurationField(help_text="Duration of the workout (e.g., HH:MM:SS)")
    exercises_done = models.ManyToManyField(Exercise)
    workout_date = models.DateTimeField(help_text="Date and time of the workout captured from the watch")
    avg_heart_rate = models.IntegerField(help_text="Average Heart Rate for Workout")
    mood = models.IntegerField(help_text="1-3 From Sad To Happy")
    energy_burned = models.FloatField(help_text="Kcal")
    muscle_groups = models.ManyToManyField(MuscleGroup, blank=True)
    strength_gained = models.PositiveIntegerField(default=0, help_text="Player's strength attribute.")
    agility_gained = models.PositiveIntegerField(default=0, help_text="Player's agility attribute.")
    speed_gained = models.PositiveIntegerField(default=0, help_text="Player's speed attribute.")

    def __str__(self):
        return f"{self.user.username}'s workout on {self.workout_date.strftime('%Y-%m-%d %H:%M:%S')}"


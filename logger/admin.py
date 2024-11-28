# admin.py
from django.contrib import admin
from .models import Workout

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'duration', 'workout_date')
    search_fields = ('user__username', 'exercises_done')
    list_filter = ('workout_date',)
    ordering = ('-workout_date',)

    # Optional: Display exercises_done more readably if it's JSON
    def exercises_summary(self, obj):
        return str(obj.exercises_done)

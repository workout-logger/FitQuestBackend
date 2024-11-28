from django.contrib import admin
from .models import Exercise, MuscleGroup, Equipment, Image

class ImageInline(admin.TabularInline):
    model = Image
    extra = 1

class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_muscle_groups', 'equipment', 'description')
    inlines = [ImageInline]

    def get_muscle_groups(self, obj):
        return ", ".join([muscle.name for muscle in obj.muscle_groups.all()])
    get_muscle_groups.short_description = 'Muscle Groups'

admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(MuscleGroup)
admin.site.register(Equipment)
admin.site.register(Image)

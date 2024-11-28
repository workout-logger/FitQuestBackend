import os
import json
from django.core.management.base import BaseCommand
from exercises.models import Exercise, MuscleGroup, Equipment, Image

class Command(BaseCommand):
    help = 'Import exercises from JSON data'

    def handle(self, *args, **kwargs):
        file_path = 'exercises.json'  # Update with the correct path to your JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        for item in data:
            exercise = Exercise.objects.create(
                name=item['name'],
                description=item['description']
            )

            for muscle_name in item['muscles']:
                if muscle_name and muscle_name.strip():  # Check for non-empty muscle names
                    muscle_group, _ = MuscleGroup.objects.get_or_create(name=muscle_name.strip())
                    exercise.muscle_groups.add(muscle_group)

            if 'equipment' in item and item['equipment'].strip():  # Check for non-empty equipment names
                equipment, _ = Equipment.objects.get_or_create(name=item['equipment'].strip())
                exercise.equipment = equipment
                exercise.save()

            for image_url in item.get('images', []):
                if image_url and image_url.strip():
                    Image.objects.create(exercise=exercise, url=image_url.strip())

        self.stdout.write(self.style.SUCCESS('Successfully imported exercises'))

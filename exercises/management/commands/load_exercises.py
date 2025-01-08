import json
import boto3
from exercises.models import MuscleGroup, Equipment, Exercise, Image
from django.conf import settings

def upload_to_s3(file_path, bucket_name, object_name):
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    with open(file_path, 'rb') as file:
        s3_client.upload_fileobj(file, bucket_name, object_name)
    return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

def load_data_to_db(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
        data = json.load(file)

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    for exercise in data:
        # Add or get Muscle Groups
        muscle_group_objects = []
        for muscle in exercise.get('primary', []):
            muscle_obj, created = MuscleGroup.objects.get_or_create(name=muscle)
            muscle_group_objects.append(muscle_obj)

        for muscle in exercise.get('secondary', []):
            muscle_obj, created = MuscleGroup.objects.get_or_create(name=muscle)
            muscle_group_objects.append(muscle_obj)

        # Add or get Equipment
        equipment_name = exercise['equipment'][0] if exercise['equipment'] else None
        equipment_obj = None
        if equipment_name:
            equipment_obj, created = Equipment.objects.get_or_create(name=equipment_name)

        # Add Exercise
        exercise_obj, created = Exercise.objects.get_or_create(
            name=exercise['title'],
            defaults={
                'description': exercise['primer'],
                'equipment': equipment_obj
            }
        )

        # Link Muscle Groups to Exercise
        exercise_obj.muscle_groups.set(muscle_group_objects)

        # Add Images
        for img_url in exercise.get('png', []):
            object_name = f"exercise_images/{img_url.split('/')[-1]}"
            s3_url = upload_to_s3(img_url, bucket_name, object_name)
            Image.objects.get_or_create(
                exercise=exercise_obj,
                url=s3_url
            )

        print(f"Added/Updated exercise: {exercise['title']}")


# Call the function with your JSON file path
load_data_to_db('exercises.json')

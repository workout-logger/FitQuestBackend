from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from exercises.models import Exercise, MuscleGroup


@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    muscle_type = request.query_params.get('muscle_type', None)
    if muscle_type is not None:
        try:
            muscle_group = MuscleGroup.objects.get(name=muscle_type)
            exercises = Exercise.objects.filter(muscle_groups=muscle_group)
            data = [{
                "name": exercise.name,
                "description": get_first_three_sentences(exercise.description),
                "equipment": exercise.equipment.name if exercise.equipment else None,
                "images": [image.url for image in exercise.images.all()]
            } for exercise in exercises]
            return Response(data)
        except MuscleGroup.DoesNotExist:
            return Response({"error": "Muscle type not found"}, status=404)
    else:
        return Response({"error": "Muscle type parameter is required"}, status=400)

@permission_classes([AllowAny])
def get_first_three_sentences(description):
    sentences = description.split('. ')
    return '. '.join(sentences[:3]) + ('.' if len(sentences) > 3 else '')

@api_view(['GET'])
@permission_classes([AllowAny])
def exercises_all(request):
    try:
        exercises = Exercise.objects.all()
        data = [{
            "name": exercise.name,
            "muscle_groups": [muscle.name for muscle in exercise.muscle_groups.all()],
            "description": exercise.description,
            "equipment": exercise.equipment.name if exercise.equipment else None,
            "images": [image.url for image in exercise.images.all()]
        } for exercise in exercises]
        return Response(data)
    except MuscleGroup.DoesNotExist:
        return Response({"error": "Muscle type not found"}, status=404)



@api_view(['GET'])
@permission_classes([AllowAny])
def muscles(request):
    muscles = MuscleGroup.objects.all()
    data = [{"name": muscle.name} for muscle in muscles]
    return Response(data)

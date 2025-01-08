from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from exercises.models import Exercise, MuscleGroup


@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    muscle_type = request.query_params.get('muscle_type', None)
    page = request.query_params.get('page', 1)
    items_per_page = request.query_params.get('items_per_page', 10)

    try:
        page = int(page)
    except ValueError:
        return Response({"error": "Invalid page number"}, status=400)

    try:
        items_per_page = int(items_per_page)
    except ValueError:
        return Response({"error": "Invalid items_per_page value"}, status=400)

    if muscle_type is not None:
        try:
            muscle_group = MuscleGroup.objects.get(name=muscle_type)
            # Filter exercises that belong to the muscle group and have at least one image
            exercises = Exercise.objects.filter(muscle_groups=muscle_group, images__isnull=False).distinct()

            # Add pagination
            paginator = Paginator(exercises, items_per_page)
            try:
                paginated_exercises = paginator.page(page)
            except PageNotAnInteger:
                return Response({"error": "Page number is not an integer"}, status=400)
            except EmptyPage:
                return Response({"error": "Page out of range"}, status=404)

            data = [{
                "name": exercise.name,
                "description": get_first_three_sentences(exercise.description),
                "equipment": exercise.equipment.name if exercise.equipment else None,
                "images": [image.url for image in exercise.images.all()]
            } for exercise in paginated_exercises]

            return Response({
                "total_pages": paginator.num_pages,
                "current_page": paginated_exercises.number,
                "total_items": paginator.count,
                "items_per_page": paginator.per_page,
                "exercises": data
            })
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

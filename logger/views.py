# views.py
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.timezone import make_aware

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Workout
from exercises.models import MuscleGroup
from .serializers import WorkoutSerializer


# List all workouts or create a new workout
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workout_list(request):
    if request.method == 'GET':
        workouts = Workout.objects.filter(user=request.user)
        serializer = WorkoutSerializer(workouts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = WorkoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, update, or delete a specific workout
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def workout_detail(request, pk):
    try:
        workout = Workout.objects.get(pk=pk, user=request.user)
    except Workout.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkoutSerializer(workout)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = WorkoutSerializer(workout, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        workout.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def print_post_data(request):
    if request.method == 'POST':
        # Convert the received data to JSON format
        json_data = json.dumps(request.data, indent=4)

        # Print the received data to the console for debugging
        print("Received POST data:", json_data)

        # Define the path to save the file
        file_path = "post_data.json"

        # Write the JSON data to a file
        with open(file_path, 'w') as file:
            file.write(json_data)

        # Optionally, return the data back in the response for testing
        return Response(request.data, status=status.HTTP_200_OK)


@csrf_exempt  # Disable CSRF protection for this view
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_workouts(request):
    user = request.user
    print("Authorization Header:", request.headers.get('Authorization'))
    print(user.username)

    parsed_workouts = []

    for workout in request.data.get('workout_data', []):
        workout_type = workout['value'].get('workoutActivityType')

        if workout_type != "WALKING":
            total_energy_burned = workout['value'].get('totalEnergyBurned') or 0
            start_date = workout.get('start_date')
            end_date = workout.get('end_date')

            if start_date and end_date:
                start_dt = timezone.make_aware(datetime.fromisoformat(start_date.replace("Z", "")))
                end_dt = timezone.make_aware(datetime.fromisoformat(end_date.replace("Z", "")))
                duration = end_dt - start_dt

                # Check if duration is less than 5 minutes
                if duration < timedelta(minutes=5):
                    print(f"Workout duration {duration} is less than 5 minutes. Skipping.")
                    continue

            if Workout.objects.filter(user=user, workout_date=start_dt).exists():
                print(f"Workout on {start_dt} already exists for {user.username}. Skipping.")
                continue

            heart_rates = [
                hr['value']['numericValue']
                for hr in request.data.get('heartrate_data', [])
                if hr.get('start_date') and hr.get('end_date')
                   and start_dt <= timezone.make_aware(
                    datetime.fromisoformat(hr['start_date'].replace("Z", ""))) <= end_dt
            ]

            if heart_rates:
                avg_heart_rate = sum(heart_rates) / len(heart_rates)
            else:
                # Calculate the average of previous average heart rates
                previous_workouts = Workout.objects.filter(user=user).exclude(avg_heart_rate__lte=0)
                prev_avg_heart_rates = previous_workouts.values_list('avg_heart_rate', flat=True)

                if prev_avg_heart_rates:
                    avg_heart_rate = sum(prev_avg_heart_rates) / len(prev_avg_heart_rates)
                else:
                    avg_heart_rate = 0  # Default to 0 if no previous data is available

            workout_instance = Workout.objects.create(
                user=user,
                duration=duration,
                workout_date=start_dt,
                avg_heart_rate=avg_heart_rate,
                mood=workout.get('mood', 2),
                energy_burned=total_energy_burned
            )

            parsed_workouts.append({
                'id': workout_instance.id,
                'workoutActivityType': workout_type,
                'totalEnergyBurned': total_energy_burned,
                'start_date': start_date,
                'end_date': end_date,
                'duration': duration.total_seconds(),
                'average_heart_rate': avg_heart_rate
            })

    return Response({
        'user': user.username,
        'parsed_data': parsed_workouts
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def last_workout(request):
    today = datetime.now().date() - timedelta(days=1)

    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = make_aware(datetime.combine(start_of_week, datetime.min.time()))

    workouts = Workout.objects.filter(user=request.user, workout_date__gte=start_of_week).order_by('-workout_date')

    workout_durations = [0] * 7

    for workout in workouts:
        day_index = workout.workout_date.weekday()
        duration_minutes = int(workout.duration.total_seconds() // 60)
        workout_durations[day_index] += duration_minutes

    latest_workout = Workout.objects.filter(user=request.user).order_by('-workout_date').first()
    if latest_workout:
        workout_data = {
            'totalEnergyBurned': latest_workout.energy_burned,
            'start_date': latest_workout.workout_date.strftime('%b %d'),  # Format as "May 12"
            'duration': int(latest_workout.duration.total_seconds() // 60),  # Convert to minutes, remove decimal
            'average_heart_rate': latest_workout.avg_heart_rate,
            'mood': latest_workout.mood,
            'workout_durations': workout_durations,
            'muscleGroups': ", ".join(str(muscle) for muscle in
                                      latest_workout.muscle_groups.all()) if latest_workout.muscle_groups.exists() else ""

        }
        return Response(workout_data, status=status.HTTP_200_OK)
    else:
        return Response({
            'message': 'No workout data available for the user.'
        }, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_latest_muscle_groups(request):
    latest_workout = Workout.objects.filter(user=request.user).order_by('-workout_date').first()

    if not latest_workout:
        return Response({'error': 'No workout data available to update.'}, status=status.HTTP_404_NOT_FOUND)

    muscle_group_names = request.data.get('muscleGroups')
    if not muscle_group_names:
        return Response({'error': 'No muscle groups provided.'}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve or create MuscleGroup instances based on names
    muscle_groups = []
    for name in muscle_group_names:
        muscle_group, created = MuscleGroup.objects.get_or_create(name=name)
        muscle_groups.append(muscle_group)

    # Set the muscle groups for the latest workout with their IDs
    latest_workout.muscle_groups.set([mg.id for mg in muscle_groups])
    latest_workout.save()

    return Response({'message': 'Muscle groups updated successfully.'}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def this_weeks_workouts(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = make_aware(datetime.combine(start_of_week, datetime.min.time()))

    workouts = Workout.objects.filter(user=request.user, workout_date__gte=start_of_week).order_by('-workout_date')

    workout_data = [
        {
            'day_of_week': workout.workout_date.strftime('%A'),
            'duration': int(workout.duration.total_seconds() // 60),
        }
        for workout in workouts
    ]

    return Response(workout_data, status=status.HTTP_200_OK if workout_data else status.HTTP_404_NOT_FOUND)

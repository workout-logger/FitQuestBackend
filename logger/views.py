# views.py
import json
from datetime import datetime, timedelta

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import make_aware

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Workout
from exercises.models import MuscleGroup, Exercise
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

CALORIES_PER_SET = 30  # Calories burned per set
STRENGTH_GAIN_PER_SET = 1  # Strength gained per set
AGILITY_GAIN_PER_SET = 1  # Agility gained per set
SPEED_GAIN_PER_SET = 1  # Speed gained per set


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workout_receiver(request):
    """
    Handles incoming workout data and saves it to the database.
    Calculates energy burned and attribute gains based on the number of sets.
    Resets stats if the last workout was within 24 hours.
    """
    try:
        user = request.user
        data = request.data

        # -----------------------
        # 1. Validate and Extract Data
        # -----------------------
        print(data)
        # Duration
        duration_ms = data.get("duration")
        if duration_ms is None:
            return JsonResponse({"error": "Duration is required."}, status=400)
        try:
            duration_ms = int(duration_ms)
            if duration_ms < 0:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "Duration must be a non-negative integer representing milliseconds."},
                                status=400)
        duration = timedelta(milliseconds=duration_ms)

        # Average Heart Rate
        avg_heart_rate = data.get("avg_heart_rate", 100)
        try:
            avg_heart_rate = int(avg_heart_rate)
            if not (30 <= avg_heart_rate <= 220):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "Average heart rate must be an integer between 30 and 220."}, status=400)

        # Mood
        mood = data.get("mood", 2)
        try:
            mood = int(mood)
            if not (1 <= mood <= 3):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "Mood must be an integer between 1 and 3."}, status=400)

        # Exercises
        exercises = data.get("exercises", [])
        if not isinstance(exercises, list) or not exercises:
            return JsonResponse({"error": "Exercises must be a non-empty list."}, status=400)

        # -----------------------
        # 2. Check Last Workout
        # -----------------------
        last_workout = Workout.objects.filter(user=user).order_by('-workout_date').first()
        within_24_hours = False
        if last_workout:
            time_difference = timezone.now() - last_workout.workout_date
            within_24_hours = time_difference <= timedelta(hours=24)

        # -----------------------
        # 3. Start Transaction
        # -----------------------
        with transaction.atomic():
            # Create Workout object without exercises_done and muscle_groups
            workout = Workout.objects.create(
                user=user,
                duration=duration,
                workout_date=timezone.now(),
                avg_heart_rate=avg_heart_rate,
                mood=mood,
                energy_burned=0.0,  # Will update later
                strength_gained=0,
                agility_gained=0,
                speed_gained=0,
            )

            # Initialize totals
            total_calories = 0.0
            total_strength = 0
            total_agility = 0
            total_speed = 0
            muscle_groups_set = set()

            for idx, exercise_data in enumerate(exercises, start=1):
                # Validate each exercise entry
                if not isinstance(exercise_data, dict):
                    print(f"Exercise entry {idx} is not a dictionary. Skipping.")
                    continue

                exercise_name = exercise_data.get("name")
                sets = exercise_data.get("sets", 1)
                reps = exercise_data.get("reps", 1)  # Not used in calculation, but can be stored if needed

                # Validate exercise_name
                if not exercise_name:
                    print(f"Exercise entry {idx} missing 'name'. Skipping.")
                    continue

                # Validate sets
                try:
                    sets = int(sets)
                    if sets < 1:
                        raise ValueError
                except (ValueError, TypeError):
                    print(f"Exercise entry {idx} has invalid 'sets'. Defaulting to 1.")
                    sets = 1

                # Validate reps (optional)
                try:
                    reps = int(reps)
                    if reps < 1:
                        raise ValueError
                except (ValueError, TypeError):
                    print(f"Exercise entry {idx} has invalid 'reps'. Defaulting to 1.")
                    reps = 1

                # Retrieve the exercise object
                try:
                    exercise = Exercise.objects.get(name=exercise_name)
                except Exercise.DoesNotExist:
                    print(f"Exercise '{exercise_name}' does not exist. Skipping.")
                    continue

                # Add to exercises_done
                workout.exercises_done.add(exercise)

                # Accumulate muscle groups
                muscle_groups = exercise.muscle_groups.all()
                for mg in muscle_groups:
                    muscle_groups_set.add(mg)

                # Calculate calories for this exercise
                calories = CALORIES_PER_SET * sets
                total_calories += calories

                # Calculate attribute gains
                strength_gain = STRENGTH_GAIN_PER_SET * sets
                agility_gain = AGILITY_GAIN_PER_SET * sets
                speed_gain = SPEED_GAIN_PER_SET * sets

                total_strength += strength_gain
                total_agility += agility_gain
                total_speed += speed_gain

            # Assign muscle groups to the workout
            workout.muscle_groups.set(muscle_groups_set)

            # Update energy_burned and attribute gains
            workout.energy_burned = total_calories
            if not within_24_hours:
                workout.strength_gained = min(total_strength, 5)
                workout.agility_gained = min(total_agility, 5)
                workout.speed_gained = min(total_speed, 5)
            else:
                workout.strength_gained = 0
                workout.agility_gained = 0
                workout.speed_gained = 0
            workout.save()
            user.strength += min(total_strength, 5)
            user.agility += min(total_agility, 5)
            user.speed += min(total_speed, 5)
            user.save()

        # -----------------------
        # 4. Return Success Response
        # -----------------------
        return JsonResponse({
            "message": "Workout saved successfully.",
            "total_calories": total_calories,
            "strength_gained": workout.strength_gained,
            "agility_gained": workout.agility_gained,
            "speed_gained": workout.speed_gained
        }, status=201)

    except Exception as e:
        # Log the exception using Django's logging framework
        print("Error saving workout: %s", str(e))
        return JsonResponse({"error": "An internal error occurred. Please try again later."}, status=500)


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
    from datetime import datetime, timedelta
    from django.utils.timezone import now as timezone_now
    from rest_framework.response import Response
    from rest_framework import status

    # Get the current time (timezone-aware) and the start of this week (Monday)
    now = timezone_now()
    monday_of_week = now.date() - timedelta(days=now.weekday())  # Start of the week
    start_of_week = make_aware(datetime.combine(monday_of_week, datetime.min.time()))

    # Debug: Log the current time and filtering range
    print(f"Current time (now): {now}")
    print(f"Start of the week: {start_of_week}")

    # Filter workouts from Monday to now
    workouts = Workout.objects.filter(
        user=request.user,
        workout_date__gte=start_of_week,
        workout_date__lte=now  # Ensure filtering includes current time
    ).order_by('-workout_date')

    # Debug: Log the query and fetched workouts
    print(f"Query: {workouts.query}")
    print(f"Fetched workouts: {list(workouts)}")

    # Initialize workout durations for each day of the week (Monday=0, Sunday=6)
    workout_durations = [0] * 7

    for workout in workouts:
        day_index = workout.workout_date.weekday()  # Determine the day of the week
        duration_minutes = int(workout.duration.total_seconds() // 60)  # Convert duration to minutes
        workout_durations[day_index] += duration_minutes

    # Fetch the most recent workout
    latest_workout = workouts.first()  # Use already filtered workouts
    if latest_workout:
        workout_data = {
            'totalEnergyBurned': latest_workout.energy_burned,
            'start_date': latest_workout.workout_date.strftime('%b %d'),  # e.g., "Jan 12"
            'duration': int(latest_workout.duration.total_seconds() // 60),  # Convert to minutes
            'average_heart_rate': latest_workout.avg_heart_rate,
            'mood': latest_workout.mood,
            'workout_durations': workout_durations,
            'muscleGroups': ", ".join(
                str(muscle) for muscle in latest_workout.muscle_groups.all()
            ) if latest_workout.muscle_groups.exists() else "",
            'stats': f"+{latest_workout.strength_gained}, +{latest_workout.agility_gained}, +{latest_workout.speed_gained}",
        }
        return Response(workout_data, status=status.HTTP_200_OK)
    else:
        return Response(
            {'message': 'No workout data available for the user.'},
            status=status.HTTP_404_NOT_FOUND
        )


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
    from datetime import datetime, timedelta
    from django.utils.timezone import make_aware
    from rest_framework.response import Response
    from rest_framework import status

    # Get today's date
    today = datetime.now().date()

    # Calculate the most recent Monday
    monday_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is the start of the week
    start_of_week = make_aware(datetime.combine(monday_of_week, datetime.min.time()))

    # Fetch workouts for the current user, starting from Monday
    workouts = Workout.objects.filter(
        user=request.user,
        workout_date__gte=start_of_week
    ).order_by('-workout_date')

    # Prepare workout data
    workout_data = [
        {
            'day_of_week': workout.workout_date.strftime('%A'),
            'duration': int(workout.duration.total_seconds() // 60),  # Convert duration to minutes
        }
        for workout in workouts
    ]
    print(workout_data)
    # Return the response
    return Response(
        workout_data,
        status=status.HTTP_200_OK if workout_data else status.HTTP_404_NOT_FOUND
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def past_workouts(request):
    """
    Retrieve all past workouts of the authenticated user without using a serializer.
    A workout is considered past if its workout_date is earlier than the current time.
    """
    try:
        # Get the current time
        now = timezone.now()

        # Query for workouts where workout_date is in the past
        workouts = Workout.objects.filter(user=request.user, workout_date__lt=now).order_by('-workout_date')

        # Manually construct the list of workouts
        workout_list = []
        for workout in workouts:
            workout_data = {
                'id': workout.id,
                'duration': int(workout.duration.total_seconds()),  # Duration in seconds
                'workout_date': workout.workout_date.isoformat(),
                'avg_heart_rate': workout.avg_heart_rate,
                'mood': workout.mood,
                'energy_burned': workout.energy_burned,
                'strength_gained': workout.strength_gained,
                'agility_gained': workout.agility_gained,
                'speed_gained': workout.speed_gained,
                'exercises_done': list(workout.exercises_done.values('id', 'name')),
                'muscle_groups': list(workout.muscle_groups.values('id', 'name')),
                'created_at': workout.created_at.isoformat() if hasattr(workout, 'created_at') else None,
                'updated_at': workout.updated_at.isoformat() if hasattr(workout, 'updated_at') else None,
            }
            workout_list.append(workout_data)

        # Return the constructed list as JSON
        return JsonResponse(workout_list, safe=False, status=status.HTTP_200_OK)

    except Exception as e:
        # Log the exception (replace print with proper logging as needed)
        print(f"Error retrieving past workouts: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching past workouts."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

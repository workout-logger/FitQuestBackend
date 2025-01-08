from exercises.models import MuscleGroup

# Mapping of old names to new readable names
rename_map = {
    "should": "Shoulder",
    "hip abductors": "Hip Abductors",
    "quadriceps": "Quadriceps",
    "obliques": "Obliques",
    "glutaeus maximus": "Gluteus Maximus",
    "soleus": "Soleus",
    "gastrocnemius": "Gastrocnemius",
    "ischiocrural muscles": "Hamstrings",
    "deltoideus (clavicula)": "Clavicular Deltoid",
    "core": "Core",
    "erector spinae": "Erector Spinae",
    "back": "Back",
    "abdominals": "Abdominals",
    "latissimus dorsi": "Latissimus Dorsi",
    "upper back": "Upper Back",
    "biceps brachii": "Biceps Brachii",
    "forearm": "Forearm",
    "pectoralis major": "Pectoralis Major",
    "triceps brachii": "Triceps Brachii",
    "deltoid": "Deltoid",
    "trapezius": "Trapezius",
}

# Update names in the database
for old_name, new_name in rename_map.items():
    try:
        muscle_group = MuscleGroup.objects.get(name=old_name)
        muscle_group.name = new_name
        muscle_group.save()
        print(f"Renamed '{old_name}' to '{new_name}'")
    except MuscleGroup.DoesNotExist:
        print(f"Muscle group '{old_name}' not found")

from exercises.models import MuscleGroup, Exercise

from django.db import transaction
from exercises.models import MuscleGroup, Exercise

from django.db import transaction
from exercises.models import MuscleGroup, Exercise

def merge_muscle_groups(merge_map):
    """
    Merge muscle groups based on the provided mapping.

    :param merge_map: Dictionary where keys are new names and values are lists of old names to merge.
    """
    for new_name, old_names in merge_map.items():
        # Get or create the new muscle group
        new_group, created = MuscleGroup.objects.get_or_create(name=new_name)
        if created:
            print(f"Created new muscle group '{new_name}'")
        else:
            print(f"Using existing muscle group '{new_name}'")

        for old_name in old_names:
            if old_name == new_name:
                print(f"Skipping merge of '{old_name}' into itself.")
                continue  # Skip if the old name is the same as the new name

            try:
                old_group = MuscleGroup.objects.get(name=old_name)

                with transaction.atomic():
                    # Reassign exercises from the old group to the new group
                    exercises = Exercise.objects.filter(muscle_groups=old_group)
                    for exercise in exercises:
                        if not exercise.muscle_groups.filter(id=new_group.id).exists():
                            exercise.muscle_groups.add(new_group)

                    # After reassignment, remove the old muscle group from all exercises
                    for exercise in exercises:
                        exercise.muscle_groups.remove(old_group)

                    # Finally, delete the old muscle group
                    old_group.delete()
                    print(f"Merged '{old_name}' into '{new_name}'")

            except MuscleGroup.DoesNotExist:
                print(f"Muscle group '{old_name}' does not exist")



# Define the mapping of new names to old names to merge
merge_map = {
    "Legs": ["Soleus", "Gastrocnemius"],
    "Shoulders": ["Trapezius"],
    "Back": ["Latissimus Dorsi", "Upper Back"],
    "Core": ["Obliques", "Abdominals"],
    "Biceps": ["Biceps Brachii"],
    "Triceps": ["Triceps Brachii"],
    "Forearms": ["Forearm"],
    "Chest": ["Pectoralis Major"],
    "Glutes": ["Gluteus Maximus"],
    "Lower Back": ["Erector Spinae"]
}


# Call the function to perform the merge
merge_muscle_groups(merge_map)

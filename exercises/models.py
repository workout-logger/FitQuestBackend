from django.db import models

class MuscleGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    name = models.CharField(max_length=100)
    muscle_groups = models.ManyToManyField(MuscleGroup)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Image(models.Model):
    exercise = models.ForeignKey(Exercise, related_name='images', on_delete=models.CASCADE)
    url = models.URLField(max_length=200)

    def __str__(self):
        return f"Image for {self.exercise.name}"
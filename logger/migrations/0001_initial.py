# Generated by Django 4.2.13 on 2024-11-30 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('exercises', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Workout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DurationField(help_text='Duration of the workout (e.g., HH:MM:SS)')),
                ('workout_date', models.DateTimeField(help_text='Date and time of the workout captured from the watch')),
                ('avg_heart_rate', models.IntegerField(help_text='Average Heart Rate for Workout')),
                ('mood', models.IntegerField(help_text='1-3 From Sad To Happy')),
                ('energy_burned', models.FloatField(help_text='Kcal')),
                ('exercises_done', models.ManyToManyField(to='exercises.exercise')),
                ('muscle_groups', models.ManyToManyField(blank=True, to='exercises.musclegroup')),
            ],
        ),
    ]

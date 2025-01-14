from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    BODY_COLOR_CHOICES = [
        (1, 'Color 1'),
        (2, 'Color 2'),
        (3, 'Color 3'),
        (4, 'Color 4'),
        (5, 'Color 5'),
    ]

    EYE_COLOR_CHOICES = [
        (1, 'Eye Color 1'),
        (2, 'Eye Color 2'),
        (3, 'Eye Color 3'),
        (4, 'Eye Color 4'),
        (5, 'Eye Color 5'),
    ]

    bio = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    coins = models.PositiveIntegerField(default=0)
    body_color = models.PositiveSmallIntegerField(choices=BODY_COLOR_CHOICES, blank=True, null=True)
    eye_color = models.PositiveSmallIntegerField(choices=EYE_COLOR_CHOICES, blank=True, null=True)

    strength = models.PositiveIntegerField(default=10, help_text="Player's strength attribute.")
    agility = models.PositiveIntegerField(default=10, help_text="Player's agility attribute.")
    intelligence = models.PositiveIntegerField(default=10, help_text="Player's intelligence attribute.")
    stealth = models.PositiveIntegerField(default=10, help_text="Player's stealth attribute.")
    speed = models.PositiveIntegerField(default=10, help_text="Player's speed attribute.")
    defence = models.PositiveIntegerField(default=10, help_text="Player's defence attribute.")

    def __str__(self):
        return self.username
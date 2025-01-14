from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.utils.timezone import now

User = get_user_model()


class Item(models.Model):
    CATEGORY_CHOICES = [
        ('wings', 'Wings'),
        ('headpiece', 'Headpiece'),
        ('armour', 'Armour'),
        ('melee', 'Melee'),
        ('shield', 'Shield'),
        ('legs', 'Legs'),
        ('coins', 'Coins'),
    ]

    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    file_name = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')

    strength = models.PositiveIntegerField(default=0, help_text="Player's strength attribute.")
    agility = models.PositiveIntegerField(default=0, help_text="Player's agility attribute.")
    intelligence = models.PositiveIntegerField(default=0, help_text="Player's intelligence attribute.")
    stealth = models.PositiveIntegerField(default=0, help_text="Player's stealth attribute.")
    speed = models.PositiveIntegerField(default=0, help_text="Player's speed attribute.")
    defence = models.PositiveIntegerField(default=0, help_text="Player's defence attribute.")


    def __str__(self):
        return f"{self.name} ({self.category})"


class Inventory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory')
    items = models.ManyToManyField(Item, related_name='inventories')

    def __str__(self):
        return f"Inventory of {self.user.username}"


class EquippedItem(models.Model):
    inventory = models.OneToOneField(
        Inventory, on_delete=models.CASCADE, related_name='equipped_items'
    )
    wings = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_wings'
    )
    legs = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_legs'
    )
    headpiece = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_headpieces'
    )
    shield = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_shields'
    )
    melee = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_melee'
    )
    armour = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_armours'
    )

    def __str__(self):
        return f"Equipped items for {self.inventory.user.username}"


class Chest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    cost = models.PositiveIntegerField()
    item_pool = models.ManyToManyField(Item, related_name='chests')

    def __str__(self):
        return f"{self.name} (Cost: {self.cost})"


class MarketListing(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='listings')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='market_listings')
    listed_price = models.DecimalField(max_digits=10, decimal_places=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - ${self.listed_price}"

class DungeonSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_health = models.PositiveIntegerField(default=100)
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(null=True, blank=True)
    items_collected = models.ManyToManyField('Item', related_name='dungeon_sessions', blank=True)
    next_item_time = models.DateTimeField(null=True, blank=True)
    npc_event_triggered = models.BooleanField(default=False)
    npc_event_data = models.JSONField(null=True, blank=True)  # Stores the paused NPC event data
    paused = models.BooleanField(default=False)  # Indicates if the session is waiting for user input
    logs = models.JSONField(null=True, blank=True, default=list)  # Initialize as empty list
    next_escapade_time = models.DateTimeField(default=now)  # Initialize to start_time by default

    def save(self, *args, **kwargs):
        if not self.pk and not self.next_escapade_time:
            self.next_escapade_time = self.start_time + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def add_log(self, message):
        """Append a new log entry to the logs field."""
        if self.logs is None:
            self.logs = []
        self.logs.append({
            "timestamp": now().isoformat(),
            "message": message
        })
        self.save(update_fields=['logs'])

class NPC(models.Model):
    """
    Represents an NPC (Non-Player Character) in the game.
    """
    name = models.CharField(max_length=100)
    short_description = models.TextField()
    likes = models.TextField()  # A comma-separated list of things the NPC likes
    dislikes = models.TextField()  # A comma-separated list of things the NPC dislikes
    file_name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

    def get_likes_list(self):
        """Returns likes as a list."""
        return [like.strip() for like in self.likes.split(",")]

    def get_dislikes_list(self):
        """Returns dislikes as a list."""
        return [dislike.strip() for dislike in self.dislikes.split(",")]
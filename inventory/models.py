from django.db import models
from django.conf import settings


class Item(models.Model):
    CATEGORY_CHOICES = [
        ('wings', 'Wings'),
        ('headpiece', 'Headpiece'),
        ('armour', 'Armour'),
        ('melee', 'Melee'),
        ('shield', 'Shield'),
        ('legs', 'Legs'),
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

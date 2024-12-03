from django.db import models
from django.conf import settings


class Item(models.Model):
    CATEGORY_CHOICES = [
        ('wings', 'Wings'),
        ('headpiece', 'Headpiece'),
        ('armour', 'Armour'),
        ('melee_weapon', 'Melee_weapon'),
        ('shield', 'Shield'),
        ('legs', 'Legs'),
    ]
    file_name = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

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
    melee_weapon = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_melee_weapons'
    )
    armour = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='equipped_armours'
    )

    def __str__(self):
        return f"Equipped items for {self.inventory.user.username}"

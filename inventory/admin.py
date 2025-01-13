# inventory/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Item, Inventory, EquippedItem, Chest, NPC
from .forms import ItemForm


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ('id', 'name', 'category', 'rarity', 'strength', 'agility', 'intelligence', 'stealth', 'speed', 'defence')
    search_fields = ('name', 'category', 'rarity','strength', 'agility', 'intelligence', 'stealth', 'speed', 'defence')
    list_filter = ('category',)
    ordering = ('id',)


@admin.register(NPC)
class NPCAdmin(admin.ModelAdmin):
    # Display these fields in the admin list view
    list_display = ('name', 'short_description', 'file_name')

    # Add search functionality for name and short description
    search_fields = ('name', 'short_description')

    # Display these fields in the detail/edit view
    fields = ('name', 'short_description', 'likes', 'dislikes', 'file_name')

    # Read-only display of likes and dislikes as lists (optional for better insights)
    readonly_fields = ('display_likes_list', 'display_dislikes_list')

    def display_likes_list(self, obj):
        """Displays likes as a list in the admin panel."""
        return obj.get_likes_list()

    def display_dislikes_list(self, obj):
        """Displays dislikes as a list in the admin panel."""
        return obj.get_dislikes_list()

    display_likes_list.short_description = "Likes (List)"
    display_dislikes_list.short_description = "Dislikes (List)"

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__username',)
    filter_horizontal = ('items',)
    ordering = ('id',)

    def get_queryset(self, request):
        """
        Customize the queryset to prefetch related items for optimization.
        """
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('items')


@admin.register(EquippedItem)
class EquippedItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'inventory', 'legs', 'headpiece', 'shield', 'melee', 'armour')
    search_fields = ('inventory__user__username',)
    list_select_related = ('inventory', 'legs', 'headpiece', 'shield', 'melee', 'armour')
    ordering = ('id',)

    def get_queryset(self, request):
        """
        Customize the queryset to prefetch related inventory and items for optimization.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'inventory',
            'legs',
            'headpiece',
            'shield',
            'melee',
            'armour'
        )

    def save_model(self, request, obj, form, change):
        # Ensure the inventory exists
        if not obj.inventory:
            raise ValidationError("EquippedItem must be associated with a valid inventory.")
        # Ensure all equipped items exist in the inventory
        equipped_items = [obj.legs, obj.headpiece, obj.shield, obj.melee, obj.armour]
        for item in equipped_items:
            if item and item not in obj.inventory.items.all():
                raise ValidationError(f"The item '{item}' is not part of the inventory.")
        super().save_model(request, obj, form, change)


@admin.register(Chest)
class ChestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cost')
    search_fields = ('name',)
    filter_horizontal = ('item_pool',)
    ordering = ('id',)

    def save_model(self, request, obj, form, change):
        """
        Save the Chest instance first, then update the item_pool.
        """
        # Save the Chest object to generate an ID
        if not obj.pk:
            super().save_model(request, obj, form, change)

        # Update the item_pool after the object has an ID
        item_pool = form.cleaned_data.get('item_pool', [])
        if item_pool:
            obj.item_pool.set(item_pool)  # Use set to ensure items are updated
        super().save_model(request, obj, form, change)

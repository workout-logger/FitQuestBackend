# inventory/admin.py
from django.contrib import admin
from .models import Item, Inventory, EquippedItem
from django.core.exceptions import ValidationError


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    search_fields = ('name', 'category')
    list_filter = ('category',)
    ordering = ('id',)


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
    list_display = ('id', 'inventory', 'legs', 'headpiece', 'shield', 'melee_weapon', 'armour')
    search_fields = ('inventory__user__username',)
    list_select_related = ('inventory', 'legs', 'headpiece', 'shield', 'melee_weapon', 'armour')
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
            'melee_weapon',
            'armour'
        )

    def save_model(self, request, obj, form, change):
        # Ensure the inventory exists
        if not obj.inventory:
            raise ValidationError("EquippedItem must be associated with a valid inventory.")
        # Ensure all equipped items exist in the inventory
        equipped_items = [obj.legs, obj.headpiece, obj.shield, obj.melee_weapon, obj.armour]
        for item in equipped_items:
            if item and item not in obj.inventory.items.all():
                raise ValidationError(f"The item '{item}' is not part of the inventory.")
        super().save_model(request, obj, form, change)

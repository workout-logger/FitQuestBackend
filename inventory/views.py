from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Inventory, EquippedItem, Chest


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_equipped_items(request):
    try:
        # Fetch the user's inventory
        inventory = Inventory.objects.get(user=request.user)

        # Get equipped items
        equipped_items = EquippedItem.objects.get(inventory=inventory)
        equipped_data = {
            "legs": equipped_items.legs.file_name if equipped_items.legs else None,
            "headpiece": equipped_items.headpiece.file_name if equipped_items.headpiece else None,
            "shield": equipped_items.shield.file_name if equipped_items.shield else None,
            "melee": equipped_items.melee.file_name if equipped_items.melee else None,
            "armour": equipped_items.armour.file_name if equipped_items.armour else None,
            "wings": equipped_items.wings.file_name if equipped_items.wings else None,
        }

        return JsonResponse({"success": True, "equipped_items": equipped_data}, status=200)

    except Inventory.DoesNotExist:
        return JsonResponse({"success": False, "message": "Inventory not found."}, status=404)

    except EquippedItem.DoesNotExist:
        return JsonResponse({"success": False, "equipped_items": {}}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_chest(request):
    try:
        chest_id = request.data.get('chest_id')
        user = request.user  # Get the user object
        user_currency = user.coins  # Assuming coins is a field on the user model

        # Fetch the chest
        chest = Chest.objects.get(id=chest_id)

        if user_currency < chest.cost:
            return JsonResponse({"success": False, "message": "Not enough currency to buy this chest."}, status=400)

        # Deduct the cost from the user's currency
        user.coins -= chest.cost
        user.save()  # Save the updated user instance

        # Add up to 5 random items from the chest's item pool to the user's inventory
        inventory, created = Inventory.objects.get_or_create(user=user)
        random_items = chest.item_pool.order_by('?')[:5]  # Get up to 5 random items
        if not random_items.exists():
            return JsonResponse({"success": False, "message": "The chest has no items available."}, status=400)

        for item in random_items:
            inventory.items.add(item)

        # Include all relevant fields for each item in the response
        received_items = [
            {
                "id": item.id,
                "itemName": item.name,
                "category": item.category,  # Example: Weapon, Armor, etc.
                "rarity": item.rarity,  # Example: Common, Rare, Epic
                "fileName": item.file_name,

            }
            for item in random_items
        ]

        return JsonResponse({
            "success": True,
            "message": "You have received the following items:",
            "items": received_items,
        }, status=200)

    except Chest.DoesNotExist:
        return JsonResponse({"success": False, "message": "Chest not found."}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Inventory, EquippedItem


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
            "headpiece": equipped_items.headpiece.file_name if equipped_items.headpiece else "head_blue.png",
            "shield": equipped_items.shield.file_name if equipped_items.shield else None,
            "melee": equipped_items.melee.file_name if equipped_items.melee else None,
            "armour": equipped_items.armour.file_name if equipped_items.armour else "armour_amber.png",
            "wings": equipped_items.wings.file_name if equipped_items.wings else None,
        }

        return JsonResponse({"success": True, "equipped_items": equipped_data}, status=200)

    except Inventory.DoesNotExist:
        return JsonResponse({"success": False, "message": "Inventory not found."}, status=404)

    except EquippedItem.DoesNotExist:
        return JsonResponse({"success": False, "equipped_items": {}}, status=200)

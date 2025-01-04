from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Inventory, EquippedItem, Chest, MarketListing


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_listing(request):
    try:
        item_name = request.data.get('item_name')
        price = request.data.get('price')

        # Validate inputs
        if not item_name or not price:
            return JsonResponse({"success": False, "message": "Item name and price are required."}, status=400)

        # Check if the inventory exists for the user
        inventory = get_object_or_404(Inventory, user=request.user)

        # Find the item in the user's inventory by name
        item = inventory.items.filter(name=item_name).first()
        if not item:
            return JsonResponse({"success": False, "message": f"Item '{item_name}' not found in inventory."}, status=404)

        # Create a new market listing
        listing = MarketListing.objects.create(
            item=item,
            seller=request.user,
            listed_price=price
        )

        return JsonResponse({
            "success": True,
            "message": "Item listed successfully.",
            "listing": {
                "id": listing.id,
                "itemName": listing.item.name,
                "price": listing.listed_price,
                "category": listing.item.category,
                "rarity": listing.item.rarity
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_from_listing(request):
    try:
        listing_id = request.data.get('listing_id')

        # Validate input
        if not listing_id:
            return JsonResponse({"success": False, "message": "Listing ID is required."}, status=400)

        # Fetch the listing
        listing = get_object_or_404(MarketListing, id=listing_id, is_active=True)

        # Check if the user has enough coins
        buyer = request.user
        if buyer.coins < listing.listed_price:
            return JsonResponse({"success": False, "message": "Not enough currency to buy this item."}, status=400)

        # Deduct coins from the buyer
        buyer.coins -= listing.listed_price
        buyer.save()

        # Add the item to the buyer's inventory
        inventory, _ = Inventory.objects.get_or_create(user=buyer)
        inventory.items.add(listing.item)

        # Mark the listing as inactive
        listing.is_active = False
        listing.save()

        # Add coins to the seller
        listing.seller.coins += listing.listed_price
        listing.seller.save()

        return JsonResponse({
            "success": True,
            "message": f"You successfully bought {listing.item.name}.",
            "item": {
                "id": listing.item.id,
                "itemName": listing.item.name,
                "price": listing.listed_price,
                "category": listing.item.category,
                "rarity": listing.item.rarity
            }
        }, status=200)

    except MarketListing.DoesNotExist:
        return JsonResponse({"success": False, "message": "Listing not found or no longer available."}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def show_listings(request):
    try:
        listings = MarketListing.objects.filter(is_active=True).select_related('item', 'seller')

        listing_data = [
            {
                "id": listing.id,
                "itemName": listing.item.name,
                "price": listing.listed_price,
                "seller": listing.seller.username,
                "category": listing.item.category,
                "rarity": listing.item.rarity
            }
            for listing in listings
        ]

        return JsonResponse({
            "success": True,
            "listings": listing_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

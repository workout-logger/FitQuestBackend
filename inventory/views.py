from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Inventory, EquippedItem, Chest, MarketListing, Item


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
        if not chest_id:
            return JsonResponse(
                {"success": False, "message": "Chest ID is required."},
                status=400
            )

        user = request.user  # Get the user object
        user_currency = user.coins  # Assuming coins is a field on the user model

        # Fetch the chest
        chest = Chest.objects.get(id=chest_id)

        if user_currency < chest.cost:
            return JsonResponse(
                {"success": False, "message": "Not enough currency to buy this chest."},
                status=400
            )

        with transaction.atomic():
            # Deduct the cost from the user's currency
            user.coins -= chest.cost
            user.save()  # Save the updated user instance

            # Add up to 5 items to the user's inventory, ensuring at least 2 are coins
            inventory, created = Inventory.objects.get_or_create(user=user)
            item_pool = chest.item_pool.exclude(category='coins')  # Exclude coins for random selection

            # Fetch or create the coin item
            coin_item = Item.objects.filter(category='coins').first()
            if not coin_item:
                return JsonResponse(
                    {"success": False, "message": "Coin item not found in the database."},
                    status=500
                )



            # Add the value of the coins to the user's currency
            user.coins += 20  # Adjust as per the value each coin should add
            user.save()

            # Randomly select 3 other items from the item pool
            random_items = item_pool.order_by('?')[:3]
            for item in random_items:
                inventory.items.add(item)

            # Function to include only non-zero stats
            def get_item_stats(item):
                stats = {}
                if item.strength > 0:
                    stats["strength"] = item.strength
                if item.agility > 0:
                    stats["agility"] = item.agility
                if item.intelligence > 0:
                    stats["intelligence"] = item.intelligence
                if item.stealth > 0:
                    stats["stealth"] = item.stealth
                if item.speed > 0:
                    stats["speed"] = item.speed
                if item.defence > 0:
                    stats["defence"] = item.defence
                return stats

            # Prepare response with all received items, including their non-zero stats
            received_items = []
            # Add coin items first
            for _ in range(2):
                received_items.append({
                    "id": coin_item.id,
                    "itemName": coin_item.name,
                    "category": coin_item.category,
                    "rarity": coin_item.rarity,
                    "fileName": coin_item.file_name,
                    # Assuming coins don't have stats; omit if they do, similar to below
                })
            # Add random items
            for item in random_items:
                item_data = {
                    "id": item.id,
                    "itemName": item.name,
                    "category": item.category,
                    "rarity": item.rarity,
                    "fileName": item.file_name,
                }
                item_stats = get_item_stats(item)
                item_data.update(item_stats)
                received_items.append(item_data)

            return JsonResponse({
                "success": True,
                "message": "You have received the following items:",
                "items": received_items,
                "currency": user.coins,
            }, status=200)

    except Chest.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Chest not found."},
            status=404
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": str(e)},
            status=500
        )

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

        # Check if the buyer already owns the item (based on the item name)
        buyer = request.user
        inventory, _ = Inventory.objects.get_or_create(user=buyer)
        if inventory.items.filter(name=listing.item.name).exists():
            return JsonResponse({"success": False, "message": "You already own this item."}, status=400)

        # Check if the user has enough coins
        if buyer.coins < listing.listed_price:
            return JsonResponse({"success": False, "message": "Not enough currency to buy this item."}, status=400)

        # Deduct coins from the buyer
        buyer.coins -= listing.listed_price
        buyer.save()

        # Add the item to the buyer's inventory
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
                "fileName": (
                    f"assets/character/{listing.item.category}/{listing.item.file_name}"
                    if listing.item.category.lower() == "armour"
                    else f"assets/character/{listing.item.category}/{listing.item.file_name}_inv"
                ),
                "price": listing.listed_price,
                "seller": listing.seller.username,
                "category": listing.item.category,
                "rarity": listing.item.rarity,
            }
            for listing in listings
        ]

        return JsonResponse({
            "success": True,
            "listings": listing_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

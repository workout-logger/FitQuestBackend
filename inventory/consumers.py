# inventory/consumers.py
from random import choice

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async, async_to_sync
import logging

from django.utils.timezone import now


logger = logging.getLogger(__name__)
class InventoryConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None


    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            # Allow connection
            await self.accept()

            # # Load and send inventory data
            inventory_data = await self.get_inventory_data()
            await self.send_inventory_update(inventory_data)

            currency_data = await self.get_currency_data()
            await self.send_currency_update(currency_data)
        else:
            # Close connection for unauthenticated users
            await self.close()

    async def disconnect(self, close_code):
        """
        Handles the WebSocket disconnect event.
        """
        pass

    async def receive(self, text_data):
        """
        Handles incoming messages from the WebSocket client.
        """
        data = json.loads(text_data)
        action = data.get("action")

        if action == "add_item":
            item_id = data.get("item_id")
            await self.add_item(item_id)
        elif action == "remove_item":
            item_id = data.get("item_id")
            await self.remove_item(item_id)
        elif action == "equip_item":
            item_name = data.get("item_name")
            category = data.get("category")
            await self.equip_item(item_name, category)
        elif action == "unequip_item":
            category = data.get("category")
            await self.unequip_item(category)
        elif action == "fetch_inventory_data":
            inventory_data = await self.get_inventory_data()
            await self.send_inventory_update(inventory_data)
        elif action == "fetch_currency_data":
            currency_data = await self.get_currency_data()
            await self.send_currency_update(currency_data)
        elif action == "fetch_character_colors":
            colors_data = await self.get_character_colors()
            await self.send_character_colors(colors_data)
        elif action == "add_listing":
            item_id = data.get("item_id")
            price = data.get("price")
            await self.add_listing(item_id, price)
        elif action == "buy_listing":
            listing_id = data.get("listing_id")
            await self.buy_from_listing(listing_id)
        elif action == "fetch_market_listings":
            await self.fetch_market_listings()
        elif action == "start_dungeon":
            await self.handle_start_dungeon()
        elif action == "stop_dungeon":
            await self.stop_dungeon()
        elif action == "handle_dungeon_choice":
            choice_index = data.get("choice_index", 0)
            await self.handle_dungeon_choice(choice_index)
        elif action == "fetch_dungeon_data":
            dungeon_data = await self.get_dungeon_data()
            await self.send(text_data=json.dumps({
                "type": "dungeon_data",
                "data": dungeon_data
            }))
        elif action == "check_dungeon_status":
            await self.is_player_in_dungeon()


    async def send_inventory_update(self, inventory_data):
        """
        Sends the updated inventory data to the client.
        """
        await self.send(text_data=json.dumps({
            "type": "inventory_update",
            "data": inventory_data
        }))

    @sync_to_async
    def get_inventory_data(self):
        from .models import Inventory, EquippedItem
        try:
            inventory = Inventory.objects.get(user=self.user)
            items = inventory.items.all()

            # Initialize equipped_items to handle cases where it might not be set
            equipped_items = None
            equipped_data = {}

            try:
                equipped_items = inventory.equipped_items
                equipped_data = {
                    "legs": equipped_items.legs.file_name if equipped_items.legs else None,
                    "headpiece": equipped_items.headpiece.file_name if equipped_items.headpiece else None,
                    "shield": equipped_items.shield.file_name if equipped_items.shield else None,
                    "melee": equipped_items.melee.file_name if equipped_items.melee else None,
                    "armour": equipped_items.armour.file_name if equipped_items.armour else None,
                    "wings": equipped_items.wings.file_name if equipped_items.wings else None,
                }
            except EquippedItem.DoesNotExist:
                # Log the absence of equipped items if needed
                equipped_items = None

            # Include is_equipped for each item
            item_list = []
            for item in items:
                is_equipped = (
                        equipped_items is not None and any(
                    getattr(equipped_items, key, None) and getattr(equipped_items, key).file_name == item.file_name
                    for key in ["legs", "headpiece", "shield", "melee", "armour", "wings"]
                )
                )
                # Append `_inv` to file_name for everything except armour
                file_name = f"{item.file_name}_inv" if item.category != "armour" else item.file_name

                item_list.append({
                    "id": item.id,
                    "name": item.name,
                    "file_name": item.file_name,
                    "file_name_inv": file_name,
                    "category": item.category,
                    "rarity": item.rarity,
                    "is_equipped": is_equipped
                })

            # Fetch player stats from the user object
            stats = {
                "strength": self.user.strength,
                "agility": self.user.agility,
                "intelligence": self.user.intelligence,
                "stealth": self.user.stealth,
                "speed": self.user.speed,
                "defence": self.user.defence,
            }

            # Add stats from equipped items
            if equipped_items:
                for key in ["legs", "headpiece", "shield", "melee", "armour", "wings"]:
                    item = getattr(equipped_items, key, None)
                    if item:
                        stats["strength"] += getattr(item, "strength", 0)
                        stats["agility"] += getattr(item, "agility", 0)
                        stats["intelligence"] += getattr(item, "intelligence", 0)
                        stats["stealth"] += getattr(item, "stealth", 0)
                        stats["speed"] += getattr(item, "speed", 0)
                        stats["defence"] += getattr(item, "defence", 0)

            return {
                "items": item_list,
                "equipped": equipped_data,
                "stats": stats
            }
        except Inventory.DoesNotExist:
            return {"items": [], "equipped": {}, "stats": {}}  # Default empty stats if no inventory exists

    async def send_currency_update(self, currency_data):
        """
        Sends the updated currency data to the client.
        """
        await self.send(text_data=json.dumps({
            "type": "currency_update",
            "data": currency_data
        }))

    @sync_to_async
    def get_currency_data(self):
        """
        Fetches the user's current currency data.
        """
        from .models import Inventory
        try:
            return {"currency": self.user.coins}  # Assuming currency is a field in the Inventory model
        except Inventory.DoesNotExist:
            return {"currency": 0}

    @sync_to_async
    def add_item(self, item_id):
        """
        Adds an item to the user's inventory.
        """
        from .models import Item, Inventory
        try:
            item = Item.objects.get(id=item_id)
            inventory, _ = Inventory.objects.get_or_create(user=self.user)
            inventory.items.add(item)
        except Item.DoesNotExist:
            pass

    @sync_to_async
    def remove_item(self, item_id):
        from .models import Item, Inventory, EquippedItem
        try:
            item = Item.objects.get(id=item_id)
            inventory = Inventory.objects.get(user=self.user)
            inventory.items.remove(item)
            try:
                equipped_items = inventory.equipped_items
                for field in ["legs", "headpiece", "shield", "wings", "melee", "armour"]:
                    equipped_item = getattr(equipped_items, field)
                    if equipped_item == item:
                        setattr(equipped_items, field, None)
                equipped_items.save()
            except EquippedItem.DoesNotExist:
                pass
        except (Item.DoesNotExist, Inventory.DoesNotExist):
            pass

    @sync_to_async
    def equip_item(self, item_name, category):
        """
        Equips an item in the specified category.
        """
        from .models import Item, Inventory, EquippedItem
        try:
            print(item_name)
            items = Item.objects.filter(file_name=item_name)
            if not items.exists():
                raise Item.DoesNotExist
            print(items)
            item = items.first()  # Handle potential duplicates by taking the first result
            print(item)
            inventory = Inventory.objects.get(user=self.user)
            equipped_items, _ = EquippedItem.objects.get_or_create(inventory=inventory)

            if category in ["legs", "headpiece", "shield", "wings", "melee", "armour"]:
                if item in inventory.items.all() and item.category == category:
                    setattr(equipped_items, category, item)
                    equipped_items.save()
        except (Item.DoesNotExist, Inventory.DoesNotExist):
            print("Item or Inventory does not exist.")

    @sync_to_async
    def unequip_item(self, category):
        """
        Unequips an item from the specified category.
        """
        from .models import Inventory, EquippedItem
        try:
            inventory = Inventory.objects.get(user=self.user)
            equipped_items, _ = EquippedItem.objects.get_or_create(inventory=inventory)

            if category in ["legs", "headpiece", "shield", "wings", "melee", "armour"]:
                setattr(equipped_items, category, None)
                equipped_items.save()
        except Inventory.DoesNotExist:
            pass

    async def send_character_colors(self, colors_data):
        """
        Sends the character colors data to the client.
        """
        print(colors_data)
        await self.send(text_data=json.dumps({
            "type": "character_colors",
            "data": colors_data
        }))

    @sync_to_async
    def get_character_colors(self):
        """
        Fetches the user's body_color and eye_color from the database to ensure up-to-date values.
        """
        # Re-fetch the user object from the database
        user = self.user.__class__.objects.get(pk=self.user.pk)
        return {
            "body_color": user.body_color,
            "eye_color": user.eye_color,
        }

    @sync_to_async
    def create_market_listing(self, item_id, price):
        """
        Creates a marketplace listing for an item.
        """
        from .models import Item, Inventory, MarketListing
        try:
            inventory = Inventory.objects.get(user=self.user)
            item = inventory.items.get(id=item_id)

            # Validate price
            if price <= 0:
                raise ValueError("Price must be greater than zero.")

            # Create listing
            listing = MarketListing.objects.create(
                item=item,
                seller=self.user,
                listed_price=price
            )

            return {
                "id": listing.id,
                "itemName": listing.item.name,
                "price": listing.listed_price,
                "category": listing.item.category,
                "rarity": listing.item.rarity
            }
        except Inventory.DoesNotExist:
            raise ValueError("User inventory not found.")
        except Item.DoesNotExist:
            raise ValueError("Item not found in inventory.")

    async def add_listing(self, item_id, price):
        """
        Adds an item to the marketplace.
        """
        try:
            listing_data = await self.create_market_listing(item_id, price)
            await self.send(text_data=json.dumps({
                "type": "market_listing_added",
                "data": listing_data
            }))
        except ValueError as e:
            await self.send_error(str(e))

    @sync_to_async
    def purchase_market_listing(self, listing_id):
        """
        Handles the purchase of an item from the marketplace.
        """
        from .models import Inventory, MarketListing
        try:
            listing = MarketListing.objects.get(id=listing_id, is_active=True)
            buyer = self.user

            # Check if buyer has enough coins
            if buyer.coins < listing.listed_price:
                raise ValueError("Not enough currency to buy this item.")

            # Deduct coins from buyer
            buyer.coins -= listing.listed_price
            buyer.save()

            # Add item to buyer's inventory
            inventory, _ = Inventory.objects.get_or_create(user=buyer)
            inventory.items.add(listing.item)

            # Mark the listing as inactive
            listing.is_active = False
            listing.save()

            # Add coins to seller
            listing.seller.coins += listing.listed_price
            listing.seller.save()

            return {
                "id": listing.item.id,
                "itemName": listing.item.name,
                "price": listing.listed_price,
                "category": listing.item.category,
                "rarity": listing.item.rarity
            }
        except MarketListing.DoesNotExist:
            raise ValueError("Listing not found or no longer available.")

    async def buy_from_listing(self, listing_id):
        """
        Processes a marketplace purchase.
        """
        try:
            purchase_data = await self.purchase_market_listing(listing_id)
            await self.send(text_data=json.dumps({
                "type": "market_purchase_success",
                "data": purchase_data
            }))
        except ValueError as e:
            await self.send(str(e))

    @sync_to_async
    def get_active_market_listings(self):
        """
        Fetches all active marketplace listings.
        """
        from .models import MarketListing
        listings = MarketListing.objects.filter(is_active=True).select_related('item', 'seller')
        return [
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

    async def fetch_market_listings(self):
        """
        Fetches and sends active marketplace listings to the client.
        """
        try:
            listings = await self.get_active_market_listings()
            await self.send(text_data=json.dumps({
                "type": "market_listings",
                "data": listings
            }))
        except Exception as e:
            await self.send("Failed to fetch market listings.")

    # ------------------ DUNGEON-RELATED CODE ------------------ #

    @sync_to_async
    def start_dungeon(self):
        """
        Starts an offline/online dungeon session for the user.
        Schedules item rewards and an NPC event offline via Celery tasks.
        """
        from django.utils.timezone import now, timedelta
        from .models import DungeonSession
        print("here")

        # Check if a dungeon session is already active
        try:
            active_session = DungeonSession.objects.filter(
                user=self.user,
                end_time__isnull=True,
                paused=False
            ).order_by('-start_time').first()

            if active_session:
                print("session already exists")
                return False

            # Create a new DungeonSession
            session = DungeonSession.objects.create(
                user=self.user,
                start_time=now(),
                next_item_time=now() + timedelta(minutes=1)  # First item in ~10 minutes
            )
            print("session created")
            return True

        except Exception as e:
            print(f"Error in start_dungeon: {e}")
            return False

    async def handle_start_dungeon(self):
        """
        Wrapper method to handle the dungeon start process asynchronously
        """
        success = await self.start_dungeon()

        if success:
            await self.send(text_data=json.dumps({
                "type": "dungeon_started",
                "message": "Dungeon run started."
            }))
        else:
            await self.send(text_data=json.dumps({
                "type": "dungeon_error",
                "message": "A dungeon session is already in progress."
            }))

    async def stop_dungeon(self):
        from .models import DungeonSession, Inventory

        # Retrieve the active dungeon session
        session = await self.get_active_dungeon_session_end()
        if not session:
            await self.send(text_data=json.dumps({
                "type": "dungeon_error",
                "message": "No active dungeon session to stop."
            }))
            return

        # Only process inventory if session is not paused
        if not session.paused:
            try:
                # Wrap all synchronous operations in sync_to_async
                @sync_to_async
                def update_inventory():
                    # Get or create inventory in a single transaction
                    inventory, created = Inventory.objects.get_or_create(user=session.user)
                    print(f"Inventory {'created' if created else 'retrieved'} for user")

                    # Get collected items
                    collected_items = list(session.items_collected.all())
                    print(f"Found {len(collected_items)} collected items")

                    if collected_items:
                        # Add items to inventory
                        inventory.items.add(*collected_items)
                        print(f"Added {len(collected_items)} items to inventory")

                    # Verify final inventory state
                    updated_items = list(inventory.items.all())
                    print(f"Updated inventory contains {len(updated_items)} items")

                    return True

                # Execute the inventory update
                await update_inventory()

            except Exception as e:
                error_message = f"An error occurred while updating your inventory: {str(e)}"
                print(error_message)
                await self.send(text_data=json.dumps({
                    "type": "inventory_error",
                    "message": error_message
                }))
                return

        try:
            # Wrap session update in a sync_to_async function
            @sync_to_async
            def update_session():
                session.end_time = now()
                session.save()

            await update_session()

            await self.send(text_data=json.dumps({
                "type": "dungeon_stopped",
                "message": "Dungeon run stopped successfully."
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "dungeon_error",
                "message": f"Error saving session: {str(e)}"
            }))

    @database_sync_to_async
    def save_session(self, session):
        session.save()

    @database_sync_to_async
    def add_coins_sync(self, user, amount: int):
        user.coins += amount
        user.save()

    @database_sync_to_async
    def get_paused_session(self, user_id):
        from .models import DungeonSession
        return DungeonSession.objects.filter(
            user_id=user_id, end_time__isnull=True, paused=True
        ).first()

    @database_sync_to_async
    def update_user_health(self, session, health_change):
        session.user_health += health_change
        session.user_health = max(0, session.user_health)  # Prevent negative health
        session.save(update_fields=["user_health"])

    @database_sync_to_async
    def add_item_by_name_local_sync(self, user, item_name: str):
        from .models import Item, Inventory
        item = Item.objects.get(name=item_name)
        inv, _ = Inventory.objects.get_or_create(user=user)
        inv.items.add(item)

    @database_sync_to_async
    def save_dungeon_session(self, session):
        session.save()

    async def handle_dungeon_choice(self, choice_index):
        session = await self.get_paused_session(self.user.id)
        if not session:
            await self.send("No paused dungeon session found.")
            return

        if not session.npc_event_data:
            await self.send("No NPC event data to resolve.")
            return

        event_data = session.npc_event_data.get("event", {})
        choices = event_data.get("choices", [])

        if choice_index < 0 or choice_index >= len(choices):
            await self.send("Invalid choice index.")
            return

        choice = choices[choice_index].get("consequences", {})

        # 2) Modify user stats in a thread-safe way
        health_change = choice.get("health_change", 0)
        currency_change = choice.get("currency_change", 0)

        await self.update_user_health(session, health_change)
        await self.add_coins_sync(self.user, currency_change)

        # 3) Add any items gained
        for item_name in choice.get("inventory_additions", []):
            print(item_name)
            await self.add_item_by_name_local_sync(self.user, item_name)

        # 4) Unpause and save the session
        session.paused = False
        session.npc_event_data = None

        from django.utils.timezone import now, timedelta
        session.next_item_time = now() + timedelta(minutes=10)

        # Use our lazy method to save the session
        await self.save_dungeon_session(session)

        # 5) Send feedback
        await self.send(text_data=json.dumps({
            "type": "choice_feedback",
            "consequence_text": choice.get("consequence_text", "")
        }))

    @sync_to_async
    def add_item_by_name_local(self, item_name):
        """
        Adds an item to the user's inventory by name (local import).
        """
        from .models import Item, Inventory
        try:
            item = Item.objects.get(name=item_name)
            inventory, _ = Inventory.objects.get_or_create(user=self.user)
            inventory.items.add(item)
        except Item.DoesNotExist:
            pass

    @sync_to_async
    def get_active_dungeon_session(self):
        print("get_active_dungeon_session")
        from .models import DungeonSession
        try:
            sess = DungeonSession.objects.filter(
                user=self.user,
                end_time__isnull=True,
                paused=False
            ).order_by('-start_time').first()

            if sess:
                print(f"Active dungeon session found: {sess}")
            else:
                print(f"No active dungeon session found for user: {self.user.username}")

            return sess
        except Exception as e:
            print(f"Error fetching active dungeon session: {e}")
            return None

    @sync_to_async
    def get_active_dungeon_session_end(self):
        from .models import DungeonSession
        try:
            sess = DungeonSession.objects.filter(
                user=self.user,
                end_time__isnull=True,
            ).order_by('-start_time').first()

            if sess:
                print(f"Active dungeon session found: {sess}")
            else:
                print(f"No active dungeon session found for user: {self.user.username}")

            return sess
        except Exception as e:
            print(f"Error fetching active dungeon session: {e}")
            return None

    @sync_to_async
    def get_paused_dungeon_session(self):
        """
        Returns a paused session if it exists (NPC event triggered).
        """
        from .models import DungeonSession
        return DungeonSession.objects.filter(
            user=self.user, end_time__isnull=True, paused=True
        ).first()

    @sync_to_async
    def get_dungeon_data(self):
        from .models import DungeonSession, Item

        session = DungeonSession.objects.filter(
            user=self.user,
            end_time__isnull=True
        ).first()

        if not session:
            return {
                "items": [],
                "npc_event": {},
                "message": "No active dungeon session."
            }

        items_collected = []
        for i in session.items_collected.all():
            items_collected.append({
                "id": i.id,
                "name": i.name,
                "rarity": i.rarity,
                "file_name": i.file_name,
                "category": i.category,
            })

        death_occurred = session.user_health <= 0
        if death_occurred:
            session.end_time = now()

        return {
            "items": items_collected,
            "logs": session.logs,
            "current_health": session.user_health,
            "npc_event": session.npc_event_data or {},
            "paused": session.paused,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "message": "Dungeon data fetched successfully.",
            "death": death_occurred
        }

    @staticmethod
    def generate_event_data(npc):
        """
        Generates a structured event (dialogue + choices) for an NPC encounter.
        This is a simplistic example—customize as needed.
        """
        # For demonstration, we use a random scenario from a list,
        # or you can generate text dynamically with an AI service like Amazon Bedrock
        scenarios = [
            {
                "dialogue": f"{npc.name} glances at you warily. 'We don't get many travelers here...'",
                "choices": [
                    {
                        "choice_text": "Ask for directions.",
                        "consequences": {
                            "health_change": 0,
                            "inventory_additions": [],
                            "currency_change": 0,
                            "consequence_text": "The NPC gives you directions, though they seem unsure."
                        }
                    },
                    {
                        "choice_text": "Attack immediately.",
                        "consequences": {
                            "health_change": -10,
                            "inventory_additions": [],
                            "currency_change": 0,
                            "consequence_text": "You strike first, dealing 10 damage—but the NPC quickly retaliates."
                        }
                    }
                ]
            },
            {
                "dialogue": f"{npc.name} stands by a strange portal. 'Care to step through and test your luck?'",
                "choices": [
                    {
                        "choice_text": "Enter the portal.",
                        "consequences": {
                            "health_change": -20,
                            "inventory_additions": ["Mysterious Crystal"],
                            "currency_change": 0,
                            "consequence_text": "You feel a strange force draining your energy, but gain a shimmering crystal."
                        }
                    },
                    {
                        "choice_text": "Refuse and walk away.",
                        "consequences": {
                            "health_change": 0,
                            "inventory_additions": [],
                            "currency_change": 0,
                            "consequence_text": "You keep your distance, missing out on whatever lay beyond the portal."
                        }
                    }
                ]
            }
        ]

        scenario = choice(scenarios)  # pick a random scenario
        return scenario

    async def send_health_update(self, event):
        """
        Handles a health update message sent via the channel layer.
        """
        health_data = event["data"]
        await self.send(text_data=json.dumps({
            "type": "health_update",
            "data": health_data
        }))

    @sync_to_async
    def is_player_in_dungeon(self):
        """
        Checks if the current user is currently in a dungeon session (not ended).
        Returns True if a session is active or paused; otherwise False.
        """
        from .models import DungeonSession
        print("checking dungeon status")
        session = DungeonSession.objects.filter(
            user=self.user,
            end_time__isnull=True
        ).first()

        if session is not None:
            self.send(text_data=json.dumps({
                "type": "dungeon_status",
                "data": {"is_running": True}
            }))
        else:
            self.send(text_data=json.dumps({
                "type": "dungeon_status",
                "data": {"is_running": False}
            }))

    @staticmethod
    def generate_dynamic_event(npc) -> dict:
        """
        Generates a dynamic dungeon event involving the specified NPC using Amazon Bedrock.
        """
        # Fallback example event structure
        example_event = {
            "dialogue": f"{npc.name} glances at you warily. '{npc.short_description}'",
            "choices": [
                {
                    "choice_text": "Ask for directions.",
                    "consequences": {
                        "health_change": 0,
                        "currency_change": 0,
                        "consequence_text": "The NPC gives you directions, though they seem unsure."
                    }
                },
                {
                    "choice_text": "Attack immediately.",
                    "consequences": {
                        "health_change": -10,
                        "currency_change": 0,
                        "consequence_text": "You strike first, dealing 10 damage—but the NPC quickly retaliates."
                    }
                }
            ]
        }

        # Define the revised prompt for the model
        prompt = (
            "Act as a creative game event generator. Given an NPC's details, create a dungeon event that includes "
            "dialogue from the NPC and exactly two choices. Each choice must have a 'choice_text' and corresponding "
            "'consequences' including 'health_change', 'currency_change', and 'consequence_text'.\n\n"
            "Output only the JSON object without any additional text or formatting.\n"
            "Example:\n"
            "{\n"
            '    "dialogue": "Sloan Rho leans against a cracked concrete wall, cleaning a sleek pistol with practiced movements. \'You\'re not from around here. What\'s your business in this sector?\' Their eyes scan you coldly, waiting for a response.",\n'
            '    "choices": [\n'
            '        {\n'
            '            "choice_text": "Offer to help with a local problem.",\n'
            '            "consequences": {\n'
            '                "health_change": 0,\n'
            '                "currency_change": 50,\n'
            '                "consequence_text": "Sloan considers your offer, then nods. They share a quick job that pays well, appreciating your straightforward approach."\n'
            '            }\n'
            '        },\n'
            '        {\n'
            '            "choice_text": "Claim you\'re just passing through.",\n'
            '            "consequences": {\n'
            '                "health_change": -5,\n'
            '                "currency_change": -20,\n'
            '                "consequence_text": "Sloan doesn\'t believe your story. They rough you up a bit and search your pockets, taking some of your credits as \'insurance\'."\n'
            '            }\n'
            '        }\n'
            '    ]\n'
            "}\n"
            "\n"
            "Generate a dungeon event based on the following NPC details:\n"
            f'"name": "{npc.name}",\n'
            f'"description": "{npc.short_description}"\n'
        )

        # Prepare the request payload (adjust according to Bedrock's API)
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }

        # Convert the request to JSON
        request = json.dumps(native_request)

        # Create the Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name="us-east-2")
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

        try:
            # Invoke the model with the request
            streaming_response = client.invoke_model_with_response_stream(
                modelId=model_id, body=request
            )

            # Collect the response content from text_deltas
            full_response = ""
            for event in streaming_response.get("body", []):
                try:
                    chunk_str = event.get("chunk", {}).get("bytes", b"").decode('utf-8')
                    if not chunk_str:
                        continue  # Skip empty chunks

                    # Each chunk_str is a JSON object, parse it
                    chunk_json = json.loads(chunk_str)

                    # Check if it's a content_block_delta with text_delta
                    if chunk_json.get("type") == "content_block_delta":
                        delta = chunk_json.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            full_response += text  # Accumulate the text
                except json.JSONDecodeError as e:
                    print(f"Error decoding chunk: {e}")
                    print(f"Chunk content: {chunk_str}")
                    continue  # Skip malformed chunks

            # Debugging: Print the full_response to inspect its content
            print("Full Response from Model:", full_response)

            if not full_response.strip():
                print("Received empty response from the model. Using fallback example_event.")
                return example_event  # Return fallback if the response is empty

            # Attempt to parse the accumulated full_response as JSON
            try:
                response_data = json.loads(full_response)
            except json.JSONDecodeError as json_err:
                print(f"JSON decoding error after accumulation: {json_err}")
                print(f"Accumulated JSON string was: {full_response}")
                return example_event  # Return fallback structure

            # Extract dialogue and choices with defaults
            dialogue = response_data.get("dialogue", example_event["dialogue"])
            choices = response_data.get("choices", example_event["choices"])

            # Validate that choices contain required fields
            validated_choices = []
            for choice in choices:
                choice_text = choice.get("choice_text", "Default choice")
                consequences = choice.get("consequences", {})
                health_change = consequences.get("health_change", 0)
                currency_change = consequences.get("currency_change", 0)
                consequence_text = consequences.get("consequence_text", "")

                validated_choices.append({
                    "choice_text": choice_text,
                    "consequences": {
                        "health_change": health_change,
                        "currency_change": currency_change,
                        "consequence_text": consequence_text
                    }
                })

            # Ensure exactly two choices
            if len(validated_choices) != 2:
                print(f"Expected 2 choices, but got {len(validated_choices)}. Using fallback choices.")
                return example_event

            # Format and return the structured output
            return {
                "dialogue": dialogue.strip(),
                "choices": validated_choices
            }

        except Exception as e:
            print(f"Error generating dynamic event: {e}")
            return example_event  # Return fallback structure

    @sync_to_async
    def get_random_npc(self):
        """
        Retrieves a random NPC from the database.
        """
        from inventory.models import NPC

        try:
            npc = NPC.objects.order_by('?').first()
            if npc:
                logger.info("Selected NPC '%s' for dungeon event.", npc.name)
            else:
                logger.warning("No NPCs found in the database.")
            return npc
        except Exception as e:
            logger.error(f"Error fetching random NPC: {e}")
            return None
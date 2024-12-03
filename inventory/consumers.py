# inventory/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import Item, Inventory, EquippedItem

User = get_user_model()

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
            item_id = data.get("item_id")
            category = data.get("category")
            await self.equip_item(item_id, category)

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
        try:
            inventory = Inventory.objects.get(user=self.user)
            items = inventory.items.all()
            try:
                equipped_items = inventory.equipped_items
                equipped_data = {
                    "legs": equipped_items.legs.id if equipped_items.legs else None,
                    "headpiece": equipped_items.headpiece.id if equipped_items.headpiece else None,
                    "shield": equipped_items.shield.id if equipped_items.shield else None,
                    "melee_weapon": equipped_items.melee_weapon.id if equipped_items.melee_weapon else None,
                    "armour": equipped_items.armour.id if equipped_items.armour else None,
                }
            except EquippedItem.DoesNotExist:
                equipped_data = {}
            return {
                "items": [{"id": item.id, "name": item.name, "file_name": item.file_name, "category": item.category} for item in items],
                "equipped": equipped_data
            }
        except Inventory.DoesNotExist:
            return {"items": [], "equipped": {}}

    @sync_to_async
    def add_item(self, item_id):
        """
        Adds an item to the user's inventory.
        """
        try:
            item = Item.objects.get(id=item_id)
            inventory, _ = Inventory.objects.get_or_create(user=self.user)
            inventory.items.add(item)
        except Item.DoesNotExist:
            pass

    @sync_to_async
    def remove_item(self, item_id):
        try:
            item = Item.objects.get(id=item_id)
            inventory = Inventory.objects.get(user=self.user)
            inventory.items.remove(item)
            try:
                equipped_items = inventory.equipped_items
                for field in ["legs", "headpiece", "shield", "wings", "melee_weapon", "armour"]:
                    equipped_item = getattr(equipped_items, field)
                    if equipped_item == item:
                        setattr(equipped_items, field, None)
                equipped_items.save()
            except EquippedItem.DoesNotExist:
                pass
        except (Item.DoesNotExist, Inventory.DoesNotExist):
            pass

    @sync_to_async
    def equip_item(self, item_id, category):
        """
        Equips an item in the specified category.
        """
        try:
            item = Item.objects.get(id=item_id)
            inventory = Inventory.objects.get(user=self.user)
            equipped_items, _ = EquippedItem.objects.get_or_create(inventory=inventory)

            if category in ["legs", "headpiece", "shield", "wings", "melee_weapon", "armour"]:
                if item in inventory.items.all() and item.category == category:
                    setattr(equipped_items, category, item)
                    equipped_items.save()
        except (Item.DoesNotExist, Inventory.DoesNotExist):
            pass

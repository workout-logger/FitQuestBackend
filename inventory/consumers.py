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
                    "legs": equipped_items.legs.file_name if equipped_items.legs else None,
                    "headpiece": equipped_items.headpiece.file_name if equipped_items.headpiece else None,
                    "shield": equipped_items.shield.file_name if equipped_items.shield else None,
                    "melee": equipped_items.melee.file_name if equipped_items.melee else None,
                    "armour": equipped_items.armour.file_name if equipped_items.armour else None,
                    "wings": equipped_items.wings.file_name if equipped_items.wings else None,
                }
            except EquippedItem.DoesNotExist:
                equipped_data = {}

            # Include is_equipped for each item
            item_list = []
            for item in items:
                is_equipped = any(
                    getattr(equipped_items, key, None) and getattr(equipped_items, key).file_name == item.file_name
                    for key in ["legs", "headpiece", "shield", "melee", "armour", "wings"]
                )
                item_list.append({
                    "id": item.id,
                    "name": item.name,
                    "file_name": item.file_name,
                    "category": item.category,
                    "rarity": item.rarity,
                    "is_equipped": is_equipped
                })

            return {
                "items": item_list,
                "equipped": equipped_data
            }
        except Inventory.DoesNotExist:
            return {"items": [], "equipped": {}}

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
        try:
            return {"currency": self.user.coins}  # Assuming currency is a field in the Inventory model
        except Inventory.DoesNotExist:
            return {"currency": 0}

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

        try:
            print(item_name)
            item = Item.objects.get(file_name=item_name)
            print(item)
            inventory = Inventory.objects.get(user=self.user)
            equipped_items, _ = EquippedItem.objects.get_or_create(inventory=inventory)

            if category in ["legs", "headpiece", "shield", "wings", "melee", "armour"]:
                if item in inventory.items.all() and item.category == category:
                    setattr(equipped_items, category, item)
                    equipped_items.save()
        except (Item.DoesNotExist, Inventory.DoesNotExist):
            pass

    @sync_to_async
    def unequip_item(self, category):
        """
        Unequips an item from the specified category.
        """
        try:
            inventory = Inventory.objects.get(user=self.user)
            equipped_items, _ = EquippedItem.objects.get_or_create(inventory=inventory)

            if category in ["legs", "headpiece", "shield", "wings", "melee", "armour"]:
                setattr(equipped_items, category, None)
                equipped_items.save()
        except Inventory.DoesNotExist:
            pass

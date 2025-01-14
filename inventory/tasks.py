# tasks.py

from celery import shared_task
from django.utils.timezone import now, timedelta
from django.db import transaction
from .consumers import InventoryConsumer
import random

@shared_task
def process_dungeon_sessions():
    from .models import DungeonSession, Item, NPC

    """
    Periodic task to process all active dungeon sessions:
    - Generate item rewards if the time has come.
    - Trigger an NPC event after a specified duration if not yet triggered.
    - Generate escapade events every 10 minutes and log them.
    - Pause and stop the session if the user's health drops to zero or below.
    """
    sessions = DungeonSession.objects.filter(end_time__isnull=True, paused=False)
    print(f"Processing {sessions.count()} active dungeon sessions.")

    for session in sessions:
        with transaction.atomic():
            # Check if it's time for an item reward
            if session.next_item_time and now() >= session.next_item_time:
                random_item = Item.objects.exclude(category='coins').order_by("?").first()
                if random_item:
                    session.items_collected.add(random_item)
                    session.add_log(f"Collected item: {random_item.name} ({random_item.category}, {random_item.rarity})")


                    # Schedule the next reward (10 minutes from now)
                    session.next_item_time = now() + timedelta(minutes=10)
                    session.save(update_fields=['next_item_time'])

            # Trigger NPC event after 1 hour if not triggered
            elapsed = now() - session.start_time
            if not session.npc_event_triggered and elapsed.total_seconds() >= 360:  # 3600 seconds = 1 hour
                npc = NPC.objects.order_by("?").first()
                if npc:
                    session.npc_event_triggered = True
                    session.paused = True
                    event_data = InventoryConsumer.generate_dynamic_event(npc)
                    session.npc_event_data = {
                        "npc": {
                            "name": npc.name,
                            "description": npc.short_description,
                        },
                        "event": event_data
                    }
                    session.add_log(f"Encountered NPC: {npc.name} - {npc.short_description}")
                    session.save(update_fields=['npc_event_triggered', 'paused', 'npc_event_data', 'logs'])



            if session.next_escapade_time and now() >= session.next_escapade_time:
                generate_escapade(session)
                # Schedule the next escapade 10 minutes later
                session.next_escapade_time = now() + timedelta(minutes=10)
                session.save(update_fields=['next_escapade_time'])

            # **Health Check: Pause and Stop Session if Health <= 0**
            if session.user_health <= 0 and not session.paused:
                session.add_log("You have died in the dungeon.")

                # Set the end_time to mark the session as ended
                # session.end_time = now()
                session.paused = True

                # Optionally, add additional logs or handle rewards/punishments
                # For example: session.add_log("Session ended due to death.")

                # Save the session with updated fields
                session.save(update_fields=['end_time', 'logs','paused'])

                # **Notify Frontend** about the death event
                # Assuming you have a method to send messages via WebSocket


def generate_escapade(session):
    """
    Generates an escapade event for the session and logs it.
    Possible escapades:
    - Fighting a monster
    - Finding a trap
    - Discovering a hidden chamber
    - Solving a puzzle
    - Resting to regain health
    """
    escapades = [
        fight_monster,
        find_trap,
        discover_hidden_chamber,
        solve_puzzle,
        rest_regain_health
    ]

    escapade = random.choice(escapades)
    escapade(session)


def fight_monster(session):
    monsters = [
        {"name": "Goblin", "description": "A sneaky green creature with sharp teeth."},
        {"name": "Skeleton Warrior", "description": "An animated skeleton armed with a rusty sword."},
        {"name": "Orc Brute", "description": "A large and muscular orc with a menacing axe."},
        {"name": "Dark Sorcerer", "description": "A mysterious figure cloaked in dark robes, wielding arcane powers."}
    ]
    monster = random.choice(monsters)
    damage = random.randint(10, 25)
    session.user_health = max(session.user_health - damage, 0)
    session.add_log(f"Fought a {monster['name']}: {monster['description']}. Took {damage} damage.")
    session.save(update_fields=['user_health', 'logs'])


def find_trap(session):
    traps = [
        "a spike trap that deals damage",
        "a poison dart trap that reduces health over time",
        "a collapsing ceiling that restricts movement"
    ]
    trap = random.choice(traps)
    damage = random.randint(15, 25)
    session.user_health = max(session.user_health - damage, 0)
    session.add_log(f"Triggered {trap}. Took {damage} damage.")
    session.save(update_fields=['user_health', 'logs'])


def discover_hidden_chamber(session):
    treasures = [
        {"name": "Ancient Relic", "description": "An old relic radiating mysterious energy."},
        {"name": "Healing Potion", "description": "A potion that restores health."},
        {"name": "Mana Crystal", "description": "A crystal that enhances magical abilities."}
    ]
    treasure = random.choice(treasures)
    session.add_log(f"Discovered a hidden chamber containing {treasure['name']}: {treasure['description']}.")
    session.save(update_fields=['logs'])


def solve_puzzle(session):
    puzzles = [
        "a riddle inscribed on the wall",
        "a complex mechanism that needs to be aligned",
        "a series of pressure plates that must be stepped on in the correct order"
    ]
    puzzle = random.choice(puzzles)
    success = random.random() < 0.7  # 70% chance to solve
    if success:
        session.add_log(f"Solved {puzzle}. Progressed further into the dungeon.")
    else:
        damage = random.randint(5, 10)
        session.user_health = max(session.user_health - damage, 0)
        session.add_log(f"Failed to solve {puzzle}. Took {damage} damage.")
    session.save(update_fields=['user_health', 'logs'])


def rest_regain_health(session):
    health_regained = random.randint(10, 15)
    session.user_health = min(session.user_health + health_regained, 100)
    session.add_log(f"Rested and regained {health_regained} health.")
    session.save(update_fields=['user_health', 'logs'])

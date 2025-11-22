import discord
from discord.ext import (tasks)
import datetime
import json
import os
from dotenv import load_dotenv

# Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
USER_ID = os.getenv('USER_ID')

# Intents setzen
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
intents.reactions = True

client = discord.Client(intents=intents)

watched_messages = {}

# ============ Funktionen ===========

def load_data():
    global watched_messages
    if os.path.exists("reminder_data.json"):
        with open("reminder_data.json", "r") as f:
            watched_messages = json.load(f)

# w = write
# r = read
def save_data():
    global watched_messages
    with open("reminder_data.json", "w") as f:
        json.dump(watched_messages, f, indent=4)

# ============ Events ===============

@client.event
async def on_ready():
    print(f"{client.user} has connected to Channels\n")
    for server in client.guilds:
        print(f"{server.name} (id: {server.id})")
        for channel in server.channels:
            print(f"{channel.name} (id: {channel.id})")
    load_data()
    check_reminders.start()  # Task starten

@client.event
async def on_message(message):
    # Nur bestimmten Channel abhören
    message_embeds = message.embeds

    if len(message_embeds) == 0:
        return

    embed = message_embeds[0]
    embed_content = embed.description
    if message.channel.id == int(CHANNEL_ID) and "abmelden" in embed_content.lower():
        watched_messages[str(message.id)] = {
            "channel_id": message.channel.id,
            "user_id": message.author.id,
            "reaction_received": False,
            "timestamp": datetime.datetime.now().timestamp()
        }
        save_data()
        print(f"Nachricht {message.id} in Channel {message.channel.id} gespeichert.")

@client.event
async def on_reaction_add(reaction, user):
    msg_id = str(reaction.message.id)

    if msg_id in watched_messages:
        # Nur auf ✅ reagieren
        if str(reaction.emoji) == "✅":
            watched_messages[msg_id]["reaction_received"] = True

            save_data()
            print(f"Nachricht {msg_id} von {user} als erledigt markiert")

# ============ Tasks ================
@tasks.loop(minutes=1)
async def check_reminders():
    now = datetime.datetime.now()

    # Alte Nachrichten aufräumen
    removed = False
    for msg_id, data in list(watched_messages.items()):
        if data.get("reaction_received") is True:
            watched_messages.pop(msg_id)
            removed = True
            print(f"Alte Nachricht {msg_id} gelöscht")
    if removed:
        save_data()

    # Reminder 22:30
    for message_id, data in list(watched_messages.items()):
        if not data["reaction_received"]:
            msg_time = datetime.datetime.fromtimestamp(data["timestamp"])
            diff = now - msg_time

            # Wenn 2,5 Stunden (9000 Sekunden) vergangen sind
            if diff.total_seconds() >= 2.5 * 3600:
                channel = client.get_channel(data["channel_id"])
                if channel:
                    await channel.send(f"<@{USER_ID}> hast du dich abgemeldet?")


# ==================================
client.run(TOKEN)

import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session = os.environ["SESSION"]

client = TelegramClient(StringSession(session), api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    if event.sender_id == 777000:
        text = event.raw_text
        print("[TG NOTI]", text, flush=True)
        with open("tg_noti.log", "a", encoding="utf-8") as f:
            f.write(text + "\n---\n")

client.start()
print("Listening...")
client.run_until_disconnected()

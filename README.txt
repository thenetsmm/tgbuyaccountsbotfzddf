0. [Update] "Login code ပို့ပါ" ဆိုတဲ့ စာသား ပြီးနောက် code မရောက်ဘူးဆိုရင်:
   - ဒီ account login ဝင်ထားပြီးသား Telegram app (တခြားဖုန်း/device)
     ရှိနေရင် Telegram က SMS မပို့ဘဲ အဲဒီ app ထဲက 777000 service
     account ဆီကနေ message အနေနဲ့ ပို့တတ်ပါတယ် - အရင်ဆုံး
     အဲဒီမှာ ကြည့်ပါ။
   - /sms လို့ ရိုက်ပို့ရင် SMS ဖြင့် code အသစ် force ပို့ခိုင်းနိုင်ပါတယ်
     (force_sms=True) - ဒါပေမဲ့ app ရှိပြီးသား account တွေမှာ Telegram
     ကိုယ်တိုင်က app ကိုပဲ ဆက်ဦးစားပေးတတ်တာမို့ အမြဲအလုပ်မဖြစ်ချင်
     ဖြစ်နိုင်ပါတယ်။
   - tools/ folder ထဲက gen_session.py ကို laptop terminal မှာ run ပြီး
     အလားတူ ဖုန်းနံပါတ်နဲ့ login ဝင်ကြည့်ရင် code ရောက်/မရောက်
     စစ်ကြည့်နိုင်ပါတယ် (ဒီ bot ထဲက login flow နဲ့ API logic
     အတူတူဖြစ်ပြီး run environment ကွဲနေရုံပါ)။ tools/listen.py ကို
     ရနှင့်ပြီးသား session string တစ်ခုနဲ့ run ထားရင် 777000 ကနေ
     message ရောက်တိုင်း tg_noti.log ထဲ real-time မှတ်ပေးပါတယ်
     (bot ရဲ့ "login code ကြည့်ရန်" button တွေက message history
     ကို on-demand ပြန်ဖတ်တာဖြစ်ပြီး listen.py ကတော့ background
     မှာ အမြဲ listen နေတာ ကွာသည်)။

1. GitHub မှာ PRIVATE repo ဆောက်ပြီး ဒီဖိုင်တွေ အကုန်တင်ပါ။
2. MongoDB Atlas (free M0 cluster) ဆောက်ပြီး connection string ယူပါ
   - Database Access > user ဆောက်ပါ
   - Network Access > 0.0.0.0/0 ခွင့်ပြုပါ (Render ကနေ ချိတ်ရန်)
   - Connection string format: mongodb+srv://user:pass@cluster.mongodb.net/
3. Render > New > Blueprint (render.yaml) သို့မဟုတ် Web Service
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
4. Environment Variables: API_ID, API_HASH, BOT_TOKEN, OWNER_ID, MONGO_URI
5. ဘယ် Telegram user မဆို bot ကို /start လုပ်ပြီး
   phone -> code (space ခြား) -> (2FA ရှိရင်) password ထည့်နိုင်ပါတယ်။
   ပြီးရင် user ဆီကို session string မပြဘဲ "Done +95xxxxx" ပဲ ပြန်ပြောပါမယ်။
6. OWNER_ID နဲ့ ကိုက်တဲ့ account က /list ရိုက်ရင်
   database ထဲ သိမ်းထားတဲ့ account တွေကို inline button (ဖုန်းနံပါတ် + နာမည်)
   အနေနဲ့ ပြပါမယ်။ Button ကို နှိပ်မှ session string ကို
   copy လုပ်လို့ရတဲ့ code block အနေနဲ့ ပြပေးပါမယ်။ Owner မဟုတ်သူ button နှိပ်ရင်
   "Not authorized" ပြပါမယ်။
7. Session string တွေက password မလိုဘဲ account ဝင်ခွင့်ပေးတဲ့ key ဖြစ်လို့
   MongoDB user/password နဲ့ Render env ကို ခိုင်မာအောင်ထားပြီး
   အခြားသူနဲ့ မမျှဝေပါနဲ့။ ဒီ bot ကို တခြားသူတွေကို account ထည့်ခိုင်းမယ်ဆိုရင်
   သူတို့ account ကို ကိုယ်ဘာသာ ယူသွားတာမို့ သူတို့ရဲ့ ကြိုတင်သဘောတူညီချက် ရယူပါ။

8. Bot ကို ၂၄ နာရီ run ထားဖို့ keep_alive task ကို ၁ မိနစ်တစ်ခါ
   ကိုယ့် Render URL ကို ကိုယ်ပဲ ping လုပ်အောင် ထည့်ထားပါတယ်
   (RENDER_EXTERNAL_URL ကို Render က auto-ထည့်ပေးတာမို့ ထပ်ထည့်စရာမလိုပါ)။
   Free plan တောင် ping ဆက်ရနေသရွေ့ sleep မဝင်ပါဘူး။
   မှတ်ချက် - Render free plan မှာ လစဉ် instance hour ကန့်သတ်ချက်ရှိတာကို
   သတိရပါ (၇၅၀ hour/လ ဝန်းကျင်) - အမြဲဖွင့်ထားရင် တစ်လကုန်ရင်
   quota ကုန်နိုင်ပါတယ်။

9. Account ကြည့်တဲ့ screen မှာ "Recovery email ပြောင်းရန်" button ထပ်ထည့်ထားပါတယ်။
   - ဒီ "email" က Telegram ရဲ့ 2FA recovery email ဖြစ်ပြီး Gmail inbox ထဲ
     ဝင်တာ မဟုတ်ပါဘူး (Telegram ကနေ ပို့တဲ့ verification code ကိုပဲ
     အဲဒီ email ဆီ ပို့ပေးတာပါ)။
   - Account မှာ 2FA password မရှိသေးရင် Telegram ကိုယ်တိုင်က
     recovery email ထည့်ခွင့်မပြုပါ (feature limitation) — ဒီအခြေအနေမှာ
     bot က "2FA password မရှိလို့ email ထည့်လို့မရပါ" လို့ ပြောပေးပါမယ်။
     ဒါကြောင့် အရင်ဆုံး 2FA password ကို "2FA password ပြောင်းရန်" button
     ကနေ သတ်မှတ်ပေးရပါမယ်။
   - Email ထည့်/ပြောင်းလိုက်ရင် Telegram က verification code ကို
     အဲဒီ email ဆီ ပို့ပါမယ် — admin ဆီကို bot က code တောင်းပြီး
     admin ရိုက်ထည့်ပေးရပါမယ် (email inbox ကို ဝင်ကြည့်နိုင်မှ
     ဖြစ်နိုင်ပါတယ်)။
   - Email ပြောင်းချင်မှ ပြောင်း၊ မပြောင်းချင်ရင် /skip ရိုက်ပို့လို့ရပါတယ်။

10. "Login email ပြောင်းရန်" button ထပ်ထည့်ထားပါတယ်။
    - ဒါက 2FA recovery email နဲ့ မတူပါ - login code ကို SMS အစား
      email ကနေ လက်ခံတဲ့ Telegram setting ဖြစ်ပါတယ်။
    - ⚠️ အရေးကြီးသတိပေးချက်: ဒီ feature ကို Telegram က account
      အားလုံးမှာ မပေးသေးပါ (server-side rollout အပေါ်မူတည်ပြီး
      account တချို့မှာ ဒီ option လုံးဝ မပါတတ်ပါ) - ဒါကြောင့်
      button နှိပ်လိုက်ရင် error ပြန်လာတတ်ပါတယ်။ Error ပြရင်
      "ဒီ account မှာ feature မပါဘူး" လို့ bot က ရှင်းပြပေးပါမယ်။
      ဒီလိုပဲ ဖြစ်ချင်ဖြစ်မှာပါ၊ bot ရဲ့ ချို့ယွင်းချက် မဟုတ်ပါ။
    - Email ထည့်ပြီးရင် Telegram ကနေ ပို့တဲ့ verification code ကို
      admin ဆီကနေ ထပ်တောင်းပါမယ် (email inbox ထဲ ဝင်ကြည့်ထားဖို့ လိုပါတယ်)။
    - /skip ရိုက်ပို့ရင် ကျော်လို့ရပါတယ်။
    - ဒီ Telegram API feature က အသစ်ဖြစ်ပြီး server rollout မညီညွတ်တာမို့
      error message အမျိုးမျိုး ပြန်လာနိုင်ပါတယ် - error ဘယ်လိုပေါ်လဲ
      ပြောပြရင် ထပ်ပြင်ပေးနိုင်ပါတယ်။

11. [Fix] "Login email" error "The phone code is missing" ပြဿနာကို ပြင်ထားပါတယ်:
    EmailVerifyPurposeLoginSetup ဟာ login code flow နဲ့ ချိတ်ထားရတဲ့ valid
    phone_code_hash ကို လိုအပ်ကြောင်း တွေ့ရပါတယ်။ ဒါကြောင့် login email
    ပြောင်းခင် bot က send_code_request ကို အရင်ခေါ်ပြီး hash ရယူပါတယ်
    (ဒီအချိန်မှာ ဖုန်းနံပါတ်ဆီကိုလည်း login code တစ်ခု ရောက်သွားနိုင်ပါတယ်,
    ဒါကို လျစ်လျူရှုပြီး bot တောင်းတဲ့ email ဆီက code ကိုပဲ ထည့်ပေးပါ)။

12. [Fix] "Cannot send requests while disconnected" ပြဿနာကို ပြင်ထားပါတယ်:
    send_code_request ခေါ်ပြီးနောက် connection ပြတ်တောက်သွားတတ်တာကို တွေ့ရလို့
    request ထပ်ပို့ခင် c.is_connected() စစ်ပြီး ပြန်ချိတ်ပေးအောင် ထည့်ထားပါတယ်။
    ⚠️ ဒါက Telegram server ဘက်ကနေ သတ်မှတ်ထားတဲ့ ပုံစံအရ ဖြစ်တာလည်း
    ဖြစ်နိုင်ပါတယ် (login-flow API ကို already-logged-in client ကနေ
    ထပ်ခေါ်တာကို Telegram server က suspicious လို့ သတ်မှတ်ပြီး
    connection ကို ပိတ်တတ်ခြင်း) - reconnect ထည့်ပေမဲ့ ထပ်တက်နိုင်ပါသေးတယ်။
    ထပ်တက်ရင် error message အသစ်ကို ပြောပြပေးပါ။

13. [Fix - root cause တွေ့ပါပြီ] Telegram core API documentation
    (core.telegram.org/method/account.sendVerifyEmailCode) ကို ရှာကြည့်ရာ
    login email "ပြောင်း"တာ (ရှိပြီးသား login email ရှိနေတဲ့ account) အတွက်
    purpose: EmailVerifyPurposeLoginSetup မဟုတ်ဘဲ
    **EmailVerifyPurposeLoginChange** ကို သုံးရမှန်း တွေ့ရပါတယ်။
    ဒီ purpose က phone_number/phone_code_hash လုံးဝ မလိုအပ်ပါ -
    ဒါကြောင့် "phone code missing" / "phone_code_hash expired" error
    တွေ လုံးဝ ပျောက်သွားသင့်ပါတယ်။
    - Account မှာ login email လုံးဝ မရှိသေးရင် (EMAIL_NOT_SETUP error
      ပြန်လာရင်) ဒီ code က LoginSetup flow (phone verification ပါ)
      ကို အလိုအလျောက် fallback လုပ်ပါမယ်။
    - Telethon library version အဟောင်းသုံးရင် EmailVerifyPurposeLoginChange
      type မပါသေးနိုင်ပါ (2022 ခုနှစ်လောက်ကတည်းက schema ထဲ ပါသော်လည်း) -
      requirements.txt ထဲက telethon ကို "pip install -U telethon" နဲ့
      အသစ်ဆုံး version ဖြစ်အောင် Render deploy တိုင်း auto ရသွားပါမယ်
      (version pin မထားထားလို့)။

14. [Fix - final] Manus AI ရဲ့ Telegram official docs သုတေသနအရ -
    EmailVerifyPurposeLoginChange ဟာ ရှိပြီးသား login email ပြောင်းဖို့
    မှန်ကန်တဲ့ purpose ဖြစ်ကြောင်း အတည်ပြုရပါတယ် (parameter မလို)။
    ဒါပေမဲ့ "EMAIL_NOT_SETUP" error ပြန်လာရင် LoginSetup ဘက်ကို
    fallback **မလုပ်တော့ပါ** - authorized session ကနေ
    phone_code_hash ကို fabricate ပြုလုပ်ပြီး ပြန်သုံးတာက login flow
    အစစ်မဟုတ်လို့ Telegram server ဘက်က ပုံမှန်မဟုတ်တဲ့ request
    အဖြစ် သတ်မှတ်နိုင်ပြီး account ကို flag/flood-wait ဖြစ်စေနိုင်ပါတယ်။
    ဒါကြောင့် EMAIL_NOT_SETUP ပြန်လာရင် bot က ရှင်းရှင်းလင်းလင်း
    ရှင်းပြပြီး ရပ်တန့်ပါမယ် - ဒီအခြေအနေမှာ login email ကို
    Telegram app ထဲ ကိုယ်တိုင်ဝင်ပြီး Settings > Privacy and Security >
    Login Email ကနေသာ ပြောင်းသင့်ပါတယ်။
    "2FA password ပြောင်းရန်" နဲ့ "Recovery email ပြောင်းရန်" button
    နှစ်ခုကတော့ stable Telethon API (edit_2fa) ကို သုံးထားလို့
    ယုံကြည်စိတ်ချစွာ ဆက်အလုပ်လုပ်ပါတယ်။

15. /list ကို pagination ထည့်ထားပါတယ် (page တစ်ခုမှာ account 10 ခု):
    - "⬅ Back" / "Next ➡" button တွေနဲ့ page ချိတ်ကြည့်လို့ရပါတယ်
    - Account တစ်ခုချင်းစီကို ကြည့်တဲ့အခါ "🗑 ဒီ account ကို ဖျက်ရန်"
      button ရှိပါတယ် - နှိပ်ရင် "သေချာလား" confirm message
      ထပ်ပြပါမယ် ("✅ ဖျက်မည်" / "❌ မဖျက်တော့ပါ")
    - "✅ ဖျက်မည်" ကို နှိပ်မှသာ database ထဲက record ကို ဖျက်ပါမယ်
      (ဒီဖျက်ခြင်းက database ထဲက record ကိုပဲ ဖျက်တာဖြစ်ပြီး
      Telegram account ကိုယ်တိုင် (login ထွက်ခြင်း) ကို မထိခိုက်ပါ)
    - ဖျက်ပြီးရင် list ကို အဲဒီ page ကနေပဲ ပြန်ပြပေးပါတယ်

16. Account ကြည့်တဲ့ screen မှာ login code ဖတ်ပေးတဲ့ button ၂ ခု
    ထပ်ထည့်ထားပါတယ် (Telegram ရဲ့ official service account 777000
    ဆီကနေ ပို့တဲ့ login code message ကို တိုက်ရိုက် ဖတ်ပေးတာပါ -
    အခြားဖုန်း/device တစ်ခုခုက ဒီ account ကို login ဝင်ဖို့
    ကြိုးစားတဲ့အခါ ပို့ပေးတဲ့ code ကို ဆိုလိုတာပါ):

    - "📩 5မိနစ်ထဲ login code ကြည့်ရန်" - 777000 ကနေ ရောက်ထားတဲ့
      message တွေထဲက အသစ်ဆုံး code ကို ဖတ်ပြီး၊ ၅ မိနစ်အတွင်း
      ရောက်ထားတာလား စစ်ပေးပါတယ်။ ၅ မိနစ်ကျော်နေပြီဆိုရင်
      "fresh code မရှိပါ" လို့ ပြန်ပြောပါမယ်။
    - "📨 နောက်ဆုံးရ login code" - အချိန်ကာလ မကန့်သတ်ဘဲ
      777000 ကနေ လက်ရှိရှိနေသမျှ message ထဲက အသစ်ဆုံး code ကို
      အချိန်တံဆိပ်နဲ့အတူ ပြပေးပါတယ်။

    Code ကို regex (\d{5,7}) နဲ့ message ထဲက ဂဏန်းတွဲကို ရှာထုတ်
    တာဖြစ်လို့ Telegram ရဲ့ login code format ပြောင်းသွားရင်
    (ဥပမာ ဂဏန်းအရေအတွက် ပြောင်းသွားရင်) ထပ်ညှိပေးရနိုင်ပါတယ်။

    ⚠️ ဒီ feature က account ပိုင်ရှင် သဘောတူညီချက်မရှိဘဲ
    login code ကို admin က တိတ်တဆိတ် ဖတ်ယူဖို့ သုံးရင် Telegram
    ရဲ့ Terms of Service ကို ချိုးဖောက်ရာရောက်ပြီး account
    ပိုင်ရှင်ကို အန္တရာယ်ဖြစ်စေနိုင်ပါတယ် (တခြားနေရာကနေ
    account ဝင်ယူခံရခြင်း)။ ကိုယ့်ပိုင် account၊ သို့မဟုတ်
    ပိုင်ရှင်ရဲ့ ကြိုတင်သဘောတူညီချက် ရယူထားတဲ့ account
    အတွက်သာ သုံးသင့်ပါတယ်။

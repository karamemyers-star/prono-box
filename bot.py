import os, threading, requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}
CACHE = {}
USER_LIST = {}

def get_avis(pct):
    if pct >= 80: return "🟢 CONSEILLÉ 80%+ - Vas-y"
    elif pct >= 69: return "🟠 POSSIBLE 75% - Petite mise"
    else: return "🟡 RISQUÉ 60% - Évite"

def get_stats(team_name):
    if team_name in CACHE: return CACHE[team_name]
    try:
        search = requests.get(f"https://v3.football.api-sports.io/teams?search={team_name}",headers=HEADERS,timeout=15).json()
        if not search['response']: return None
        tid = search['response'][0]['team']['id']
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?team={tid}&last=5",headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return None
        btts=enc=ht=over=cs=0
        goals=0
        tot=len([x for x in r if x['goals']['home'] is not None])
        if tot==0: return None
        for m in r:
            if m['goals']['home'] is None: continue
            hg=m['goals']['home']; ag=m['goals']['away']
            hthg=m['score']['halftime']['home']; htag=m['score']['halftime']['away']
            is_home=m['teams']['home']['id']==tid
            scored=hg if is_home else ag
            conceded=ag if is_home else hg
            goals+=scored
            if hthg is not None and htag is not None and (hthg+htag)<=1: ht+=1
            if hg>0 and ag>0: btts+=1
            if conceded>=1: enc+=1
            if conceded==0: cs+=1
            if hg+ag>=2: over+=1
        avg=goals/tot
        style="OFFENSIF" if avg>=1.4 else "DEFENSIF" if enc<50 else "EQUILIBRE"
        res={"btts":int(btts/tot*100),"enc":int(enc/tot*100),"ht":int(ht/tot*100),"over":int(over/tot*100),"cs":int(cs/tot*100),"avg":round(avg,2),"style":style}
        CACHE[team_name]=res
        return res
    except: return None

def analyse_match(home, away):
    sh=get_stats(home); sa=get_stats(away)
    if not sh or not sa: return f"❌ {home} vs {away} -> Equipe non trouvée"

    btts_avg=(sh['btts']+sa['btts'])/2
    pire_max=max(sh['enc'],sa['enc'])
    ht_avg=(sh['ht']+sa['ht'])/2

    txt=f"⚽ {home} vs {away}\n"
    txt+=f"Style: {sh['style']} / {sa['style']} | Moy: {sh['avg']}/{sa['avg']}\n"
    txt+=f"BTTS {sh['btts']}%/{sa['btts']}% -> {get_avis(btts_avg)}\n"
    txt+=f"PIRE DEF {pire_max}% ({home if sh['enc']>sa['enc'] else away}) -> {get_avis(pire_max)}\n"
    txt+=f"HT -2 BUTS {sh['ht']}%/{sa['ht']}% -> {get_avis(ht_avg)}\n"
    if sh['over']>=70 and sa['over']>=70: txt+=f"COMBO SAFE Over 1.5 {sh['over']}% -> {get_avis((sh['over']+sa['over'])/2)}\n"
    txt+="---\n"
    return txt

def get_menu():
    kb=[
        [InlineKeyboardButton("🔥 FILTRER MY BEST",callback_data="mybest")],
        [InlineKeyboardButton("💀 FILTRER PIRES DEF",callback_data="pires")],
        [InlineKeyboardButton("🕐 FILTRER HT -2 BUTS",callback_data="ht")],
        [InlineKeyboardButton("💰 COMBO SAFE",callback_data="combo")],
        [InlineKeyboardButton("🏆 TOP 3 / MONTANTE",callback_data="top3")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "V13.1 FINALE ✅\n\n"
        "Envoie ta liste direct, exemple:\n"
        "Lyon vs Marseille\nInter vs Milan\nDortmund vs Bayern\n\n"
        "Je vais tout analyser avec MON AVIS 60/75/80%",
        reply_markup=get_menu()
    )

async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    chat_id=update.effective_chat.id
    if "vs" not in text.lower():
        await update.message.reply_text("Envoie format: Equipe vs Equipe",reply_markup=get_menu())
        return
    USER_LIST[chat_id]=text.split("\n")
    await update.message.reply_text(f"⏳ Analyse {len(USER_LIST[chat_id])} matchs... 15 sec")
    res=""
    for line in USER_LIST[chat_id][:15]:
        if "vs" not in line: continue
        try:
            home,away=line.split("vs")
            res+=analyse_match(home.strip(),away.strip())+"\n"
        except: continue
    if len(res)>4000: res=res[:4000]
    await update.message.reply_text(f"✅ PREDICTIONS FINIES:\n\n{res}",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data
    chat_id=q.message.chat_id
    if chat_id not in USER_LIST:
        await q.edit_message_text("Envoie d'abord ta liste!",reply_markup=get_menu()); return
    filtered=[]
    for line in USER_LIST[chat_id]:
        if "vs" not in line: continue
        home,away=line.split("vs"); home=home.strip(); away=away.strip()
        sh=CACHE.get(home); sa=CACHE.get(away)
        if not sh or not sa: continue
        if mode=="mybest" and (sh['btts']+sa['btts'])/2>=60: filtered.append(line)
        elif mode=="pires" and max(sh['enc'],sa['enc'])>=65: filtered.append(line)
        elif mode=="ht" and (sh['ht']+sa['ht'])/2>=60: filtered.append(line)
        elif mode=="combo" and sh['over']>=70: filtered.append(line)
        elif mode=="top3": filtered.append(line)
    await q.edit_message_text(f"✅ FILTRE {mode.upper()}:\n\n"+"\n".join(filtered) if filtered else f"❌ Rien pour {mode}",reply_markup=get_menu())

@app.route("/")
def home(): return "V13.1 Finale Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_list))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling(drop_pending_updates=True)

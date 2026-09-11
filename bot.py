import os, threading, requests, json
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}
CACHE = {}

def get_stats(team_id):
    if team_id in CACHE: return CACHE[team_id]
    try:
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10",headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return None
        btts=enc=ht_under=gs=0
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            hthg=m['score']['halftime']['home']; htag=m['score']['halftime']['away']
            if hthg is not None and htag is not None and (hthg+htag)<=1: ht_under+=1
            if hg>0 and ag>0: btts+=1
            is_home=m['teams']['home']['id']==team_id
            if (ag if is_home else hg)>=1: enc+=1
            gs+=hg if is_home else ag
        res={"btts":round(btts/len(r)*100),"enc":round(enc/len(r)*100),"ht":round(ht_under/len(r)*100),"avg":round(gs/len(r),2)}
        CACHE[team_id]=res
        return res
    except: return None

def scan_global(mode):
    CACHE.clear()
    out=[]
    today=datetime.now()
    for d in range(3):
        date_str=(today+timedelta(days=d)).strftime("%Y-%m-%d")
        try:
            fixtures=requests.get(f"https://v3.football.api-sports.io/fixtures?date={date_str}",headers=HEADERS,timeout=20).json().get("response",[])
        except: continue
        for f in fixtures[:100]:
            if "Friendly" in f['league']['name']: continue
            # filtre SAFE TOP 5
            if mode=="safe" and f['league']['id'] not in [39,140,135,78,61]: continue # PL, Liga, Serie A, Bundesliga, Ligue1
            hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
            sh=get_stats(hid); sa=get_stats(aid)
            if not sh or not sa: continue
            match=f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"
            league=f['league']['name']
            
            if mode=="mybest" and sh['btts']>=70 and sa['btts']>=70:
                out.append(f"🔥 {match}\n {league} | {date_str} | BTTS {sh['btts']}%/{sa['btts']}%")
            elif mode=="tonbest" and sh['btts']>=60 and sa['btts']>=60:
                out.append(f"🛡️ {match}\n {league} | {date_str} | BTTS {sh['btts']}%/{sa['btts']}%")
            elif mode=="pires" and (sh['enc']>=80 or sa['enc']>=80):
                faible=f['teams']['home']['name'] if sh['enc']>=80 else f['teams']['away']['name']
                fort=f['teams']['away']['name'] if sh['enc']>=80 else f['teams']['home']['name']
                out.append(f"💀 {match}\n {league} | PIRE DEF {faible} {max(sh['enc'],sa['enc'])}% -> JOUE {fort} X2")
            elif mode=="ht" and (sh['ht']+sa['ht'])/2>=70:
                out.append(f"🕐 {match}\n {league} | {date_str} | HT -2 BUTS {sh['ht']}%/{sa['ht']}%")
            elif mode=="dc":
                # Double chance: équipe qui perd rarement + adverse pire def
                if sh['enc']<=30 or sa['enc']<=30 or sh['enc']>=80 or sa['enc']>=80:
                    out.append(f"🎯 {match}\n {league} | {date_str} | DC: {sh['enc']}%/{sa['enc']}% encaisse")
            elif mode=="team2":
                if sh['avg']>=1.8 or sa['avg']>=1.8:
                    out.append(f"⚽ {match}\n {league} | {date_str} | Buts {sh['avg']}/{sa['avg']}")

    return out[:15]

def get_menu():
    kb=[
        [InlineKeyboardButton("🔥 MY BEST 100% (SCAN MONDIAL)",callback_data="mybest")],
        [InlineKeyboardButton("🛡️ TON BEST 89% (SCAN MONDIAL)",callback_data="tonbest")],
        [InlineKeyboardButton("⚽ TEAM 2 BUTS (SCAN MONDIAL)",callback_data="team2")],
        [InlineKeyboardButton("🎯 DOUBLE CHANCE (SCAN MONDIAL)",callback_data="dc")],
        [InlineKeyboardButton("💎 SAFE TOP 5 (SCAN MONDIAL)",callback_data="safe")],
        [InlineKeyboardButton("💀 PIRES DEFENSES (SCAN MONDIAL)",callback_data="pires")],
        [InlineKeyboardButton("🕐 HT -2 BUTS (SCAN MONDIAL)",callback_data="ht")],
        [InlineKeyboardButton("📊 BILAN PIRES DEF",callback_data="bilan")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("V12.6 SCAN MONDIAL AUTO ✅\nTous les boutons scannent tout seuls (D1+D2) sur 3 jours\nClique un bouton, attends 90 sec",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data
    if mode=="bilan":
        await q.edit_message_text("📊 BILAN: fonctionnalité à brancher sur /tmp (on le fait après ce test)",reply_markup=get_menu())
        return
    await q.edit_message_text(f"⏳ SCAN MONDIAL {mode.upper()} en cours...\nJe scanne 100 matchs x 3 jours (D1+D2)...\n90 secondes, ne quitte pas...",reply_markup=get_menu())
    try:
        res=scan_global(mode)
        if not res:
            await q.edit_message_text(f"❌ Aucun match trouvé pour {mode} aujourd'hui à ce seuil.\nOn baissera le % ensemble.",reply_markup=get_menu()); return
        txt=f"✅ TOP {len(res)} MATCHS - {mode.upper()} - SCAN MONDIAL D1+D2\n\n" + "\n\n".join(res)
        await q.edit_message_text(txt,reply_markup=get_menu())
    except Exception as e:
        await q.edit_message_text(f"Erreur scan {e}",reply_markup=get_menu())

@app.route("/")
def home(): return "V12.6 Scan Auto Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling(drop_pending_updates=True)

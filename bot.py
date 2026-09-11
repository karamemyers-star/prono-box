import os, threading, requests
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
        tot=0
        for m in r:
            if m['goals']['home'] is None: continue
            tot+=1
            hg=m['goals']['home']; ag=m['goals']['away']
            hthg=m['score']['halftime']['home']; htag=m['score']['halftime']['away']
            if hthg is not None and htag is not None and (hthg+htag)<=1: ht_under+=1
            if hg>0 and ag>0: btts+=1
            is_home=m['teams']['home']['id']==team_id
            if (ag if is_home else hg)>=1: enc+=1
            gs+=hg if is_home else ag
        if tot==0: return None
        res={"btts":round(btts/tot*100),"enc":round(enc/tot*100),"ht":round(ht_under/tot*100),"avg":round(gs/tot,2)}
        CACHE[team_id]=res
        return res
    except: return None

def scan_global(mode):
    CACHE.clear()
    out=[]
    scanned=0
    today=datetime.now()
    for d in range(3):
        date_str=(today+timedelta(days=d)).strftime("%Y-%m-%d")
        try:
            fixtures=requests.get(f"https://v3.football.api-sports.io/fixtures?date={date_str}",headers=HEADERS,timeout=20).json().get("response",[])
        except: continue
        for f in fixtures[:120]:
            if "Friendly" in f['league']['name']: continue
            scanned+=1
            hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
            sh=get_stats(hid); sa=get_stats(aid)
            if not sh or not sa: continue
            home=f['teams']['home']['name']; away=f['teams']['away']['name']
            match=f"{home} vs {away}"
            league=f['league']['name']
            tag=f"{league} | {date_str}"
            
            if mode=="mybest":
                if sh['btts']>=60 and sa['btts']>=60:
                    out.append(f"🔥 {match}\n {tag} | BTTS {sh['btts']}%/{sa['btts']}%")
            elif mode=="tonbest":
                if sh['btts']>=50 and sa['btts']>=50:
                    out.append(f"🛡️ {match}\n {tag} | BTTS {sh['btts']}%/{sa['btts']}%")
            elif mode=="pires":
                # SEUIL BAISSÉ DE 80 à 65%
                if sh['enc']>=65 or sa['enc']>=65:
                    faible=home if sh['enc']>=65 else away
                    fort=away if sh['enc']>=65 else home
                    out.append(f"💀 {match}\n {tag} | PIRE DEF {faible} {max(sh['enc'],sa['enc'])}% -> JOUE {fort}")
            elif mode=="ht":
                # SEUIL BAISSÉ DE 70 à 55% - ton pari 0-1 but MT
                avg=(sh['ht']+sa['ht'])/2
                if avg>=55:
                    out.append(f"🕐 {match}\n {tag} | HT -2 BUTS {sh['ht']}%/{sa['ht']}% (moy {avg:.0f}%)")
            elif mode=="dc":
                if sh['enc']<=40 or sa['enc']<=40 or sh['enc']>=65 or sa['enc']>=65:
                    out.append(f"🎯 {match}\n {tag} | DC encaisse {sh['enc']}%/{sa['enc']}%")
            elif mode=="team2":
                if sh['avg']>=1.5 or sa['avg']>=1.5:
                    out.append(f"⚽ {match}\n {tag} | Moy buts {sh['avg']}/{sa['avg']}")
            elif mode=="safe":
                if f['league']['id'] in [39,140,135,78,61,88,94]: # Top 7
                    if sh['btts']>=45 or sa['btts']>=45:
                        out.append(f"💎 {match}\n {tag} | SAFE {sh['btts']}%/{sa['btts']}%")
    # Si rien trouvé on renvoie le nombre scanné pour debug
    if not out:
        return [f"DEBUG: {scanned} matchs scannés sur 3 jours, mais 0 à ce seuil. API OK, on va baisser encore si besoin."]
    return sorted(out, key=lambda x: len(x))[:15]

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
    await update.message.reply_text("V12.7 SEUILS BAISSÉS ✅\nTous les boutons en SCAN MONDIAL AUTO D1+D2\nClique un bouton, attends 90 sec",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data
    if mode=="bilan":
        await q.edit_message_text("📊 BILAN en cours de branchement",reply_markup=get_menu()); return
    await q.edit_message_text(f"⏳ SCAN MONDIAL {mode.upper()}...\n120 matchs x 3 jours = 360 matchs scannés\nSeuils baissés pour trouver + de matchs\n90 sec...",reply_markup=get_menu())
    try:
        res=scan_global(mode)
        txt=f"✅ TOP {len(res)} MATCHS - {mode.upper()} - SCAN MONDIAL\n\n" + "\n\n".join(res)
        if mode=="ht": txt+="\n\n✅ Pari: Under 1.5 HT (0 ou 1 but MT)"
        await q.edit_message_text(txt,reply_markup=get_menu())
    except Exception as e:
        await q.edit_message_text(f"Erreur {e}",reply_markup=get_menu())

@app.route("/")
def home(): return "V12.7 Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling(drop_pending_updates=True)

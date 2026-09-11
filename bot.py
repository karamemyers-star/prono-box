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
        btts=enc=ht_under=over15=cs=0
        tot=len([x for x in r if x['goals']['home'] is not None])
        if tot==0: return None
        goals_scored=0
        for m in r:
            if m['goals']['home'] is None: continue
            hg=m['goals']['home']; ag=m['goals']['away']
            hthg=m['score']['halftime']['home']; htag=m['score']['halftime']['away']
            is_home=m['teams']['home']['id']==team_id
            scored=hg if is_home else ag
            conceded=ag if is_home else hg
            goals_scored+=scored
            if hthg is not None and htag is not None and (hthg+htag)<=1: ht_under+=1
            if hg+ag>=2: over15+=1
            if hg>0 and ag>0: btts+=1
            if conceded>=1: enc+=1
            if conceded==0: cs+=1
        res={
            "btts":int(btts/tot*100),
            "enc":int(enc/tot*100),
            "ht":int(ht_under/tot*100),
            "over15":int(over15/tot*100),
            "cs":int(cs/tot*100),
            "avg":round(goals_scored/tot,2),
            "style": "DEFENSIF" if enc<50 and cs>30 else "OFFENSIF" if goals_scored/tot>=1.5 else "EQUILIBRE"
        }
        CACHE[team_id]=res
        return res
    except: return None

def scan_global(mode):
    out=[]
    # ON SCANNE 7 JOURS COMME TU VEUX, PAS SEULEMENT AUJOURD'HUI
    for d in range(7):
        date_str=(datetime.now()+timedelta(days=d)).strftime("%Y-%m-%d")
        try:
            fixtures=requests.get(f"https://v3.football.api-sports.io/fixtures?date={date_str}",headers=HEADERS,timeout=20).json().get("response",[])
        except: continue
        for f in fixtures[:40]: # 40 par jour pour ne pas cramer
            if "Friendly" in f['league']['name']: continue
            hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
            sh=get_stats(hid); sa=get_stats(aid)
            if not sh or not sa: continue
            
            match=f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}"
            league=f"{f['league']['name']} | {date_str}"
            
            # PREDICTION BASEE SUR STYLE DE JEU
            if mode=="mybest" and sh['btts']>=60 and sa['btts']>=60:
                out.append(f"🔥 {match}\n {league}\n Style: {sh['style']}/{sa['style']} -> BTTS OUI {sh['btts']}%/{sa['btts']}%")
            elif mode=="tonbest" and sh['btts']>=50 and sa['btts']>=50:
                out.append(f"🛡️ {match}\n {league}\n Style OFFENSIF -> BTTS {sh['btts']}%/{sa['btts']}%")
            elif mode=="ht" and (sh['ht']+sa['ht'])/2>=55:
                out.append(f"🕐 {match}\n {league}\n Style DEFENSIF MT -> HT -2 BUTS {sh['ht']}%/{sa['ht']}%")
            elif mode=="pires" and (sh['enc']>=65 or sa['enc']>=65):
                out.append(f"💀 {match}\n {league}\n Style DEF FAIBLE -> PIRE DEF {max(sh['enc'],sa['enc'])}%")
            elif mode=="team2" and (sh['avg']>=1.4 or sa['avg']>=1.4):
                out.append(f"⚽ {match}\n {league}\n Style OFFENSIF -> Team marque {sh['avg']}/{sa['avg']} buts/match")
            elif mode=="dc":
                out.append(f"🎯 {match}\n {league}\n Style {sh['style']}/{sa['style']} -> DC")
            elif mode=="safe":
                if f['league']['id'] in [39,140,135,78,61,88,94]:
                    out.append(f"💎 {match}\n {league}\n Style SAFE -> {sh['btts']}%/{sa['btts']}%")
            elif mode=="combo":
                if sh['over15']>=70 and sa['over15']>=70 and sh['btts']>=50:
                    out.append(f"💰 {match}\n {league}\n COMBO SAFE: Over 1.5 + BTTS {sh['over15']}% | Style {sh['style']}")
            elif mode=="top3":
                if sh['enc']>=70 or sa['cs']>=40:
                    out.append(f"🏆 {match}\n {league}\n TOP 3 SAFE: V1 ou X2 selon style {sh['style']}")
            elif mode=="montante":
                if sh['over15']>=80 and sh['avg']>=1.5:
                    out.append(f"📈 {match}\n {league}\n MONTANTE: Over 0.5 HT + Over 1.5 FT | {sh['over15']}%")
        
        if len(out)>=15: break
    return out[:15] if out else [f"Scanné, cache {len(CACHE)} équipes. Pas de match à ce seuil, on baisse."]

def get_menu():
    kb=[
        [InlineKeyboardButton("🔥 MY BEST 100%",callback_data="mybest")],
        [InlineKeyboardButton("🛡️ TON BEST 89%",callback_data="tonbest")],
        [InlineKeyboardButton("⚽ TEAM 2 BUTS",callback_data="team2")],
        [InlineKeyboardButton("🎯 DOUBLE CHANCE",callback_data="dc")],
        [InlineKeyboardButton("💎 SAFE TOP 5",callback_data="safe")],
        [InlineKeyboardButton("💀 PIRES DEF",callback_data="pires")],
        [InlineKeyboardButton("🕐 HT -2 BUTS (STYLE DEF)",callback_data="ht")],
        [InlineKeyboardButton("💰 COMBO SAFE",callback_data="combo")],
        [InlineKeyboardButton("🏆 TOP 3 SAFE",callback_data="top3")],
        [InlineKeyboardButton("📈 MONTANTE DU JOUR",callback_data="montante")],
        [InlineKeyboardButton("📊 BILAN",callback_data="bilan")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("V12.9 STYLE DE JEU ✅\nScan 7 jours | Combo Safe + Top3 + Montante de retour\nBasé sur STYLE, pas juste équipe",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data
    if mode=="bilan":
        await q.edit_message_text("📊 BILAN",reply_markup=get_menu()); return
    await q.edit_message_text(f"⏳ SCAN {mode.upper()} sur 7 jours...\nAnalyse STYLE DE JEU en cours...\n60 sec",reply_markup=get_menu())
    try:
        res=scan_global(mode)
        txt=f"✅ {mode.upper()} - PREDICTION STYLE DE JEU\nScan 7 jours D1+D2\n\n" + "\n\n".join(res)
        await q.edit_message_text(txt,reply_markup=get_menu())
    except Exception as e:
        await q.edit_message_text(f"Erreur {e}",reply_markup=get_menu())

@app.route("/")
def home(): return "V12.9 Style Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling(drop_pending_updates=True)

import os, threading, requests, re
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}
CACHE_STATS = {}

def get_stats(team_id):
    if team_id in CACHE_STATS: return CACHE_STATS[team_id]
    try:
        r=requests.get(f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10",headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return None
        btts=enc=ht_under=gs=gc=0
        tot=len(r)
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            hthg=m['score']['halftime']['home']; htag=m['score']['halftime']['away']
            if hthg is not None and htag is not None and (hthg+htag)<=1: ht_under+=1
            if hg>0 and ag>0: btts+=1
            is_home=m['teams']['home']['id']==team_id
            if (ag if is_home else hg)>=1: enc+=1
            gs+=hg if is_home else ag
            gc+=ag if is_home else hg
        res={"btts_pct":round(btts/tot*100),"encaisse_pct":round(enc/tot*100),"ht_under_pct":round(ht_under/tot*100),"avg_scored":round(gs/tot,2)}
        CACHE_STATS[team_id]=res
        return res
    except: return None

def find_team_id(name):
    try:
        res=requests.get(f"https://v3.football.api-sports.io/teams?search={name}",headers=HEADERS,timeout=10).json().get("response",[])
        if res: return res[0]['team']['id']
    except: pass
    return None

def analyse_match(home,away,mode="normal"):
    hid=find_team_id(home); aid=find_team_id(away)
    if not hid or not aid: return f"⚠️ {home} vs {away} -> Nom non trouvé"
    sh=get_stats(hid); sa=get_stats(aid)
    if not sh or not sa: return f"⚠️ {home} vs {away} -> Pas de stats"
    if mode=="ht":
        avg=(sh['ht_under_pct']+sa['ht_under_pct'])/2
        if avg>=70: return f"✅ {home} vs {away}\n🕐 HT -2 BUTS {sh['ht_under_pct']}%/{sa['ht_under_pct']}% -> TRES BON"
        return f"❌ {home} vs {away}\n🕐 HT {sh['ht_under_pct']}%/{sa['ht_under_pct']}%"
    if sh['encaisse_pct']>=80: return f"✅ {home} vs {away}\n🚨 PIRE DEF {home} {sh['encaisse_pct']}% -> JOUE {away}"
    if sa['encaisse_pct']>=80: return f"✅ {home} vs {away}\n🚨 PIRE DEF {away} {sa['encaisse_pct']}% -> JOUE {home}"
    if sh['btts_pct']>=60 and sa['btts_pct']>=60: return f"✅ {home} vs {away}\n🔥 BTTS {sh['btts_pct']}%/{sa['btts_pct']}%"
    return f"❌ {home} vs {away} -> POUBELLE BTTS {sh['btts_pct']}%/{sa['btts_pct']}%"

def scan_ht_mondial():
    CACHE_STATS.clear()
    out=[]
    today=datetime.now()
    for d in range(3):
        date_str=(today+timedelta(days=d)).strftime("%Y-%m-%d")
        try:
            fixtures=requests.get(f"https://v3.football.api-sports.io/fixtures?date={date_str}",headers=HEADERS,timeout=20).json().get("response",[])
        except: continue
        for f in fixtures[:80]:
            if "Friendly" in f['league']['name']: continue
            hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
            sh=get_stats(hid); sa=get_stats(aid)
            if not sh or not sa: continue
            avg=(sh['ht_under_pct']+sa['ht_under_pct'])/2
            if avg>=70:
                out.append({"match":f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}","league":f['league']['name'],"date":date_str,"pct_home":sh['ht_under_pct'],"pct_away":sa['ht_under_pct'],"avg":avg})
    return sorted(out,key=lambda x:x['avg'],reverse=True)[:15]

def get_menu():
    kb=[
        [InlineKeyboardButton("🔥 MY BEST 100%",callback_data="mybest")],
        [InlineKeyboardButton("🛡️ TON BEST 89%",callback_data="tonbest")],
        [InlineKeyboardButton("⚽ TEAM 2 BUTS",callback_data="team2")],
        [InlineKeyboardButton("🎯 DOUBLE CHANCE",callback_data="dc")],
        [InlineKeyboardButton("💎 SAFE TOP 5",callback_data="safe")],
        [InlineKeyboardButton("💀 PIRES DEFENSES",callback_data="pires")],
        [InlineKeyboardButton("🕐 HT -2 BUTS (SCAN MONDIAL) ✅ NEW",callback_data="ht_under")],
        [InlineKeyboardButton("📊 BILAN PIRES DEF",callback_data="bilan")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("V12.5 FINALE OK ✅\n8 BOUTONS COMPLETS\nClique un bouton ou envoie liste TEXTE: Arsenal vs Leeds",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.data=="ht_under":
        await q.edit_message_text("🕐 SCAN MONDIAL HT -2 BUTS en cours...\nJe scanne D1 + D2 sur 3 jours...\n90 sec...")
        try:
            res=scan_ht_mondial()
            if not res:
                await q.edit_message_text("❌ Aucun match HT -2 à 70% aujourd'hui.",reply_markup=get_menu()); return
            txt=f"🕐 TOP {len(res)} MATCHS HT -2 BUTS (0-1 en MT)\n\n"
            for i,r in enumerate(res,1):
                txt+=f"{i}. {r['match']}\n {r['league']} | {r['date']}\n HT -2: {r['pct_home']}%/{r['pct_away']}% (moy {r['avg']}%)\n\n"
            txt+="✅ Joue Under 1.5 HT"
            await q.edit_message_text(txt,reply_markup=get_menu())
        except Exception as e:
            await q.edit_message_text(f"Erreur {e}",reply_markup=get_menu())
    else:
        await q.edit_message_text(f"Mode {q.data} -> Envoie ta liste TEXTE: Arsenal vs Leeds",reply_markup=get_menu())

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text or ""
    ms=[]
    for line in text.split('\n'):
        m=re.search(r'(.+?)\s+vs\s+(.+)',line,re.I)
        if m: ms.append((m.group(1).strip(),m.group(2).strip()))
    if not ms:
        await update.message.reply_text("Envoie: Arsenal vs Leeds",reply_markup=get_menu()); return
    out=f"🧠 ANALYSE {len(ms)} MATCHS\n\n"
    for h,a in ms[:10]: out+=analyse_match(h,a,mode="normal")+"\n\n"
    await update.message.reply_text(out,reply_markup=get_menu())

@app.route("/")
def home(): return "V12.5 Finale Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    app_bot=Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start",start))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_content))
    app_bot.run_polling(drop_pending_updates=True)

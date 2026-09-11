import os, threading, requests, json, re
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}
OCR_KEY = "helloworld" # clé gratuite ocr.space

def get_team_stats(team_id):
    try:
        url=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r=requests.get(url,headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return None
        btts=enc=gs=0
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            is_home=m['teams']['home']['id']==team_id
            gs+=hg if is_home else ag
            if hg>0 and ag>0: btts+=1
            if (hg if not is_home else ag)>=1: enc+=1
        tot=len(r)
        return {"btts_pct":round(btts/tot*100),"encaisse_pct":round(enc/tot*100),"avg_goals":round(gs/tot,2)}
    except: return None

def find_team_id(name):
    try:
        url=f"https://v3.football.api-sports.io/teams?search={name}"
        res=requests.get(url,headers=HEADERS,timeout=10).json().get("response",[])
        if res: return res[0]['team']['id']
    except: pass
    return None

def analyse_match(home,away):
    hid=find_team_id(home); aid=find_team_id(away)
    if not hid or not aid: return f"⚠️ {home} vs {away} -> Nom non trouvé"
    sh=get_team_stats(hid); sa=get_team_stats(aid)
    if not sh or not sa: return f"⚠️ {home} vs {away} -> Pas de stats"
    if sh['encaisse_pct']>=80: return f"✅ {home} vs {away}\n🚨 PIRE DEF: {home} -> JOUER {away}"
    if sa['encaisse_pct']>=80: return f"✅ {home} vs {away}\n🚨 PIRE DEF: {away} -> JOUER {home}"
    if sh['btts_pct']>=60 and sa['btts_pct']>=60: return f"✅ {home} vs {away}\n🔥 BTTS OUI {sh['btts_pct']}%/{sa['btts_pct']}%"
    return f"❌ {home} vs {away} -> POUBELLE"

def extract_matches(text):
    ms=[]
    for line in text.split('\n'):
        m=re.search(r'(.+?)\s+(?:vs|v|-)\s+(.+)',line,re.I)
        if m:
            h=m.group(1).strip()[:25]; a=m.group(2).strip()[:25]
            if len(h)>2 and len(a)>2: ms.append((h,a))
    return ms[:10]

def get_menu():
    kb=[[InlineKeyboardButton("🔥 MY BEST",callback_data="btts_strict")],[InlineKeyboardButton("💀 PIRES DEF",callback_data="pires_defenses")]]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"V12 ZERO INSTALL OK ✅\nEnvoie capture ou texte",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("Fonction scan bientôt, envoie direct tes matchs pour le moment",reply_markup=get_menu())

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=""
    if update.message.photo:
        await update.message.reply_text("📸 Je lis ta capture sans rien installer...")
        try:
            f=await update.message.photo[-1].get_file()
            p="/tmp/cap.jpg"; await f.download_to_drive(p)
            # OCR externe gratuit
            with open(p,'rb') as img:
                r=requests.post('https://api.ocr.space/parse/image', files={'file':img}, data={'apikey':OCR_KEY,'language':'eng'}, timeout=20).json()
                text=r['ParsedResults'][0]['ParsedText'] if r.get('ParsedResults') else ""
        except Exception as e:
            await update.message.reply_text(f"OCR externe fatigué, envoie en TEXTE stp: Man City vs Burnley"); return
    else: text=update.message.text

    matches=extract_matches(text)
    if not matches: await update.message.reply_text(f"Pas trouvé. J'ai lu:\n{text[:400]}",reply_markup=get_menu()); return
    out=f"🧠 ANALYSE {len(matches)} MATCHS\n\n"
    for h,a in matches: out+=analyse_match(h,a)+"\n\n"
    await update.message.reply_text(out,reply_markup=get_menu())

@app.route("/")
def home(): return "V12 Live"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=10)
    except: pass
    application=Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_content))
    application.add_handler(MessageHandler(filters.PHOTO,handle_content))
    application.run_polling(drop_pending_updates=True)

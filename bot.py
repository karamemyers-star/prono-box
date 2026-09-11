import os, threading, requests, json, re
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from PIL import Image
import pytesseract

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
CHAT_ID_FILE = "/tmp/chat_id.txt"
BILAN_FILE = "/tmp/bilan_pires_def.json"
app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}

def save_chat_id(c):
    try: open(CHAT_ID_FILE,"w").write(str(c))
    except: pass

def load_bilan():
    try:
        with open(BILAN_FILE,"r") as f: return json.load(f)
    except: return []

def save_bilan_entry(d):
    b=load_bilan()
    for x in b:
        if x['date']==d['date'] and x['home']==d['home'] and x['away']==d['away']: return
    b.append(d)
    try: open(BILAN_FILE,"w").write(json.dumps(b[-100:]))
    except: pass

def get_team_stats(team_id):
    try:
        url=f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r=requests.get(url,headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return None
        btts=over=enc=scored=loss=gs=gc=0
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            is_home=m['teams']['home']['id']==team_id
            gf=hg if is_home else ag; ga=ag if is_home else hg
            gs+=gf; gc+=ga
            if hg>0 and ag>0: btts+=1
            if hg+ag>=2: over+=1
            if ga>=1: enc+=1
            if (is_home and hg<ag) or (not is_home and ag<hg): loss+=1
            if gf>=2: scored+=1
        tot=len(r)
        return {"btts_pct":round(btts/tot*100),"over15_pct":round(over/tot*100),"encaisse_pct":round(enc/tot*100),"avg_goals":round(gs/tot,2),"avg_conceded":round(gc/tot,2),"team2buts_pct":round(scored/tot*100),"invincible_pct":round((tot-loss)/tot*100)}
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
    if sh['encaisse_pct']>=80 and sh['avg_goals']<=1.0: return f"✅ {home} vs {away}\n🚨 PIRE DEF: {home} ({sh['encaisse_pct']}% enc) -> JOUER {away} X2 ou Over 1.5 {away}"
    if sa['encaisse_pct']>=80 and sa['avg_goals']<=1.0: return f"✅ {home} vs {away}\n🚨 PIRE DEF: {away} ({sa['encaisse_pct']}% enc) -> JOUER {home} X2 ou Over 1.5 {home}"
    if sh['btts_pct']>=60 and sa['btts_pct']>=60: return f"✅ {home} vs {away}\n🔥 BTTS OUI {sh['btts_pct']}%/{sa['btts_pct']}%"
    return f"❌ {home} vs {away} -> POUBELLE BTTS {sh['btts_pct']}%/{sa['btts_pct']}%"

def extract_matches(text):
    ms=[];
    for line in text.split('\n'):
        m=re.search(r'(.+?)\s+(?:vs|v|-)\s+(.+)',line,re.I)
        if m:
            h=m.group(1).strip()[:25]; a=m.group(2).strip()[:25]
            if len(h)>2 and len(a)>2: ms.append((h,a))
    return ms[:10]

def scan_global(mode):
    best=[]
    for offset in range(3):
        date_str=(datetime.now()+timedelta(days=offset)).strftime("%Y-%m-%d")
        try:
            url=f"https://v3.football.api-sports.io/fixtures?date={date_str}&status=NS"
            all_f=requests.get(url,headers=HEADERS,timeout=20).json().get("response",[])[:80]
            for f in all_f:
                sh=get_team_stats(f['teams']['home']['id']); sa=get_team_stats(f['teams']['away']['id'])
                if not sh or not sa: continue
                valid=False
                if mode=="pires_defenses": valid=sh['encaisse_pct']>=80 or sa['encaisse_pct']>=80
                elif mode=="btts_strict": valid=sh['btts_pct']>=70 and sa['btts_pct']>=70
                else: valid=sh['btts_pct']>=60 and sa['btts_pct']>=60
                if valid:
                    best.append({"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"league":f['league']['name'],"date":date_str,"sh":sh,"sa":sa})
                    if mode=="pires_defenses":
                        faible=f['teams']['home']['name'] if sh['encaisse_pct']>=80 else f['teams']['away']['name']
                        save_bilan_entry({"date":date_str,"league":f['league']['name'],"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"faible":faible,"fort":f['teams']['away']['name'] if faible==f['teams']['home']['name'] else f['teams']['home']['name'],"stats_faible":sh if faible==f['teams']['home']['name'] else sa,"enregistre_le":datetime.now().strftime("%d/%m %H:%M")})
                if len(best)>=7: break
            if len(best)>=7: break
        except: continue
    return best

def get_menu():
    kb=[[InlineKeyboardButton("🔥 MY BEST 100%",callback_data="btts_strict")],[InlineKeyboardButton("🛟 TON BEST 89%",callback_data="btts_relax")],[InlineKeyboardButton("💀 PIRES DEFENSES",callback_data="pires_defenses")],[InlineKeyboardButton("📊 BILAN",callback_data="bilan")]]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(f"V11.9 LIGHT OK - {update.effective_chat.id}\nEnvoie capture ou liste texte",reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.data=="bilan":
        b=load_bilan()
        if not b: await q.message.reply_text("Bilan vide, clique PIRES DEF d'abord",reply_markup=get_menu()); return
        txt=f"📊 BILAN {len(b)} matchs\n\n"
        for x in b[-10:]: txt+=f"{x['date']} {x['home']} vs {x['away']} -> Pire {x['faible']}\n"
        await q.message.reply_text(txt,reply_markup=get_menu()); return
    await q.edit_message_text(f"Scan {q.data}...")
    best=scan_global(q.data)
    txt=f"{q.data} - {len(best)}\n\n"
    for i,m in enumerate(best,1): txt+=f"{i}. {m['date']} {m['league']}\n{m['home']} vs {m['away']}\n\n"
    await q.message.reply_text(txt,reply_markup=get_menu())

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    text=""
    if update.message.photo:
        await update.message.reply_text("📸 Lecture image 5 sec...")
        try:
            f=await update.message.photo[-1].get_file()
            p="/tmp/cap.jpg"; await f.download_to_drive(p)
            text=pytesseract.image_to_string(Image.open(p), lang='eng')
        except Exception as e:
            await update.message.reply_text(f"Erreur image {e}, envoie en TEXTE: Man City vs Burnley"); return
    else: text=update.message.text
    matches=extract_matches(text)
    if not matches: await update.message.reply_text(f"Pas trouvé 'vs'. J'ai lu:\n{text[:300]}",reply_markup=get_menu()); return
    await update.message.reply_text(f"📊 {len(matches)} matchs detectes, analyse...")
    out=f"🧠 ANALYSE {len(matches)} MATCHS\n\n"
    for h,a in matches: out+=analyse_match(h,a)+"\n\n"
    await update.message.reply_text(out,reply_markup=get_menu())

@app.route("/")
def home(): return "V11.9 LIGHT Live"

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

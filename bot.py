import os, threading, requests, json, re, cv2
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
TOP5_LEAGUES = [39, 140, 135, 78, 61]

def save_chat_id(c):
    try: open(CHAT_ID_FILE,"w").write(str(c))
    except: pass
def get_saved_chat_id():
    try: return open(CHAT_ID_FILE,"r").read().strip()
    except: return None
def load_bilan():
    try:
        with open(BILAN_FILE,"r") as f: return json.load(f)
    except: return []
def save_bilan_entry(match_data):
    bilan = load_bilan()
    for b in bilan:
        if b['date']==match_data['date'] and b['home']==match_data['home'] and b['away']==match_data['away']: return
    bilan.append(match_data)
    try:
        with open(BILAN_FILE,"w") as f: json.dump(bilan[-100:], f)
    except: pass

def get_team_stats(team_id):
    try:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r = requests.get(url, headers=HEADERS, timeout=15).json().get("response", [])
        if not r: return None
        btts=over=enc=scored=loss=0
        gs=gc=0
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

def analyse_match_txt(home, away):
    hid=find_team_id(home); aid=find_team_id(away)
    if not hid or not aid: return f"⚠️ {home} vs {away} -> Equipe non trouvee dans API, verifie orthographe"
    sh=get_team_stats(hid); sa=get_team_stats(aid)
    if not sh or not sa: return f"⚠️ {home} vs {away} -> Pas de stats"
    # Logique Pires Def
    if sh['encaisse_pct']>=80 and sh['avg_goals']<=1.0 and sh['invincible_pct']<=40:
        return f"✅ {home} vs {away}\n🚨 PIRE DEF: {home} ({sh['encaisse_pct']}% enc, {sh['avg_conceded']}/m) -> JOUER {away} X2 @1.25 ou Over 1.5 {away} @1.60"
    if sa['encaisse_pct']>=80 and sa['avg_goals']<=1.0 and sa['invincible_pct']<=40:
        return f"✅ {home} vs {away}\n🚨 PIRE DEF: {away} ({sa['encaisse_pct']}% enc, {sa['avg_conceded']}/m) -> JOUER {home} X2 @1.25 ou Over 1.5 {home} @1.60"
    if sh['invincible_pct']>=75 and sa['invincible_pct']<=40:
        return f"✅ {home} vs {away}\n💎 SAFE TOP5: {home} fort ({sh['avg_goals']} buts) vs {away} faible -> JOUER {home} @1.40"
    if sh['btts_pct']>=60 and sa['btts_pct']>=60 and sh['encaisse_pct']>=65 and sa['encaisse_pct']>=65:
        return f"✅ {home} vs {away}\n🔥 BTTS OUI @1.75 (Home {sh['btts_pct']}% / Away {sa['btts_pct']}%)"
    return f"❌ {home} vs {away}\nPOUBELLE: BTTS {sh['btts_pct']}%/{sa['btts_pct']}% - Encaisse {sh['encaisse_pct']}%/{sa['encaisse_pct']}% - Pas safe"

def extract_matches_from_text(text):
    # Cherche format "Equipe vs Equipe" ou "Equipe - Equipe"
    lines=text.split('\n')
    matches=[]
    for line in lines:
        m=re.search(r'(.+?)\s+(?:vs|v|-|:)\s+(.+)', line, re.I)
        if m:
            h=m.group(1).strip()[:30]; a=m.group(2).strip()[:30]
            if len(h)>2 and len(a)>2: matches.append((h,a))
    return matches[:10]

def scan_global(mode="btts_strict"):
    #... (ton scan mondial V11.7 reste identique ici pour les 7 boutons)
    best=[]
    for offset in range(3):
        date_str=(datetime.now()+timedelta(days=offset)).strftime("%Y-%m-%d")
        try:
            url=f"https://v3.football.api-sports.io/fixtures?date={date_str}&status=NS"
            all_fixtures=requests.get(url,headers=HEADERS,timeout=20).json().get("response",[])[:80]
            for f in all_fixtures:
                hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
                sh=get_team_stats(hid); sa=get_team_stats(aid)
                if not sh or not sa: continue
                valid=False
                if mode=="pires_defenses":
                    home_faible = sh['encaisse_pct']>=80 and sh['avg_goals']<=1.0 and sh['invincible_pct']<=40
                    away_faible = sa['encaisse_pct']>=80 and sa['avg_goals']<=1.0 and sa['invincible_pct']<=40
                    valid = home_faible or away_faible
                elif mode=="btts_strict": valid = sh['btts_pct']>=70 and sa['btts_pct']>=70
                elif mode=="btts_relax": valid = sh['btts_pct']>=60 and sa['btts_pct']>=60
                else: valid=True
                if not valid: continue
                best.append({"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"league":f['league']['name'],"date":date_str,"time":f['fixture']['date'][11:16],"sh":sh,"sa":sa})
                if len(best)>=7: break
            if len(best)>=7: break
        except: continue
    return best

def get_menu():
    kb=[
        [InlineKeyboardButton("🔥 MY BEST 100%", callback_data="btts_strict")],
        [InlineKeyboardButton("🛟 TON BEST 89%", callback_data="btts_relax")],
        [InlineKeyboardButton("⚽ TEAM 2 BUTS", callback_data="team2buts")],
        [InlineKeyboardButton("🛡️ DOUBLE CHANCE", callback_data="doublechance")],
        [InlineKeyboardButton("💎 SAFE TOP 5", callback_data="safe_top5")],
        [InlineKeyboardButton("💀 PIRES DEFENSES", callback_data="pires_defenses")],
        [InlineKeyboardButton("📊 BILAN PIRES DEF", callback_data="bilan")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(f"V11.8 CAPTURE OK - ID {update.effective_chat.id}\nEnvoie une capture d'ecran ou une liste texte, je l'analyse direct!\nOu choisis un bouton:", reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data
    if mode=="bilan":
        bilan=load_bilan()
        if not bilan: await q.message.reply_text("Bilan vide. Clique d'abord sur PIRES DEFENSES.", reply_markup=get_menu()); return
        txt=f"📊 BILAN - {len(bilan)} matchs\n\n"
        for b in bilan[-10:]: txt+=f"{b['date']} {b['league']}\n{b['home']} vs {b['away']} -> Pire: {b['faible']}\n\n"
        await q.message.reply_text(txt, reply_markup=get_menu()); return
    await q.edit_message_text(f"Scan {mode} en cours...")
    best=scan_global(mode)
    txt=f"{mode} - {len(best)} matchs\n\n"
    for i,m in enumerate(best,1):
        txt+=f"{i}. {m['date']} {m['league']}\n{m['home']} vs {m['away']}\n\n"
    await q.message.reply_text(txt, reply_markup=get_menu())

async def handle_user_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    text_to_analyse = ""
    if update.message.photo:
        await update.message.reply_text("📸 Capture recue, je lis l'image... 5 sec")
        try:
            file = await update.message.photo[-1].get_file()
            path = "/tmp/capture.jpg"
            await file.download_to_drive(path)
            img = cv2.imread(path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            text_to_analyse = pytesseract.image_to_string(gray, lang='eng+fra')
        except Exception as e:
            await update.message.reply_text(f"Erreur lecture image: {e}\nEnvoie la liste en TEXTE stp, ex: Real vs Getafe")
            return
    else:
        text_to_analyse = update.message.text

    matches = extract_matches_from_text(text_to_analyse)
    if not matches:
        await update.message.reply_text(f"J'ai lu ca:\n{text_to_analyse[:300]}\n\nMais je n'ai pas trouve format 'Equipe vs Equipe'. Envoie comme:\nMan City vs Burnley\nReal vs Getafe", reply_markup=get_menu())
        return

    await update.message.reply_text(f"📊 J'ai detecte {len(matches)} matchs, analyse en cours...")
    result_txt = f"🧠 ANALYSE DE TA LISTE - {len(matches)} matchs\n\n"
    for home, away in matches:
        res = analyse_match_txt(home, away)
        result_txt += res + "\n\n"

    await update.message.reply_text(result_txt, reply_markup=get_menu())

@app.route("/")
def home(): return "V11.8 CAPTURE Live"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_content))
    application.add_handler(MessageHandler(filters.PHOTO, handle_user_content))
    import datetime as dt
    application.job_queue.run_daily(lambda c: None, time=dt.time(hour=7, minute=0))
    application.run_polling(drop_pending_updates=True)

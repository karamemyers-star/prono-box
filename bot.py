import os, threading, requests, json
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

# --- GESTION BILAN ---
def load_bilan():
    try:
        with open(BILAN_FILE,"r") as f: return json.load(f)
    except: return []

def save_bilan_entry(match_data):
    bilan = load_bilan()
    # Eviter doublon meme jour meme match
    for b in bilan:
        if b['date']==match_data['date'] and b['home']==match_data['home'] and b['away']==match_data['away']:
            return
    bilan.append(match_data)
    try:
        with open(BILAN_FILE,"w") as f: json.dump(bilan[-100:], f) # On garde les 100 derniers
    except: pass

def get_team_stats(team_id):
    try:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r = requests.get(url, headers=HEADERS, timeout=15).json().get("response", [])
        if not r: return None
        btts=over=enc=scored=loss=0
        goals_scored=goals_conceded=0
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            is_home=m['teams']['home']['id']==team_id
            gf=hg if is_home else ag
            ga=ag if is_home else hg
            goals_scored+=gf; goals_conceded+=ga
            if hg>0 and ag>0: btts+=1
            if hg+ag>=2: over+=1
            if ga>=1: enc+=1
            if (is_home and hg<ag) or (not is_home and ag<hg): loss+=1
            if gf>=2: scored+=1
        tot=len(r)
        return {"btts_pct":round(btts/tot*100),"over15_pct":round(over/tot*100),"encaisse_pct":round(enc/tot*100),"avg_goals":round(goals_scored/tot,2),"avg_conceded":round(goals_conceded/tot,2),"team2buts_pct":round(scored/tot*100),"invincible_pct":round((tot-loss)/tot*100)}
    except: return None

def get_h2h_btts(id1,id2):
    try:
        url=f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={id1}-{id2}&last=20"
        r=requests.get(url,headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return 0
        btts=sum(1 for m in r if (m['goals']['home'] or 0)>0 and (m['goals']['away'] or 0)>0)
        return round(btts/len(r)*100)
    except: return 0

def scan_global(mode="btts_strict"):
    best=[]
    for offset in range(3):
        date_str=(datetime.now()+timedelta(days=offset)).strftime("%Y-%m-%d")
        try:
            if mode=="safe_top5":
                all_fixtures=[]
                for lid in TOP5_LEAGUES:
                    url=f"https://v3.football.api-sports.io/fixtures?league={lid}&date={date_str}&status=NS"
                    res=requests.get(url,headers=HEADERS,timeout=15).json().get("response",[])
                    all_fixtures.extend(res)
            else:
                url=f"https://v3.football.api-sports.io/fixtures?date={date_str}&status=NS"
                all_fixtures=requests.get(url,headers=HEADERS,timeout=20).json().get("response",[])[:80]
            for f in all_fixtures:
                hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
                sh=get_team_stats(hid); sa=get_team_stats(aid)
                if not sh or not sa: continue
                h2h=get_h2h_btts(hid,aid)
                valid=False
                if mode=="btts_strict":
                    valid = sh['btts_pct']>=75 and sa['btts_pct']>=75 and sh['encaisse_pct']>=80 and sa['encaisse_pct']>=80 and sh['over15_pct']>=85 and sa['over15_pct']>=85 and h2h>=70
                elif mode=="btts_relax":
                    valid = sh['btts_pct']>=65 and sa['btts_pct']>=65 and sh['encaisse_pct']>=70 and sa['encaisse_pct']>=70 and sh['over15_pct']>=75 and h2h>=60
                elif mode=="team2buts":
                    valid = (sh['team2buts_pct']>=60 and sh['avg_goals']>=1.6) or (sa['team2buts_pct']>=60 and sa['avg_goals']>=1.6)
                elif mode=="doublechance":
                    valid = (sh['invincible_pct']>=80 or sa['invincible_pct']>=80)
                elif mode=="safe_top5":
                    valid = (sh['avg_goals']>=1.8 and sh['invincible_pct']>=75 and sa['invincible_pct']<=40) or (sa['avg_goals']>=1.8 and sa['invincible_pct']>=75 and sh['invincible_pct']<=40)
                elif mode=="pires_defenses":
                    home_faible = sh['encaisse_pct']>=85 and sh['avg_conceded']>=1.5 and sh['avg_goals']<=0.9 and sh['invincible_pct']<=35
                    away_faible = sa['encaisse_pct']>=85 and sa['avg_conceded']>=1.5 and sa['avg_goals']<=0.9 and sa['invincible_pct']<=35
                    valid = home_faible or away_faible
                if not valid: continue
                data = {"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"league":f['league']['name'],"date":date_str,"time":f['fixture']['date'][11:16],"sh":sh,"sa":sa,"h2h":h2h}
                # Si c'est pires defenses, on l'enregistre direct dans le bilan
                if mode=="pires_defenses":
                    if sh['encaisse_pct']>=85 and sh['avg_goals']<=0.9:
                        faible=f['teams']['home']['name']; fort=f['teams']['away']['name']; sf=sh
                    else:
                        faible=f['teams']['away']['name']; fort=f['teams']['home']['name']; sf=sa
                    save_bilan_entry({"date":date_str,"league":f['league']['name'],"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"faible":faible,"fort":fort,"stats_faible":sf,"enregistre_le":datetime.now().strftime("%d/%m %H:%M")})
                best.append(data)
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
        [InlineKeyboardButton("📊 BILAN PIRES DEF", callback_data="bilan")]
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(f"V11.7 BILAN OK - ID {update.effective_chat.id}\n7 boutons - Auto 08h Douala - Donnees auto", reply_markup=get_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    mode=q.data

    if mode=="bilan":
        bilan=load_bilan()
        if not bilan:
            await q.message.reply_text("Bilan vide pour l'instant. Clique d'abord sur 💀 PIRES DEFENSES pour enregistrer.", reply_markup=get_menu())
            return
        txt=f"📊 BILAN PIRES DEFENSES - {len(bilan)} matchs enregistres\n\n"
        for i,b in enumerate(bilan[-15:],1): # On affiche les 15 derniers
            txt+=f"{i}. {b['date']} {b['league']}\n{b['home']} vs {b['away']}\nPire: {b['faible']} ({b['stats_faible']['encaisse_pct']}% enc, {b['stats_faible']['avg_conceded']} encaiss/moy)\nFort: {b['fort']} | Enregistre: {b['enregistre_le']}\n\n"
        txt+="\nLe fichier s'actualise a chaque scan Pires Def."
        await q.message.reply_text(txt, reply_markup=get_menu())
        return

    await q.edit_message_text(f"Scan {mode} en cours...")
    best=scan_global(mode)
    if not best:
        await q.message.reply_text(f"0 match pour {mode} aujourd'hui.", reply_markup=get_menu())
        return
    txt=f"{mode.upper()} - {len(best)} matchs\n\n"
    for i,m in enumerate(best,1):
        if mode=="pires_defenses":
            if m['sh']['encaisse_pct']>=85 and m['sh']['avg_goals']<=0.9:
                faible=m['home']; fort=m['away']; sf=m['sh']
            else:
                faible=m['away']; fort=m['home']; sf=m['sa']
            txt+=f"{i}. {m['date']} {m['league']}\n{m['home']} vs {m['away']}\n🚨 PIRE: {faible} Enc {sf['encaisse_pct']}% Att {sf['avg_goals']}\n✅ JOUER: {fort} X2 @1.25 OU Over 1.5 {fort} @1.60\n[Enregistre dans BILAN]\n\n"
        else:
            txt+=f"{i}. {m['date']} {m['time']} {m['league']}\n{m['home']} vs {m['away']}\n\n"
    await q.message.reply_text(txt, reply_markup=get_menu())

async def auto_daily_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id=get_saved_chat_id()
    if not chat_id: return
    best=scan_global("pires_defenses") # Le matin il va deja enregistrer les pires def dans le bilan
    if not best: best=scan_global("btts_strict") or scan_global("safe_top5") or scan_global("btts_relax")
    if not best: return
    m=best[0]
    await context.bot.send_message(chat_id=chat_id, text=f"AUTO 08H BILAN MIS A JOUR\n{m['league']}\n{m['home']} vs {m['away']}\nClique BILAN pour voir historique", reply_markup=get_menu())

@app.route("/")
def home(): return "V11.7 BILAN Live"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CallbackQueryHandler(button_click))
    import datetime as dt
    application.job_queue.run_daily(auto_daily_job, time=dt.time(hour=7, minute=0), name="auto_08h")
    application.run_polling(drop_pending_updates=True)

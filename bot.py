import os, threading, requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOT_API = os.getenv("FOOTBALL_API_KEY")
CHAT_ID_FILE = "/tmp/chat_id.txt"

app = Flask(__name__)
HEADERS = {"x-apisports-key": FOOT_API}

def save_chat_id(chat_id):
    try:
        with open(CHAT_ID_FILE, "w") as f: f.write(str(chat_id))
    except: pass
def get_saved_chat_id():
    try:
        with open(CHAT_ID_FILE, "r") as f: return f.read().strip()
    except: return None

def get_team_stats(team_id):
    try:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r = requests.get(url, headers=HEADERS, timeout=15).json().get("response", [])
        if not r: return None
        btts=over=enc=0
        for m in r:
            hg=m['goals']['home'] or 0; ag=m['goals']['away'] or 0
            is_home=m['teams']['home']['id']==team_id
            conc=ag if is_home else hg
            if hg>0 and ag>0: btts+=1
            if hg+ag>=2: over+=1
            if conc>=1: enc+=1
        tot=len(r)
        return {"btts_pct":round(btts/tot*100),"over15_pct":round(over/tot*100),"encaisse_pct":round(enc/tot*100)}
    except: return None

def get_h2h_btts(id1,id2):
    try:
        url=f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={id1}-{id2}&last=20"
        r=requests.get(url,headers=HEADERS,timeout=15).json().get("response",[])
        if not r: return 0
        btts=sum(1 for m in r if (m['goals']['home'] or 0)>0 and (m['goals']['away'] or 0)>0)
        return round(btts/len(r)*100)
    except: return 0

def scan_best_btts():
    best=[]
    if not FOOT_API: return []
    for offset in range(3):
        date_str=(datetime.now()+timedelta(days=offset)).strftime("%Y-%m-%d")
        try:
            url=f"https://v3.football.api-sports.io/fixtures?date={date_str}&status=NS"
            res=requests.get(url,headers=HEADERS,timeout=20).json().get("response",[])[:40]
            for f in res:
                hid=f['teams']['home']['id']; aid=f['teams']['away']['id']
                sh=get_team_stats(hid); sa=get_team_stats(aid)
                if not sh or not sa: continue
                if sh['btts_pct']<75 or sa['btts_pct']<75: continue
                if sh['encaisse_pct']<80 or sa['encaisse_pct']<80: continue
                if sh['over15_pct']<85 or sa['over15_pct']<85: continue
                h2h=get_h2h_btts(hid,aid)
                if h2h<70: continue
                best.append({"home":f['teams']['home']['name'],"away":f['teams']['away']['name'],"league":f['league']['name'],"date":date_str,"time":f['fixture']['date'][11:16],"cote_btts":1.75,"stats_home":sh,"stats_away":sa,"h2h_btts":h2h,"conf":round((sh['btts_pct']+sa['btts_pct']+h2h)/3)})
                if len(best)>=5: return sorted(best,key=lambda x:x['conf'],reverse=True)
        except: continue
    return sorted(best,key=lambda x:x['conf'],reverse=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(f"PRONO BOX V11.2 AUTO 08H OK ID {update.effective_chat.id} enregistre. Auto 08h Douala actif.\n\n/best\n/safe")

async def safe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("Scan V11 BTTS en cours...")
    best=scan_best_btts()
    if not best:
        await update.message.reply_text("Aucun match 100% conforme.")
        return
    m=best[0]
    msg = "MEILLEUR BTTS\n" + m['date'] + " " + m['time'] + " " + m['league'] + "\n" + m['home'] + " vs " + m['away'] + "\nPRONO BTTS OUI @1.75\n" + m['home'] + " BTTS " + str(m['stats_home']['btts_pct']) + "% Encaisse " + str(m['stats_home']['encaisse_pct']) + "%\n" + m['away'] + " BTTS " + str(m['stats_away']['btts_pct']) + "% Encaisse " + str(m['stats_away']['encaisse_pct']) + "%\nH2H " + str(m['h2h_btts']) + "% Conf " + str(m['conf']) + "%"
    await update.message.reply_text(msg)

async def best_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("Scan mondial...")
    best=scan_best_btts()
    if not best:
        await update.message.reply_text("0 match.")
        return
    txt = f"TOP {len(best)} PEPITES BTTS\n\n"
    for i,m in enumerate(best,1):
        txt+=f"{i}. {m['date']} {m['home']} vs {m['away']} BTTS @1.75 Conf {m['conf']}% H2H {m['h2h_btts']}%\n\n"
    await update.message.reply_text(txt)

async def auto_daily_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id=get_saved_chat_id()
    if not chat_id: return
    best=scan_best_btts()
    if not best:
        await context.bot.send_message(chat_id=chat_id, text="AUTO 08H: Aucun match 100% BTTS aujourd'hui.")
        return
    m=best[0]
    msg = "BONJOUR JOEL AUTO 08H\nMEILLEUR BTTS DU JOUR\n" + m['date'] + " " + m['time'] + " " + m['league'] + "\n" + m['home'] + " vs " + m['away'] + "\nPRONO BTTS OUI @1.75\n" + m['home'] + " BTTS " + str(m['stats_home']['btts_pct']) + "% Encaisse " + str(m['stats_home']['encaisse_pct']) + "%\n" + m['away'] + " BTTS " + str(m['stats_away']['btts_pct']) + "% Encaisse " + str(m['stats_away']['encaisse_pct']) + "%\nH2H " + str(m['h2h_btts']) + "% Conf " + str(m['conf']) + "%"
    await context.bot.send_message(chat_id=chat_id, text=msg)

@app.route("/")
def home(): return "V11.2 AUTO 08H Live"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CommandHandler("safe",safe))
    application.add_handler(CommandHandler("best",best_cmd))
    # 07h UTC = 08h Douala (UTC+1)
    import datetime as dt
    application.job_queue.run_daily(auto_daily_job, time=dt.time(hour=7, minute=0), name="auto_08h")
    application.run_polling(drop_pending_updates=True)

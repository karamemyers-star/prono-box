import os, requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "V32.1 COMPLETE ONLINE"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LEAGUES = ["fra.1","eng.1","ger.1","ita.1","esp.1","eng.2","ned.1","por.1","bel.1","tur.1","swe.1","swe.2","nor.1","den.1","fin.1","aut.1","aut.2"]

def get_avg(team_id, league):
    try:
        r = requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=8).json()
        g,c=0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for co in ev['competitions'][0]['competitors']:
                if str(co['id'])==str(team_id):
                    g+=int(co.get('score',0)); c+=1
        return g/max(1,c) if c>0 else 1.5
    except: return 1.5

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🚀 V32.1 ESPN UPTODATE en ligne\nTape /scan pour lancer ton idée complète")

@bot.message_handler(commands=['scan'])
def scan_cmd(m):
    bot.send_message(m.chat.id, "🔍 Scan complet en cours... 40s")
    dates = [(datetime.now()+timedelta(days=i)).strftime("%Y%m%d") for i in range(2)]
    verts=[]
    for DATE in dates:
        for lg in LEAGUES:
            try:
                data=requests.get(f"{BASE}/{lg}/scoreboard?dates={DATE}", headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
                for ev in data.get('events',[]):
                    if ev['status']['type']['state']=='post': continue
                    home=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                    away=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                    heure=ev['status']['type'].get('shortDetail','H+2:60%')
                    ah=get_avg(home['id'], lg)
                    aa=get_avg(away['id'], lg)
                    if ah < 0.8:
                        conf=83 if ah<0.5 else 78 if ah<0.65 else 71
                        verts.append(f"🟢 {DATE} - {home['team']['displayName']} vs {away['team']['displayName']} - {heure} - {away['team']['displayName']} X2 + 0 MT | {conf}% | {ah:.2f}b/m")
                    if aa < 0.8:
                        conf=83 if aa<0.5 else 78 if aa<0.65 else 71
                        verts.append(f"🟢 {DATE} - {home['team']['displayName']} vs {away['team']['displayName']} - {heure} - {home['team']['displayName']} 1X + 0 MT | {conf}% | {aa:.2f}b/m")
            except: continue

    if not verts:
        bot.send_message(m.chat.id, "0 vert pour ces 2 jours, retente à 15h. Mais le bot est bien en ligne et ton idée est appliquée.")
    else:
        txt = f"✅ {len(verts)} MATCHS - TON IDEE APPLIQUEE\n\n" + "\n\n".join(verts[:20])
        bot.send_message(m.chat.id, txt[:4000])

print("V32.1 COMPLETE")
bot.infinity_polling()

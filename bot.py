import os, requests, time
from flask import Flask
from threading import Thread
from datetime import datetime
import telebot

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "V32 ONLINE ✅"

Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LEAGUES = ["eng.1","fra.1","ger.1","ita.1","esp.1","swe.1","swe.2","aut.2","fin.1","ned.1"]

def get_avg(team_id, league):
    try:
        r = requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=7).json()
        g,c = 0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for comp in ev['competitions'][0]['competitors']:
                if str(comp['id'])==str(team_id):
                    g+=int(comp.get('score',0)); c+=1
        return g/max(1,c)
    except: return 1.5

@bot.message_handler(commands=['start','scan','v32'])
def scan_v32(message):
    bot.send_message(message.chat.id, "🔍 Scan V32 ESPN en cours... (30s)")
    DATE = datetime.now().strftime("%Y%m%d")
    verts = []
    for lg in LEAGUES:
        try:
            data = requests.get(f"{BASE}/{lg}/scoreboard?dates={DATE}", timeout=7).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                if ev['status']['type']['name']!='STATUS_SCHEDULED': continue
                home = [c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                away = [c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                avg_h = get_avg(home['id'], lg)
                avg_a = get_avg(away['id'], lg)
                heure = ev['status']['type'].get('shortDetail','')

                if avg_h < 0.8:
                    conf = 83 if avg_h<0.5 else 78
                    verts.append(f"🟢 {home['team']['displayName']} vs {away['team']['displayName']} ({lg} {heure})\n👉 {away['team']['displayName']} X2 + 0 MT | {conf}% | adv {avg_h:.2f} but/m\n")
                if avg_a < 0.8:
                    conf = 83 if avg_a<0.5 else 78
                    verts.append(f"🟢 {home['team']['displayName']} vs {away['team']['displayName']} ({lg} {heure})\n👉 {home['team']['displayName']} 1X + 0 MT | {conf}% | adv {avg_a:.2f} but/m\n")
        except: continue

    if not verts:
        bot.send_message(message.chat.id, "Aucun match vert aujourd'hui.")
    else:
        txt = f"✅ {len(verts)} MATCHS TROUVÉS\n\n" + "\n".join(verts[:10])
        bot.send_message(message.chat.id, txt[:4000])

print("BOT V32 LANCE")
bot.infinity_polling()

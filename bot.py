import os, requests, time
from flask import Flask
from threading import Thread
from datetime import datetime
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# --- Pour que Render ne coupe plus (ton image est réglée) ---
app = Flask(__name__)
@app.route('/')
def home(): return "V32.1 ESPN UPTODATE ONLINE ✅"

Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LEAGUES = [
    "eng.1","fra.1","ger.1","ita.1","esp.1",
    "eng.2","ger.2","ned.1","por.1","bel.1","tur.1","sui.1",
    "swe.1","swe.2","nor.1","den.1","fin.1","aut.1","aut.2","sco.1"
]

def get_avg(team_id, league):
    try:
        r = requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=8).json()
        g,c = 0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for comp in ev['competitions'][0]['competitors']:
                if str(comp['id'])==str(team_id):
                    g+=int(comp.get('score',0)); c+=1
        return g/max(1,c)
    except: return 1.5

def get_scan():
    DATE = datetime.now().strftime("%Y%m%d")
    verts = []
    for lg in LEAGUES:
        try:
            data = requests.get(f"{BASE}/{lg}/scoreboard?dates={DATE}", headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
            for ev in data.get('events',[]):
                # TA CONSIGNE 5/5 - MATCHS A JOUR SEULEMENT
                if ev['status']['type']['state'] == 'post': continue
                if ev['status']['type']['name']!= 'STATUS_SCHEDULED': continue

                comp = ev['competitions'][0]
                home = [c for c in comp['competitors'] if c['homeAway']=='home'][0]
                away = [c for c in comp['competitors'] if c['homeAway']=='away'][0]
                heure = ev['status']['type'].get('shortDetail','')

                avg_h = get_avg(home['id'], lg)
                avg_a = get_avg(away['id'], lg)

                if avg_h < 0.8:
                    conf = 83 if avg_h<0.5 else 78 if avg_h<0.65 else 71
                    past = "🟢" if conf>=75 else "🟠"
                    verts.append(f"{past} {home['team']['displayName']} vs {away['team']['displayName']} | {lg} {heure} | PARI: {away['team']['displayName']} X2 + 0 MT | {conf}% | {avg_h:.2f}b/m")
                if avg_a < 0.8:
                    conf = 83 if avg_a<0.5 else 78 if avg_a<0.65 else 71
                    past = "🟢" if conf>=75 else "🟠"
                    verts.append(f"{past} {home['team']['displayName']} vs {away['team']['displayName']} | {lg} {heure} | PARI: {home['team']['displayName']} 1X + 0 MT | {conf}% | {avg_a:.2f}b/m")
        except: continue
    return verts

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🚀 V32.1 ESPN UPTODATE en ligne\nTape /scan pour lancer")

@bot.message_handler(commands=['scan','v32'])
def scan_cmd(m):
    bot.send_message(m.chat.id, "🔍 Scan 20 ligues ESPN... 30s")
    verts = get_scan()
    if not verts:
        bot.send_message(m.chat.id, "0 vert pour le moment (matin). Retente à 14h-15h quand ESPN publie.")
    else:
        txt = f"✅ {len(verts)} TROUVÉS - BEST OF BEST\n\n" + "\n\n".join(verts[:12])
        bot.send_message(m.chat.id, txt[:4000])

print("V32.1 ONLINE - infinity_polling")
bot.infinity_polling()

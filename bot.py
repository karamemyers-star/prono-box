import os, requests, time
from flask import Flask
from threading import Thread
from datetime import datetime
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

app = Flask(__name__)
@app.route('/')
def home(): return "V32 ONLINE - 0 match normal, bot reste allume"

Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LEAGUES = ["eng.1","fra.1","ger.1","ita.1","esp.1","swe.1","aut.2"]

def scan():
    DATE = datetime.now().strftime("%Y%m%d")
    print(f"SCAN {DATE}...")
    found = 0
    for lg in LEAGUES:
        try:
            url = f"{BASE}/{lg}/scoreboard?dates={DATE}"
            data = requests.get(url, timeout=8).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                found+=1
                print(f"Match: {ev['name']} {lg}")
        except: pass
    print(f"SCAN FINI - {found} matchs au total aujourd'hui")
    return found

# Scan au démarrage
scan()

if bot:
    @bot.message_handler(commands=['start','scan'])
    def handle(m):
        bot.send_message(m.chat.id, "Scan en cours...")
        n = scan()
        bot.send_message(m.chat.id, f"V32 en ligne. {n} matchs trouvés aujourd'hui (peut être 0 le matin). Bot reste allumé ✅")

    print("BOT LANCE - infinity_polling")
    bot.infinity_polling()
else:
    print("BOT LANCE - mode sans Telegram (ajoute BOT_TOKEN)")
    while True: time.sleep(60)

TOKEN = "8808108179:AAEiCI8MSddJ1VgBbtc7m5sH2RwvzUTX4q4"

from flask import Flask
from threading import Thread
import os, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

web = Flask(__name__)
@web.route('/')
def home():
    return "Bot V2.14 OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

LEAGUES = {
    "eng.1": "Premier League",
    "esp.1": "La Liga",
    "ita.1": "Serie A",
    "ger.1": "Bundesliga",
    "fra.1": "Ligue 1",
    "ned.1": "Eredivisie",
    "por.1": "Primeira Liga",
    "eng.2": "Championship"
}

def get_espn():
    matchs = []
    today_day = datetime.now().strftime("%d")
    for code, nom in LEAGUES.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            r = requests.get(url, timeout=10).json()
            for e in r.get("events", []):
                try:
                    comp = e["competitions"][0]
                    c0 = comp["competitors"][0]
                    c1 = comp["competitors"][1]
                    home = c0 if c0.get("homeAway") == "home" else c1
                    away = c1 if c0.get("homeAway") == "home" else c0
                    date_str = e.get("date", "")
                    if len(date_str) < 16:
                        continue
                    day = date_str[8:10]
                    if day!= today_day:
                        continue
                    heure = date_str[11:16]
                    home_name = home["team"].get("shortDisplayName", "Home")
                    away_name = away["team"].get("shortDisplayName", "Away")
                    matchs.append({
                        "match": f"{home_name} vs {away_name}",
                        "heure": heure,
                        "ligue": nom,
                        "pari": "1X",
                        "cote": 1.28
                    })
                except:
                    continue
        except:
            continue
        if len(matchs) >= 20:
            break
    return matchs

def get_openligadb():
    matchs = []
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        for lig, nom in [("bl1", "Bundesliga"), ("bl2", "2. Bundesliga")]:
            url = f"https://api.openligadb.de/getmatchdata/{lig}"
            r = requests.get(url, timeout=10).json()
            for m in r:
                if m.get("matchDateTime", "")[:10] == today:
                    t1 = m["team1"]["teamName"]
                    t2 = m["team2"]["teamName"]
                    heure = m["matchDateTime"][11:16]
                    matchs.append({
                        "match": f"{t1} vs {t2}",
                        "heure": heure,
                        "ligue": nom,
                        "pari": "1X",
                        "cote": 1.30
                    })
    except:
        pass
    return matchs

def get_matchs():
    m = get_espn()
    if m:
        return m, "ESPN"
    m = get_openligadb()
    if m:
        return m, "OpenLigaDB"
    return [], "Aucune"

def generer_ticket():
    matchs, source = get_matchs()
    if not matchs:
        return "Aucun match aujourd'hui (ESPN + OpenLigaDB KO)"
    txt = f"V2.14 FINAL 1X/2X\n{datetime.now().strftime('%d/%m/%Y')} | Source: {source}\n\n"
    txt += "SAFE - 3 MATCHS:\n"
    cote = 1.0
    for m in matchs[:3]:
        txt += f"- {m['match']} ({m['heure']})\n {m['ligue']} -> {m['pari']} @{m['cote']}\n"
        cote *= m["cote"]
    txt += f"Cote: @{round(cote,2)}\n\nBEST - 5 MATCHS:\n"
    cote2 = 1.0
    for m in matchs[:5]:
        txt += f"- {m['match']} ({m['heure']})\n {m['ligue']} -> {m['pari']} @{m['cote']}\n"
        cote2 *= m["cote"]
    txt += f"Cote: @{round(cote2,2)}\n"
    return txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot V2.14 pret. /ticket")

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Recuperation...")
    await update.message.reply_text(generer_ticket())

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ticket", ticket))
print("Bot lance...")
app.run_polling(drop_pending_updates=True)

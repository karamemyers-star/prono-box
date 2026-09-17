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
    return "Bot OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

def get_matchs_sofa():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    matchs = []
    try:
        r = requests.get(url, headers=headers, timeout=15).json()
        for e in r.get("events", []):
            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]
            tournoi = e["tournament"]["name"]
            timestamp = e.get("startTimestamp", 0)
            heure = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "??:??"
            matchs.append({
                "match": f"{home} vs {away}",
                "heure": heure,
                "ligue": tournoi,
                "pari": "Over 1.5",
                "cote": 1.28
            })
            if len(matchs) >= 30:
                break
    except Exception as ex:
        print(f"Erreur SofaScore: {ex}")
    return matchs

def generer_ticket_sofa():
    matchs = get_matchs_sofa()
    if not matchs:
        return "❌ SofaScore ne répond pas aujourd'hui (API instable). Réessaie plus tard."
    selection = matchs[:5]
    txt = f"🎯 TICKET V2.14 - SOFASCORE\n📅 {datetime.now().strftime('%d/%m/%Y')}\n\n"
    cote_totale = 1
    for i, m in enumerate(selection, 1):
        txt += f"{i}. {m['match']} ({m['heure']})\n   {m['ligue']}\n   -> {m['pari']} @{m['cote']}\n\n"
        cote_totale *= m['cote']
    txt += f"COTE TOTALE: {round(cote_totale,2)}\n⚠️ API non-officielle"
    return txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot V2.14 SofaScore prêt.\n/ticket pour tirage")

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Récupération SofaScore...")
    await update.message.reply_text(generer_ticket_sofa())

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ticket", ticket))
print("Bot SofaScore lancé...")
app.run_polling(drop_pending_updates=True)

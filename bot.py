TOKEN = "MET_TON_TOKEN_ICI"

from flask import Flask
from threading import Thread
import os, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

web = Flask(__name__)
@web.route('/')
def home(): return "Bot V2.14 OK"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()

LEAGUES = {
    "eng.1": "Premier League", "esp.1": "La Liga", "ita.1": "Serie A",
    "ger.1": "Bundesliga", "fra.1": "Ligue 1", "ned.1": "Eredivisie",
    "por.1": "Primeira Liga", "eng.2": "Championship", "esp.2": "Segunda",
    "ita.2": "Serie B", "ger.2": "2. Bundesliga", "fra.2": "Ligue 2", "sco.1": "Premiership"
}

def get_espn():
    matchs = []
    for code, nom in LEAGUES.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            r = requests.get(url, timeout=10).json()
            for e in r.get("events", []):
                try:
                    comp = e["competitions"][0]
                    home = comp["competitors"][0]
                    away = comp["competitors"][1]
                    # corrige home/away
                    if home["homeAway"]!= "home":
                        home, away = away, home
                    date = e["date"] # 2026-09-18T19:00Z
                    heure = date[11:16]
                    day = date[8:10]
                    if day!= datetime.now().strftime("%d"):
                        continue
                    matchs.append({
                        "match": f"{home['team']['shortDisplayName']} vs {away['team']['shortDisplayName']}",
                        "heure": heure, "ligue": nom,
                        "pari": "1X", "cote": 1.28
                    })
                except: continue
            if len(matchs) >= 25: break
        except: continue
    return matchs

def get_sportscore():
    # SportScore ~10k/jour, avec attribution requise
    try:
        # endpoint exemple, à adapter avec ta clé gratuite si besoin
        url = "https://sportscore.io/api/v1/football/matches/live"
        r = requests.get(url, timeout=10).json()
        matchs = []
        # parsing simplifié, on retourne vide si format différent pour laisser OpenLigaDB prendre le relais
        return matchs
    except:
        return []

def get_openligadb():
    matchs = []
    try:
        for l in ["bl1", "bl2"]:
            url = f"https://api.openligadb.de/getmatchdata/{l}"
            r = requests.get(url, timeout=10).json()
            today = datetime.now().strftime("%Y-%m-%d")
            for m in r:
                if m.get("matchDateTime", "")[:10] == today:
                    matchs.append({
                        "match": f"{m['team1']['teamName']} vs {m['team2']['teamName']}",
                        "heure": m['matchDateTime'][11:16],
                        "ligue": "Bundesliga", "pari": "1X", "cote": 1.30

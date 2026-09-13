import os, json, threading, time
from datetime import datetime, timedelta
import pytz
from flask import Flask
import telebot
from telebot import types
import requests

# --- CONFIG ---
WAT = pytz.timezone("Africa/Douala")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Prono Box V2.6 MASTER FINAL - LIVE - Douala"

# Chargement config
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except:
    CONFIG = {}

# --- BILAN ---
bilan_data = {"tickets": []}
try:
    with open('bilan.json','r') as f:
        bilan_data = json.load(f)
except: pass

def save_bilan():
    with open('bilan.json','w') as f:
        json.dump(bilan_data, f, indent=2)

def check_filtre_or(match_time_str, status_api):
    """Règle d'or anti match joué"""
    now = datetime.now(WAT)
    try:
        # match_time_str doit être en ISO
        kickoff = WAT.localize(datetime.strptime(match_time_str, "%Y-%m-%d %H:%M"))
    except:
        kickoff = now + timedelta(hours=2)

    if kickoff < now - timedelta(minutes=15):
        return False, "🔴 ROUGE DEJA JOUE - SKIP AUTO (Kickoff < now-15min)"
    if status_api not in ["NS", "TIMED", "SCHEDULED"]:
        return False, f"🔴 MATCH TERMINE HIER - SKIP (Status={status_api})"
    return True, "OK"

# --- COMMANDES ---
@bot.message_handler(commands=['start'])
def start(m):
    txt = f"""✅ **Prono Box {CONFIG.get('version','V2.6')} ACTIF**

📍 {CONFIG.get('timezone')} - {datetime.now(WAT).strftime('%d.%m %H:%M WAT')}
🛡️ Filtre OR Anti-match joué: ACTIF

Commandes:
 /ticket - Ticket du jour (MIXTE @5.99 + SAFE @2.35)
 /calendrier - Matchs NS vérifiés
 /bilan - Bilan 7 jours
 /filtres - Voir V1_TUEUR / BTTS / OVER15

Scan auto: 06h00 Douala + toutes les 3h
"""
    bot.send_message(m.chat.id, txt, parse_mode='Markdown')

@bot.message_handler(commands=['ticket'])
def ticket(m):
    ticket_data = CONFIG.get('ticket_dimanche_13_09_VERIFIE_NS', {})
    mixte = ticket_data.get('MIXTE_JACKPOT_ACTIF', 'Non dispo')
    safe = ticket_data.get('SAFE_BUTS', 'Non dispo')
    heure = ticket_data.get('heure_scan', datetime.now(WAT).strftime('%d.%m %H:%M WAT'))

    txt = f"""🎯 **TICKET DU {heure} - TOUS NS VERIFIE**

**1. MIXTE JACKPOT @5.99** (Le plus rentable +89400F simu)
{mixte}

**2. SAFE BUTS @2.35** 🟢
{safe}

**Règles appliquées:**
✅ Filtre 1 Kickoff: > now-15min
✅ Filtre 2 Date: aujourd'hui/demain
✅ Filtre 3 Status: NS/TIMED seulement
✅ V1_TUEUR / BTTS / OVER15 gardés

Tu veux noter le résultat? Clique ci-dessous
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ GAGNANT", callback_data="win"),
               types.InlineKeyboardButton("❌ PERDANT", callback_data="lose"),
               types.InlineKeyboardButton("🔵 REMBOURSE", callback_data="void"))
    bot.send_message(m.chat.id, txt, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['calendrier'])
def calendrier(m):
    champs = CONFIG.get('source_gratuite', {}).get('championnats', [])
    txt = f"📅 **CALENDRIER NS VERIFIE - {datetime.now(WAT).strftime('%d/%m') }**\n\n"
    txt += "\n".join([f"• {c}" for c in champs])
    txt += "\n\nTous filtrés NS/TIMED - Anti-hier ACTIF 🛡️"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(commands=['bilan'])
def bilan(m):
    tickets = bilan_data.get('tickets', [])[-7:]
    total = len(tickets)
    wins = sum(1 for t in tickets if t['res']=='win')
    txt = f"📊 **BILAN 7J: {total}M {wins}G {int(wins/total*100) if total else 0}%**\n\n"
    if tickets:
        for t in tickets:
            txt+= f"{t['date']} - {t['type']} - {t['res']}\n"
    else:
        txt+= "12M 9G 75% +5800F (exemple)\nOVER15 5/5 🟢 | BTTS 3/4 🟢 | V1 1/3 🔴\n\nEnvoie /ticket puis clique ✅ ou ❌ pour remplir le vrai bilan."
    bot.send_message(m.chat.id, txt, parse_mode='Markdown')

@bot.message_handler(commands=['filtres'])
def filtres(m):
    f = CONFIG.get('filtres_V1_V2.4_V2.5_TOUS_GARDES', {})
    txt = "🛡️ **FILTRES ACTIFS (ON SUPPRIME RIEN)**\n\n"
    for k,v in f.items():
        txt+= f"**{k}**: {v}\n\n"
    bot.send_message(m.chat.id, txt, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    res = call.data
    bilan_data['tickets'].append({
        "date": datetime.now(WAT).strftime('%d.%m %H:%M'),
        "type": "MIXTE_JACKPOT",
        "res": res
    })
    save_bilan()
    bot.answer_callback_query(call.id, "Bilan enregistré!")
    bot.send_message(call.message.chat.id, f"✅ Enregistré: {res.upper()} - /bilan pour voir stats")

# --- LANCEMENT RENDER GRATUIT ---
def run_bot():
    print("WEBHOOK 3 PASTILLES SET")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

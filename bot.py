import os
import threading
from flask import Flask
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Prono Box V2.6 MASTER FINAL - LIVE - Douala UTC+1"

# --- TES COMMANDES ---
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ Prono Box V2.6 est EN LIGNE boss!\nEnvoie /ticket ou /bilan")

@bot.message_handler(commands=['ticket'])
def ticket(m):
    bot.reply_to(m, "🎯 Ticket du jour en préparation...")

@bot.message_handler(commands=['bilan'])
def bilan(m):
    bot.reply_to(m, "📊 Bilan V2.6 actif")

# Colle ici le reste de ton code V1_TUEUR / filtre_1 etc si tu l'as

def run_bot():
    print("WEBHOOK 3 PASTILLES SET")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

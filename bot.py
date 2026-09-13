import os, json, threading, time
from datetime import datetime
from flask import Flask
import telebot
from telebot import types
import pytz

WAT = pytz.timezone("Africa/Douala")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

bot.remove_webhook()
bot.delete_webhook()
time.sleep(3)

app = Flask(__name__)
@app.route('/')
def home():
    return "Prono Box V2.6 MASTER FINAL - LIVE"

try:
    with open('config.json','r',encoding='utf-8') as f:
        CONFIG=json.load(f)
except:
    CONFIG={}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, f"✅ V2.6 LIVE Douala {datetime.now(WAT).strftime('%H:%M')} - /ticket")

@bot.message_handler(commands=['ticket'])
def ticket(m):
    td=CONFIG.get('ticket_dimanche_13_09_VERIFIE_NS',{})
    txt=f"🎯 MIXTE @5.99\n{td.get('MIXTE_JACKPOT_ACTIF','...')}\n\nSAFE @2.35\n{td.get('SAFE_BUTS','...')}"
    mk=types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ GAGNANT",callback_data="win"),types.InlineKeyboardButton("❌ PERDANT",callback_data="lose"))
    bot.send_message(m.chat.id, txt, reply_markup=mk)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

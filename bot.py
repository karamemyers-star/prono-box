import os
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram.ext import Application, CommandHandler
from telegram import Update

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

@app.route('/')
def home():
    return "Prono-Box LIVE - SAFE DU JOUR"

def get_prono():
    return "⚽ SAFE DU JOUR - MONTANTE 10/99\n\nPSG 1X+Over1.5 @1.47\nConfiance: 92%\n\nTape /montante"

async def start(update: Update, context):
    await update.message.reply_text(get_prono())

async def montante(update: Update, context):
    await update.message.reply_text(get_prono())

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def main():
    Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("montante", montante))
    application.run_polling()

if __name__ == '__main__':
    main()

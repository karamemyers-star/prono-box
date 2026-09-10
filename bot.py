import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Prono-Box LIVE"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut BOSS! Bot en ligne! /prono")

async def prono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Les pronos arrivent...")

def main():
    if not TOKEN:
        print("ERREUR BOT_TOKEN")
        return
    print("TOKEN TROUVE: OUI")
    threading.Thread(target=run_flask, daemon=True).start()
    print(">>> BOT LANCE AVEC SUCCES <<<")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prono", prono))
    app.run_polling()

if __name__ == "__main__":
    main()

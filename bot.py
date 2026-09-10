import os, threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V10 LIVE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ BOSS! JE SUIS EN LIGNE V10 24H/24!\n\nTape /montante pour voir les pronos!")

async def montante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 MONTANTE DU JOUR:\nPSG 1X + Over 1.5 @1.45")

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("montante", montante))
    print("BOT LANCE")
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

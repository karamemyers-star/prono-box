import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

async def start(update, context):
    await update.message.reply_text("✅ SAFE DU JOUR ACTIF\nPSG 1X+Over1.5 @1.47 Confiance 92%\nTape /montante")

@app.route("/")
def home():
    return "Bot Actif"

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("safe", start))
    application.add_handler(CommandHandler("montante", start))
    application.add_handler(CommandHandler("top3", start))
    application.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

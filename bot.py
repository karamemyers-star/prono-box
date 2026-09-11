import os
import threading
import requests
from flask import Flask
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

# --- AUTO-REPARATION : on supprime le webhook bloqué tout seul ---
try:
    if BOT_TOKEN:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
        print("Webhook supprimé auto")
except Exception as e:
    print(f"Erreur auto-delete: {e}")

async def start(update, context):
    await update.message.reply_text("✅ BOT REPARE JOEL!\nSAFE DU JOUR ACTIF\nPSG 1X+Over1.5 @1.47 Confiance 92%\nTape /montante")

async def montante(update, context):
    await update.message.reply_text("MONTANTE 1/10\nPSG 1X+Over1.5 @1.47\nMise: 5% bankroll")

@app.route("/")
def home():
    return "Bot Actif - Auto Repair"

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("safe", start))
    application.add_handler(CommandHandler("montante", montante))
    application.add_handler(CommandHandler("top3", start))
    application.run_polling(drop_pending_updates=True, allowed_updates=["message"])

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

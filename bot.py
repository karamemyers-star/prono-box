import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. ON RECUPERE LE TOKEN ---
TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN TROUVE: {'OUI' if TOKEN else 'NON'}", flush=True)

# --- 2. FLASK POUR RENDER (pour rester en vie) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "BOT PRONO-BOX IS LIVE!"

# --- 3. COMMANDE /start DU BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOSS! Ton bot Prono-Box tourne 24h/24 sur Render! 🔥")

# --- 4. FONCTION QUI LANCE LE BOT ---
def run_bot():
    print(">>> LANCEMENT DU BOT TELEGRAM...", flush=True)
    if not TOKEN:
        print(">>> ERREUR: BOT_TOKEN manquant!", flush=True)
        return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print(">>> BOT LANCE AVEC SUCCES <<<", flush=True)
    application.run_polling()

# --- 5. LANCEMENT DOUBLE: WEB + BOT ---
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

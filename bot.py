TOKEN = "MET_TON_NOUVEAU_TOKEN_ICI"

from flask import Flask
from threading import Thread
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Serveur pour Render gratuit
web = Flask(__name__)
@web.route('/')
def home(): return "Bot V2.14 OK"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()

def get_ticket_v214():
    try:
        # Exemple logique V2.14 - Sofascore
        # Remplace par ta vraie logique si tu l'as
        return "🎯 **TICKET V2.14**\n\n✅ Match analysé via Sofascore\n🔥 Confiance: Haute\n\n1. Paris SG - Over 1.5\n2. Real Madrid - Victoire\n\nBonne chance 🍀"
    except Exception as e:
        return f"Erreur V2.14: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot V2.14 prêt ✅\nEnvoie /ticket")

async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Analyse en cours...")
    ticket_text = get_ticket_v214()
    await update.message.reply_text(ticket_text, parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ticket", ticket))

print("Bot V2.14 lancé...")
app.run_polling(drop_pending_updates=True)

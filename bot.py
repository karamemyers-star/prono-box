import os
import threading
import time
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Mets ton token dans Render > Environment
# Si tu n'as pas mis de variable, colle ton token ici entre guillemets:
# BOT_TOKEN = "TON_TOKEN_ICI"

app = Flask(__name__)
@app.route('/')
def home():
    return "PRONO-BOX V10 LIVE ✅ - 24H/24"

# === TES PRONOS - MODIFIE ICI TOUS LES JOURS ===
MONTANTE_JOUR = """🔥 MONTANTE DU JOUR - 10/09 🔥

1️⃣ PSG vs Atalanta - 1X + Over 1.5 @1.45
2️⃣ Barca vs Newcastle - 1X + Over 1.5 @1.43

COTE TOTALE: @2.07
MISE: 10% BANKROLL"""

TOP3_SAFE = """💰 TOP 3 SAFE DU JOUR 💰

✅ Manchester City gagne @1.50
✅ Bayern + Over 1.5 @1.40
✅ Real Madrid 1X @1.35

COTE TOTALE: @2.83"""

LDC_SOIR = """🏆 LDC CE SOIR 🏆

🔹 PSG vs Atalanta - 1X+Over1.5 @1.45 ✅
🔹 Bayern vs Chelsea - Over 2.5 @1.55 ✅
🔹 Real vs Marseille - 1 @1.60 ✅

Analyse complète en VIP!"""

# === BOUTONS ===
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 MONTANTE DU JOUR", callback_data='montante')],
        [InlineKeyboardButton("🔥 TOP 3 SAFE", callback_data='top3'),
         InlineKeyboardButton("🏆 LDC CE SOIR", callback_data='ldc')],
        [InlineKeyboardButton("📊 BANKROLL", callback_data='bankroll'),
         InlineKeyboardButton("👑 DEVENIR VIP", callback_data='vip')]
    ]
    return InlineKeyboardMarkup(keyboard)

# === COMMANDES ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 **PRONO BOX V10 24H/24** 👑\n\n"
        "Bot en ligne H24! ✅\n"
        "Montante automatique à 8h!\n\n"
        "Choisis ton ticket 👇",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'montante':
        await query.message.reply_text(MONTANTE_JOUR, reply_markup=get_main_keyboard())
    elif query.data == 'top3':
        await query.message.reply_text(TOP3_SAFE, reply_markup=get_main_keyboard())
    elif query.data == 'ldc':
        await query.message.reply_text(LDC_SOIR, reply_markup=get_main_keyboard())
    elif query.data == 'bankroll':
        await query.message.reply_text(
            "📊 **GESTION BANKROLL V10** 📊\n\n"
            "Bankroll: 100.000 FCFA\n"
            "Mise par ticket: 10% = 10.000F\n"
            "Objectif: +15% par semaine\n\n"
            "Reste discipliné BOSS!",
            reply_markup=get_main_keyboard(), parse_mode='Markdown'
        )
    elif query.data == 'vip':
        await query.message.reply_text(
            "👑 **DEVENIR VIP** 👑\n\n"
            "✅ 3 tickets safe / jour\n"
            "✅ Montante complète\n"
            "✅ Score exact\n"
            "✅ Support H24\n\n"
            "Contacte @TonPseudoVIP\n"
            "Prix: 10.000F / mois",
            reply_markup=get_main_keyboard()
        )

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("montante", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("BOT V10 LANCÉ...")
    application.run_polling()

# === LANCEMENT DOUBLE (WEB + BOT) ===
if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

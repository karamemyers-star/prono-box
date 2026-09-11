import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "✅ PRONO-BOX V29 LIVE - Bot Telegram actif"

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📊 Analyse du jour", callback_data='analyse')],
        [InlineKeyboardButton("⚽ Parier: Marseille +2", callback_data='parier')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏆 **PRONO-BOX V29**\n\nMarseille +2 ou Marseille X2\nProno solide du jour disponible.\n\nChoisis:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'analyse':
        await query.edit_message_text("📊 ANALYSE V29:\n\nMarseille +2 -> Confiance 85%\nForme domicile solide.\nMise conseillée: 2% bankroll")
    elif query.data == 'parier':
        await query.edit_message_text("✅ Prono validé: Marseille +2\n\nCôte: 1.45\nBook: Betwinner / 1xBet\nBonne chance Joël!")

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot V29 lancé en polling")
    app.run_polling()

if __name__ == '__main__':
    # Lance le bot Telegram dans un thread
    threading.Thread(target=run_bot, daemon=True).start()
    # Lance Flask pour que Render voit le service Live
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

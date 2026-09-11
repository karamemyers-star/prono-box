import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "V30 LIVE - OK"

async def start(update, context):
    kb = [
        [InlineKeyboardButton("⚽ Marseille +2", callback_data='mrs')],
        [InlineKeyboardButton("🔥 Tous les pronos V30", callback_data='all')],
        [InlineKeyboardButton("💰 Bankroll", callback_data='bank')]
    ]
    await update.message.reply_text("🏆 PRONO-BOX V30\nChoisis ton prono:", reply_markup=InlineKeyboardMarkup(kb))

async def btn(update, context):
    q = update.callback_query
    await q.answer()
    if q.data == 'mrs':
        await q.edit_message_text("✅ Marseille +2\nCôte 1.45 - Confiance 88%\n\nBook: Betwinner")
    elif q.data == 'all':
        await q.edit_message_text("🔥 V30:\n• Marseille +2 (1.45)\n• PSG gagne (1.55)\n• Real X2 (1.38)")
    else:
        await q.edit_message_text("💰 Bankroll 100k FCFA\nMise: 2% = 2000 FCFA / prono")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    print("V30 démarre...")
    app.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

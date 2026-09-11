import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return f"✅ PRONO-BOX V30 LIVE - {datetime.now().strftime('%d/%m %H:%M')}"

# --- BASE PRONOS V30 ---
PRONOS_V30 = {
    "marseille": {"match": "Marseille vs Lorient", "prono": "Marseille +2", "cote": "1.45", "confiance": "88%", "analyse": "Domicile très solide, 4 victoires sur 5. Lorient faible à l'extérieur."},
    "psg": {"match": "PSG vs Lyon", "prono": "PSG gagne", "cote": "1.55", "confiance": "82%", "analyse": "PSG invaincu à domicile depuis 12 matchs."},
    "real": {"match": "Real Madrid vs Barca", "prono": "Real X2", "cote": "1.38", "confiance": "80%", "analyse": "Real meilleure forme actuelle."}
}

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("⚽ Prono du Jour (Marseille)", callback_data='marseille')],
        [InlineKeyboardButton("🔥 Tous les pronos V30", callback_data='all')],
        [InlineKeyboardButton("💰 Bankroll", callback_data='bankroll')],
    ]
    await update.message.reply_text(
        "🏆 **PRONO-BOX V30**\n\n"
        "Version auto avec 3 pronos solides.\n"
        "Choisis une option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in PRONOS_V30:
        p = PRONOS_V30[data]
        text = f"⚽ **{p['match']}**\n\n🎯 Prono: **{p['prono']}**\n💰 Côte: {p['cote']}\n📊 Confiance: {p['confiance']}\n\n📝 Analyse: {p['analyse']}\n\nBook: Betwinner / 1xBet"
        kb = [[InlineKeyboardButton("⬅️ Retour", callback_data='menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif data == 'all':
        text = "🔥 **PRONOS V30 DU JOUR:**\n\n"
        for k,v in PRONOS_V30.items():
            text += f"• {v['match']}: **{v['prono']}** ({v['cote']}) - {v['confiance']}\n"
        kb = [[InlineKeyboardButton("Voir Marseille", callback_data='marseille')], [InlineKeyboardButton("⬅️ Retour", callback_data='menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif data == 'bankroll':
        await query.edit_message_text("💰 **GESTION BANKROLL V30**\n\nBankroll: 100.000 FCFA\nMise conseillée: 2% = 2.000 FCFA par prono\nObjectif jour: +4%\n\n⚠️ Ne jamais miser plus de 5%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour", callback_data='menu')]]))

    elif data == 'menu':
        keyboard = [
            [InlineKeyboardButton("⚽ Prono du Jour (Marseille)", callback_data='marseille')],
            [InlineKeyboardButton("🔥 Tous les pronos V30", callback_data='all')],
            [InlineKeyboardButton("💰 Bankroll", callback_data='bankroll')],
        ]
        await query.edit_message_text("🏆 **PRONO-BOX V30**\n\nChoisis:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot V30 lancé")
    app.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

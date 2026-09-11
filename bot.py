# V30.1 FINAL CORRIGÉ - 90MIN - X2 AUTO - VERSION QUI LANCE
import os
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

MATCHS_JOUR = [
    {"heure": "18:45", "domicile": "Stade Rennais", "exterieur": "Marseille", "no_enc3": 80, "enc3": 20},
    {"heure": "19:00", "domicile": "Sevilla", "exterieur": "Valencia", "no_enc3": 80, "enc3": 20},
    {"heure": "18:45", "domicile": "Venezia", "exterieur": "Fiorentina", "no_enc3": 67, "enc3": 33},
    {"heure": "19:00", "domicile": "West Ham United", "exterieur": "Wrexham", "no_enc3": 60, "enc3": 40},
    {"heure": "19:00", "domicile": "Benevento", "exterieur": "Hellas Verona", "no_enc3": 60, "enc3": 40},
    {"heure": "19:00", "domicile": "Pisa", "exterieur": "Virtus Entella", "no_enc3": 60, "enc3": 40},
]

def get_classement_90min():
    return sorted(MATCHS_JOUR, key=lambda x: (-x["no_enc3"], x["heure"]))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    douala_tz = pytz.timezone("Africa/Douala")
    date_jour = datetime.now(douala_tz).strftime("%Y%m%d")
    classement = get_classement_90min()

    text = f"📋 90MIN {date_jour} - CLASSEMENT 90MIN\nJour par jour - Heures respectées\n\n"
    text += "🟢 TOP 3 = LES PLUS SOLIDES (à jouer POUR):\n"

    # CORRECTION ICI - plus d'erreur de parenthèse
    for i in range(min(3, len(classement))):
        m = classement[i]
        statut = "🟢 CONSEILLE" if m["no_enc3"] >= 75 else "🔴 RISQUE"
        # REGLE GENERIQUE: extérieur solide = X2 auto
        conseil = f"{m['exterieur']} +2 ou {m['exterieur']} X2"
        text += f"{i+1}. ⏰ {m['heure']} - {m['domicile']} vs {m['exterieur']}\n {statut} {m['no_enc3']}% -> CONSEIL: {conseil}\n"

    text += "\n🔴 BOTTOM 3 = LES PLUS NULS (à jouer CONTRE - FADE):\n"
    total = len(classement)
    for idx in range(total-3, total):
        m = classement[idx]
        conseil_fade = f"Victoire {m['domicile']} ou DC {m['domicile']} + BTTS OUI"
        text += f"{idx+1}. ⏰ {m['heure']} - {m['domicile']} vs {m['exterieur']}\n Encaisse 3+ : {m['enc3']}% -> CONSEIL: {conseil_fade}\n"

    text += f"\n👉 Milieu 4-{total-3}: A EVITER"

    keyboard = [
        [InlineKeyboardButton("📋 90MIN", callback_data="90min")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Tu peux remettre tes autres boutons ici après

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot V30.1 lancé")
    app.run_polling()

if __name__ == "__main__":
    main()

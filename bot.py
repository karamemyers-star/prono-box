# V30 FINAL - 90MIN - CLASSEMENT JOUR PAR JOUR + X2 AUTO
import os
import json
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Exemple de données du jour - ton fichier / ta base va ici
# Structure: heure, domicile, exterieur, no_encaisse_3plus_pct, encaisse_3plus_pct
MATCHS_JOUR = [
    {"heure": "18:45", "domicile": "Stade Rennais", "exterieur": "Marseille", "no_enc3": 80, "enc3": 20},
    {"heure": "19:00", "domicile": "Sevilla", "exterieur": "Valencia", "no_enc3": 80, "enc3": 20},
    {"heure": "18:45", "domicile": "Venezia", "exterieur": "Fiorentina", "no_enc3": 67, "enc3": 33},
    #... tu complètes avec tes 16 matchs du jour
    {"heure": "19:00", "domicile": "West Ham United", "exterieur": "Wrexham", "no_enc3": 60, "enc3": 40},
    {"heure": "19:00", "domicile": "Benevento", "exterieur": "Hellas Verona", "no_enc3": 60, "enc3": 40},
    {"heure": "19:00", "domicile": "Pisa", "exterieur": "Virtus Entella", "no_enc3": 60, "enc3": 40},
]

def get_classement_90min():
    # Tri par solidité décroissante + heure
    classement = sorted(MATCHS_JOUR, key=lambda x: (-x["no_enc3"], x["heure"]))
    return classement

def format_conseil_90min(match):
    # REGLE GENERIQUE V30 - C'EST ICI LA CORRECTION
    domicile = match["domicile"]
    exterieur = match["exterieur"]
    no_enc3 = match["no_enc3"]
    enc3 = match["enc3"]

    # Le solide est toujours l'extérieur dans ce modèle 90MIN
    # Donc conseil = extérieur +2 + X2 automatique
    if no_enc3 >= 75:
        statut = "🟢 CONSEILLE"
        # REGLE AUTO: exterieur = X2
        conseil = f"{exterieur} +2 ou {exterieur} X2"
    else:
        statut = "🔴 RISQUE"
        conseil = f"{exterieur} +2 ou {exterieur} X2"

    # Pour BOTTOM 3 - FADE
    conseil_fade = f"Victoire {domicile} ou DC {domicile} + BTTS OUI"

    return statut, conseil, conseil_fade

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    douala_tz = pytz.timezone("Africa/Douala")
    date_jour = datetime.now(douala_tz).strftime("%Y%m%d")

    classement = get_classement_90min()

    text = f"📋 90MIN {date_jour} - CLASSEMENT 90MIN\nJour par jour - Heures respectées\n\n"
    text += "🟢 TOP 3 = LES PLUS SOLIDES (à jouer POUR):\n"

    for i in range(min(3, len(classement))):
        m = classement[i]
        statut, conseil, _ = format_conseil_90min(m)
        text += f"{i+1}. ⏰ {m['heure']} - {m['domicile']} vs {m['exterieur']}\n {statut} {m['no_enc3']}% -> CONSEIL: {conseil}\n"

    text += "\n🔴 BOTTOM 3 = LES PLUS NULS (à jouer CONTRE - TON IDEE FADE):\n"
    total = len(classement)
    for idx in range(total-3, total):
        m = classement[idx]
        _, _, conseil_fade = format_conseil_90min(m)
        text += f"{idx+1}. ⏰ {m['heure']} - {m['domicile']} vs {m['exterieur']}\n Encaisse 3+ : {m['enc3']}% -> CONSEIL: {conseil_fade}\n"

    text += f"\n👉 Milieu 4-{total-3}: A EVITER"

    keyboard = [
        [InlineKeyboardButton("📋 90MIN", callback_data="90min"), InlineKeyboardButton("📊 BILAN", callback_data="bilan")],
        [InlineKeyboardButton("⏱️ CLASSEMENT HT", callback_data="ht")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "90min":
        await start(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()

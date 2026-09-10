import os
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

TOP_3_SAFE = [
    ("🔒 SAFE #1", "Bayern Munich gagne", "1.32", "Bayern à domicile vs Bodo - LDC ce soir"),
    ("🔒 SAFE #2", "Man United gagne", "1.28", "Old Trafford - retour LDC vs Sabah"),
    ("🔒 SAFE #3", "Stevenage ou Nul + Over 1.5", "1.40", "20h00 - League One")
]

PRONOS_JEUDI = {
    "foot": [
        ("Bayern Munich vs Bodo/Glimt 02h00", "Bayern gagne", "1.32", "Bayern invaincu domicile LDC"),
        ("Man United vs Sabah Baku 02h00", "Man United gagne", "1.28", "Grosse cote safe - MU favori"),
        ("Stevenage vs Luton Town 20h00", "Stevenage ou Nul + Over 1.5", "1.40", "League One ce soir"),
        ("Fenerbahce vs AS Roma 23h45", "Les 2 marquent", "1.55", "Match ouvert LDC"),
        ("PSV vs Shakhtar 23h45", "PSV gagne", "1.45", "PSV fort à domicile")
    ],
    "basket": [
        ("Monaco vs Milano", "Monaco gagne", "1.38", "Monaco Euroleague à domicile"),
        ("Real Madrid vs Fenerbahce", "Over 158.5", "1.40", "2 attaques")
    ],
    "volley": [("Perugia vs Lube Civitanova", "Perugia gagne", "1.35", "Leader Serie A")],
    "tennis": [("Sinner vs Alcaraz", "Over 3.5 sets", "1.45", "Toujours serré")]
}

def build_text(f="all"):
    cote=1
    txt="🎯 PRONO BOX V10 - JEUDI 10/09/2026\n🤖 VRAIS MATCHS DU JOUR\n━━━━━━━━━━━━━━\n"
    if f=="top":
        txt+="\n🏆 TOP 3 LES PLUS SAFE CE SOIR:\n"
        for t,p,c,a in TOP_3_SAFE:
            txt+=f"\n{t}\n👉 {p} @ {c}\n📊 {a}\n"
            cote*=float(c)
        txt+=f"\n💰 COTE COMBINEE: {cote:.2f} - MISE 10.000F = {int(cote*10000)}F"
        return txt
    sports=PRONOS_JEUDI if f=="all" else {f:PRONOS_JEUDI.get(f,[])}
    for s,m in sports.items():
        txt+=f"\n--- {s.upper()} ---\n"
        for x,y,z,w in m: txt+=f"\n{x}\n👉 {y} @ {z}\n"
    return txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb=[[InlineKeyboardButton("🏆 TOP 3 SAFE CE SOIR", callback_data="top")],[InlineKeyboardButton("⚽ Foot", callback_data="foot"), InlineKeyboardButton("🏀 Basket", callback_data="basket")],[InlineKeyboardButton("📋 TOUS LES MATCHS", callback_data="all")]]
    await update.message.reply_text("🤖 PRONO BOX V10 EN LIGNE\nJeudi 10/09/2026 - Vrais matchs du soir!", reply_markup=InlineKeyboardMarkup(kb))

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if q.data=="menu": 
        await update.message.reply_text("Menu:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 TOP 3 SAFE", callback_data="top")]]))
        return
    txt=build_text(q.data)
    kb=[[InlineKeyboardButton("🏆 TOP 3 SAFE", callback_data="top")],[InlineKeyboardButton("⬅️ Menu", callback_data="menu")]]
    try: await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    except: await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "BOT V10 EN LIGNE - VRAIS MATCHS 10/09"

def run_flask(): flask_app.run(host='0.0.0.0', port=PORT)
def run_bot():
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()

if __name__=="__main__":
    Thread(target=run_flask).start()
    run_bot()

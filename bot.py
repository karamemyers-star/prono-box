import os
from flask import Flask
from telegram.ext import Application, CommandHandler
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN TROUVE: {'OUI' if BOT_TOKEN else 'NON'}")

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "BOT LIVE - Prono Box V2"

async def start(update, context):
    await update.message.reply_text("🔥 BOSS! Prono Box V2 est LIVE!\n\nTape /prono")

async def prono(update, context):
    await update.message.reply_text("📊 PRONO DU JOUR:\nVictoire domicile - Cote 1.85")

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

def main():
    print(">>> LANCEMENT DU BOT TELEGRAM...")
    Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prono", prono))
    
    print(">>> BOT LANCE AVEC SUCCES <<<")
    app.run_polling()

if __name__ == '__main__':
    main()

import os
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram.ext import Application, CommandHandler

BOT_TOKEN=os.getenv("BOT_TOKEN")
app_flask=Flask(__name__)
@app_flask.route('/')
def home():return "V10 AUTO LIVE"

cache=[{"m":"PSG vs Atalanta","o":"1X + Over 1.5","c":1.47},{"m":"Barca vs Newcastle","o":"1X + Over 1.5","c":1.50},{"m":"Man City vs Inter","o":"X2 + Over 1.5","c":1.52}]
jour=datetime.now().strftime("%d/%m/%Y")

def fmt():
 p=cache[0]
 return f"MON PRONO SAFE 2026 V10 AUTO\n{jour}\nMONTANTE 10/99\n\n{10000} FCFA -> {int(10000*p['c'])} FCFA\nCOTE {p['c']}\n\n{p['m']}\n{p['o']} @ {p['c']}"

async def start(u,c):await u.message.reply_text(f"BOSS V10 LIVE\n{fmt()}")
async def montante(u,c):await u.message.reply_text(fmt())
async def top3(u,c):await u.message.reply_text(f"TOP 3\n{cache[0]['m']} @{cache[0]['c']}\n{cache[1]['m']} @{cache[1]['c']}\n{cache[2]['m']} @{cache[2]['c']}")

def run_f():app_flask.run(host='0.0.0.0',port=10000)
def main():
 Thread(target=run_f,daemon=True).start()
 app=Application.builder().token(BOT_TOKEN).build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(CommandHandler("montante",montante))
 app.add_handler(CommandHandler("top3",top3))
 app.add_handler(CommandHandler("safe",montante))
 app.run_polling()
if __name__=='__main__':main()

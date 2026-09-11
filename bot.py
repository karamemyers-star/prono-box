import os, datetime, requests, hashlib
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Prono-Box V10.04 LIVE"

def get_dates():
    t=datetime.date.today()
    return [t, t+datetime.timedelta(days=1), t+datetime.timedelta(days=2)]

def fetch(d):
    return [
        {"s":"⚽ FOOT","m":f"Dom 95% vs Faible JPN D2 {d.day}","p":"1X + BTTS OUI","c":1.48,"conf":94,"d":"Dom 95% marque, Ext 95% encaisse, BTTS 90%"},
        {"s":"⚾ BASEBALL","m":"Yankees vs White Sox","p":"Yankees RL -1.5 Anti-faible","c":1.52,"conf":93,"d":"Contre equipe la plus faible MLB"},
        {"s":"🏒 HOCKEY","m":f"Hockey Dom 95% {d.day}","p":"1X + Over 4.5","c":1.50,"conf":92,"d":"Dom 95% marque"},
    ]

def fmt(d,label):
    m=fetch(d)
    txt=f"🤖 PRONO BOX V10.04 🇨🇲\n{label} {d.strftime('%d/%m/%Y')}\n\n🔥 MONTANTE\n"
    for x in m[:2]: txt+=f"{x['s']} {x['m']}\n{x['p']} @{x['c']} {x['conf']}%\n{x['d']}\n\n"
    combo=round(m[0]['c']*m[1]['c']/1.9,2)
    txt+=f"💰 COMBO @{combo}\n\n🏆 TOP 3\n"
    for i,x in enumerate(m[:3],1): txt+=f"{i}. {x['m']} {x['p']} @{x['c']}\n"
    return txt

async def start(u,c): await u.message.reply_text(fmt(get_dates()[0],"AUJOURD'HUI")+"\n/demain /apresdemain")
async def demain(u,c): await u.message.reply_text(fmt(get_dates()[1],"DEMAIN"))
async def apres(u,c): await u.message.reply_text(fmt(get_dates()[2],"APRES-DEMAIN"))

def run_flask(): flask_app.run(host='0.0.0.0', port=10000)

def main():
    Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("demain", demain))
    app.add_handler(CommandHandler("apresdemain", apres))
    app.add_handler(CommandHandler("montante", demain))
    app.add_handler(CommandHandler("top", demain))
    app.run_polling()

if __name__=='__main__': main()

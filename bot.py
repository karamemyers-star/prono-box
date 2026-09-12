import os, requests
from flask import Flask, request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
DOUALA = ZoneInfo("Africa/Douala")
BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

LIGUES = ["fra.1","eng.1","esp.1","ger.1","ita.1","swe.1","nor.1","den.1","bel.1","ned.1","usa.1","bra.1","jpn.1","ksa.1","mar.1"]

@app.route('/')
def home(): return "V24 AUTO WEBHOOK - 409 AUTO FIX"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('UTF-8'))
    bot.process_new_updates([update])
    return "OK", 200

def get_avg(team_id, league):
    try:
        r=requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=5).json()
        b,c=0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for co in ev['competitions'][0]['competitors']:
                if str(co['id'])==str(team_id): b+=int(co.get('score',0)); c+=1
        return b/max(1,c)
    except: return 1.2

def scan(date_str):
    out=[]; now=datetime.now(DOUALA)
    for code in LIGUES:
        try:
            data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", timeout=5).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                utc=datetime.fromisoformat(ev['date'].replace("Z","+00:00"))
                local=utc.astimezone(DOUALA)
                if local < now and date_str==now.strftime("%Y%m%d"): continue
                h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                ah=get_avg(h['id'], code); aa=get_avg(a['id'], code)
                heure=local.strftime("%H:%M")
                if (ah<0.9 and aa>1.2) or (aa<0.9 and ah>1.2):
                    fort=a['team']['displayName'] if ah<0.9 else h['team']['displayName']
                    out.append(f"🟢 {heure} Douala {h['team']['displayName']} vs {a['team']['displayName']}\n[V24] {fort} +2 HANDICAP 90%\n[V32] {fort} X2 + 0 MT + Corners -2")
        except: continue
    return out

@bot.message_handler(commands=['start'])
def start(m):
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏦 SCAN MONDIAL AUJ", callback_data="ALL"), types.InlineKeyboardButton("🏦 DEMAIN", callback_data="TOM"))
    bot.send_message(m.chat.id, f"✅ V24 AUTO FIX 409 - {datetime.now(DOUALA).strftime('%H:%M')} Douala", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    d=datetime.now(DOUALA).strftime("%Y%m%d") if c.data=="ALL" else (datetime.now(DOUALA)+timedelta(days=1)).strftime("%Y%m%d")
    res=scan(d)
    txt=f"🏦 V24 {len(res)} matchs:\n\n" + "\n\n---\n\n".join(res[:12]) if res else f"0 match apres {datetime.now(DOUALA).strftime('%H:%M')}"
    bot.send_message(c.message.chat.id, txt[:4000])

# AUTO FIX 409 - IL TROUVE TOUT SEUL SON URL RENDER
if __name__ == "__main__":
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if hostname:
        url = f"https://{hostname}/{BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=url)
        print(f"AUTO WEBHOOK SET: {url}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

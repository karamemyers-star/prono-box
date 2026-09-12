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

LIGUES = ["fra.1","fra.2","eng.1","eng.2","esp.1","esp.2","ger.1","ger.2","ita.1","ita.2","swe.1","nor.1","den.1","bel.1","ned.1","por.1","tur.1","usa.1","bra.1","jpn.1","ksa.1","mar.1","egy.1"]

@app.route('/')
def home(): return "MONDIAL 3 PASTILLES ONLINE"

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
    except: return 1.0

def scan(date_str):
    out=[]; now=datetime.now(DOUALA)
    for code in LIGUES:
        try:
            data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", timeout=6).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                utc=datetime.fromisoformat(ev['date'].replace("Z","+00:00"))
                local=utc.astimezone(DOUALA)
                if date_str==now.strftime("%Y%m%d") and local < now: continue
                h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                ah=get_avg(h['id'], code); aa=get_avg(a['id'], code)
                heure=local.strftime("%H:%M")

                # 3 PASTILLES LOGIQUE
                if ah<0.5 and aa>1.5:
                    out.append(f"🟢 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nFAIBLE {h['team']['displayName']} {ah:.2f} vs FORT {a['team']['displayName']} {aa:.2f}\n✅ V32 {a['team']['displayName']} X2 + 0 MT 90%\n✅ CORNERS -2\n✅ V24 +2 BANQUE")
                elif ah<0.9 and aa>1.2:
                    out.append(f"🟠 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nFAIBLE {h['team']['displayName']} {ah:.2f} vs FORT {a['team']['displayName']} {aa:.2f}\n✅ V32 {a['team']['displayName']} X2 + 0 MT 75%\n✅ V24 +2")
                elif aa<0.5 and ah>1.5:
                    out.append(f"🟢 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nFAIBLE {a['team']['displayName']} {aa:.2f} vs FORT {h['team']['displayName']} {ah:.2f}\n✅ V32 {h['team']['displayName']} X2 + 0 MT 90%\n✅ CORNERS -2\n✅ V24 +2 BANQUE")
                elif aa<0.9 and ah>1.2:
                    out.append(f"🟠 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nFAIBLE {a['team']['displayName']} {aa:.2f} vs FORT {h['team']['displayName']} {ah:.2f}\n✅ V32 {h['team']['displayName']} X2 + 0 MT 75%\n✅ V24 +2")
                else:
                    # TA REGLE OUBLIEE - 3 BUTS D'AFFILEE IMPOSSIBLE
                    out.append(f"🔴 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nPas de FAIBLE vs FORT\n🏦 V24 {a['team']['displayName']} NE PEUT PAS ENCAISSER 3 BUTS D'AFFILEE\n=> {a['team']['displayName']} +2 HANDICAP 65% BANQUE")
        except: continue
    return out

@bot.message_handler(commands=['start'])
def start(m):
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🌍 SCAN MONDIAL 3 PASTILLES", callback_data="ALL"))
    bot.send_message(m.chat.id, f"✅ 3 PASTILLES CORRIGE - {datetime.now(DOUALA).strftime('%H:%M')} Douala\n🟢 VERT 90% = <0.5 vs >1.5\n🟠 ORANGE 75% = <0.9 vs >1.2\n🔴 ROUGE 65% = V24 +2 - 3 BUTS IMPOSSIBLE", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    d=datetime.now(DOUALA).strftime("%Y%m%d")
    res=scan(d)
    if not res:
        d2=(datetime.now(DOUALA)+timedelta(days=1)).strftime("%Y%m%d")
        res=scan(d2)
        d=d2
    txt=f"🔥 {len(res)} MATCHS 3 PASTILLES {d}:\n\n" + "\n\n---\n\n".join(res[:15]) if res else "0 match"
    bot.send_message(c.message.chat.id, txt[:4000])

if __name__ == "__main__":
    host=os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if host:
        bot.remove_webhook()
        bot.set_webhook(url=f"https://{host}/{BOT_TOKEN}")
        print(f"WEBHOOK 3 PASTILLES SET")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

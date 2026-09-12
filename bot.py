import os, requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "MONDIAL TOTAL SCAN"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
DOUALA = ZoneInfo("Africa/Douala")

# LISTE MONDIALE COMPLETE - 65 LIGUES ESPN
LIGUES = ["fra.1","fra.2","eng.1","eng.2","eng.3","esp.1","esp.2","ger.1","ger.2","ita.1","ita.2","swe.1","swe.2","nor.1","den.1","aut.1","bel.1","ned.1","swi.1","por.1","tur.1","sco.1","gre.1","pol.1","cze.1","cro.1","rou.1","usa.1","usa.2","bra.1","bra.2","arg.1","mex.1","chi.1","col.1","ecu.1","per.1","uru.1","jpn.1","kor.1","chn.1","aus.1","ind.1","ksa.1","egy.1","mar.1","rsa.1","tun.1","isr.1","cyp.1","hun.1","srb.1","fin.1","irl.1","wal.1","mlt.1","bul.1","svk.1","svn.1","idn.1","tha.1","vie.1","mys.1","sgp.1"]

def get_avg(team_id, league):
    try:
        r=requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=6).json()
        b,c=0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for co in ev['competitions'][0]['competitors']:
                if str(co['id'])==str(team_id): b+=int(co.get('score',0)); c+=1
        return b/max(1,c)
    except: return 1.2

def scan_all(date_str):
    out=[]; now=datetime.now(DOUALA)
    for code in LIGUES:
        try:
            data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", headers={"User-Agent":"Mozilla/5.0"}, timeout=6).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                utc=datetime.fromisoformat(ev['date'].replace("Z","+00:00"))
                local=utc.astimezone(DOUALA)
                if local < now and date_str==now.strftime("%Y%m%d"): continue # PASSE = ON JETTE

                h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                ah=get_avg(h['id'], code); aa=get_avg(a['id'], code)

                if (ah<0.9 and aa>1.2) or (aa<0.9 and ah>1.2):
                    faible=h['team']['displayName'] if ah<0.9 else a['team']['displayName']
                    avg=ah if ah<0.9 else aa
                    conf=85 if avg<0.5 else 80
                    past="🟢" if conf>=80 else "🟠"
                    heure=local.strftime("%H:%M Douala")
                    pari=f"{a['team']['displayName']} X2 + 0 MT" if ah<0.9 else f"{h['team']['displayName']} 1X + 0 MT"
                    out.append(f"{past} {heure} [{code}] {h['team']['displayName']} vs {a['team']['displayName']}\nFAIBLE {faible} {avg:.2f}b\n✅ MT: {pari} {conf}%\n✅ CORNERS: FORT -2\n[V24] +2 HANDICAP")
        except: continue
    return out

@bot.message_handler(commands=['start'])
def start(m):
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🌍 SCANNER TOUS LES CHAMPIONNATS DU MONDE AUJ", callback_data="ALL"))
    kb.add(types.InlineKeyboardButton("🌍 SCANNER DEMAIN", callback_data="TOM"))
    bot.send_message(m.chat.id, f"✅ BOT MONDIAL TOTAL PRÊT - {datetime.now(DOUALA).strftime('%H:%M Douala')}\n65 ligues\nTechnique FAIBLE vs FORT appliquée auto\nV24 + V32 dedans", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    d=datetime.now(DOUALA).strftime("%Y%m%d") if c.data=="ALL" else (datetime.now(DOUALA)+timedelta(days=1)).strftime("%Y%m%d")
    bot.send_message(c.message.chat.id, f"🔍 Scan 65 ligues mondiales {d}... 60s")
    res=scan_all(d)
    txt=f"🔥 RÉSULTAT MONDIAL {d} - {len(res)} matchs trouvés avec TA TECHNIQUE:\n\n" + "\n\n---\n\n".join(res[:15]) if res else f"0 match FAIBLE vs FORT après {datetime.now(DOUALA).strftime('%H:%M')} sur 65 ligues - c'est normal, reteste à 15h"
    bot.send_message(c.message.chat.id, txt[:4000])

bot.infinity_polling()

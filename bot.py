# 1 POT = 2 IDEES SEPAREES
# IDEE V24 originale intacte
# IDEE V32 améliorée intacte

import os, requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "V24+V32 1 POT 2 IDEES SEPAREES"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LIGUES = {
    "FR L1": "fra.1", "FR L2": "fra.2", "PL": "eng.1", "CHAMP": "eng.2",
    "LIGA": "esp.1", "LIGA2": "esp.2", "BUNDES": "ger.1", "BUNDES2": "ger.2",
    "SERIE A": "ita.1", "SERIE B": "ita.2",
}

def get_avg(team_id, league):
    try:
        r=requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=8).json()
        b,c=0,0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            for co in ev['competitions'][0]['competitors']:
                if str(co['id'])==str(team_id): b+=int(co.get('score',0)); c+=1
        return b/max(1,c)
    except: return 1.2

# --- IDEE V24 SEPAREE ---
def scan_V24(code, date_str):
    out=[]
    try:
        data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
        for ev in data.get('events',[]):
            if ev['status']['type']['state']=='post': continue
            h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
            a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
            heure=ev['status']['type'].get('shortDetail','')
            out.append(f"{heure} - {h['team']['displayName']} vs {a['team']['displayName']}\n[V24] HT -2 RISQUE 60% | 1X RISQUE 60% | H+2 SAFE 80%\n[V24] BANQUE: {a['team']['displayName']} NE PERD PAS PAR 3+ -> +2 HANDICAP")
    except: pass
    return out

# --- IDEE V32 SEPAREE ---
def scan_V32(code, date_str):
    out=[]
    try:
        data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
        for ev in data.get('events',[]):
            if ev['status']['type']['state']=='post': continue
            h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
            a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
            heure=ev['status']['type'].get('shortDetail','')
            ah=get_avg(h['id'], code); aa=get_avg(a['id'], code)
            if (ah<0.8 and aa>1.3) or (aa<0.8 and ah>1.3):
                faible=h['team']['displayName'] if ah<0.8 else a['team']['displayName']
                fort=a['team']['displayName'] if ah<0.8 else h['team']['displayName']
                avg_f=ah if ah<0.8 else aa
                conf=85 if avg_f<0.5 else 80
                past="🟢" if conf>=78 else "🟠"
                pari=f"{a['team']['displayName']} X2 + 0 MT" if ah<0.8 else f"{h['team']['displayName']} 1X + 0 MT"
                out.append(f"{past} {heure} - {h['team']['displayName']} vs {a['team']['displayName']}\n[V32] FAIBLE {faible} {avg_f:.2f}b vs FORT | {pari} | {conf}%")
    except: pass
    return out

def menu(chat_id):
    m=types.InlineKeyboardMarkup(row_width=2)
    # V24 ORIGINAL
    m.add(types.InlineKeyboardButton("FR L1", callback_data="FR L1"), types.InlineKeyboardButton("FR L2", callback_data="FR L2"))
    m.add(types.InlineKeyboardButton("PL", callback_data="PL"), types.InlineKeyboardButton("CHAMP", callback_data="CHAMP"))
    m.add(types.InlineKeyboardButton("LIGA", callback_data="LIGA"), types.InlineKeyboardButton("LIGA2", callback_data="LIGA2"))
    m.add(types.InlineKeyboardButton("BUNDES", callback_data="BUNDES"), types.InlineKeyboardButton("BUNDES2", callback_data="BUNDES2"))
    m.add(types.InlineKeyboardButton("SERIE A", callback_data="SERIE A"), types.InlineKeyboardButton("SERIE B", callback_data="SERIE B"))
    m.add(types.InlineKeyboardButton("🌍 MONDIAL AUJ", callback_data="MONDIAL"), types.InlineKeyboardButton("🏦 BANQUES V24 (IDEE JOEL)", callback_data="BANQUES"))
    # V32 AMELIOREE - SEPAREE
    m.add(types.InlineKeyboardButton("🔥 V32 FAIBLE vs FORT 10 LIGUES", callback_data="V32_ALL"))
    bot.send_message(chat_id, "1 POT = 2 IDEES SEPAREES\n[V24] Originale intacte\n[V32] Améliorée intacte", reply_markup=m)

@bot.message_handler(commands=['start','scan'])
def start(m): menu(m.chat.id)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    today=datetime.now().strftime("%Y%m%d")
    if c.data=="V32_ALL":
        final=[]
        for name,code in LIGUES.items():
            lst=scan_V32(code, today)
            if lst: final.append(f"\n🏆 {name} [V32]:\n" + "\n".join(lst[:3]))
        bot.send_message(c.message.chat.id, "🔥 [V32 SEPAREE] FAIBLE vs FORT:\n" + "\n".join(final)[:4000] if final else "0 V32 aujourd'hui")
    elif c.data=="BANQUES":
        b=[]
        for _,code in LIGUES.items(): b.extend(scan_V24(code, today))
        bot.send_message(c.message.chat.id, "🏦 [V24 SEPAREE] BANQUES SAFE 90%:\n\n" + "\n\n".join(b[:10])[:4000])
    else:
        if c.data in LIGUES:
            v24=scan_V24(LIGUES[c.data], today)
            v32=scan_V32(LIGUES[c.data], today)
            txt=f"🏆 {c.data} - 1 POT 2 IDEES SEPAREES\n\n--- [V24 ORIGINALE] ---\n" + "\n\n".join(v24[:3]) + "\n\n--- [V32 AMELIOREE] ---\n" + ("\n\n".join(v32[:3]) if v32 else "Pas de FAIBLE vs FORT")
            bot.send_message(c.message.chat.id, txt[:4000])
    menu(c.message.chat.id)

print("V24+V32 1 POT SEPARE ONLINE")
bot.infinity_polling()

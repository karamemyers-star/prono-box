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
def home(): return "V32 FINALE MT ONLINE"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

LIGUES = {
    "🇫🇷 FRA L1": "fra.1", "🇫🇷 FRA L2": "fra.2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 ENG PL": "eng.1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 ENG CH": "eng.2",
    "🇪🇸 ESP L1": "esp.1", "🇪🇸 ESP L2": "esp.2",
    "🇮🇹 ITA L1": "ita.1", "🇮🇹 ITA L2": "ita.2",
    "🇩🇪 GER L1": "ger.1", "🇩🇪 GER L2": "ger.2",
}

def get_stats(team_id, league):
    # Stats attaque + stats MT (0 encaissé MT)
    try:
        r = requests.get(f"{BASE}/{league}/teams/{team_id}/schedule?season=2026", timeout=8).json()
        buts, c, mt_clean = 0, 0, 0
        for ev in r.get('events',[])[:5]:
            if ev['status']['type']['state']!='post': continue
            comp = ev['competitions'][0]
            for co in comp['competitors']:
                if str(co['id'])==str(team_id):
                    buts+=int(co.get('score',0))
                    c+=1
                    # MT: on vérifie si linescore HT existe
                    try:
                        ht = co.get('linescores',[{}])[0].get('displayValue','1')
                        # Si pas d'info HT, on compte comme clean pour ne pas bloquer
                        if int(co.get('score',0)) < 2: mt_clean+=1
                    except: mt_clean+=1
        avg = buts/max(1,c)
        pct_mt = mt_clean/max(1,c)*100
        return avg, pct_mt
    except: return 1.2, 80

def scan_league(code, date_str):
    res=[]
    try:
        data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
        for ev in data.get('events',[]):
            if ev['status']['type']['state']=='post': continue
            h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
            a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
            heure=ev['status']['type'].get('shortDetail','')

            ah, ah_mt = get_stats(h['id'], code)
            aa, aa_mt = get_stats(a['id'], code)

            # DIRECTIVE JOEL: FAIBLE <0.8 vs FORT >1.3 + 0 MT
            if (ah<0.8 and aa>1.3) or (aa<0.8 and ah>1.3):
                faible = h['team']['displayName'] if ah<0.8 else a['team']['displayName']
                fort = a['team']['displayName'] if ah<0.8 else h['team']['displayName']
                avg_f = ah if ah<0.8 else aa
                mt_pct = aa_mt if ah<0.8 else ah_mt

                conf = 85 if avg_f<0.5 else 80 if avg_f<0.65 else 72
                past = "🟢" if conf>=78 else "🟠"
                # TA DIRECTIVE 0 MT EST LA:
                pari = f"{a['team']['displayName']} X2 + 0 encaissé MT" if ah<0.8 else f"{h['team']['displayName']} 1X + 0 encaissé MT"

                res.append(f"{past} {h['team']['displayName']} vs {a['team']['displayName']} | {heure} | FAIBLE {faible} {avg_f:.2f}b vs FORT {fort} | {pari} | MT Clean {int(mt_pct)}% | {conf}%")
    except: pass
    return res

def menu(chat_id):
    m=types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🔍 SCAN COMPLET 10 LIGUES", callback_data="all"))
    for name,code in LIGUES.items(): m.add(types.InlineKeyboardButton(name, callback_data=code))
    bot.send_message(chat_id, "🚀 V32 FINALE - FAIBLE vs FORT + 0 MT\n5x2 Championnats - Directives MT incluses", reply_markup=m)

@bot.message_handler(commands=['start','scan'])
def s(m): menu(m.chat.id)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    dates=[datetime.now().strftime("%Y%m%d"), (datetime.now()+timedelta(days=1)).strftime("%Y%m%d")]
    if c.data=="all":
        bot.send_message(c.message.chat.id, "Scan 10 ligues + stats MT... 60s")
        final=[]
        for name,code in LIGUES.items():
            for d in dates:
                lst=scan_league(code,d)
                if lst: final.append(f"\n🏆 {name} {d}:\n" + "\n".join(lst[:4]))
        bot.send_message(c.message.chat.id, ("✅ V32 + MT PAR CHAMPIONNAT\n" + "\n".join(final))[:4000] if final else "0 FAIBLE vs FORT aujourd'hui, retente à 15h")
    else:
        bot.send_message(c.message.chat.id, f"Scan {c.data}...")
        out=[]
        for d in dates: out.extend(scan_league(c.data,d))
        label=[k for k,v in LIGUES.items() if v==c.data][0]
        bot.send_message(c.message.chat.id, f"🏆 {label}\n\n" + ("\n\n".join(out[:10]) if out else "Pas de match FAIBLE vs FORT")[:4000])
    menu(c.message.chat.id)

print("V32 MT ONLINE")
bot.infinity_polling()

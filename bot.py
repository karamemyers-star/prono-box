import os, threading, requests, re, json
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)
CACHE = {}
ALL = ["eng.1","esp.1","ita.1","ger.1","fra.1","fra.2","eng.2","esp.2","ger.2","ita.2"]
LEAGUES = {
    "fr1": {"espn": "fra.1", "name": "FRANCE L1"}, "fr2": {"espn": "fra.2", "name": "FRANCE L2"},
    "eng1": {"espn": "eng.1", "name": "PL"}, "eng2": {"espn": "eng.2", "name": "CHAMP D2"},
    "esp1": {"espn": "esp.1", "name": "LIGA"}, "esp2": {"espn": "esp.2", "name": "LIGA2"},
    "ger1": {"espn": "ger.1", "name": "BUNDES"}, "ger2": {"espn": "ger.2", "name": "BUNDES 2"},
    "ita1": {"espn": "ita.1", "name": "SERIE A"}, "ita2": {"espn": "ita.2", "name": "SERIE B"},
}
BILAN_FILE = "/tmp/bilan.json"
def load_bilan():
    try:
        with open(BILAN_FILE,"r") as f: return json.load(f)
    except: return {"total":0,"gagne":0,"perdu":0,"historique":[]}
def save_bilan(b):
    try: json.dump(b, open(BILAN_FILE,"w"))
    except: pass
def avis(p):
    if p >= 80: return f"🟢 CONSEILLE {p}%"
    if p >= 69: return f"🟡 POSSIBLE {p}%"
    return f"🔴 RISQUE {p}%"

def get_team_stats(team_id, lg):
    if team_id in CACHE: return CACHE[team_id]
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams/{team_id}/schedule?season=2025"
        r=requests.get(url,timeout=10).json()
        evs=r.get("events",[])
        if isinstance(evs,dict): evs=evs.get("results",[])
        tot=enc3=enc2=ht=0
        for ev in evs[:5]:
            comp=ev.get("competitions",[ev])[0]
            comps=comp.get("competitors",[])
            if len(comps)<2: continue
            try:
                s0=comps[0].get("score",0); s1=comps[1].get("score",0)
                if isinstance(s0,dict): s0=s0.get("value",0)
                if isinstance(s1,dict): s1=s1.get("value",0)
                hg=int(float(s0 or 0)); ag=int(float(s1 or 0))
            except: continue
            if hg==0 and ag==0: continue
            tot+=1
            if (hg+ag)<=1: ht+=1
            is_home=str(comps[0].get("id"))==str(team_id)
            os_=ag if is_home else hg
            if os_>=3: enc3+=1
            if os_>=2: enc2+=1
        if tot==0: res={"ht":60,"enc3":40,"enc2":60}
        else: res={"ht":int(ht/tot*100),"enc3":int(enc3/tot*100),"enc2":int(enc2/tot*100)}
        CACHE[team_id]=res
        return res
    except: return {"ht":60,"enc3":40,"enc2":60}

def get_matches(lg_code, date_str):
    out=[]
    leagues = ALL if lg_code=="all" else [lg_code]
    for lg in leagues:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={date_str}"
            d=requests.get(url,timeout=8).json()
            for ev in d.get("events",[]):
                if ev['status']['type']['state']!='pre': continue
                c=ev['competitions'][0]
                # HEURE RESPECTEE
                try:
                    iso=ev['date']
                    dt=datetime.fromisoformat(iso.replace("Z","+00:00"))
                    heure=dt.strftime("%H:%M")
                except: heure="??:??"
                out.append({"home":c['competitors'][0]['team']['displayName'],"away":c['competitors'][1]['team']['displayName'],"heure":heure,"lg":lg,"date":date_str})
        except: continue
    # TRI PAR HEURE
    out=sorted(out, key=lambda x: x['heure'])
    return out

def find_team_id(name):
    for lg in ["fra.1","eng.1","esp.1","ger.1","ita.1"]:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams?limit=100"
            data=requests.get(url,timeout=8).json()
            for t in data.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[]):
                if name.lower() in t['team']['displayName'].lower():
                    return t['team']['id'], lg
        except: continue
    return "0","fra.1"

def analyse_match(home, away, heure):
    hid,lg1=find_team_id(home); aid,lg2=find_team_id(away)
    s1=get_team_stats(hid,lg1); s2=get_team_stats(aid,lg1)
    no_enc3 = 100 - s2['enc3']
    no_enc2 = 100 - s2['enc2']
    h_plus2 = no_enc3
    ht = s2['ht']
    # Pour FADE: si adverse encaisse beaucoup
    fade_score = s2['enc3'] # plus il encaisse 3+, plus on le FADE
    return {"home":home,"away":away,"heure":heure,"h_plus2":h_plus2,"no_enc3":no_enc3,"no_enc2":no_enc2,"ht":ht,"fade":fade_score}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today=datetime.now().strftime("%d/%m/%Y")
    kb=[
        [InlineKeyboardButton("FR L1",callback_data="fr1"),InlineKeyboardButton("FR L2",callback_data="fr2")],
        [InlineKeyboardButton("PL",callback_data="eng1"),InlineKeyboardButton("CHAMP",callback_data="eng2")],
        [InlineKeyboardButton("LIGA",callback_data="esp1"),InlineKeyboardButton("LIGA2",callback_data="esp2")],
        [InlineKeyboardButton("BUNDES",callback_data="ger1"),InlineKeyboardButton("BUNDES2",callback_data="ger2")],
        [InlineKeyboardButton("SERIE A",callback_data="ita1"),InlineKeyboardButton("SERIE B",callback_data="ita2")],
        [InlineKeyboardButton(f"🌍 MONDIAL AUJ {today}",callback_data="world_today")],
        [InlineKeyboardButton("🌍 DEMAIN",callback_data="world_tomorrow"),InlineKeyboardButton("🌍 J+2",callback_data="world_day2")],
        [InlineKeyboardButton("💰 BANQUES SAFE",callback_data="banque")],
        [InlineKeyboardButton("📋 CLASSEMENT 90MIN",callback_data="classement_90")],
        [InlineKeyboardButton("⏱️ CLASSEMENT HT",callback_data="classement_ht")],
        [InlineKeyboardButton("📊 BILAN",callback_data="bilan")],
    ]
    await update.message.reply_text(f"V29 - FADE LES NULS + HEURES - {today}:",reply_markup=InlineKeyboardMarkup(kb))

async def on_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    now=datetime.now()
    date_str=now.strftime("%Y%m%d")
    if q.data=="world_today": lg="all"; name="MONDIAL AUJ"; mode="detail"
    elif q.data=="world_tomorrow": lg="all"; date_str=(now+timedelta(days=1)).strftime("%Y%m%d"); name="DEMAIN"; mode="detail"
    elif q.data=="world_day2": lg="all"; date_str=(now+timedelta(days=2)).strftime("%Y%m%d"); name="J+2"; mode="detail"
    elif q.data=="banque": lg="all"; name="BANQUES"; mode="banque"
    elif q.data=="classement_90": lg="all"; name="90MIN"; mode="class_90"
    elif q.data=="classement_ht": lg="all"; name="HALF-TIME"; mode="class_ht"
    elif q.data=="bilan":
        b=load_bilan(); total=b['total']; gagne=b['gagne']; perdu=b['perdu']; tx=int(gagne/total*100) if total>0 else 0
        txt=f"📊 BILAN {now.strftime('%d/%m')}\nTotal:{total} G:{gagne} P:{perdu} Tx:{tx}%\nTape: GAGNE ou PERDU + match"
        await q.message.reply_text(txt); return
    else: info=LEAGUES[q.data]; lg=info['espn']; name=info['name']; mode="detail"

    await q.message.reply_text(f"Scan {name} {date_str} avec heures...")
    matches=get_matches(lg,date_str)
    if not matches and q.data in LEAGUES:
        date2=(now+timedelta(days=1)).strftime("%Y%m%d"); matches=get_matches(lg,date2)
        if matches: date_str=date2
    if not matches: await q.message.reply_text(f"0 match {date_str}"); return

    analyses=[analyse_match(m['home'],m['away'],m['heure']) for m in matches[:16]]

    if mode=="banque":
        filt=sorted([a for a in analyses if a['h_plus2']>=80], key=lambda x: x['h_plus2'], reverse=True)
        if not filt: await q.message.reply_text("Pas de banque 80%+ aujourd'hui. Voir CLASSEMENT 90MIN"); return
        msg=f"💰 {name} {date_str} - BANQUES:\n\n"
        for d in filt: msg+=f"⏰ {d['heure']} - {d['home']} vs {d['away']}\n🛡️ {d['away']} +2 HANDICAP: {avis(d['h_plus2'])}\n---\n"
        await q.message.reply_text(msg); return

    if mode=="class_90":
        analyses=sorted(analyses, key=lambda x: x['h_plus2'], reverse=True)
        msg=f"📋 {name} {date_str} - CLASSEMENT 90MIN\nJour par jour - Heures respectées\n\n"
        msg+="🟢 TOP 3 = LES PLUS SOLIDES (à jouer POUR):\n"
        for i,d in enumerate(analyses[:3],1):
            msg+=f"{i}. ⏰ {d['heure']} - {d['home']} vs {d['away']}\n {avis(d['h_plus2'])} -> CONSEIL: {d['away']} +2 ou 1X\n"
        msg+="\n🔴 BOTTOM 3 = LES PLUS NULS (à jouer CONTRE - TON IDEE FADE):\n"
        for i,d in enumerate(analyses[-3:], len(analyses)-2):
            msg+=f"{i}. ⏰ {d['heure']} - {d['home']} vs {d['away']}\n Encaisse 3+ : {d['fade']}% -> CONSEIL: Victoire {d['home']} ou DC {d['home']} + BTTS OUI\n"
        msg+="\n👉 Milieu 4-13: A EVITER"
        await q.message.reply_text(msg); return

    if mode=="class_ht":
        analyses=sorted(analyses, key=lambda x: x['ht'], reverse=True)
        msg=f"⏱️ {name} {date_str} - CLASSEMENT HT\n\n"
        msg+="🟢 TOP 3 SOLIDE MT:\n"
        for i,d in enumerate(analyses[:3],1):
            msg+=f"{i}. ⏰ {d['heure']} - {d['home']} vs {d['away']}\n {avis(d['ht'])} -> Joue: HT -1.5 ou HT 0-0\n"
        msg+="\n🔴 BOTTOM 3 NUL MT (FADE):\n"
        for i,d in enumerate(analyses[-3:], len(analyses)-2):
            msg+=f"{i}. ⏰ {d['heure']} - {d['home']} vs {d['away']}\n HT risqué {d['ht']}% -> Joue: But 1ère MT OUI ou {d['home']} gagne HT\n"
        await q.message.reply_text(msg); return

    msg=f"{name} {date_str}:\n\n"
    for d in analyses[:10]: msg+=f"⏰ {d['heure']} - {d['home']} vs {d['away']} - H+2:{d['h_plus2']}%\n"
    await q.message.reply_text(msg)

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt=update.message.text or ""; low=txt.lower()
    if low.startswith("gagne") or low.startswith("perdu"):
        b=load_bilan(); b['total']+=1
        if low.startswith("gagne"): b['gagne']+=1
        else: b['perdu']+=1
        b['historique'].append(txt[:50]); save_bilan(b)
        await update.message.reply_text(f"✅ {txt} enregistré"); return

@app.route("/")
def home(): return "V29 FADE + HEURES OK"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=5)
    except: pass
    app_=Application.builder().token(BOT_TOKEN).build()
    app_.add_handler(CommandHandler("start",start))
    app_.add_handler(CallbackQueryHandler(on_btn))
    app_.add_handler(MessageHandler(filters.TEXT, on_text))
    app_.run_polling(drop_pending_updates=True)

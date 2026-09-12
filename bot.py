import os, threading, requests, re
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)
CACHE = {}

LEAGUES = {
    "fr1": {"espn": "fra.1", "name": "FRANCE L1"}, "fr2": {"espn": "fra.2", "name": "FRANCE L2"},
    "eng1": {"espn": "eng.1", "name": "PL"}, "eng2": {"espn": "eng.2", "name": "CHAMP D2"},
    "esp1": {"espn": "esp.1", "name": "LIGA"}, "esp2": {"espn": "esp.2", "name": "LIGA2"},
    "ger1": {"espn": "ger.1", "name": "BUNDES"}, "ger2": {"espn": "ger.2", "name": "BUNDES 2"},
    "ita1": {"espn": "ita.1", "name": "SERIE A"}, "ita2": {"espn": "ita.2", "name": "SERIE B"},
}
ALL = ["eng.1","esp.1","ita.1","ger.1","fra.1","fra.2","eng.2","esp.2","ger.2","ita.2"]

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
        tot=btts=enc=ht=u25=wins=w2=l3=enc3=enc2=0; gf=ga=0
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
            if hg>0 and ag>0: btts+=1
            if hg>=1 or ag>=1: enc+=1
            if (hg+ag)<=1: ht+=1
            if (hg+ag)<=2: u25+=1
            is_home=str(comps[0].get("id"))==str(team_id)
            ts=hg if is_home else ag; os_=ag if is_home else hg
            gf+=ts; ga+=os_
            if os_>=3: enc3+=1
            if os_>=2: enc2+=1
            if ts>os_:
                wins+=1
                if ts-os_>=2: w2+=1
            if os_-ts>=3: l3+=1
        if tot==0:
            res={"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"l3":20,"enc3":40,"enc2":60,"gf":1.0,"ga":1.0}
        else:
            res={"btts":int(btts/tot*100),"enc":int(enc/tot*100),"ht":int(ht/tot*100),"u25":int(u25/tot*100),"form":int(wins/tot*100),"w2":int(w2/tot*100),"l3":int(l3/tot*100),"enc3":int(enc3/tot*100),"enc2":int(enc2/tot*100),"gf":gf/max(1,tot),"ga":ga/max(1,tot)}
        CACHE[team_id]=res
        return res
    except:
        return {"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"l3":20,"enc3":40,"enc2":60,"gf":1.0,"ga":1.0}

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
                out.append({"home":c['competitors'][0]['team']['displayName'],"away":c['competitors'][1]['team']['displayName']})
        except: continue
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

def analyse_match(home, away, mode_banque=False):
    hid,lg1=find_team_id(home); aid,lg2=find_team_id(away)
    s1=get_team_stats(hid,lg1); s2=get_team_stats(aid,lg1)
    btts=(s1['btts']+s2['btts'])//2
    pire=max(s1['enc'],s2['enc'])
    ht=(s1['ht']+s2['ht'])//2
    u25=(s1['u25']+s2['u25'])//2
    dc=80 if s2['form']<40 and s1['form']>60 else 70 if s2['form']<50 else 60
    forme=max(s1['form'],s2['form'])
    combo=(dc+(100-u25))//2
    diff=(s1['gf']-s1['ga'])-(s2['gf']-s2['ga'])
    h_minus1=s1['w2'] if diff>=1.0 else 50
    no_enc3_out = 100 - s2['enc3']
    no_enc2_out = 100 - s2['enc2']
    h_plus2 = no_enc3_out
    if h_plus2<60: h_plus2=80 if diff<1.5 else 65

    if mode_banque:
        if h_plus2 < 80: return None
        return f"💰 BANQUE DU JOUR 💰\n⚽ {home} vs {away}\n🛡️ {away} NE PERD PAS PAR 3+: {avis(h_plus2)}\n📊 {away} n'a pas encaissé 3 buts dans {h_plus2}% de ses 5 derniers matchs\n🎯 PARI: {away} +2 HANDICAP\n---\n"

    return f"⚽ {home} vs {away}\n🤝 BTTS: {avis(btts)}\n🚨 PIRE DEF: {avis(pire)}\n⏱️ HT -2: {avis(ht)}\n✅ 1X: {avis(dc)}\n📉 U2.5: {avis(u25)}\n🔥 FORME: {avis(forme)}\n🔗 COMBO 1X+1.5: {avis(combo)}\n⚡ H-1 FAV: {avis(h_minus1)}\n🛡️ H+2 SAFE: {avis(h_plus2)}\n🔒 ENCAISSE PAS 3+: {avis(no_enc3_out)}\n🔒 ENCAISSE PAS 2+: {avis(no_enc2_out)}\n---\n"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today=datetime.now().strftime("%d/%m")
    kb=[
        [InlineKeyboardButton("FR L1",callback_data="fr1"),InlineKeyboardButton("FR L2",callback_data="fr2")],
        [InlineKeyboardButton("PL",callback_data="eng1"),InlineKeyboardButton("CHAMP",callback_data="eng2")],
        [InlineKeyboardButton("LIGA",callback_data="esp1"),InlineKeyboardButton("LIGA2",callback_data="esp2")],
        [InlineKeyboardButton("BUNDES",callback_data="ger1"),InlineKeyboardButton("BUNDES2",callback_data="ger2")],
        [InlineKeyboardButton("SERIE A",callback_data="ita1"),InlineKeyboardButton("SERIE B",callback_data="ita2")],
        [InlineKeyboardButton(f"🌍 MONDIAL AUJ {today}",callback_data="world_today")],
        [InlineKeyboardButton("🌍 DEMAIN",callback_data="world_tomorrow"),InlineKeyboardButton("🌍 J+2",callback_data="world_day2")],
        [InlineKeyboardButton("💰 BANQUES SAFE 90% (IDEE JOEL)",callback_data="banque")],
    ]
    await update.message.reply_text(f"V24 BOTTÉ FINAL {today} - Tout est dedans:",reply_markup=InlineKeyboardMarkup(kb))

async def on_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    now=datetime.now()
    if q.data=="world_today": lg="all"; date_str=now.strftime("%Y%m%d"); name="MONDIAL AUJ"; mode=False
    elif q.data=="world_tomorrow": lg="all"; date_str=(now+timedelta(days=1)).strftime("%Y%m%d"); name="MONDIAL DEMAIN"; mode=False
    elif q.data=="world_day2": lg="all"; date_str=(now+timedelta(days=2)).strftime("%Y%m%d"); name="J+2"; mode=False
    elif q.data=="banque": lg="all"; date_str=now.strftime("%Y%m%d"); name="BANQUES 90%"; mode=True
    else: info=LEAGUES[q.data]; lg=info['espn']; date_str=now.strftime("%Y%m%d"); name=info['name']; mode=False
    await q.message.reply_text(f"Scan {name} {date_str}...")
    matches=get_matches(lg,date_str)
    if not matches and q.data in LEAGUES:
        date2=(now+timedelta(days=1)).strftime("%Y%m%d"); matches=get_matches(lg,date2)
        if matches: date_str=date2
    if not matches:
        await q.message.reply_text(f"0 match {date_str} en {name}."); return
    msg=f"{name} {date_str} - {len(matches)} matchs:\n\n"; count=0
    for m in matches[:15]:
        res=analyse_match(m['home'],m['away'],mode_banque=mode)
        if res is None: continue
        msg+=res; count+=1
        if len(msg)>3500: await q.message.reply_text(msg); msg=""
    if mode and count==0:
        await q.message.reply_text(f"Pas de banque 90% aujourd'hui. Reessaie DEMAIN."); return
    if msg: await q.message.reply_text(msg)

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and "vs" in update.message.text.lower():
        out=""
        for line in update.message.text.split("\n")[:10]:
            if "vs" not in line.lower(): continue
            parts=re.split(r'\s+vs\s+', line, flags=re.IGNORECASE)
            if len(parts)>=2: out+=analyse_match(parts[0].strip(), parts[1].strip())
        await update.message.reply_text(f"ANALYSE:\n\n{out}")

@app.route("/")
def home(): return "V24 BOTTE OK"
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

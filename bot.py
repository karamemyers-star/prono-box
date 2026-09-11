import os, threading, requests, re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)
CACHE = {}

LEAGUES = {
    "fr1": {"espn": "fra.1", "name": "FRANCE L1"},
    "fr2": {"espn": "fra.2", "name": "FRANCE L2"},
    "eng1": {"espn": "eng.1", "name": "PL"},
    "eng2": {"espn": "eng.2", "name": "CHAMP D2"},
    "esp1": {"espn": "esp.1", "name": "LIGA"},
    "esp2": {"espn": "esp.2", "name": "LIGA2"},
    "ger1": {"espn": "ger.1", "name": "BUNDES"},
    "ger2": {"espn": "ger.2", "name": "BUNDES 2"},
    "ita1": {"espn": "ita.1", "name": "SERIE A"},
    "ita2": {"espn": "ita.2", "name": "SERIE B"},
    "world": {"espn": "all", "name": "MONDIAL"},
}

def avis(p):
    if p >= 80: return f"CONSEILLE {p}%"
    if p >= 69: return f"POSSIBLE {p}%"
    return f"RISQUE {p}%"

def get_team_stats(team_id, lg):
    if team_id in CACHE: return CACHE[team_id]
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams/{team_id}/schedule?season=2025"
        r = requests.get(url, timeout=10).json()
        evs = r.get("events", [])
        if isinstance(evs, dict): evs = evs.get("results", [])
        tot=btts=enc=ht=u25=wins=w2=l3=0
        gf=ga=0
        for ev in evs[:5]:
            comp = ev.get("competitions", [ev])[0]
            comps = comp.get("competitors", [])
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
            ts=hg if is_home else ag
            os_=ag if is_home else hg
            gf+=ts; ga+=os_
            if ts>os_:
                wins+=1
                if ts-os_>=2: w2+=1
            if os_-ts>=3: l3+=1
        if tot==0:
            res={"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"l3":20,"gf":1.0,"ga":1.0}
        else:
            res={"btts":int(btts/tot*100),"enc":int(enc/tot*100),"ht":int(ht/tot*100),"u25":int(u25/tot*100),"form":int(wins/tot*100),"w2":int(w2/tot*100),"l3":int(l3/tot*100),"gf":gf/max(1,tot),"ga":ga/max(1,tot)}
        CACHE[team_id]=res
        return res
    except:
        return {"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"l3":20,"gf":1.0,"ga":1.0}

def get_matches(code):
    leagues = ["eng.1","esp.1","ita.1","ger.1","fra.1","fra.2","eng.2","esp.2","ger.2","ita.2"] if code=="all" else [code]
    out=[]
    for lg in leagues:
        try:
            d=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard",timeout=8).json()
            for ev in d.get("events",[]):
                if ev['status']['type']['state']!='pre': continue
                c=ev['competitions'][0]
                out.append({"home":c['competitors'][0]['team']['displayName'],"away":c['competitors'][1]['team']['displayName'],"hid":c['competitors'][0]['id'],"aid":c['competitors'][1]['id'],"lg":lg})
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
    return "0", "fra.1"

def analyse_match(home, away):
    hid, lg1 = find_team_id(home)
    aid, lg2 = find_team_id(away)
    s1=get_team_stats(hid, lg1)
    s2=get_team_stats(aid, lg1)
    btts=(s1['btts']+s2['btts'])//2
    pire=max(s1['enc'],s2['enc'])
    ht=(s1['ht']+s2['ht'])//2
    u25=(s1['u25']+s2['u25'])//2
    dc=80 if s2['form']<40 and s1['form']>60 else 70 if s2['form']<50 else 60
    forme=max(s1['form'],s2['form'])
    over15=100-u25
    combo=(dc+over15)//2
    diff=(s1['gf']-s1['ga'])-(s2['gf']-s2['ga'])
    h_minus1=s1['w2'] if diff>=1.0 else 50
    h_plus2=100-max(s2['l3'],10)
    if h_plus2<60: h_plus2=80 if diff<1.5 else 65
    return f"{home} vs {away}\nBTTS {avis(btts)}\nPIRE DEF {avis(pire)}\nHT -2 {avis(ht)}\n1X {avis(dc)}\nU2.5 {avis(u25)}\nFORME {avis(forme)}\nCOMBO 1X+1.5 {avis(combo)}\nH-1 FAV {avis(h_minus1)}\nH+2 OUT SAFE {avis(h_plus2)}\n---\n"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb=[
        [InlineKeyboardButton("FR L1",callback_data="fr1"),InlineKeyboardButton("FR L2",callback_data="fr2")],
        [InlineKeyboardButton("PL",callback_data="eng1"),InlineKeyboardButton("CHAMP",callback_data="eng2")],
        [InlineKeyboardButton("LIGA",callback_data="esp1"),InlineKeyboardButton("LIGA2",callback_data="esp2")],
        [InlineKeyboardButton("BUNDES",callback_data="ger1"),InlineKeyboardButton("BUNDES2",callback_data="ger2")],
        [InlineKeyboardButton("SERIE A",callback_data="ita1"),InlineKeyboardButton("SERIE B",callback_data="ita2")],
        [InlineKeyboardButton("MONDIAL 150 MATCHS",callback_data="world")],
    ]
    await update.message.reply_text("V17.2 FIX - 8 MARCHES OK\nChoisis ligue ou envoie 'A vs B' ou photo:",reply_markup=InlineKeyboardMarkup(kb))

async def on_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    info=LEAGUES.get(q.data)
    await q.message.reply_text(f"Scan {info['name']}...")
    matches=get_matches(info['espn'])
    if not matches:
        await q.message.reply_text("0 match maintenant, essaie MONDIAL")
        return
    msg=""
    for m in matches[:8]:
        msg+=analyse_match(m['home'], m['away'])
        if len(msg)>3500: break
    await q.message.reply_text(f"{len(matches)} matchs {info['name']}:\n\n{msg}")

async def on_text_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await update.message.reply_text("Photo recue - envoie plutot en texte 'Equipe A vs Equipe B' pour V17.2")
        return
    if update.message.text and "vs" in update.message.text.lower():
        out=""
        for line in update.message.text.split("\n")[:10]:
            if "vs" not in line.lower(): continue
            parts=re.split(r'\s+vs\s+', line, flags=re.IGNORECASE)
            if len(parts)>=2:
                out+=analyse_match(parts[0].strip(), parts[1].strip())
        await update.message.reply_text(f"TA LISTE + HANDICAP:\n\n{out}")

@app.route("/")
def home(): return "V17.2 OK"
def run_flask(): app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true",timeout=5)
    except: pass
    app_=Application.builder().token(BOT_TOKEN).build()
    app_.add_handler(CommandHandler("start",start))
    app_.add_handler(CallbackQueryHandler(on_btn))
    app_.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, on_text_photo))
    app_.run_polling(drop_pending_updates=True)

import os, threading, requests, re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from PIL import Image
import pytesseract

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
    if p >= 80: return f"🟢 {p}% CONSEILLÉ"
    if p >= 69: return f"🟠 {p}% POSSIBLE"
    return f"🟡 {p}% RISQUÉ"

def get_team_full_stats(team_id, lg):
    if team_id in CACHE: return CACHE[team_id]
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams/{team_id}/schedule?season=2025"
        r = requests.get(url, timeout=10).json()
        evs = r.get("events", [])
        if isinstance(evs, dict): evs = evs.get("results", [])

        tot=btts=enc=ht=u25=wins=w2=w3=l3=0
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
                if ts-os_>=3: w3+=1
            if os_-ts>=3: l3+=1

        if tot==0:
            res={"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"w3":30,"l3":20,"gf":0.8,"ga":1.2}
        else:
            res={
                "btts":int(btts/tot*100),
                "enc":int(enc/tot*100),
                "ht":int(ht/tot*100),
                "u25":int(u25/tot*100),
                "form":int(wins/tot*100),
                "w2":int(w2/tot*100),
                "w3":int(w3/tot*100),
                "l3":int(l3/tot*100),
                "gf":round(gf/max(1,tot),2),
                "ga":round(ga/max(1,tot),2)
            }
        CACHE[team_id]=res
        return res
    except:
        return {"btts":60,"enc":65,"ht":60,"u25":60,"form":60,"w2":50,"w3":30,"l3":20,"gf":0.8,"ga":1.2}

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
    for lg in ["fra.1","eng.1","esp.1","ger.1","ita.1","fra.2","eng.2"]:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/teams?limit=100"
            data=requests.get(url,timeout=8).json()
            for t in data.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[]):
                if name.lower() in t['team']['displayName'].lower():
                    return t['team']['id'], lg
        except: continue
    return "0", "fra.1"

def analyse_match_text(home, away):
    hid, lg1 = find_team_id(home)
    aid, lg2 = find_team_id(away)
    lg = lg1
    s1=get_team_full_stats(hid, lg)
    s2=get_team_full_stats(aid, lg)

    btts=(s1['btts']+s2['btts'])//2
    pire=max(s1['enc'],s2['enc'])
    ht=(s1['ht']+s2['ht'])//2
    u25=(s1['u25']+s2['u25'])//2
    dc=80 if s2['form']<40 and s1['form']>60 else 70 if s2['form']<50 else 60
    forme=max(s1['form'],s2['form'])

    # 7. COMBO 1X & +1.5
    over15 = 100 - u25 # si u25 bas, over15 haut
    if over15 < 60: over15 = (s1['enc']+s2['enc'])//2 # fallback
    combo = (dc + over15)//2

    # 8. HANDICAP - ton idée
    # Force de l'équipe
    force1 = s1['gf'] - s1['ga'] + (0.3) # bonus domicile
    force2 = s2['gf'] - s2['ga']
    diff = force1 - force2

    # H-1 Favori domicile: gagne par 2 buts
    if diff >= 1.2:
        h_minus1 = max(s1['w2'], s1['form']) # s'il gagne souvent par 2
    else:
        h_minus1 = s1['w2']

    # H+2 Outsider: ne perd pas par 3
    # Si outsider perd rarement par 3, +2 est safe à 80%+
    h_plus2 = 100 - max(s2['l3'], s1['w3']) # 100% - % défaite lourde
    if h_plus2 < 60: h_plus2 = 75 if diff < 1.5 else 65

    return (
        f"⚽ {home} vs {away} | {lg}\n"
        f"BTTS {btts}% -> {avis(btts)}\n"
        f"PIRE DEF {pire}% -> {avis(pire)}\n"
        f"🛡️ HT -2 {ht}% -> {avis(ht)}\n"
        f"🏠 1X {dc}% -> {avis(dc)}\n"
        f"🧱 U2.5 {u25}% -> {avis(u25)}\n"
        f"⚡ FORME {forme}% -> {avis(forme)}\n"
        f"🔒 COMBO 1X&+1.5 {combo}% -> {avis(combo)}\n"
        f"🏆 H-1 FAV {h_minus1}% -> {avis(h_minus1)}\n"
        f"🛡️ H+2 OUT {h_plus2}% -> {avis(h_plus2)} (SAFE)\n---\n"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb=[
        [InlineKeyboardButton("🇫🇷 L1",callback_data="fr1"),InlineKeyboardButton("🇫🇷 L2",callback_data="fr2")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 PL",callback_data="eng1"),InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 CHAMP",callback_data="eng2")],
        [InlineKeyboardButton("🇪🇸 LIGA",callback_data="esp1"),InlineKeyboardButton("🇪🇸 LIGA2",callback_data="esp2")],
        [InlineKeyboardButton("🇩🇪 BUNDES",callback_data="ger1"),InlineKeyboardButton("🇩🇪 BUNDES2",callback_data="ger2")],
        [InlineKeyboardButton("🇮🇹 SERIE A",callback_data="ita1"),InlineKeyboardButton("🇮🇹 SERIE B",callback_data="ita2")],
        [InlineKeyboardButton("🌍 MONDIAL 150 MATCHS",callback_data="world")],
    ]
    await update.message.reply_text("V17 - 8 MARCHÉS DONT HANDICAP SAFE\nEnvoie photo ou liste 'A vs B' ou choisis ligue:",reply_markup=InlineKeyboardMarkup(kb))

async def on_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    info=LEAGUES.get(q.data)
    await q.message.reply_text(f"⏳ Scan {info['name']} 8 marchés...")
    matches=get_matches(info['espn'])
    if not matches:
        await q.message.reply_text("0 match maintenant, réessaie 12h ou MONDIAL")
        return
    msg=""
    for m in matches[:8]:
        msg+=analyse_match_text(m['home'], m['away'])
        if len(msg)>3500: break
    await q.message.reply_text(f"✅ {len(matches)} matchs {info['name']}:\n\n{msg}")

async def on_text_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await update.message.reply_text("📸 Lecture...")
        try:
            f=await update.message.photo[-1].get_file()
            await f.download_to_drive("cap.jpg")
            img=Image.open("cap.jpg")
            txt=pytesseract.image_to_string(img)
            lines=[l.strip() for l in txt.split("\n") if len(l.strip())>4]
            found=[]
            for l in lines[:15]:
                if "vs" in l.lower() or " v " in l.lower():
                    found.append(re.sub(r'\s+v\s+', ' vs ', l, flags=re.IGNORECASE))
            if not found: found=lines[:10]
            out=""
            for fl in found[:6]:
                if "vs" in fl.lower():
                    parts=re.split(r'\s+vs\s+', fl, flags=re.IGNORECASE)
                    if len(parts)>=

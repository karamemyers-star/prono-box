import os, threading, requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)
CACHE = {}

LEAGUES = {
    "fr1": {"espn": "fra.1", "name": "FRANCE L1"},
    "fr2": {"espn": "fra.2", "name": "FRANCE L2"},
    "eng1": {"espn": "eng.1", "name": "ANGLETERRE PL"},
    "eng2": {"espn": "eng.2", "name": "ANGLETERRE CHAMP"},
    "esp1": {"espn": "esp.1", "name": "ESPAGNE LIGA"},
    "esp2": {"espn": "esp.2", "name": "ESPAGNE LIGA2"},
    "ger1": {"espn": "ger.1", "name": "ALLEMAGNE BUNDES"},
    "ger2": {"espn": "ger.2", "name": "ALLEMAGNE BUNDES 2"},
    "ita1": {"espn": "ita.1", "name": "ITALIE SERIE A"},
    "ita2": {"espn": "ita.2", "name": "ITALIE SERIE B"},
    "world": {"espn": "all", "name": "MONDIAL"},
}

def get_avis(pct):
    if pct >= 80: return "🟢 CONSEILLÉ 80% - Vas-y"
    if pct >= 69: return "🟠 POSSIBLE 75% - Petite mise"
    return "🟡 RISQUÉ 60% - Évite"

def get_stats(team_id, league_code):
    if team_id in CACHE: return CACHE[team_id]
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/teams/{team_id}/fixtures"
        r = requests.get(url, timeout=10).json()
        btts = enc = tot = 0
        for ev in r.get("events", [])[:5]:
            if ev['status']['type']['state']!= 'post': continue
            comp = ev['competitions'][0]
            hg = int(float(comp['competitors'][0].get('score') or 0))
            ag = int(float(comp['competitors'][1].get('score') or 0))
            tot += 1
            if hg>0 and ag>0: btts+=1
            if hg>=1 or ag>=1: enc+=1
        if tot==0: return {"btts":60,"enc":60}
        res = {"btts": int(btts/tot*100), "enc": int(enc/tot*100)}
        CACHE[team_id]=res
        return res
    except:
        return {"btts":60,"enc":65}

def get_matches(code):
    leagues = ["eng.1","esp.1","ita.1","ger.1","fra.1","eng.2","fra.2","esp.2","ger.2","ita.2"] if code=="all" else [code]
    matches=[]
    for lg in leagues:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard"
            data = requests.get(url, timeout=8).json()
            for ev in data.get("events", []):
                if ev['status']['type']['state']!= 'pre': continue
                comp = ev['competitions'][0]
                home = comp['competitors'][0]['team']['displayName']
                away = comp['competitors'][1]['team']['displayName']
                hid = comp['competitors'][0]['id']
                aid = comp['competitors'][1]['id']
                matches.append({"home":home,"away":away,"hid":hid,"aid":aid,"lg":lg})
        except: continue
    return matches

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🇫🇷 FRANCE L1", callback_data="fr1"), InlineKeyboardButton("🇫🇷 FRANCE L2", callback_data="fr2")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 PL", callback_data="eng1"), InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 CHAMP D2", callback_data="eng2")],
        [InlineKeyboardButton("🇪🇸 LIGA", callback_data="esp1"), InlineKeyboardButton("🇪🇸 LIGA2", callback_data="esp2")],
        [InlineKeyboardButton("🇩🇪 BUNDES", callback_data="ger1"), InlineKeyboardButton("🇩🇪 BUNDES 2", callback_data="ger2")],
        [InlineKeyboardButton("🇮🇹 SERIE A", callback_data="ita1"), InlineKeyboardButton("🇮🇹 SERIE B", callback_data="ita2")],
        [InlineKeyboardButton("🌍 SCAN MONDIAL 150 MATCHS", callback_data="world")],
    ]
    await update.message.reply_text("V15 PURE ESPN - 100% GRATUIT ILLIMITÉ\nChoisis une ligue:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    code = q.data
    info = LEAGUES.get(code)
    espn_code = info['espn']

    await q.message.reply_text(f"⏳ Scan {info['name']} ESPN en cours...")
    matches = get_matches(espn_code)

    if not matches:
        await q.message.reply_text(f"ESPN vide pour {info['name']} maintenant. Réessaie à 12h ou clique MONDIAL.")
        return

    out=""
    for m in matches[:15]:
        s1 = get_stats(m['hid'], m['lg'])
        s2 = get_stats(m['aid'], m['lg'])
        btts = (s1['btts']+s2['btts'])//2
        pire = max(s1['enc'], s2['enc'])
        out += f"⚽ {m['home']} vs {m['away']} | {m['lg']}\nBTTS {btts}% -> {get_avis(btts)}\nPIRE DEF {pire}% -> {get_avis(pire)}\n---\n"
        if len(out)>3500: break

    await q.message.reply_text(f"✅ {len(matches)} matchs {info['name']} aujourd'hui (ESPN pur):\n\n{out}")

@app.route("/")
def home(): return "V15 PURE ESPN OK"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    try: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except: pass
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(on_button))
    bot.run_polling(drop_pending_updates=True)

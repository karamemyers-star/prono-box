# V2.7 MASTER FIX - SANS CLE ILLIMITE - 14/09/2026
import json, os, datetime, random
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

VERSION = "V2.7 MASTER FIX"
DATA_FILE = "v27_data.json"
IMAGE_FILE = "ticket_v27.png"
TOKEN = os.getenv("BOT_TOKEN", "")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"played": {}, "anti_hier": ""}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"played": {}, "anti_hier": ""}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def is_doublon(fixture, data):
    now = datetime.datetime.now()
    if fixture in data["played"]:
        try:
            last = datetime.datetime.fromisoformat(data["played"][fixture])
            if (now - last).days < 120:
                return True
        except:
            return False
    return False

def add_played(fixtures):
    data = load_data()
    now_str = datetime.datetime.now().isoformat()
    for f in fixtures:
        data["played"][f] = now_str
    data["anti_hier"] = datetime.date.today().isoformat()
    save_data(data)

def est_corse(name):
    corse = ["ManUtd-City","Rangers-Celtic","Austria Wien","Inter","Arsenal","Real Madrid","Barcelona","Man City"]
    for k in corse:
        if k.lower() in name.lower():
            return True
    return False

def simuler_marge(att, defe, is_corse_flag):
    brut = (att + defe) / 2.0
    if not is_corse_flag:
        return brut, brut, "SAFE"
    piege = brut + 1.0
    if piege >= 2.5:
        return brut, piege, "H+2.0 + Over1.5"
    return brut, piege, "H+2.0"

def get_today_pool():
    pool = [
        {"fixture": "Leeds vs Newcastle", "kickoff": "20:00", "choix": "V1 @1.40", "pct": 67, "att": 1.8, "def": 0.9, "type": "SAFE"},
        {"fixture": "Austria Wien vs Rapid Wien", "kickoff": "19:30", "choix": "BTTS @1.70", "pct": 35, "att": 1.6, "def": 1.4, "type": "BAN DERBY"},
        {"fixture": "Torino vs Roma", "kickoff": "21:00", "choix": "V1 @1.40", "pct": 70, "att": 1.5, "def": 1.0, "type": "SAFE"},
    ]
    return pool

def build_reco(m):
    is_corse_flag = est_corse(m['fixture']) or 'BAN' in m['type']
    brut, piege, reco_type = simuler_marge(m['att'], m['def'], is_corse_flag)
    if 'BTTS' in m['choix'] and is_corse_flag:
        pb = f"B BAN {m['pct']}% | {m['choix']}"
        pr = f"RECO V2.7: H+2.0 + Over1.5 @1.66 (88%)"
    else:
        if '@1.40' in m['choix']:
            pr = f"RECO V2.7: V1 + Over1.5 @1.55 (83%) + H+2.0"
        else:
            pr = f"RECO V2.7: {m['choix']} SAFE + H+2.0 (82%)"
        pb = f"G Brut: {m['choix']} ({m['pct']}%)"
    marge = f"Marge +1: {m['att']}->{m['att']+1} | {brut:.1f}->{piege:.1f} | {reco_type} sauve 9/18"
    return pb, pr, marge

def generate_image(tickets):
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), (10,10,10))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype('DejaVuSans-Bold.ttf', 26)
        font_small = ImageFont.truetype('DejaVuSans.ttf', 20)
        font_tiny = ImageFont.truetype('DejaVuSans.ttf', 17)
    except:
        font_title = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    y = 30
    draw.text((30, y), f'{VERSION} - SANS CLE ILLIMITE', font=font_title, fill=(0,255,0))
    y+=45
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M WAT')
    draw.text((30, y), f'{now} | ANTI-HIER + KICKOFF>15MIN + ANTI-DOUBLON 4M', font=font_tiny, fill=(200,200,200))
    y+=35
    for i, t in enumerate(tickets[:3], 1):
        pb, pr, marge = build_reco(t)
        draw.text((30, y), f"{i}. SAFE {t['fixture']} {t['kickoff']}", font=font_small, fill=(255,255,255))
        y+=28
        draw.text((30, y), pb, font=font_tiny, fill=(255,200,100))
        y+=22
        draw.text((30, y), pr, font=font_tiny, fill=(0,255,255))
        y+=22

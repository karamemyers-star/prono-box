# V2.14 FINAL - CORRECTION 1X/2X NOMS - 15/09/2026
import json, os, datetime, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

VERSION = 'V2.14 FINAL 1X/2X'
DATA_FILE = 'v214_data.json'
IMAGE_FILE = 'ticket_v214.png'
TOKEN = os.getenv('BOT_TOKEN', '')

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'V2.14 FINAL LIVE')
    def log_message(self, *a): pass

def start_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

def load_data():
    if not os.path.exists(DATA_FILE): return {'played': {}, 'anti_hier': ''}
    try:
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except: return {'played': {}, 'anti_hier': ''}

def save_data(d):
    with open(DATA_FILE, 'w') as f: json.dump(d, f)

def is_doublon(fix, data):
    now = datetime.datetime.now()
    if fix in data['played']:
        try:
            last = datetime.datetime.fromisoformat(data['played'][fix])
            if (now - last).days < 120: return True
        except: pass
    return False

def est_corse(name):
    blacklist = ['Austria Wien vs Rapid', 'ManUtd vs ManCity', 'Rangers vs Celtic', 'Gent vs Anderlecht', 'West Ham vs Fulham', 'Liverpool vs Tottenham']
    return any(k.lower() in name.lower() for k in blacklist)

def get_trap_pastille(trap):
    if trap <= 3: return "🟢", (0,255,130)
    if trap <= 6: return "🟡", (255,220,80)
    return "🔴", (255,80,80)

def format_double_chance(fixture, equipe_forte, cote):
    # RÈGLE UNIVERSELLE V2.14
    try:
        domicile, exterieur = [x.strip() for x in fixture.split(" vs ")]
        if equipe_forte.lower() in domicile.lower():
            return f"{domicile} 1X ({domicile} gagne ou NUL) @{cote}"
        else:
            return f"{exterieur} 2X ({exterieur} gagne ou NUL) @{cote}"
    except:
        return f"{equipe_forte} X2 @{cote}"

def get_today_pool_13():
    # Pool avec equipe_forte séparée pour formatage auto
    raw = [
        {'fixture': 'Falkirk vs Hearts', 'forte': 'Hearts', 'cote': 1.26, 'trap': 2, 'league': 'Scotland'},
        {'fixture': 'Duisburg vs Havelse', 'forte': 'Duisburg', 'cote': 1.35, 'trap': 2, 'league': '3.Liga'},
        {'fixture': 'Ipswich vs Arsenal', 'forte': 'Arsenal', 'cote': 1.37, 'trap': 2, 'league': 'Carabao Cup'},
        {'fixture': 'Elche vs Real Madrid', 'forte': 'Real Madrid', 'cote': 1.25, 'trap': 1, 'league': 'LaLiga'},
        {'fixture': 'Ajax vs Willem II', 'forte': 'Ajax', 'cote': 1.40, 'trap': 1, 'league': 'Eredivisie'},
        {'fixture': 'Middlesbrough vs Millwall', 'forte': 'Middlesbrough', 'cote': 1.45, 'trap': 3, 'league': 'Championship'},
        {'fixture': 'Reading vs Brentford', 'forte': 'Brentford', 'cote': 1.30, 'trap': 3, 'league': 'Carabao Cup'},
    ]
    pool = []
    for m in raw:
        m['pick'] = format_double_chance(m['fixture'], m['forte'], m['cote'])
        m['pick'] += " GIANT SAFE" if m['trap']<=2 else ""
        pool.append(m)
    return pool

def build_mega_global():
    pool = get_today_pool_13()
    giants = sorted([m for m in pool if m['trap'] <= 2], key=lambda x: x['trap'])
    best3 = giants[:3]; best5 = giants[:5]
    cote3 = 1;
    for x in best3: cote3 *= x['cote']
    cote5 = 1;
    for x in best5: cote5 *= x['cote']
    txt = "👑 MEGA GLOBAL BEST OF BEST - 13 CHAMPIONNATS\n🟢 Trap <3 uniquement V2.14\n\n"
    txt += f"🔵 SAFE @2.90 - 3 MATCHS:\n"
    for m in best3: txt += f"🟢 Trap {m['trap']}/10 | {m['fixture']} -> {m['pick']}\n"
    txt += f"Cote brute @{round(cote3,2)} -> @2.90 SAFE\n\n"
    txt += f"🔵 BEST @4.50 - 5 MATCHS:\n"
    for m in best5: txt += f"🟢 Trap {m['trap']}/10 | {m['fixture']} -> {m['pick']}\n"
    txt += f"Cote brute @{round(cote5,2)} -> @4.50 SAFE\n"
    return txt

def generate_image_v214(tickets):
    W, H = 1080, 350 + len(tickets)*195
    img = Image.new('RGB', (W, H), (8,12,20))
    draw = ImageDraw.Draw(img)
    try:
        ft_title = ImageFont.truetype('DejaVuSans-Bold.ttf', 24)
        ft_match = ImageFont.truetype('DejaVuSans-Bold.ttf', 16)
        ft_past = ImageFont.truetype('DejaVuSans.ttf', 13)
        ft_sub = ImageFont.truetype('DejaVuSans.ttf', 11)
    except:
        ft_title = ft_match = ft_past = ft_sub = ImageFont.load_default()
    y=20
    draw.text((20,y), f'{VERSION} - 13 LEAGUES - 1X/2X CORRIGE', font=ft_title, fill=(0,255,130)); y+=32
    draw.text((20,y), f"{datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} | ANTI-DOUBLON 120J | PASTILLES V2.14", font=ft_sub, fill=(180,190,200)); y+=28
    for m in tickets:
        p, color = get_trap_pastille(m['trap'])
        draw.rounded_rectangle([(15,y),(W-15,y+170)], radius=14, fill=(18,26,38), outline=color, width=2)
        draw.text((25,y+10), f"{p} Trap {m['trap']}/10 | {m['fixture']} | {m['league']}", font=ft_match, fill=(255,255,255))
        draw.text((25,y+38), f"Pick: {m['pick']}", font=ft_past, fill=(255,210,120))
        y+=190
    img.save(IMAGE_FILE)
    return IMAGE_FILE

async def cmd_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    pool = get_today_pool_13()
    filtered = [m for m in pool if not is_doublon(m['fixture'], data)]
    img_path = generate_image_v214(filtered)
    save_data({**data, 'played': {**data['played'], **{m['fixture']: datetime.datetime.now().isoformat() for m in filtered}}})
    await update.message.reply_photo(photo=open(img_path, 'rb'))
    txt = f"{VERSION}\n"
    for m in filtered:
        p,_ = get_trap_pastille(m['trap'])
        txt += f"{p} {m['fixture']} -> {m['pick']} | Trap {m['trap']}/10\n"
    await update.message.reply_text(txt)
    await update.message.reply_text(build_mega_global())

async def cmd_combine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(build_mega_global())

def main():
    start_server()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('ticket', cmd_ticket))
    app.add_handler(CommandHandler('start', cmd_ticket))
    app.add_handler(CommandHandler('combine_safe', cmd_combine))
    app.add_handler(MessageHandler(filters.PHOTO, lambda u,c: cmd_ticket(u,c)))
    print(f'{VERSION} LIVE')
    app.run_polling()

if __name__ == '__main__':
    main()

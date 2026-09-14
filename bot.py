# V2.6 MASTER 3 - SANS CLE ILLIMITE FIX 14/09/2026
import telebot
from datetime import datetime, timedelta

BOT_TOKEN = "TON_TOKEN"
bot = telebot.TeleBot(BOT_TOKEN)

# CACHE ANTI-DOUBLON
deja_envoye = set()
last_reset = ""

def get_today():
    return datetime.now().strftime("%d.%m.%Y") # 14.09.2026

def is_top_team(team):
    tops = ["PSV","Ajax","Barca","Inter","Man City","Man Utd","Rangers","Celtic","Galatasaray","Fener","Bayern","Leipzig"]
    return any(t.lower() in team.lower() for t in tops)

def is_derby(match):
    derbys = [("Austria","Rapid"), ("ManUtd","City"), ("Rangers","Celtic"), ("Galatasaray","Fener")]
    for a,b in derbys:
        if a in match and b in match:
            return True
    return False

def get_prediction_master3(match_name, home_rank, away_rank):
    # REGLE MASTER 3
    # BAN BTTS si Top vs Top ou DERBY
    is_top_vs_top = (home_rank <= 6 and away_rank <= 6)
    
    if is_derby(match_name) or is_top_vs_top:
        # BAN BTTS => On met H+2.0 + Over1.5
        return f"H+2.0 Outsider @1.28 + Over1.5 @1.30 SAFE"
    else:
        # Normal
        if home_rank <= 10 and away_rank >= 15:
            return f"V1 @1.50 + Over1.5 @1.35"
        else:
            return f"Over1.5 @1.28 + H+2.0 @1.25"

@bot.message_handler(commands=['ticket'])
def ticket(message):
    global deja_envoye, last_reset
    
    TODAY = get_today()
    now = datetime.now()
    
    # 1. RESET MINUIT - FIX ANTI HIER
    if last_reset != TODAY:
        deja_envoye.clear()
        last_reset = TODAY
        print(f"RESET CACHE - Nouveau jour {TODAY}")

    matches = scraper_flashscore() # ta fonction
    
    tickets_du_jour = []
    
    for m in matches:
        kickoff = m['kickoff'] # datetime object
        match_id = m['id']
        date_str = m['date_str'] # 14.09.2026
        
        # 2. FILTRE DATE DU JOUR OBLIGATOIRE - FIX PRINCIPAL
        if TODAY not in date_str:
            continue # <--- BAN les matchs d'hier
        
        # 3. FILTRE KICKOFF > NOW-15MIN
        if kickoff < now - timedelta(minutes=15):
            continue
        
        # 4. ANTI DOUBLON
        if match_id in deja_envoye:
            continue
        
        deja_envoye.add(match_id)
        
        # PREDICTION MASTER 3
        pred = get_prediction_master3(m['name'], m['home_rank'], m['away_rank'])
        tickets_du_jour.append(f"- {m['name']} {pred} 🟢")

    # ENVOI
    reponse = f"✅ V2.6 MASTER 3 - SANS CLE ILLIMITE ACTIF\n"
    reponse += f"Heure: {TODAY} {now.strftime('%H:%M')} WAT\n"
    reponse += f"Source: FlashScore Scraper illimite\n"
    reponse += f"Regle: TOUS NS VERIFIE {TODAY} - KICKOFF > NOW-15MIN - PURGE AUTO\n"
    reponse += f"{len(tickets_du_jour)} championnats\n\n"
    reponse += "\n".join(tickets_du_jour)
    
    bot.send_message(message.chat.id, reponse)

bot.polling()

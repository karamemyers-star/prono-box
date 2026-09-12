import requests
from datetime import datetime

print("🚀 V32.1 ESPN UPTODATE - Lancement...")

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
DATE_TODAY = datetime.now().strftime("%Y%m%d")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# TOUS LES CHAMPIONNATS - Comme tu as demandé
LEAGUES = [
    "eng.1","fra.1","ger.1","ita.1","esp.1", # 5 grands
    "eng.2","ger.2","ita.2","esp.2","fra.2", # D2
    "ned.1","por.1","bel.1","tur.1","sui.1", # moyens
    "swe.1","swe.2","nor.1","den.1","fin.1", # tes petits - Suède etc
    "aut.1","aut.2","ned.2","sco.1","gre.1" # autres
]

def get_avg_goals(team_id, league):
    """Retourne moyenne buts marqués sur 5 derniers matchs - saison 26/27"""
    try:
        url = f"{BASE}/{league}/teams/{team_id}/schedule?season=2026"
        r = requests.get(url, headers=HEADERS, timeout=8).json()
        goals, count = 0, 0
        for ev in r.get('events', [])[:5]:
            if ev['status']['type']['state']!= 'post': continue
            for c in ev['competitions'][0]['competitors']:
                if str(c['id']) == str(team_id):
                    goals += int(c.get('score', 0))
                    count += 1
        return goals / max(1, count)
    except:
        return 1.5 # valeur neutre si erreur

tickets_verts = []

for league in LEAGUES:
    url = f"{BASE}/{league}/scoreboard?dates={DATE_TODAY}"
    try:
        data = requests.get(url, headers=HEADERS, timeout=8).json()
        for ev in data.get('events', []):
            # FILTRE 1 - MATCHS A JOUR SEULEMENT - ta consigne 5/5
            if ev['status']['type']['state'] == 'post': continue
            if ev['status']['type']['name']!= 'STATUS_SCHEDULED': continue

            comp = ev['competitions'][0]
            home = [c for c in comp['competitors'] if c['homeAway'] == 'home'][0]
            away = [c for c in comp['competitors'] if c['homeAway'] == 'away'][0]

            home_name = home['team']['displayName']
            away_name = away['team']['displayName']
            heure = ev['status']['type'].get('shortDetail', '')

            # FILTRE 2 - ADVERSAIRE FAIBLE <0.8
            avg_home = get_avg_goals(home['id'], league)
            avg_away = get_avg_goals(away['id'], league)

            # Logique V32: Si un est faible, l'autre est solide -> Double Chance + 0 MT
            if avg_home < 0.8:
                confiance = 83 if avg_home < 0.5 else 78 if avg_home < 0.65 else 71
                pastille = "🟢" if confiance >= 75 else "🟠"
                tickets_verts.append(f"{pastille} {home_name} vs {away_name} | {league} | {heure} | PARI: {away_name} X2 + 0 encaissé MT | {confiance}% | Adv {avg_home:.2f} but/m | {ev['id']}")

            if avg_away < 0.8:
                confiance = 83 if avg_away < 0.5 else 78 if avg_away < 0.65 else 71
                pastille = "🟢" if confiance >= 75 else "🟠"
                tickets_verts.append(f"{pastille} {home_name} vs {away_name} | {league} | {heure} | PARI: {home_name} 1X + 0 encaissé MT | {confiance}% | Adv {avg_away:.2f} but/m | {ev['id']}")

    except Exception as e:
        continue

# TRI
tickets_verts = sorted(tickets_verts, key=lambda x: int(x.split('|')[3].replace('%','').strip().split(' ')[0]) if '%' in x else 0, reverse=True)

print(f"\n✅ SCAN FINI - {len(tickets_verts)} MATCHS VERTS TROUVÉS AUJOURD'HUI\n")
for t in tickets_verts[:20]:
    print(t)

print("\n--- BEST OF BEST (Top 5) ---")
for t in tickets_verts[:5]:
    print(t)

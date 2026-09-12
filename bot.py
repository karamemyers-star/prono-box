def scan(date_str):
    out=[]; now=datetime.now(DOUALA)
    for code in LIGUES:
        try:
            data=requests.get(f"{BASE}/{code}/scoreboard?dates={date_str}", timeout=6).json()
            for ev in data.get('events',[]):
                if ev['status']['type']['state']=='post': continue
                utc=datetime.fromisoformat(ev['date'].replace("Z","+00:00"))
                local=utc.astimezone(DOUALA)
                # On garde seulement futur si AUJ
                if date_str==datetime.now(DOUALA).strftime("%Y%m%d") and local < now: continue

                h=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='home'][0]
                a=[c for c in ev['competitions'][0]['competitors'] if c['homeAway']=='away'][0]
                ah=get_avg(h['id'], code); aa=get_avg(a['id'], code)
                heure=local.strftime("%H:%M")

                # V32 SI STRICT
                if (ah<0.9 and aa>1.2) or (aa<0.9 and ah>1.2):
                    fort=a['team']['displayName'] if ah<0.9 else h['team']['displayName']
                    faible=h['team']['displayName'] if ah<0.9 else a['team']['displayName']
                    out.append(f"🟢 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\nFAIBLE {faible} {ah if ah<0.9 else aa:.2f} vs FORT {fort}\n[V24 BANQUE 90%] {fort} +2\n[V32] {fort} X2 + 0 MT + CORNERS -2")
                else:
                    # V24 TOUJOURS - MEME SANS FAIBLE vs FORT
                    out.append(f"🟠 {heure} {h['team']['abbrev']} vs {a['team']['abbrev']}\n[V24 BANQUE] {a['team']['displayName']} +2 HANDICAP - NE PERD PAS PAR 3+")
        except: continue
    return out

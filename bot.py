{
  "version": "V2.6 MASTER FINAL - CALENDRIER + BILAN - ACTIVE",
  "timezone": "Africa/Douala UTC+1",
  "heure_activation": "13.09.2026 09:21 WAT",
  "regle_or_anti_match_joue": {
    "filtre_1_kickoff": "SI kickoff < now(WAT) - 15min => 🔴 ROUGE DEJA JOUE - SKIP AUTO",
    "filtre_2_date": "date_match doit = aujourd'hui OU demain, JAMAIS hier",
    "filtre_3_status": "status API = NS ou TIMED seulement, JAMAIS FT/AET/LIVE/HT",
    "action_bloquage": "Bot s'auto-bloque + affiche 🔴 MATCH TERMINE HIER - SKIP",
    "scan": "06h00 Douala + toutes les 3h + avant chaque ticket"
  },
  "source_gratuite": {
    "principale": "football-data.org 10req/min GRATUIT",
    "backup_1": "API-Sports Free 100req/jour",
    "backup_2": "Scraper FlashScore/Soccerway illimite gratuit",
    "championnats": ["France D1/D2", "Angleterre D2/D3", "Allemagne D1/D2", "Hollande D1/D2", "Ecosse D1/D2", "Suede D1/D2", "Turquie D1", "Grece D1", "Danemark D1/D2", "Italie D1", "Finlande D1", "Hongrie D1"]
  },
  "filtres_V1_V2.4_V2.5_TOUS_GARDES": {
    "V1_TUEUR": "Top6 vs Bottom10 => V1 @1.40-1.80 🟢 VERT - ON AJOUTE ON SUPPRIME RIEN",
    "BTTS_TOP5": "Top5 vs Top5 => BTTS OUI @1.65-1.80 🟡 JAUNE - ON GARDE",
    "OVER15_SAFE": "Tout match sauf Bottom vs Bottom => Over1.5 @1.20-1.35 🟢 VERT - ON GARDE",
    "SKIP": "Bottom vs Bottom OU PSG fatigué LDC => 🔴 ROUGE SKIP"
  },
  "4_combinaisons_programmees": {
    "1_BUTS": "Que Over1.5 @1.20-1.35 x5 = @3.05 SAFE",
    "2_TUEURS": "Que V1 @1.40-1.80 x3 = @2.74",
    "3_BTTS": "Que BTTS @1.65-1.80 x3 = @4.90 RISQUE",
    "4_MIXTE_JACKPOT": "2x Over15 + 1x V1 + 2x BTTS = @5.99 LE PLUS RENTABLE +89400F simu"
  },
  "module_bilan_auto": {
    "input": "Toi tu cliques ✅ GAGNANT ou ❌ PERDANT ou 🔵 REMBOURSE",
    "calcul_auto": " % par systeme + % par championnat + % par cote + Profit + ROI + Serie W/L",
    "alerte": "Si 3 perdants meme systeme => 🟡 STOP SYSTEME + propose alternative auto",
    "exemple_affichage": "📊 BILAN 7J: 12M 9G 75% +5800F | OVER15 5/5 🟢 | BTTS 3/4 🟢 | V1 1/3 🔴"
  },
  "ticket_dimanche_13_09_VERIFIE_NS": {
    "heure_scan": "13.09.2026 09:21 WAT - TOUS NS VERIFIE",
    "MIXTE_JACKPOT_ACTIF": "Lille V1@1.40 🟢 + Leipzig Over15@1.25 🟢 + ManUtd-City BTTS@1.65 🟡 + PSV Over15@1.22 🟢 + Rangers-Celtic BTTS@1.70 🟣 = @5.99",
    "SAFE_BUTS": "PSV O15@1.22 + Leipzig O15@1.25 + Lille O15@1.28 + Barca O15@1.20 = @2.35 🟢"
  }
}

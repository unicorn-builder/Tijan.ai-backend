"""
prix_marche.py — Base de prix construction multi-pays Tijan AI
═══════════════════════════════════════════════════════════════
Sources :
  Dakar      : Prix validés terrain par Malick Tall (Mars 2026)
               + Recherche marché Avril 2026 (investissementimmoafrique.com,
                 CYPE Sénégal, prixdakar.com, Jumia.sn)
  Abidjan    : BNETD, SICOGI, marchés locaux (~Dakar +10% logistique port)
  Casablanca : CSMC, CPC Maroc, Ordre des Architectes Maroc
  Lagos      : NBRRI, NIOB, Builders Magazine Nigeria (⚠ NGN très volatile)
  Accra      : Ghana Institute of Engineers, GIBB Africa

Devise de référence : FCFA (XOF) pour Dakar/Abidjan
Autres devises converties en FCFA équivalent pour comparaison.

Mise à jour : Avril 2026
Prochaine révision : Juillet 2026
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import date

# ══════════════════════════════════════════════════════════════
# TAUX DE CHANGE (Avril 2026 — à réviser mensuellement)
# ══════════════════════════════════════════════════════════════
TAUX_CHANGE = {
    "XOF": 1.0,           # FCFA — référence
    "MAD": 60.5,          # 1 MAD = 60.5 FCFA (Dirham marocain)
    "NGN": 0.48,          # 1 NGN = 0.48 FCFA (Naira nigérian) — ⚠ très volatile, vérifier mensuellement
    "GHS": 57.0,          # 1 GHS = 57 FCFA (Cedi ghanéen)
    "EUR": 655.957,       # 1 EUR = 655.957 FCFA (fixe Zone CFA)
    "USD": 607.0,         # 1 USD ≈ 607 FCFA (Mars 2026)
}

def to_fcfa(montant: float, devise: str) -> float:
    """Convertit un montant en FCFA."""
    return montant * TAUX_CHANGE.get(devise, 1.0)

# ══════════════════════════════════════════════════════════════
# STRUCTURE DE DONNÉES PRIX
# ══════════════════════════════════════════════════════════════
@dataclass
class PrixStructure:
    """Prix matériaux et main d'œuvre — Structure."""
    # Béton (FCFA/m³ — fourni posé BPE)
    beton_c2530_m3: float       # Fondations, éléments peu sollicités
    beton_c3037_m3: float       # Standard résidentiel R+4 à R+8
    beton_c3545_m3: float       # Haute résistance R+9 et plus
    beton_c4050_m3: float       # Tours, IGH

    # Acier (FCFA/kg — fourni posé façonné)
    acier_ha400_kg: float       # Petits ouvrages R+1 à R+3
    acier_ha500_kg: float       # Standard résidentiel/bureau
    acier_ha500_vrac_kg: float  # Prix vrac (sans façonnage)

    # Coffrage (FCFA/m²)
    coffrage_bois_m2: float     # Coffrage traditionnel bois
    coffrage_metal_m2: float    # Coffrage métallique réutilisable

    # Fondations
    pieu_fore_d600_ml: float    # Pieu foré Ø600mm (FCFA/ml)
    pieu_fore_d800_ml: float    # Pieu foré Ø800mm (FCFA/ml)
    pieu_fore_d1000_ml: float   # Pieu foré Ø1000mm (FCFA/ml)
    semelle_filante_ml: float   # Semelle filante béton armé (FCFA/ml)
    radier_m2: float            # Radier général (FCFA/m²)

    # Maçonnerie (FCFA/m²)
    agglo_creux_10_m2: float    # Agglos creux 10cm (cloisons légères)
    agglo_creux_15_m2: float    # Agglos creux 15cm (cloisons standard)
    agglo_creux_20_m2: float    # Agglos creux 20cm (murs porteurs)
    agglo_plein_25_m2: float    # Agglos pleins 25cm (façades)
    brique_pleine_m2: float     # Briques pleines (premium)
    ba13_simple_m2: float       # Cloison BA13 simple rail
    ba13_double_m2: float       # Cloison BA13 double rail (séparatif)

    # Étanchéité (FCFA/m²)
    etanch_sbs_m2: float        # Étanchéité SBS bicouche toiture
    etanch_pvc_m2: float        # Étanchéité PVC membrane
    etanch_liquide_m2: float    # Étanchéité liquide salles de bain

    # Terrassement (FCFA/m³)
    terr_mecanique_m3: float    # Terrassement mécanique
    terr_manuel_m3: float       # Terrassement manuel
    remblai_m3: float           # Remblai compacté

    # Main d'œuvre (FCFA/jour)
    mo_chef_chantier_j: float
    mo_macon_j: float
    mo_ferrailleur_j: float
    mo_electricien_j: float
    mo_plombier_j: float
    mo_manœuvre_j: float


@dataclass
class PrixMEP:
    """Prix équipements MEP (FCFA — fournis posés)."""
    # Électricité
    tableau_general_bt: float       # TGBT complet (forfait)
    transfo_160kva: float           # Transformateur HTA/BT 160kVA
    transfo_250kva: float
    transfo_400kva: float
    groupe_electrogene_100kva: float
    groupe_electrogene_200kva: float
    groupe_electrogene_400kva: float
    compteur_monophase: float       # Compteur + coffret (par logement)
    compteur_triphase: float
    canalisation_cuivre_ml: float   # Câblage cuivre (FCFA/ml moyen)
    luminaire_led_standard: float   # Luminaire LED plafonnier (unité)
    luminaire_led_premium: float

    # Plomberie
    colonne_montante_ml: float      # Colonne montante acier galva (FCFA/ml)
    tuyau_pvc_dn50_ml: float
    tuyau_pvc_dn100_ml: float
    tuyau_pvc_dn150_ml: float
    robinet_standard: float         # Robinet mélangeur standard
    robinet_eco: float              # Robinet économique 6L/min
    wc_standard: float              # WC standard
    wc_double_chasse: float         # WC double chasse 3/6L
    cuve_eau_5000l: float           # Citerne polyéthylène 5000L
    cuve_eau_10000l: float
    pompe_surpresseur_1kw: float
    pompe_surpresseur_3kw: float
    chauffe_eau_electrique_100l: float
    chauffe_eau_solaire_200l: float  # CESI 200L

    # CVC
    split_1cv: float                # Split mural 1CV (9000 BTU)
    split_2cv: float                # Split mural 2CV (18000 BTU)
    split_cassette_4cv: float       # Cassette plafond 4CV
    vmc_simple_flux: float          # VMC simple flux (par logement)
    vmc_double_flux: float          # VMC double flux (par logement)
    climatiseur_central_kw: float   # Clim centrale (FCFA/kW)

    # Ascenseurs
    ascenseur_630kg_r4_r6: float    # Ascenseur 630kg 4-6 niveaux
    ascenseur_630kg_r7_r10: float   # Ascenseur 630kg 7-10 niveaux
    ascenseur_1000kg_r6_r10: float  # Ascenseur 1000kg 6-10 niveaux
    ascenseur_1000kg_r11_plus: float
    monte_charge_500kg: float

    # Courants faibles
    cablage_rj45_ml: float          # Câblage réseau RJ45 (FCFA/ml)
    prise_rj45: float               # Prise réseau (unité)
    baie_serveur_12u: float         # Baie serveur 12U
    camera_ip_interieure: float     # Caméra IP intérieure
    camera_ip_exterieure: float
    systeme_controle_acces: float   # Contrôle d'accès (par porte)
    interphone_video: float         # Interphone vidéo (par logement)

    # Sécurité incendie
    detecteur_fumee: float          # Détecteur fumée optique
    declencheur_manuel: float       # Déclencheur manuel
    sirene_flash: float             # Sirène + flash
    centrale_incendie_16zones: float
    centrale_incendie_32zones: float
    extincteur_6kg_co2: float
    extincteur_9kg_poudre: float
    ria_dn25_ml: float              # RIA DN25 (FCFA/ml)
    sprinkler_tete: float           # Tête de sprinkler (unité)
    sprinkler_centrale: float       # Centrale sprinkler

    # Automatisation
    domotique_logement: float       # Domotique par logement (basic)
    bms_systeme: float              # BMS bâtiment (forfait)
    eclairage_detecteur_presence: float  # Éclairage + détecteur


@dataclass
class PrixPays:
    """Prix complets pour un pays donné."""
    pays: str
    ville_reference: str
    devise: str
    date_maj: str
    structure: PrixStructure
    mep: PrixMEP
    notes: str = ""
    fiabilite: str = "estimation"  # "validé_terrain" | "estimation" | "à_confirmer"


# ══════════════════════════════════════════════════════════════
# DAKAR, SÉNÉGAL — PRIX VALIDÉS TERRAIN + RECHERCHE MARCHÉ (Avril 2026)
# ══════════════════════════════════════════════════════════════
DAKAR = PrixPays(
    pays="Sénégal",
    ville_reference="Dakar",
    devise="XOF",
    date_maj="2026-04",
    fiabilite="validé_terrain",
    notes=(
        "Prix validés par Malick Tall (Mars 2026) + corrections recherche marché Avril 2026. "
        "Sources: investissementimmoafrique.com, CYPE Sénégal, prixdakar.com, Jumia.sn. "
        "Fournisseurs ref: Fabrimetal (acier), CIMAF/SOCOCIM (ciment), SONETEL (élec)."
    ),
    structure=PrixStructure(
        # Béton BPE (FCFA/m³) — validé terrain, inchangé
        beton_c2530_m3=170_000,
        beton_c3037_m3=185_000,
        beton_c3545_m3=210_000,
        beton_c4050_m3=240_000,
        # Acier (FCFA/kg) — validé terrain, inchangé
        acier_ha400_kg=750,
        acier_ha500_kg=810,
        acier_ha500_vrac_kg=530,
        # Coffrage — validé, inchangé
        coffrage_bois_m2=18_000,
        coffrage_metal_m2=25_000,
        # Fondations — corrigé (investissementimmoafrique.com: ~100K Ø400-600 standard)
        pieu_fore_d600_ml=150_000,      # was 220K, marché ~100K Ø400-600 standard
        pieu_fore_d800_ml=200_000,      # was 285K, marché ~150K terrain difficile
        pieu_fore_d1000_ml=280_000,     # was 360K, extrapolation Ø800
        semelle_filante_ml=85_000,
        radier_m2=95_000,
        # Maçonnerie — corrigé (agglos ~389-1200 FCFA/unité × 13/m² + MO)
        agglo_creux_10_m2=12_000,       # was 18K, corrigé marché
        agglo_creux_15_m2=16_000,       # was 24K, corrigé marché
        agglo_creux_20_m2=30_000,       # validé
        agglo_plein_25_m2=38_000,       # validé
        brique_pleine_m2=52_000,        # validé
        ba13_simple_m2=22_000,          # was 28K, EU ~27-41€/m² mais MO Afrique ÷2-3
        ba13_double_m2=35_000,          # was 42K
        # Étanchéité — corrigé SBS (CYPE SBS: 6,744 FCFA/m²)
        etanch_sbs_m2=8_000,            # was 18.5K, CYPE: 6,744
        etanch_pvc_m2=22_000,           # validé (~CYPE 20,526)
        etanch_liquide_m2=12_000,       # validé
        # Terrassement — corrigé remblai (CYPE compacté: 15,600-16,600)
        terr_mecanique_m3=8_500,
        terr_manuel_m3=5_000,
        remblai_m3=15_000,              # was 6.5K, CYPE: 15,600-16,600
        # Main d'œuvre (FCFA/jour) — corrigé (investissementimmoafrique.com)
        mo_chef_chantier_j=10_000,      # was 35K, marché: ~8,000/j
        mo_macon_j=7_000,               # was 18K, marché: 5,000-7,000/j
        mo_ferrailleur_j=8_000,         # was 20K
        mo_electricien_j=9_000,         # was 22K
        mo_plombier_j=9_000,            # was 22K
        mo_manœuvre_j=3_000,            # was 8K, marché: 1,500-3,000/j
    ),
    mep=PrixMEP(
        # Électricité — corrigé
        tableau_general_bt=2_500_000,       # was 3.5M, EU ~400-1400€ × 2.5 markup
        transfo_160kva=22_000_000,
        transfo_250kva=32_000_000,
        transfo_400kva=48_000_000,
        groupe_electrogene_100kva=14_000_000,   # was 18M, source: 13.3M Dakar
        groupe_electrogene_200kva=22_000_000,   # was 32M, source: 15-25M range
        groupe_electrogene_400kva=42_000_000,   # was 58M, extrapolation
        compteur_monophase=150_000,             # was 180K, SENELEC ~4,689 + équipement ~140K
        compteur_triphase=280_000,
        canalisation_cuivre_ml=12_000,
        luminaire_led_standard=15_000,          # was 35K, Jumia: 8,600-12,500
        luminaire_led_premium=85_000,
        # Plomberie — corrigé
        colonne_montante_ml=22_000,
        tuyau_pvc_dn50_ml=8_500,
        tuyau_pvc_dn100_ml=8_000,               # was 14K, marché: ~3,500 brut + pose
        tuyau_pvc_dn150_ml=22_000,
        robinet_standard=25_000,                # was 45K, marché: 12-40K médiane + pose
        robinet_eco=45_000,                     # was 75K
        wc_standard=85_000,
        wc_double_chasse=130_000,
        cuve_eau_5000l=700_000,                 # was 850K, source: 690,000 TTC Dakar
        cuve_eau_10000l=1_300_000,              # was 1.5M
        pompe_surpresseur_1kw=450_000,
        pompe_surpresseur_3kw=850_000,
        chauffe_eau_electrique_100l=180_000,
        chauffe_eau_solaire_200l=650_000,       # was 2.1M, marché: thermosiphon 250-650K
        # CVC — corrigé (Jumia: split 1CV 155-228K + pose ~50K)
        split_1cv=250_000,                      # was 450K, Jumia: 155-228K + pose
        split_2cv=400_000,                      # was 750K, Jumia: 281-350K + pose
        split_cassette_4cv=1_800_000,
        vmc_simple_flux=320_000,
        vmc_double_flux=850_000,
        climatiseur_central_kw=280_000,
        # Ascenseurs (fournis posés) — corrigé (source: 6.5-15M FCFA Dakar)
        ascenseur_630kg_r4_r6=15_000_000,       # was 28M, source: 6.5-15M
        ascenseur_630kg_r7_r10=22_000_000,      # was 38M
        ascenseur_1000kg_r6_r10=30_000_000,     # was 45M
        ascenseur_1000kg_r11_plus=42_000_000,   # was 58M
        monte_charge_500kg=15_000_000,          # was 22M
        # Courants faibles — corrigé interphone
        cablage_rj45_ml=3_500,
        prise_rj45=18_000,
        baie_serveur_12u=850_000,
        camera_ip_interieure=180_000,
        camera_ip_exterieure=280_000,
        systeme_controle_acces=350_000,
        interphone_video=65_000,                # was 220K, Jumia: 26,500-250K médiane bâtiment
        # Sécurité incendie — corrigé
        detecteur_fumee=45_000,
        declencheur_manuel=35_000,
        sirene_flash=55_000,
        centrale_incendie_16zones=1_800_000,
        centrale_incendie_32zones=3_200_000,
        extincteur_6kg_co2=95_000,              # was 85K, source: 95K vérifié Dakar
        extincteur_9kg_poudre=50_000,           # was 65K, source: 45-55K
        ria_dn25_ml=45_000,
        sprinkler_tete=85_000,
        sprinkler_centrale=4_500_000,
        # Automatisation
        domotique_logement=850_000,
        bms_systeme=12_000_000,
        eclairage_detecteur_presence=95_000,
    )
)

# ══════════════════════════════════════════════════════════════
# ABIDJAN, CÔTE D'IVOIRE — Dakar ×1.10 (logistique port, BNETD)
# ══════════════════════════════════════════════════════════════
ABIDJAN = PrixPays(
    pays="Côte d'Ivoire",
    ville_reference="Abidjan",
    devise="XOF",
    date_maj="2026-04",
    fiabilite="estimation",
    notes="Estimation Dakar ×1.10 (logistique port Abidjan). Sources: BNETD, SICOGI. À confirmer terrain.",
    structure=PrixStructure(
        # Béton BPE (~Dakar +10%)
        beton_c2530_m3=187_000,
        beton_c3037_m3=204_000,
        beton_c3545_m3=231_000,
        beton_c4050_m3=264_000,
        # Acier (~Dakar +10%, transit port Abidjan)
        acier_ha400_kg=825,
        acier_ha500_kg=891,
        acier_ha500_vrac_kg=583,
        # Coffrage
        coffrage_bois_m2=20_000,
        coffrage_metal_m2=28_000,
        # Fondations (~Dakar +10%)
        pieu_fore_d600_ml=165_000,
        pieu_fore_d800_ml=220_000,
        pieu_fore_d1000_ml=308_000,
        semelle_filante_ml=94_000,
        radier_m2=105_000,
        # Maçonnerie (~Dakar +10%)
        agglo_creux_10_m2=13_200,
        agglo_creux_15_m2=17_600,
        agglo_creux_20_m2=33_000,
        agglo_plein_25_m2=42_000,
        brique_pleine_m2=57_200,
        ba13_simple_m2=24_200,
        ba13_double_m2=38_500,
        # Étanchéité
        etanch_sbs_m2=8_800,
        etanch_pvc_m2=24_200,
        etanch_liquide_m2=13_200,
        # Terrassement
        terr_mecanique_m3=9_400,
        terr_manuel_m3=5_500,
        remblai_m3=16_500,
        # MO (~Dakar +10%, salaires CI légèrement supérieurs SN)
        mo_chef_chantier_j=11_000,
        mo_macon_j=7_700,
        mo_ferrailleur_j=8_800,
        mo_electricien_j=9_900,
        mo_plombier_j=9_900,
        mo_manœuvre_j=3_300,
    ),
    mep=PrixMEP(
        # Électricité (~Dakar +10%)
        tableau_general_bt=2_750_000,
        transfo_160kva=24_200_000,
        transfo_250kva=35_200_000,
        transfo_400kva=52_800_000,
        groupe_electrogene_100kva=15_400_000,
        groupe_electrogene_200kva=24_200_000,
        groupe_electrogene_400kva=46_200_000,
        compteur_monophase=165_000,
        compteur_triphase=308_000,
        canalisation_cuivre_ml=13_200,
        luminaire_led_standard=16_500,
        luminaire_led_premium=93_500,
        # Plomberie
        colonne_montante_ml=24_200,
        tuyau_pvc_dn50_ml=9_400,
        tuyau_pvc_dn100_ml=8_800,
        tuyau_pvc_dn150_ml=24_200,
        robinet_standard=27_500,
        robinet_eco=49_500,
        wc_standard=93_500,
        wc_double_chasse=143_000,
        cuve_eau_5000l=770_000,
        cuve_eau_10000l=1_430_000,
        pompe_surpresseur_1kw=495_000,
        pompe_surpresseur_3kw=935_000,
        chauffe_eau_electrique_100l=198_000,
        chauffe_eau_solaire_200l=715_000,
        # CVC
        split_1cv=275_000,
        split_2cv=440_000,
        split_cassette_4cv=1_980_000,
        vmc_simple_flux=352_000,
        vmc_double_flux=935_000,
        climatiseur_central_kw=308_000,
        # Ascenseurs
        ascenseur_630kg_r4_r6=16_500_000,
        ascenseur_630kg_r7_r10=24_200_000,
        ascenseur_1000kg_r6_r10=33_000_000,
        ascenseur_1000kg_r11_plus=46_200_000,
        monte_charge_500kg=16_500_000,
        # Courants faibles
        cablage_rj45_ml=3_850,
        prise_rj45=19_800,
        baie_serveur_12u=935_000,
        camera_ip_interieure=198_000,
        camera_ip_exterieure=308_000,
        systeme_controle_acces=385_000,
        interphone_video=71_500,
        # Sécurité incendie
        detecteur_fumee=49_500,
        declencheur_manuel=38_500,
        sirene_flash=60_500,
        centrale_incendie_16zones=1_980_000,
        centrale_incendie_32zones=3_520_000,
        extincteur_6kg_co2=104_500,
        extincteur_9kg_poudre=55_000,
        ria_dn25_ml=49_500,
        sprinkler_tete=93_500,
        sprinkler_centrale=4_950_000,
        # Automatisation
        domotique_logement=935_000,
        bms_systeme=13_200_000,
        eclairage_detecteur_presence=104_500,
    )
)

# ══════════════════════════════════════════════════════════════
# CASABLANCA, MAROC — Corrigé Avril 2026
# ══════════════════════════════════════════════════════════════
CASABLANCA = PrixPays(
    pays="Maroc",
    ville_reference="Casablanca",
    devise="MAD",
    date_maj="2026-04",
    fiabilite="estimation",
    notes="Estimation basée sur CSMC, CPC Maroc, bordereau DPT. 1 MAD = 60.5 FCFA. Béton C30/37 corrigé à 1,050 MAD (marché ~1,066). Acier HA500 corrigé à 9.5 MAD/kg.",
    structure=PrixStructure(
        # Béton BPE (MAD/m³ → stocké en FCFA équivalent) — corrigé
        beton_c2530_m3=int(to_fcfa(900, "MAD")),     # ~900 MAD/m³ (proportionnel)
        beton_c3037_m3=int(to_fcfa(1_050, "MAD")),   # corrigé: marché ~1,066 MAD/m³
        beton_c3545_m3=int(to_fcfa(1_200, "MAD")),   # proportionnel
        beton_c4050_m3=int(to_fcfa(1_400, "MAD")),   # proportionnel
        # Acier (MAD/kg — production locale Sonasid/Longometal) — corrigé
        acier_ha400_kg=int(to_fcfa(8.5, "MAD")),     # proportionnel à HA500
        acier_ha500_kg=int(to_fcfa(9.5, "MAD")),     # corrigé: marché 9-10.5 MAD/kg
        acier_ha500_vrac_kg=int(to_fcfa(7.8, "MAD")),
        coffrage_bois_m2=int(to_fcfa(120, "MAD")),
        coffrage_metal_m2=int(to_fcfa(180, "MAD")),
        pieu_fore_d600_ml=int(to_fcfa(1_800, "MAD")),
        pieu_fore_d800_ml=int(to_fcfa(2_400, "MAD")),
        pieu_fore_d1000_ml=int(to_fcfa(3_200, "MAD")),
        semelle_filante_ml=int(to_fcfa(750, "MAD")),
        radier_m2=int(to_fcfa(850, "MAD")),
        agglo_creux_10_m2=int(to_fcfa(180, "MAD")),
        agglo_creux_15_m2=int(to_fcfa(220, "MAD")),
        agglo_creux_20_m2=int(to_fcfa(280, "MAD")),
        agglo_plein_25_m2=int(to_fcfa(350, "MAD")),
        brique_pleine_m2=int(to_fcfa(420, "MAD")),
        ba13_simple_m2=int(to_fcfa(280, "MAD")),
        ba13_double_m2=int(to_fcfa(420, "MAD")),
        etanch_sbs_m2=int(to_fcfa(180, "MAD")),
        etanch_pvc_m2=int(to_fcfa(220, "MAD")),
        etanch_liquide_m2=int(to_fcfa(120, "MAD")),
        terr_mecanique_m3=int(to_fcfa(85, "MAD")),
        terr_manuel_m3=int(to_fcfa(50, "MAD")),
        remblai_m3=int(to_fcfa(65, "MAD")),
        mo_chef_chantier_j=int(to_fcfa(500, "MAD")),
        mo_macon_j=int(to_fcfa(280, "MAD")),
        mo_ferrailleur_j=int(to_fcfa(300, "MAD")),
        mo_electricien_j=int(to_fcfa(350, "MAD")),
        mo_plombier_j=int(to_fcfa(350, "MAD")),
        mo_manœuvre_j=int(to_fcfa(150, "MAD")),
    ),
    mep=PrixMEP(
        tableau_general_bt=int(to_fcfa(55_000, "MAD")),
        transfo_160kva=int(to_fcfa(380_000, "MAD")),
        transfo_250kva=int(to_fcfa(560_000, "MAD")),
        transfo_400kva=int(to_fcfa(820_000, "MAD")),
        groupe_electrogene_100kva=int(to_fcfa(320_000, "MAD")),
        groupe_electrogene_200kva=int(to_fcfa(580_000, "MAD")),
        groupe_electrogene_400kva=int(to_fcfa(980_000, "MAD")),
        compteur_monophase=int(to_fcfa(3_500, "MAD")),
        compteur_triphase=int(to_fcfa(5_500, "MAD")),
        canalisation_cuivre_ml=int(to_fcfa(220, "MAD")),
        luminaire_led_standard=int(to_fcfa(650, "MAD")),
        luminaire_led_premium=int(to_fcfa(1_800, "MAD")),
        colonne_montante_ml=int(to_fcfa(420, "MAD")),
        tuyau_pvc_dn50_ml=int(to_fcfa(160, "MAD")),
        tuyau_pvc_dn100_ml=int(to_fcfa(280, "MAD")),
        tuyau_pvc_dn150_ml=int(to_fcfa(420, "MAD")),
        robinet_standard=int(to_fcfa(850, "MAD")),
        robinet_eco=int(to_fcfa(1_400, "MAD")),
        wc_standard=int(to_fcfa(1_600, "MAD")),
        wc_double_chasse=int(to_fcfa(2_500, "MAD")),
        cuve_eau_5000l=int(to_fcfa(15_000, "MAD")),
        cuve_eau_10000l=int(to_fcfa(26_000, "MAD")),
        pompe_surpresseur_1kw=int(to_fcfa(8_500, "MAD")),
        pompe_surpresseur_3kw=int(to_fcfa(15_000, "MAD")),
        chauffe_eau_electrique_100l=int(to_fcfa(3_200, "MAD")),
        chauffe_eau_solaire_200l=int(to_fcfa(38_000, "MAD")),
        split_1cv=int(to_fcfa(8_500, "MAD")),
        split_2cv=int(to_fcfa(14_000, "MAD")),
        split_cassette_4cv=int(to_fcfa(32_000, "MAD")),
        vmc_simple_flux=int(to_fcfa(6_500, "MAD")),
        vmc_double_flux=int(to_fcfa(16_000, "MAD")),
        climatiseur_central_kw=int(to_fcfa(4_800, "MAD")),
        ascenseur_630kg_r4_r6=int(to_fcfa(480_000, "MAD")),
        ascenseur_630kg_r7_r10=int(to_fcfa(650_000, "MAD")),
        ascenseur_1000kg_r6_r10=int(to_fcfa(780_000, "MAD")),
        ascenseur_1000kg_r11_plus=int(to_fcfa(980_000, "MAD")),
        monte_charge_500kg=int(to_fcfa(380_000, "MAD")),
        cablage_rj45_ml=int(to_fcfa(65, "MAD")),
        prise_rj45=int(to_fcfa(380, "MAD")),
        baie_serveur_12u=int(to_fcfa(16_000, "MAD")),
        camera_ip_interieure=int(to_fcfa(3_500, "MAD")),
        camera_ip_exterieure=int(to_fcfa(5_500, "MAD")),
        systeme_controle_acces=int(to_fcfa(7_500, "MAD")),
        interphone_video=int(to_fcfa(4_500, "MAD")),
        detecteur_fumee=int(to_fcfa(850, "MAD")),
        declencheur_manuel=int(to_fcfa(650, "MAD")),
        sirene_flash=int(to_fcfa(1_200, "MAD")),
        centrale_incendie_16zones=int(to_fcfa(35_000, "MAD")),
        centrale_incendie_32zones=int(to_fcfa(62_000, "MAD")),
        extincteur_6kg_co2=int(to_fcfa(1_800, "MAD")),
        extincteur_9kg_poudre=int(to_fcfa(1_200, "MAD")),
        ria_dn25_ml=int(to_fcfa(850, "MAD")),
        sprinkler_tete=int(to_fcfa(1_800, "MAD")),
        sprinkler_centrale=int(to_fcfa(85_000, "MAD")),
        domotique_logement=int(to_fcfa(18_000, "MAD")),
        bms_systeme=int(to_fcfa(220_000, "MAD")),
        eclairage_detecteur_presence=int(to_fcfa(2_200, "MAD")),
    )
)

# ══════════════════════════════════════════════════════════════
# LAGOS, NIGERIA — Corrigé Avril 2026
# ⚠ Taux NGN très volatile — vérifier mensuellement
# ══════════════════════════════════════════════════════════════
LAGOS = PrixPays(
    pays="Nigeria",
    ville_reference="Lagos",
    devise="NGN",
    date_maj="2026-04",
    fiabilite="estimation",
    notes=(
        "Estimation basée sur NBRRI, NIOB, Builders Magazine Nigeria. "
        "Marché TRÈS volatile (NGN instable). 1 NGN = 0.48 FCFA. "
        "Béton C25/30 corrigé de 420K à 160K NGN (marché: 75-90K brut + MO). "
        "À confirmer terrain urgence."
    ),
    structure=PrixStructure(
        # NGN/m³ → FCFA — corrigé: C25/30 = 160K NGN (marché 75-90K brut + MO)
        # Ratio correction: 160/420 = 0.38, appliqué proportionnellement
        beton_c2530_m3=int(to_fcfa(160_000, "NGN")),   # was 420K, corrigé
        beton_c3037_m3=int(to_fcfa(183_000, "NGN")),   # proportionnel
        beton_c3545_m3=int(to_fcfa(213_000, "NGN")),   # proportionnel
        beton_c4050_m3=int(to_fcfa(248_000, "NGN")),   # proportionnel
        acier_ha400_kg=int(to_fcfa(1_850, "NGN")),
        acier_ha500_kg=int(to_fcfa(2_100, "NGN")),
        acier_ha500_vrac_kg=int(to_fcfa(1_600, "NGN")),
        coffrage_bois_m2=int(to_fcfa(45_000, "NGN")),
        coffrage_metal_m2=int(to_fcfa(65_000, "NGN")),
        pieu_fore_d600_ml=int(to_fcfa(580_000, "NGN")),
        pieu_fore_d800_ml=int(to_fcfa(780_000, "NGN")),
        pieu_fore_d1000_ml=int(to_fcfa(1_050_000, "NGN")),
        semelle_filante_ml=int(to_fcfa(220_000, "NGN")),
        radier_m2=int(to_fcfa(280_000, "NGN")),
        agglo_creux_10_m2=int(to_fcfa(48_000, "NGN")),
        agglo_creux_15_m2=int(to_fcfa(62_000, "NGN")),
        agglo_creux_20_m2=int(to_fcfa(78_000, "NGN")),
        agglo_plein_25_m2=int(to_fcfa(95_000, "NGN")),
        brique_pleine_m2=int(to_fcfa(120_000, "NGN")),
        ba13_simple_m2=int(to_fcfa(85_000, "NGN")),
        ba13_double_m2=int(to_fcfa(130_000, "NGN")),
        etanch_sbs_m2=int(to_fcfa(55_000, "NGN")),
        etanch_pvc_m2=int(to_fcfa(68_000, "NGN")),
        etanch_liquide_m2=int(to_fcfa(38_000, "NGN")),
        terr_mecanique_m3=int(to_fcfa(28_000, "NGN")),
        terr_manuel_m3=int(to_fcfa(15_000, "NGN")),
        remblai_m3=int(to_fcfa(20_000, "NGN")),
        mo_chef_chantier_j=int(to_fcfa(120_000, "NGN")),
        mo_macon_j=int(to_fcfa(65_000, "NGN")),
        mo_ferrailleur_j=int(to_fcfa(72_000, "NGN")),
        mo_electricien_j=int(to_fcfa(85_000, "NGN")),
        mo_plombier_j=int(to_fcfa(85_000, "NGN")),
        mo_manœuvre_j=int(to_fcfa(28_000, "NGN")),
    ),
    mep=PrixMEP(
        tableau_general_bt=int(to_fcfa(12_000_000, "NGN")),
        transfo_160kva=int(to_fcfa(85_000_000, "NGN")),
        transfo_250kva=int(to_fcfa(125_000_000, "NGN")),
        transfo_400kva=int(to_fcfa(185_000_000, "NGN")),
        groupe_electrogene_100kva=int(to_fcfa(75_000_000, "NGN")),
        groupe_electrogene_200kva=int(to_fcfa(130_000_000, "NGN")),
        groupe_electrogene_400kva=int(to_fcfa(220_000_000, "NGN")),
        compteur_monophase=int(to_fcfa(650_000, "NGN")),
        compteur_triphase=int(to_fcfa(1_100_000, "NGN")),
        canalisation_cuivre_ml=int(to_fcfa(48_000, "NGN")),
        luminaire_led_standard=int(to_fcfa(145_000, "NGN")),
        luminaire_led_premium=int(to_fcfa(380_000, "NGN")),
        colonne_montante_ml=int(to_fcfa(95_000, "NGN")),
        tuyau_pvc_dn50_ml=int(to_fcfa(38_000, "NGN")),
        tuyau_pvc_dn100_ml=int(to_fcfa(62_000, "NGN")),
        tuyau_pvc_dn150_ml=int(to_fcfa(95_000, "NGN")),
        robinet_standard=int(to_fcfa(185_000, "NGN")),
        robinet_eco=int(to_fcfa(320_000, "NGN")),
        wc_standard=int(to_fcfa(380_000, "NGN")),
        wc_double_chasse=int(to_fcfa(580_000, "NGN")),
        cuve_eau_5000l=int(to_fcfa(3_800_000, "NGN")),
        cuve_eau_10000l=int(to_fcfa(6_500_000, "NGN")),
        pompe_surpresseur_1kw=int(to_fcfa(2_200_000, "NGN")),
        pompe_surpresseur_3kw=int(to_fcfa(4_500_000, "NGN")),
        chauffe_eau_electrique_100l=int(to_fcfa(850_000, "NGN")),
        chauffe_eau_solaire_200l=int(to_fcfa(9_500_000, "NGN")),
        split_1cv=int(to_fcfa(2_200_000, "NGN")),
        split_2cv=int(to_fcfa(3_800_000, "NGN")),
        split_cassette_4cv=int(to_fcfa(8_500_000, "NGN")),
        vmc_simple_flux=int(to_fcfa(1_800_000, "NGN")),
        vmc_double_flux=int(to_fcfa(4_200_000, "NGN")),
        climatiseur_central_kw=int(to_fcfa(1_350_000, "NGN")),
        ascenseur_630kg_r4_r6=int(to_fcfa(120_000_000, "NGN")),
        ascenseur_630kg_r7_r10=int(to_fcfa(165_000_000, "NGN")),
        ascenseur_1000kg_r6_r10=int(to_fcfa(200_000_000, "NGN")),
        ascenseur_1000kg_r11_plus=int(to_fcfa(260_000_000, "NGN")),
        monte_charge_500kg=int(to_fcfa(95_000_000, "NGN")),
        cablage_rj45_ml=int(to_fcfa(14_000, "NGN")),
        prise_rj45=int(to_fcfa(85_000, "NGN")),
        baie_serveur_12u=int(to_fcfa(3_800_000, "NGN")),
        camera_ip_interieure=int(to_fcfa(850_000, "NGN")),
        camera_ip_exterieure=int(to_fcfa(1_400_000, "NGN")),
        systeme_controle_acces=int(to_fcfa(1_800_000, "NGN")),
        interphone_video=int(to_fcfa(1_050_000, "NGN")),
        detecteur_fumee=int(to_fcfa(220_000, "NGN")),
        declencheur_manuel=int(to_fcfa(165_000, "NGN")),
        sirene_flash=int(to_fcfa(280_000, "NGN")),
        centrale_incendie_16zones=int(to_fcfa(8_500_000, "NGN")),
        centrale_incendie_32zones=int(to_fcfa(15_000_000, "NGN")),
        extincteur_6kg_co2=int(to_fcfa(420_000, "NGN")),
        extincteur_9kg_poudre=int(to_fcfa(320_000, "NGN")),
        ria_dn25_ml=int(to_fcfa(220_000, "NGN")),
        sprinkler_tete=int(to_fcfa(420_000, "NGN")),
        sprinkler_centrale=int(to_fcfa(22_000_000, "NGN")),
        domotique_logement=int(to_fcfa(4_200_000, "NGN")),
        bms_systeme=int(to_fcfa(58_000_000, "NGN")),
        eclairage_detecteur_presence=int(to_fcfa(480_000, "NGN")),
    )
)

# ══════════════════════════════════════════════════════════════
# ACCRA, GHANA — Corrigé Avril 2026
# ══════════════════════════════════════════════════════════════
ACCRA = PrixPays(
    pays="Ghana",
    ville_reference="Accra",
    devise="GHS",
    date_maj="2026-04",
    fiabilite="estimation",
    notes=(
        "Estimation basée sur Ghana Institute of Engineers, GIBB Africa. 1 GHS = 57 FCFA. "
        "Béton C30/37 corrigé de 3,600 à 1,800 GHS (marché: 1,400-1,800). "
        "Acier HA500 corrigé de 16 à 5 GHS/kg (marché: 3.8-4.5/tonne équiv)."
    ),
    structure=PrixStructure(
        # Béton — corrigé: C30/37 = 1,800 GHS (marché 1,400-1,800)
        # Ratio correction: 1800/3600 = 0.50, appliqué proportionnellement
        beton_c2530_m3=int(to_fcfa(1_600, "GHS")),    # was 3,200
        beton_c3037_m3=int(to_fcfa(1_800, "GHS")),    # was 3,600, corrigé
        beton_c3545_m3=int(to_fcfa(2_100, "GHS")),    # was 4,200
        beton_c4050_m3=int(to_fcfa(2_450, "GHS")),    # was 4,900
        # Acier — corrigé: HA500 = 5 GHS/kg (marché 3.8-4.5/tonne)
        acier_ha400_kg=int(to_fcfa(4.5, "GHS")),      # was 14
        acier_ha500_kg=int(to_fcfa(5, "GHS")),         # was 16, corrigé
        acier_ha500_vrac_kg=int(to_fcfa(3.8, "GHS")), # was 12
        coffrage_bois_m2=int(to_fcfa(320, "GHS")),
        coffrage_metal_m2=int(to_fcfa(480, "GHS")),
        pieu_fore_d600_ml=int(to_fcfa(4_200, "GHS")),
        pieu_fore_d800_ml=int(to_fcfa(5_800, "GHS")),
        pieu_fore_d1000_ml=int(to_fcfa(7_800, "GHS")),
        semelle_filante_ml=int(to_fcfa(1_600, "GHS")),
        radier_m2=int(to_fcfa(1_850, "GHS")),
        agglo_creux_10_m2=int(to_fcfa(340, "GHS")),
        agglo_creux_15_m2=int(to_fcfa(420, "GHS")),
        agglo_creux_20_m2=int(to_fcfa(520, "GHS")),
        agglo_plein_25_m2=int(to_fcfa(650, "GHS")),
        brique_pleine_m2=int(to_fcfa(820, "GHS")),
        ba13_simple_m2=int(to_fcfa(580, "GHS")),
        ba13_double_m2=int(to_fcfa(880, "GHS")),
        etanch_sbs_m2=int(to_fcfa(380, "GHS")),
        etanch_pvc_m2=int(to_fcfa(460, "GHS")),
        etanch_liquide_m2=int(to_fcfa(260, "GHS")),
        terr_mecanique_m3=int(to_fcfa(180, "GHS")),
        terr_manuel_m3=int(to_fcfa(95, "GHS")),
        remblai_m3=int(to_fcfa(130, "GHS")),
        mo_chef_chantier_j=int(to_fcfa(850, "GHS")),
        mo_macon_j=int(to_fcfa(480, "GHS")),
        mo_ferrailleur_j=int(to_fcfa(520, "GHS")),
        mo_electricien_j=int(to_fcfa(620, "GHS")),
        mo_plombier_j=int(to_fcfa(620, "GHS")),
        mo_manœuvre_j=int(to_fcfa(220, "GHS")),
    ),
    mep=PrixMEP(
        tableau_general_bt=int(to_fcfa(82_000, "GHS")),
        transfo_160kva=int(to_fcfa(580_000, "GHS")),
        transfo_250kva=int(to_fcfa(850_000, "GHS")),
        transfo_400kva=int(to_fcfa(1_280_000, "GHS")),
        groupe_electrogene_100kva=int(to_fcfa(520_000, "GHS")),
        groupe_electrogene_200kva=int(to_fcfa(920_000, "GHS")),
        groupe_electrogene_400kva=int(to_fcfa(1_580_000, "GHS")),
        compteur_monophase=int(to_fcfa(4_800, "GHS")),
        compteur_triphase=int(to_fcfa(8_200, "GHS")),
        canalisation_cuivre_ml=int(to_fcfa(340, "GHS")),
        luminaire_led_standard=int(to_fcfa(980, "GHS")),
        luminaire_led_premium=int(to_fcfa(2_600, "GHS")),
        colonne_montante_ml=int(to_fcfa(650, "GHS")),
        tuyau_pvc_dn50_ml=int(to_fcfa(240, "GHS")),
        tuyau_pvc_dn100_ml=int(to_fcfa(420, "GHS")),
        tuyau_pvc_dn150_ml=int(to_fcfa(650, "GHS")),
        robinet_standard=int(to_fcfa(1_280, "GHS")),
        robinet_eco=int(to_fcfa(2_100, "GHS")),
        wc_standard=int(to_fcfa(2_400, "GHS")),
        wc_double_chasse=int(to_fcfa(3_800, "GHS")),
        cuve_eau_5000l=int(to_fcfa(22_000, "GHS")),
        cuve_eau_10000l=int(to_fcfa(38_000, "GHS")),
        pompe_surpresseur_1kw=int(to_fcfa(12_000, "GHS")),
        pompe_surpresseur_3kw=int(to_fcfa(22_000, "GHS")),
        chauffe_eau_electrique_100l=int(to_fcfa(4_800, "GHS")),
        chauffe_eau_solaire_200l=int(to_fcfa(56_000, "GHS")),
        split_1cv=int(to_fcfa(12_500, "GHS")),
        split_2cv=int(to_fcfa(21_000, "GHS")),
        split_cassette_4cv=int(to_fcfa(48_000, "GHS")),
        vmc_simple_flux=int(to_fcfa(9_500, "GHS")),
        vmc_double_flux=int(to_fcfa(24_000, "GHS")),
        climatiseur_central_kw=int(to_fcfa(7_200, "GHS")),
        ascenseur_630kg_r4_r6=int(to_fcfa(720_000, "GHS")),
        ascenseur_630kg_r7_r10=int(to_fcfa(980_000, "GHS")),
        ascenseur_1000kg_r6_r10=int(to_fcfa(1_180_000, "GHS")),
        ascenseur_1000kg_r11_plus=int(to_fcfa(1_520_000, "GHS")),
        monte_charge_500kg=int(to_fcfa(580_000, "GHS")),
        cablage_rj45_ml=int(to_fcfa(98, "GHS")),
        prise_rj45=int(to_fcfa(580, "GHS")),
        baie_serveur_12u=int(to_fcfa(24_000, "GHS")),
        camera_ip_interieure=int(to_fcfa(5_200, "GHS")),
        camera_ip_exterieure=int(to_fcfa(8_500, "GHS")),
        systeme_controle_acces=int(to_fcfa(11_000, "GHS")),
        interphone_video=int(to_fcfa(6_500, "GHS")),
        detecteur_fumee=int(to_fcfa(1_280, "GHS")),
        declencheur_manuel=int(to_fcfa(980, "GHS")),
        sirene_flash=int(to_fcfa(1_800, "GHS")),
        centrale_incendie_16zones=int(to_fcfa(52_000, "GHS")),
        centrale_incendie_32zones=int(to_fcfa(92_000, "GHS")),
        extincteur_6kg_co2=int(to_fcfa(2_600, "GHS")),
        extincteur_9kg_poudre=int(to_fcfa(1_900, "GHS")),
        ria_dn25_ml=int(to_fcfa(1_280, "GHS")),
        sprinkler_tete=int(to_fcfa(2_600, "GHS")),
        sprinkler_centrale=int(to_fcfa(130_000, "GHS")),
        domotique_logement=int(to_fcfa(26_000, "GHS")),
        bms_systeme=int(to_fcfa(340_000, "GHS")),
        eclairage_detecteur_presence=int(to_fcfa(3_200, "GHS")),
    )
)

# ══════════════════════════════════════════════════════════════
# INDEX PAYS
# ══════════════════════════════════════════════════════════════
PAYS = {
    "dakar":       DAKAR,
    "senegal":     DAKAR,
    "abidjan":     ABIDJAN,
    "cote_ivoire": ABIDJAN,
    "casablanca":  CASABLANCA,
    "rabat":       CASABLANCA,  # Rabat ≈ Casablanca + 5%
    "maroc":       CASABLANCA,
    "lagos":       LAGOS,
    "abuja":       LAGOS,
    "nigeria":     LAGOS,
    "accra":       ACCRA,
    "ghana":       ACCRA,
}

def get_prix(ville: str) -> PrixPays:
    """
    Retourne la grille de prix pour une ville donnée.
    Fallback sur Dakar si ville inconnue.
    """
    key = ville.lower().strip()
    # Correspondance partielle
    for k, v in PAYS.items():
        if k in key or key in k:
            return v
    return DAKAR  # fallback

def get_prix_structure(ville: str) -> PrixStructure:
    return get_prix(ville).structure

def get_prix_mep(ville: str) -> PrixMEP:
    return get_prix(ville).mep

def comparer_prix(poste: str, villes: list = None) -> dict:
    """
    Compare un poste de prix entre plusieurs villes.
    Utile pour le rapport multi-pays.
    """
    if villes is None:
        villes = ["dakar", "abidjan", "casablanca", "lagos", "accra"]
    result = {}
    for v in villes:
        p = get_prix(v)
        val_s = getattr(p.structure, poste, None)
        val_m = getattr(p.mep, poste, None)
        val = val_s or val_m
        if val:
            result[p.ville_reference] = {
                "prix_fcfa": val,
                "devise": p.devise,
                "fiabilite": p.fiabilite,
            }
    return result


# ══════════════════════════════════════════════════════════════
# JUSTIFICATIONS DES PRIX — Sources et méthodologie
# ══════════════════════════════════════════════════════════════
JUSTIFICATIONS = {
    # ── STRUCTURE — BÉTON ──
    "beton_c2530_m3": {
        "methode": "BPE 350kg/m³ fourni posé incluant pompage, vibration et MO coulage",
        "source_dakar": "Validé terrain Malick Tall + CIMAF/SOCOCIM Mars 2026",
        "source_abidjan": "Dakar ×1.10 (logistique port, BNETD)",
        "source_casablanca": "CSMC/CPC Maroc ~900 MAD/m³",
        "source_lagos": "NBRRI estimation, très volatile (NGN instable)",
        "source_accra": "Ghana Institute of Engineers ~1,600 GHS/m³",
        "fiabilite": "haute",
    },
    "beton_c3037_m3": {
        "methode": "BPE 400kg/m³ fourni posé, standard R+4 à R+8",
        "source_dakar": "Validé terrain Malick Tall — 185,000 FCFA Sakho R+8",
        "source_abidjan": "Dakar ×1.10",
        "source_casablanca": "Corrigé à 1,050 MAD (marché ~1,066 MAD confirmé)",
        "source_lagos": "Corrigé 183K NGN (ratio 160/420 sur C25/30)",
        "source_accra": "Corrigé 1,800 GHS (marché 1,400-1,800)",
        "fiabilite": "haute",
    },
    "beton_c3545_m3": {
        "methode": "BPE haute résistance, R+9 et plus",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    "beton_c4050_m3": {
        "methode": "BPE très haute résistance, tours et IGH",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    # ── STRUCTURE — ACIER ──
    "acier_ha400_kg": {
        "methode": "Acier HA400 fourni posé façonné, petits ouvrages R+1-R+3",
        "source_dakar": "Validé terrain — Fabrimetal",
        "fiabilite": "haute",
    },
    "acier_ha500_kg": {
        "methode": "Acier HA500 fourni posé façonné, standard résidentiel",
        "source_dakar": "Validé terrain — 810 FCFA/kg Fabrimetal",
        "source_casablanca": "Corrigé 9.5 MAD/kg (marché 9-10.5 MAD, Sonasid)",
        "source_accra": "Corrigé 5 GHS/kg (marché 3.8-4.5 GHS/tonne équivalent)",
        "fiabilite": "haute",
    },
    "acier_ha500_vrac_kg": {
        "methode": "Acier HA500 vrac sans façonnage",
        "source_dakar": "Validé terrain — 530 FCFA/kg",
        "fiabilite": "haute",
    },
    # ── STRUCTURE — COFFRAGE ──
    "coffrage_bois_m2": {
        "methode": "Coffrage traditionnel bois, incluant MO",
        "source_dakar": "Estimation raisonnable — pas de donnée directe",
        "fiabilite": "moyenne",
    },
    "coffrage_metal_m2": {
        "methode": "Coffrage métallique réutilisable",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    # ── STRUCTURE — FONDATIONS ──
    "pieu_fore_d600_ml": {
        "methode": "Pieu foré Ø600mm incluant forage, ferraillage, bétonnage",
        "source_dakar": "Corrigé 150K (was 220K). investissementimmoafrique.com: ~100K Ø400-600 standard",
        "fiabilite": "moyenne",
    },
    "pieu_fore_d800_ml": {
        "methode": "Pieu foré Ø800mm, terrain difficile",
        "source_dakar": "Corrigé 200K (was 285K). Marché ~150K terrain difficile",
        "fiabilite": "moyenne",
    },
    "pieu_fore_d1000_ml": {
        "methode": "Pieu foré Ø1000mm, extrapolation",
        "source_dakar": "Corrigé 280K (was 360K). Extrapolation ×1.4 du Ø800",
        "fiabilite": "basse",
    },
    "semelle_filante_ml": {
        "methode": "Semelle filante béton armé, fouille + coffrage + BA",
        "source_dakar": "Estimation",
        "fiabilite": "moyenne",
    },
    "radier_m2": {
        "methode": "Radier général béton armé",
        "source_dakar": "Estimation",
        "fiabilite": "moyenne",
    },
    # ── STRUCTURE — MAÇONNERIE ──
    "agglo_creux_10_m2": {
        "methode": "Agglos creux 10cm posés avec mortier. ~13 agglos/m² + mortier + MO",
        "source_dakar": "Corrigé 12K (was 18K). Agglos ~389-1200 FCFA/unité, MO ~3K/j",
        "fiabilite": "moyenne",
    },
    "agglo_creux_15_m2": {
        "methode": "Agglos creux 15cm posés avec mortier",
        "source_dakar": "Corrigé 16K (was 24K). Proportionnel au 10cm",
        "fiabilite": "moyenne",
    },
    "agglo_creux_20_m2": {
        "methode": "Agglos creux 20cm posés avec mortier, murs porteurs",
        "source_dakar": "Validé terrain — 30,000 FCFA/m²",
        "fiabilite": "haute",
    },
    "agglo_plein_25_m2": {
        "methode": "Agglos pleins 25cm, façades",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    "brique_pleine_m2": {
        "methode": "Briques pleines premium",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    "ba13_simple_m2": {
        "methode": "Cloison BA13 simple rail, fourni posé",
        "source_dakar": "Corrigé 22K (was 28K). EU ~27-41 EUR/m², Afrique matériaux similaires mais MO ÷2-3",
        "fiabilite": "moyenne",
    },
    "ba13_double_m2": {
        "methode": "Cloison BA13 double rail séparatif",
        "source_dakar": "Corrigé 35K (was 42K). Proportionnel au simple",
        "fiabilite": "moyenne",
    },
    # ── STRUCTURE — ÉTANCHÉITÉ ──
    "etanch_sbs_m2": {
        "methode": "Étanchéité SBS bicouche toiture terrasse",
        "source_dakar": "Corrigé 8K (was 18.5K). CYPE Sénégal: 6,744 FCFA/m²",
        "fiabilite": "haute",
    },
    "etanch_pvc_m2": {
        "methode": "Membrane PVC toiture",
        "source_dakar": "Validé — 22K (CYPE ~20,526)",
        "fiabilite": "haute",
    },
    "etanch_liquide_m2": {
        "methode": "Étanchéité liquide salles de bain",
        "source_dakar": "Validé terrain",
        "fiabilite": "haute",
    },
    # ── STRUCTURE — TERRASSEMENT ──
    "terr_mecanique_m3": {
        "methode": "Terrassement mécanique (pelle + camion)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "terr_manuel_m3": {
        "methode": "Terrassement manuel",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "remblai_m3": {
        "methode": "Remblai compacté en place",
        "source_dakar": "Corrigé 15K (was 6.5K). CYPE compacté: 15,600-16,600 FCFA/m³",
        "fiabilite": "haute",
    },
    # ── STRUCTURE — MAIN D'OEUVRE ──
    "mo_chef_chantier_j": {
        "methode": "Chef de chantier expérimenté, tarif journalier",
        "source_dakar": "Corrigé 10K (was 35K). investissementimmoafrique.com: ~8,000/j",
        "fiabilite": "haute",
    },
    "mo_macon_j": {
        "methode": "Maçon qualifié, tarif journalier",
        "source_dakar": "Corrigé 7K (was 18K). Marché: 5,000-7,000/j",
        "fiabilite": "haute",
    },
    "mo_ferrailleur_j": {
        "methode": "Ferrailleur qualifié, tarif journalier",
        "source_dakar": "Corrigé 8K (was 20K). Proportionnel maçon qualifié",
        "fiabilite": "moyenne",
    },
    "mo_electricien_j": {
        "methode": "Électricien qualifié, tarif journalier",
        "source_dakar": "Corrigé 9K (was 22K). Spécialiste légèrement au-dessus maçon",
        "fiabilite": "moyenne",
    },
    "mo_plombier_j": {
        "methode": "Plombier qualifié, tarif journalier",
        "source_dakar": "Corrigé 9K (was 22K). Comme électricien",
        "fiabilite": "moyenne",
    },
    "mo_manœuvre_j": {
        "methode": "Manoeuvre non qualifié, tarif journalier",
        "source_dakar": "Corrigé 3K (was 8K). Marché: 1,500-3,000/j",
        "fiabilite": "haute",
    },
    # ── MEP — ÉLECTRICITÉ ──
    "tableau_general_bt": {
        "methode": "TGBT complet câblé, forfait petit immeuble",
        "source_dakar": "Corrigé 2.5M (was 3.5M). EU ~400-1,400 EUR × 2.5 markup Afrique",
        "fiabilite": "moyenne",
    },
    "transfo_160kva": {
        "methode": "Transformateur HTA/BT 160kVA fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "transfo_250kva": {
        "methode": "Transformateur HTA/BT 250kVA fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "transfo_400kva": {
        "methode": "Transformateur HTA/BT 400kVA fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "groupe_electrogene_100kva": {
        "methode": "Groupe électrogène 100kVA diesel fourni posé",
        "source_dakar": "Corrigé 14M (was 18M). Source: 13.3M Dakar confirmé",
        "fiabilite": "haute",
    },
    "groupe_electrogene_200kva": {
        "methode": "Groupe électrogène 200kVA diesel fourni posé",
        "source_dakar": "Corrigé 22M (was 32M). Source: range 15-25M",
        "fiabilite": "moyenne",
    },
    "groupe_electrogene_400kva": {
        "methode": "Groupe électrogène 400kVA diesel fourni posé",
        "source_dakar": "Corrigé 42M (was 58M). Extrapolation du 200kVA",
        "fiabilite": "basse",
    },
    "compteur_monophase": {
        "methode": "Compteur + coffret monophasé par logement",
        "source_dakar": "Corrigé 150K (was 180K). SENELEC fees ~4,689 + équipement ~140K",
        "fiabilite": "moyenne",
    },
    "compteur_triphase": {
        "methode": "Compteur + coffret triphasé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "canalisation_cuivre_ml": {
        "methode": "Câblage cuivre moyen section, fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "luminaire_led_standard": {
        "methode": "Luminaire LED plafonnier standard",
        "source_dakar": "Corrigé 15K (was 35K). Jumia: 8,600-12,500 FCFA",
        "fiabilite": "haute",
    },
    "luminaire_led_premium": {
        "methode": "Luminaire LED premium design",
        "source_dakar": "Estimation",
        "fiabilite": "moyenne",
    },
    # ── MEP — PLOMBERIE ──
    "colonne_montante_ml": {
        "methode": "Colonne montante acier galvanisé, fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "tuyau_pvc_dn50_ml": {
        "methode": "Tuyau PVC DN50 fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "tuyau_pvc_dn100_ml": {
        "methode": "Tuyau PVC DN100 fourni posé",
        "source_dakar": "Corrigé 8K (was 14K). Marché: ~3,500 brut + pose ~4,500",
        "fiabilite": "moyenne",
    },
    "tuyau_pvc_dn150_ml": {
        "methode": "Tuyau PVC DN150 fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "robinet_standard": {
        "methode": "Robinet mélangeur standard fourni posé",
        "source_dakar": "Corrigé 25K (was 45K). Marché: 12-40K, médiane avec pose",
        "fiabilite": "moyenne",
    },
    "robinet_eco": {
        "methode": "Robinet économique 6L/min fourni posé",
        "source_dakar": "Corrigé 45K (was 75K). Premium éco au-dessus du standard",
        "fiabilite": "moyenne",
    },
    "wc_standard": {
        "methode": "WC céramique standard fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "wc_double_chasse": {
        "methode": "WC double chasse 3/6L fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "cuve_eau_5000l": {
        "methode": "Citerne polyéthylène 5000L fournie posée",
        "source_dakar": "Corrigé 700K (was 850K). Source: 690,000 TTC Dakar vérifié",
        "fiabilite": "haute",
    },
    "cuve_eau_10000l": {
        "methode": "Citerne polyéthylène 10000L fournie posée",
        "source_dakar": "Corrigé 1.3M (was 1.5M). Proportionnel 5000L",
        "fiabilite": "moyenne",
    },
    "pompe_surpresseur_1kw": {
        "methode": "Pompe surpresseur 1kW fournie posée",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "pompe_surpresseur_3kw": {
        "methode": "Pompe surpresseur 3kW fournie posée",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "chauffe_eau_electrique_100l": {
        "methode": "Chauffe-eau électrique 100L fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "chauffe_eau_solaire_200l": {
        "methode": "CESI thermosiphon 200L fourni posé",
        "source_dakar": "Corrigé 650K (was 2.1M). Marché: thermosiphon 250-650K, pressurisé jusqu'à 2M",
        "fiabilite": "haute",
    },
    # ── MEP — CVC ──
    "split_1cv": {
        "methode": "Split mural 1CV (9000 BTU) fourni posé",
        "source_dakar": "Corrigé 250K (was 450K). Jumia: 155-228K + pose ~50K",
        "fiabilite": "haute",
    },
    "split_2cv": {
        "methode": "Split mural 2CV (18000 BTU) fourni posé",
        "source_dakar": "Corrigé 400K (was 750K). Jumia: 281-350K + pose ~50K",
        "fiabilite": "haute",
    },
    "split_cassette_4cv": {
        "methode": "Split cassette plafond 4CV fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "vmc_simple_flux": {
        "methode": "VMC simple flux par logement",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "vmc_double_flux": {
        "methode": "VMC double flux par logement",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "climatiseur_central_kw": {
        "methode": "Climatisation centrale (FCFA/kW installé)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "basse",
    },
    # ── MEP — ASCENSEURS ──
    "ascenseur_630kg_r4_r6": {
        "methode": "Ascenseur 630kg 4-6 niveaux, fourni posé avec gaine",
        "source_dakar": "Corrigé 15M (was 28M). Source: 6.5-15M FCFA Dakar vérifié",
        "fiabilite": "haute",
    },
    "ascenseur_630kg_r7_r10": {
        "methode": "Ascenseur 630kg 7-10 niveaux, fourni posé",
        "source_dakar": "Corrigé 22M (was 38M). Proportionnel R4-R6",
        "fiabilite": "moyenne",
    },
    "ascenseur_1000kg_r6_r10": {
        "methode": "Ascenseur 1000kg 6-10 niveaux, fourni posé",
        "source_dakar": "Corrigé 30M (was 45M). Extrapolation",
        "fiabilite": "basse",
    },
    "ascenseur_1000kg_r11_plus": {
        "methode": "Ascenseur 1000kg 11+ niveaux, fourni posé",
        "source_dakar": "Corrigé 42M (was 58M). Extrapolation",
        "fiabilite": "basse",
    },
    "monte_charge_500kg": {
        "methode": "Monte-charge 500kg fourni posé",
        "source_dakar": "Corrigé 15M (was 22M). Proportionnel ascenseur",
        "fiabilite": "basse",
    },
    # ── MEP — COURANTS FAIBLES ──
    "cablage_rj45_ml": {
        "methode": "Câblage réseau RJ45 Cat6 fourni posé",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "prise_rj45": {
        "methode": "Prise réseau RJ45 fournie posée",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "baie_serveur_12u": {
        "methode": "Baie serveur 12U murale",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "camera_ip_interieure": {
        "methode": "Caméra IP intérieure fournie posée",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "camera_ip_exterieure": {
        "methode": "Caméra IP extérieure fournie posée",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "systeme_controle_acces": {
        "methode": "Contrôle d'accès par porte, badge + lecteur + gâche",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "interphone_video": {
        "methode": "Interphone vidéo par logement",
        "source_dakar": "Corrigé 65K (was 220K). Jumia: 26,500-250K, médiane bâtiment",
        "fiabilite": "moyenne",
    },
    # ── MEP — SÉCURITÉ INCENDIE ──
    "detecteur_fumee": {
        "methode": "Détecteur fumée optique adressable",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "declencheur_manuel": {
        "methode": "Déclencheur manuel incendie",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "sirene_flash": {
        "methode": "Sirène + flash alarme incendie",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "centrale_incendie_16zones": {
        "methode": "Centrale de détection incendie 16 zones",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "centrale_incendie_32zones": {
        "methode": "Centrale de détection incendie 32 zones",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "extincteur_6kg_co2": {
        "methode": "Extincteur CO2 6kg fourni",
        "source_dakar": "Corrigé 95K (was 85K). Source: 95K Dakar vérifié",
        "fiabilite": "haute",
    },
    "extincteur_9kg_poudre": {
        "methode": "Extincteur poudre ABC 9kg fourni",
        "source_dakar": "Corrigé 50K (was 65K). Source: 45-55K vérifié",
        "fiabilite": "haute",
    },
    "ria_dn25_ml": {
        "methode": "RIA DN25 réseau incendie (FCFA/ml)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "sprinkler_tete": {
        "methode": "Tête de sprinkler (unité)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
    "sprinkler_centrale": {
        "methode": "Centrale sprinkler complète",
        "source_dakar": "Estimation terrain",
        "fiabilite": "basse",
    },
    # ── MEP — AUTOMATISATION ──
    "domotique_logement": {
        "methode": "Domotique basique par logement (éclairage + volets)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "basse",
    },
    "bms_systeme": {
        "methode": "BMS bâtiment complet (forfait)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "basse",
    },
    "eclairage_detecteur_presence": {
        "methode": "Luminaire + détecteur de présence (unité)",
        "source_dakar": "Estimation terrain",
        "fiabilite": "moyenne",
    },
}


# ══════════════════════════════════════════════════════════════
# SYSTÈME DE MISE À JOUR DES PRIX
# ══════════════════════════════════════════════════════════════
DERNIERE_MAJ = "2026-04"
PROCHAINE_MAJ = "2026-07"
FREQUENCE_MAJ = "trimestrielle"

POSTES_PRIORITAIRES_MAJ = [
    # These prices are most volatile and should be checked first
    "acier_ha500_kg",      # Cours mondiaux acier
    "acier_ha400_kg",
    "beton_c3037_m3",      # Prix ciment local
    "beton_c3545_m3",
    "split_1cv",           # Taux de change (imports)
    "split_2cv",
    "groupe_electrogene_100kva",
    "groupe_electrogene_200kva",
]

def verifier_validite_prix():
    """Returns True if prices are still within validity period."""
    from datetime import date
    today = date.today()
    parts = PROCHAINE_MAJ.split("-")
    next_date = date(int(parts[0]), int(parts[1]), 1)
    return today < next_date

def rapport_fiabilite():
    """Generate a reliability report for all prices."""
    rapport = {}
    for ville, prix_pays in PAYS.items():
        if ville in ('senegal', 'cote_ivoire', 'maroc', 'nigeria', 'ghana'):
            continue  # Skip aliases
        p = prix_pays
        rapport[p.ville_reference] = {
            "fiabilite": p.fiabilite,
            "date_maj": p.date_maj,
            "valide": verifier_validite_prix(),
        }
    return rapport


# ══════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== BASE DE PRIX TIJAN AI — MULTI-PAYS ===\n")
    for ville in ["dakar", "abidjan", "casablanca", "lagos", "accra"]:
        p = get_prix(ville)
        s = p.structure
        print(f"{p.pays} ({p.ville_reference}) — {p.fiabilite}")
        print(f"  Béton C30/37    : {s.beton_c3037_m3:>12,} FCFA/m³")
        print(f"  Acier HA500     : {s.acier_ha500_kg:>12,} FCFA/kg")
        print(f"  Pieu Ø800       : {s.pieu_fore_d800_ml:>12,} FCFA/ml")
        print(f"  Agglos 15cm     : {s.agglo_creux_15_m2:>12,} FCFA/m²")
        m = p.mep
        print(f"  Split 1CV       : {m.split_1cv:>12,} FCFA")
        print(f"  Asc. 630kg R4-6 : {m.ascenseur_630kg_r4_r6:>12,} FCFA")
        print()

    print("=== VALIDITÉ DES PRIX ===")
    print(f"Dernière MAJ: {DERNIERE_MAJ}")
    print(f"Prochaine MAJ: {PROCHAINE_MAJ}")
    print(f"Prix valides: {verifier_validite_prix()}")
    print()
    print("=== RAPPORT FIABILITÉ ===")
    for ville, info in rapport_fiabilite().items():
        print(f"  {ville}: {info}")

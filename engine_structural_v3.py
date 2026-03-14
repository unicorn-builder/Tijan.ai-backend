"""
engine_structural_v3.py — Moteur de calcul structurel Tijan AI
Eurocodes EC2/EC8 — Descente de charges niveau par niveau
Marché : Dakar, Sénégal
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math


# ══════════════════════════════════════════════════════════════
# DONNÉES D'ENTRÉE
# ══════════════════════════════════════════════════════════════

@dataclass
class DonneesProjet:
    nom: str = "Projet Tijan"
    ville: str = "Dakar"
    nb_niveaux: int = 5
    hauteur_etage_m: float = 3.0
    surface_emprise_m2: float = 500.0
    portee_max_m: float = 5.5
    portee_min_m: float = 4.0
    nb_travees_x: int = 4
    nb_travees_y: int = 3
    classe_beton: str = "C30/37"
    classe_acier: str = "HA500"
    pression_sol_MPa: float = 0.20
    zone_sismique: str = "faible"
    # Paramètres optionnels
    surcharge_exploitation_kNm2: float = 2.5
    charge_permanente_kNm2: float = 6.5


# ══════════════════════════════════════════════════════════════
# RÉSULTATS
# ══════════════════════════════════════════════════════════════

@dataclass
class ResultatPoteau:
    label: str
    niveau: int
    NEd_kN: float
    section_mm: int          # côté carré
    nb_barres: int
    diametre_mm: int
    cadre_diam_mm: int
    espacement_cadres_mm: int
    taux_armature_pct: float
    NRd_kN: float
    verif_ok: bool


@dataclass
class ResultatPoutre:
    b_mm: int
    h_mm: int
    As_inf_cm2: float
    As_sup_cm2: float
    etrier_diam_mm: int
    etrier_esp_mm: int
    portee_m: float


@dataclass
class ResultatFondation:
    type_fond: str
    nb_pieux: int
    diam_pieu_mm: int
    longueur_pieu_m: float
    As_cm2: float
    section_semelle_m: Optional[float] = None


@dataclass
class ResultatBOQ:
    beton_total_m3: float
    acier_total_kg: float
    cout_total_bas: int
    cout_total_haut: int
    ratio_fcfa_m2: int
    detail_lots: dict = field(default_factory=dict)


@dataclass
class ResultatsCalcul:
    poteaux_par_niveau: List[ResultatPoteau]
    poutre_type: ResultatPoutre
    fondation: ResultatFondation
    boq: ResultatBOQ


# ══════════════════════════════════════════════════════════════
# CONSTANTES MATÉRIAUX EC2
# ══════════════════════════════════════════════════════════════

BETONS = {
    "C25/30": {"fck": 25, "fcd": 16.7, "Ecm": 31000},
    "C30/37": {"fck": 30, "fcd": 20.0, "Ecm": 33000},
    "C35/45": {"fck": 35, "fcd": 23.3, "Ecm": 34000},
}

ACIERS = {
    "HA400": {"fyk": 400, "fyd": 348, "Es": 200000},
    "HA500": {"fyk": 500, "fyd": 435, "Es": 200000},
}

# Prix marché Dakar (FCFA) — estimatif, vérifier CIMAF/SONACOS
PRIX_BETON_M3 = 120_000      # béton armé coulé en place
PRIX_ACIER_KG = {
    8:  750, 10: 720, 12: 700, 14: 690,
    16: 680, 20: 670, 25: 660, 32: 650,
}
PRIX_ACIER_MOYEN_KG = 690
PRIX_COFFRAGE_M2 = 8_500
PRIX_PIEU_ML = 45_000        # pieu béton armé ø800 foré


# ══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════

def section_standard(NEd_kN: float, fcd: float) -> int:
    """
    Calcule la section minimale d'un poteau selon EC2 §5.8.
    Retourne le côté en mm (section carrée).
    """
    # NEd = fcd * Ac * (1 + omega) avec omega ≈ 0.2 (taux armature initial)
    # Ac = NEd / (fcd * 1.2) en mm²
    NEd_N = NEd_kN * 1000
    Ac_min = NEd_N / (fcd * 1.2)  # mm²
    cote = math.ceil(math.sqrt(Ac_min) / 25) * 25  # arrondi au multiple de 25mm
    cote = max(200, min(cote, 600))  # limites pratiques EC2
    return cote


def armatures_poteau(NEd_kN: float, section_mm: int, fcd: float, fyd: float):
    """
    Calcule les armatures longitudinales selon EC2 §9.5.
    Retourne (nb_barres, diam_mm, taux_pct, NRd_kN).
    """
    Ac = section_mm ** 2  # mm²
    NEd_N = NEd_kN * 1000

    # Armatures nécessaires : As = (NEd - 0.8*fcd*Ac) / fyd
    As_necessaire = max(0, (NEd_N - 0.8 * fcd * Ac) / fyd)

    # Limites EC2 §9.5.2 : As_min = max(0.002*Ac, 0.1*NEd/fyd)
    As_min = max(0.002 * Ac, 0.1 * NEd_N / fyd)
    As_min = max(As_min, 4 * math.pi * (10**2) / 4)  # minimum 4HA10

    As_calc = max(As_necessaire, As_min)

    # Choisir diamètre et nombre de barres
    candidats = [
        (4, 12), (4, 14), (4, 16), (4, 20), (4, 25),
        (6, 16), (6, 20), (6, 25),
        (8, 16), (8, 20), (8, 25), (8, 32),
        (12, 20), (12, 25), (12, 32),
    ]
    nb_barres, diam_mm = 4, 12
    for nb, d in candidats:
        As_fourni = nb * math.pi * (d**2) / 4
        if As_fourni >= As_calc:
            nb_barres, diam_mm = nb, d
            break

    As_fourni = nb_barres * math.pi * (diam_mm**2) / 4
    taux_pct = As_fourni / Ac * 100

    # NRd selon EC2 §6.1
    NRd_N = fcd * (Ac - As_fourni) + fyd * As_fourni
    NRd_kN = NRd_N / 1000

    # Cadres — espacement selon EC2 §9.5.3
    if section_mm <= 300:
        cadre_diam = 8
    elif section_mm <= 400:
        cadre_diam = 10
    else:
        cadre_diam = 12

    esp_cadre = min(
        20 * diam_mm,          # 20 × diam long
        section_mm,             # min dimension section
        400                     # 400mm max
    )
    esp_cadre = (esp_cadre // 25) * 25  # arrondi 25mm

    return nb_barres, diam_mm, cadre_diam, esp_cadre, round(taux_pct, 2), round(NRd_kN, 1)


def surface_tributaire(d: DonneesProjet) -> float:
    """Surface tributaire d'un poteau central."""
    return (d.portee_max_m + d.portee_min_m) / 2 * (d.portee_max_m + d.portee_min_m) / 2 * 0.8


# ══════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════

def calculer_projet(d: DonneesProjet) -> ResultatsCalcul:
    """
    Calcul structurel complet selon Eurocodes EC2/EC8.
    Descente de charges niveau par niveau — sections variables.
    """
    beton = BETONS.get(d.classe_beton, BETONS["C30/37"])
    acier = ACIERS.get(d.classe_acier, ACIERS["HA500"])
    fcd = beton["fcd"]
    fyd = acier["fyd"]

    # Charges caractéristiques (kN/m²)
    G = d.charge_permanente_kNm2       # permanente
    Q = d.surcharge_exploitation_kNm2  # exploitation
    # Combinaison fondamentale EC0 : 1.35G + 1.5Q
    p_Ed = 1.35 * G + 1.5 * Q         # charge de calcul par m²

    S_trib = surface_tributaire(d)     # m² par poteau

    # ── Descente de charges — du haut vers le bas ──
    # La toiture ne reprend qu'1 niveau, le RDC cumule tous les niveaux
    poteaux = []
    charge_niveau = p_Ed * S_trib  # kN par niveau
    poids_poteau_par_etage = 25 * (0.35**2) * d.hauteur_etage_m * 1.35  # kN

    # On itère depuis la toiture (1 niveau porté) jusqu'au RDC (nb_niveaux portés)
    # position=1 → toiture, position=nb_niveaux → RDC
    for position in range(1, d.nb_niveaux + 1):
        niveaux_portes = position
        NEd = niveaux_portes * (charge_niveau + poids_poteau_par_etage)

        section_mm = section_standard(NEd, fcd)
        nb_barres, diam_mm, cadre_diam, esp_cadre, taux_pct, NRd_kN = \
            armatures_poteau(NEd, section_mm, fcd, fyd)

        verif = NRd_kN >= NEd * 0.95

        if position == 1:
            label = "Toiture"
        elif position == d.nb_niveaux:
            label = "RDC"
        else:
            label = f"N{d.nb_niveaux - position}"

        poteaux.append(ResultatPoteau(
            label=label,
            niveau=position,
            NEd_kN=round(NEd, 1),
            section_mm=section_mm,
            nb_barres=nb_barres,
            diametre_mm=diam_mm,
            cadre_diam_mm=cadre_diam,
            espacement_cadres_mm=esp_cadre,
            taux_armature_pct=taux_pct,
            NRd_kN=NRd_kN,
            verif_ok=verif,
        ))

    # Trier RDC en premier (position max) → Toiture en dernier (position 1)
    poteaux.sort(key=lambda p: -p.niveau)

    # ── Poutre type ──
    portee = d.portee_max_m
    h_poutre = max(400, round(portee * 1000 / 12 / 25) * 25)  # L/12, arrondi 25mm
    b_poutre = max(200, round(h_poutre * 0.5 / 25) * 25)

    # Moment de calcul simplifié (poutre continue)
    charge_lin = p_Ed * (d.portee_min_m + d.portee_max_m) / 2
    Med_travee = charge_lin * portee**2 / 10  # kN.m
    Med_appui  = charge_lin * portee**2 / 8   # kN.m

    z = 0.9 * h_poutre  # bras de levier
    As_inf = (Med_travee * 1e6) / (fyd * z)   # mm²
    As_sup = (Med_appui  * 1e6) / (fyd * z)   # mm²

    # Étriers
    VEd = charge_lin * portee / 2
    etrier_diam = 8 if h_poutre < 500 else 10
    esp_etrier = min(
        int(0.75 * h_poutre),
        300,
        round(b_poutre * 0.9)
    )
    esp_etrier = (esp_etrier // 25) * 25

    poutre = ResultatPoutre(
        b_mm=b_poutre,
        h_mm=h_poutre,
        As_inf_cm2=round(As_inf / 100, 2),
        As_sup_cm2=round(As_sup / 100, 2),
        etrier_diam_mm=etrier_diam,
        etrier_esp_mm=esp_etrier,
        portee_m=portee,
    )

    # ── Fondations ──
    NEd_rdc = poteaux[0].NEd_kN  # charge au RDC

    if d.pression_sol_MPa >= 0.20:
        # Semelle isolée
        A_semelle = (NEd_rdc * 1.1) / (d.pression_sol_MPa * 1000)  # m²
        cote_semelle = math.ceil(math.sqrt(A_semelle) * 10) / 10
        As_semelle_cm2 = round(NEd_rdc * 1000 / (4 * fyd) / 100, 1)
        fond = ResultatFondation(
            type_fond="Semelle isolée béton armé",
            nb_pieux=0,
            diam_pieu_mm=0,
            longueur_pieu_m=0,
            As_cm2=As_semelle_cm2,
            section_semelle_m=round(cote_semelle, 2),
        )
    else:
        # Pieux forés
        cap_pieu = 1200  # kN par pieu ø800 L=10m (sol médio)
        nb_pieux = max(2, math.ceil(NEd_rdc * 1.2 / cap_pieu))
        if nb_pieux == 3:
            nb_pieux = 4
        As_pieu = max(6 * math.pi * (16**2) / 4, 0.005 * math.pi * (400**2))
        fond = ResultatFondation(
            type_fond="Pieux forés béton armé",
            nb_pieux=nb_pieux,
            diam_pieu_mm=800,
            longueur_pieu_m=10.0,
            As_cm2=round(As_pieu / 100, 1),
        )

    # ── BOQ ──
    # Volumes béton
    V_poteaux = sum(
        (p.section_mm / 1000)**2 * d.hauteur_etage_m
        for p in poteaux
    ) * d.nb_travees_x * d.nb_travees_y

    V_poutres = (
        (b_poutre / 1000) * (h_poutre / 1000) * d.portee_max_m *
        (d.nb_travees_x + d.nb_travees_y) * d.nb_niveaux
    )

    ep_dalle = 0.20  # m
    V_dalles = d.surface_emprise_m2 * ep_dalle * d.nb_niveaux

    if fond.nb_pieux > 0:
        V_fond = (math.pi * (fond.diam_pieu_mm / 2000)**2 *
                  fond.longueur_pieu_m *
                  fond.nb_pieux *
                  d.nb_travees_x * d.nb_travees_y)
    else:
        V_fond = (fond.section_semelle_m or 1.5)**2 * 0.5 * d.nb_travees_x * d.nb_travees_y

    V_total = V_poteaux + V_poutres + V_dalles + V_fond

    # Masse acier (ratio kg/m³ selon type d'élément)
    kg_poteaux = V_poteaux * 100   # ~100 kg/m³ poteaux
    kg_poutres = V_poutres * 120   # ~120 kg/m³ poutres
    kg_dalles  = V_dalles  * 90    # ~90 kg/m³ dalles
    kg_fond    = V_fond    * 110
    kg_total   = kg_poteaux + kg_poutres + kg_dalles + kg_fond

    # Coûts
    cout_beton = V_total * PRIX_BETON_M3
    cout_acier = kg_total * PRIX_ACIER_MOYEN_KG
    cout_coffrage = (V_dalles / ep_dalle + V_poteaux / 0.12 + V_poutres / 0.08) * PRIX_COFFRAGE_M2 * 0.15

    cout_bas = int(cout_beton + cout_acier + cout_coffrage)
    cout_haut = int(cout_bas * 1.20)

    surface_totale = d.surface_emprise_m2 * d.nb_niveaux
    ratio = int(cout_bas / surface_totale)

    boq = ResultatBOQ(
        beton_total_m3=round(V_total, 1),
        acier_total_kg=round(kg_total, 0),
        cout_total_bas=cout_bas,
        cout_total_haut=cout_haut,
        ratio_fcfa_m2=ratio,
        detail_lots={
            "terrassement_m3": round(d.surface_emprise_m2 * 1.5, 0),
            "fondations_m3": round(V_fond, 1),
            "superstructure_m3": round(V_poteaux + V_poutres + V_dalles, 1),
            "acier_poteaux_kg": round(kg_poteaux, 0),
            "acier_poutres_kg": round(kg_poutres, 0),
            "acier_dalles_kg": round(kg_dalles, 0),
        }
    )

    return ResultatsCalcul(
        poteaux_par_niveau=poteaux,
        poutre_type=poutre,
        fondation=fond,
        boq=boq,
    )


# ══════════════════════════════════════════════════════════════
# TEST RAPIDE
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    d = DonneesProjet(
        nom="Résidence Papa Oumar Sakho",
        ville="Dakar",
        nb_niveaux=9,
        hauteur_etage_m=3.0,
        surface_emprise_m2=2561,
        portee_max_m=6.18,
        portee_min_m=4.13,
        nb_travees_x=8,
        nb_travees_y=5,
        classe_beton="C30/37",
        classe_acier="HA500",
        pression_sol_MPa=0.15,
    )
    r = calculer_projet(d)
    print("=== POTEAUX ===")
    for p in r.poteaux_par_niveau:
        print(f"{p.label:10} NEd={p.NEd_kN:7.0f}kN  {p.section_mm}×{p.section_mm}mm  "
              f"{p.nb_barres}HA{p.diametre_mm}  τ={p.taux_armature_pct:.2f}%  "
              f"{'✓' if p.verif_ok else '✗'}")
    print(f"\n=== POUTRE TYPE ===")
    print(f"{r.poutre_type.b_mm}×{r.poutre_type.h_mm}mm  "
          f"As_inf={r.poutre_type.As_inf_cm2}cm²  As_sup={r.poutre_type.As_sup_cm2}cm²")
    print(f"\n=== FONDATION ===")
    print(f"{r.fondation.type_fond}  {r.fondation.nb_pieux}×ø{r.fondation.diam_pieu_mm}mm L={r.fondation.longueur_pieu_m}m")
    print(f"\n=== BOQ ===")
    print(f"Béton: {r.boq.beton_total_m3} m³  Acier: {r.boq.acier_total_kg:.0f} kg")
    print(f"Coût: {r.boq.cout_total_bas:,} – {r.boq.cout_total_haut:,} FCFA")
    print(f"Ratio: {r.boq.ratio_fcfa_m2:,} FCFA/m²")

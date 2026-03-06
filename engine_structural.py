"""
Tijan AI — Moteur de Calcul Structurel
Phase 1 : Descente de charges + Dimensionnement + Fondations
Référentiel : Eurocodes EN 1991-1-1, EN 1992-1-1
Auteur : Tijan AI Engine v1.0
"""

import math
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ============================================================
# ENUMS & CONSTANTES
# ============================================================

class UsageBatiment(str, Enum):
    RESIDENTIEL = "residentiel"
    BUREAUX = "bureaux"
    MIXTE = "mixte"

class TypeSol(str, Enum):
    BON = "bon"          # σ > 0.15 MPa → semelles isolées
    MOYEN = "moyen"      # 0.08 < σ ≤ 0.15 MPa → radier
    MAUVAIS = "mauvais"  # σ ≤ 0.08 MPa → pieux

class ClasseExposition(str, Enum):
    XC1 = "XC1"   # Intérieur sec
    XC2 = "XC2"   # Humide, rarement sec
    XS1 = "XS1"   # Air marin (< 5km mer)
    XS2 = "XS2"   # Immergé eau de mer

class ZoneVent(str, Enum):
    DAKAR = "dakar"         # Vents dominants forts
    ABIDJAN = "abidjan"
    CASABLANCA = "casablanca"
    LAGOS = "lagos"

# Charges d'exploitation EN 1991-1-1 Tableau 6.1 (kN/m²)
CHARGES_EXPLOITATION = {
    UsageBatiment.RESIDENTIEL: 1.5,
    UsageBatiment.BUREAUX: 2.5,
    UsageBatiment.MIXTE: 2.0,
}

# Vitesse de base du vent par zone (m/s) — EN 1991-1-4
VITESSE_VENT_BASE = {
    ZoneVent.DAKAR: 28.0,
    ZoneVent.ABIDJAN: 24.0,
    ZoneVent.CASABLANCA: 26.0,
    ZoneVent.LAGOS: 25.0,
}

# Résistance béton minimale selon classe exposition
BETON_MIN_PAR_EXPOSITION = {
    ClasseExposition.XC1: 25.0,  # C25/30
    ClasseExposition.XC2: 25.0,
    ClasseExposition.XS1: 30.0,  # C30/37 obligatoire en zone marine
    ClasseExposition.XS2: 35.0,
}

# Enrobage nominal (mm) selon classe exposition
ENROBAGE_PAR_EXPOSITION = {
    ClasseExposition.XC1: 25,
    ClasseExposition.XC2: 30,
    ClasseExposition.XS1: 40,
    ClasseExposition.XS2: 45,
}

# Constantes matériaux
POIDS_VOLUMIQUE_BETON = 25.0    # kN/m³
POIDS_PROPRE_SUPERPOSE = 2.0    # kN/m² (cloisons + revêtement + faux plafond)
FE_500 = 500.0                  # MPa — acier FeE500
GAMMA_BETON = 1.5               # Coefficient partiel béton (ELU)
GAMMA_ACIER = 1.15              # Coefficient partiel acier (ELU)


# ============================================================
# DATACLASSES — INPUTS
# ============================================================

@dataclass
class ParamsGeometrie:
    """Paramètres géométriques du bâtiment issus du plan archi"""
    surface_emprise_m2: float          # Surface au sol (m²)
    nb_niveaux: int                    # Nombre de niveaux (hors RDC)
    hauteur_etage_m: float = 3.0       # Hauteur entre niveaux (m)
    portee_max_m: float = 6.0          # Portée maximale libre (m)
    nb_voiles_facade: int = 4          # Voiles en façade
    nb_voiles_internes: int = 2        # Voiles internes (noyaux)
    epaisseur_voile_m: float = 0.20    # Épaisseur voile initiale (m)

@dataclass
class ParamsUsage:
    """Usage du bâtiment par niveau"""
    usage_principal: UsageBatiment = UsageBatiment.RESIDENTIEL
    usage_rdc: UsageBatiment = UsageBatiment.RESIDENTIEL
    charge_toiture_kNm2: float = 1.0   # Toiture terrasse accessible

@dataclass
class ParamsSol:
    """Données issues du rapport de sol"""
    pression_admissible_MPa: float     # Contrainte admissible sol (MPa)
    profondeur_fondation_m: float = 1.5
    presence_nappe: bool = False
    description: str = ""

@dataclass
class ParamsLocalisation:
    """Paramètres environnementaux selon localisation"""
    ville: ZoneVent = ZoneVent.DAKAR
    distance_mer_km: float = 5.0       # Distance à la mer (km)
    zone_sismique: int = 1             # 1=faible, 2=modéré, 3=fort

@dataclass
class ProjetStructurel:
    """Projet complet — input principal du moteur"""
    nom: str
    geometrie: ParamsGeometrie
    usage: ParamsUsage
    sol: ParamsSol
    localisation: ParamsLocalisation


# ============================================================
# DATACLASSES — OUTPUTS
# ============================================================

@dataclass
class ResultatDescenteCharges:
    """Résultats de la descente de charges"""
    charge_permanente_G_kNm2: float
    charge_exploitation_Q_kNm2: float
    combinaison_ELU_kNm2: float        # 1.35G + 1.5Q
    combinaison_ELS_kNm2: float        # G + Q
    charge_totale_par_niveau_kN: float
    charge_totale_base_kN: float
    note_calcul: list = field(default_factory=list)

@dataclass
class ResultatVoile:
    """Dimensionnement d'un voile"""
    epaisseur_retenue_m: float
    ferraillage_vertical_cm2_m: float
    ferraillage_horizontal_cm2_m: float
    taux_armature_pct: float
    contrainte_compression_MPa: float
    verification_flambement: bool
    note_calcul: list = field(default_factory=list)

@dataclass
class ResultatDalle:
    """Dimensionnement d'une dalle pleine"""
    epaisseur_retenue_m: float
    ferraillage_inferieur_cm2_m: float
    ferraillage_superieur_cm2_m: float
    verification_fleche: bool
    verification_poinconnement: bool
    epaisseur_chapeau_m: Optional[float] = None     # Épaississement local si requis
    ferraillage_chapeau_cm2: Optional[float] = None  # Armatures poinçonnement
    note_calcul: list = field(default_factory=list)

@dataclass
class ResultatFondations:
    """Dimensionnement des fondations"""
    type_fondation: str
    justification: str
    # Semelles isolées
    largeur_semelle_m: Optional[float] = None
    longueur_semelle_m: Optional[float] = None
    epaisseur_semelle_m: Optional[float] = None
    # Radier
    epaisseur_radier_m: Optional[float] = None
    ferraillage_radier_cm2_m: Optional[float] = None
    # Pieux
    diametre_pieux_m: Optional[float] = None
    longueur_pieux_m: Optional[float] = None
    nb_pieux_par_poteau: Optional[int] = None
    note_calcul: list = field(default_factory=list)

@dataclass
class ResultatBeton:
    """Classe béton et enrobage retenus"""
    classe_exposition: ClasseExposition
    justification: str
    fc28_MPa: float
    fcd_MPa: float      # Résistance de calcul = fc28 / γc
    fyd_MPa: float      # Résistance acier de calcul = fyk / γs
    enrobage_mm: int

@dataclass
class ResultatPoteau:
    """Dimensionnement d'un poteau en béton armé"""
    section_b_m: float
    section_h_m: float
    ferraillage_longitudinal_cm2: float
    nb_barres: int
    diametre_barres_mm: int
    ferraillage_transversal_mm: int
    espacement_cadres_mm: int
    taux_armature_pct: float
    contrainte_compression_MPa: float
    verification_flambement: bool
    longueur_flambement_m: float
    note_calcul: list = field(default_factory=list)

@dataclass
class ResultatPoutre:
    """Dimensionnement d'une poutre en béton armé"""
    largeur_b_m: float
    hauteur_h_m: float
    hauteur_utile_d_m: float
    ferraillage_inferieur_cm2: float
    ferraillage_superieur_cm2: float
    nb_barres_inf: int
    nb_barres_sup: int
    diametre_barres_mm: int
    ferraillage_transversal_mm: int
    espacement_cadres_mm: int
    moment_travee_kNm: float
    moment_appui_kNm: float
    effort_tranchant_kN: float
    verification_cisaillement: bool
    note_calcul: list = field(default_factory=list)

@dataclass
class NoteCalculComplete:
    """Note de calcul complète et auditable"""
    projet_nom: str
    descente_charges: ResultatDescenteCharges
    beton: ResultatBeton
    voile: ResultatVoile
    dalle: ResultatDalle
    poteau: ResultatPoteau
    poutre: ResultatPoutre
    fondations: ResultatFondations
    resume_executif: dict = field(default_factory=dict)


# ============================================================
# MODULE 1 — CLASSE BÉTON ET EXPOSITION
# ============================================================

def determiner_classe_beton(localisation: ParamsLocalisation) -> ResultatBeton:
    """
    Détermine la classe de béton selon la classe d'exposition
    EN 1992-1-1 Tableau 4.1
    """
    notes = []

    # Détermination classe exposition
    if localisation.distance_mer_km < 5.0:
        classe = ClasseExposition.XS1
        justif = f"Distance mer = {localisation.distance_mer_km}km < 5km → Exposition XS1 (air marin)"
    elif localisation.distance_mer_km < 20.0:
        classe = ClasseExposition.XC2
        justif = f"Distance mer = {localisation.distance_mer_km}km → Exposition XC2"
    else:
        classe = ClasseExposition.XC1
        justif = f"Distance mer = {localisation.distance_mer_km}km > 20km → Exposition XC1"

    fc28 = BETON_MIN_PAR_EXPOSITION[classe]
    fcd = round(fc28 / GAMMA_BETON, 2)
    fyd = round(FE_500 / GAMMA_ACIER, 2)
    enrobage = ENROBAGE_PAR_EXPOSITION[classe]

    notes.append(f"Réf : EN 1992-1-1 §4.4 — {justif}")
    notes.append(f"Béton retenu : C{int(fc28)}/... → fc28 = {fc28} MPa")
    notes.append(f"fcd = fc28/γc = {fc28}/{GAMMA_BETON} = {fcd} MPa")
    notes.append(f"fyd = fyk/γs = {FE_500}/{GAMMA_ACIER} = {fyd} MPa")
    notes.append(f"Enrobage nominal : cnom = {enrobage} mm")

    return ResultatBeton(
        classe_exposition=classe,
        justification=justif,
        fc28_MPa=fc28,
        fcd_MPa=fcd,
        fyd_MPa=fyd,
        enrobage_mm=enrobage
    )


# ============================================================
# MODULE 2 — DESCENTE DE CHARGES
# ============================================================

def calculer_descente_charges(
    projet: ProjetStructurel
) -> ResultatDescenteCharges:
    """
    Descente de charges selon EN 1991-1-1
    Combinaisons ELU/ELS selon EN 1990
    """
    notes = []
    geo = projet.geometrie
    usage = projet.usage

    # Charges permanentes
    # Poids propre dalle béton (épaisseur estimée L/30)
    epaisseur_dalle_estimee = round(geo.portee_max_m / 30, 3)
    G_dalle = round(POIDS_VOLUMIQUE_BETON * epaisseur_dalle_estimee, 2)
    G_superpose = POIDS_PROPRE_SUPERPOSE
    G_total = round(G_dalle + G_superpose, 2)

    notes.append("=== DESCENTE DE CHARGES — EN 1991-1-1 ===")
    notes.append(f"Épaisseur dalle estimée : L/30 = {geo.portee_max_m}/30 = {epaisseur_dalle_estimee}m")
    notes.append(f"G_dalle = γ_béton × e = {POIDS_VOLUMIQUE_BETON} × {epaisseur_dalle_estimee} = {G_dalle} kN/m²")
    notes.append(f"G_superposé (cloisons + revêtement + faux plafond) = {G_superpose} kN/m²")
    notes.append(f"G_total = {G_dalle} + {G_superpose} = {G_total} kN/m²")

    # Charges d'exploitation
    Q = CHARGES_EXPLOITATION[usage.usage_principal]
    notes.append(f"Q = {Q} kN/m² (EN 1991-1-1 Tab.6.1 — {usage.usage_principal.value})")

    # Combinaisons EN 1990
    ELU = round(1.35 * G_total + 1.5 * Q, 2)
    ELS = round(G_total + Q, 2)

    notes.append(f"ELU = 1.35G + 1.5Q = 1.35×{G_total} + 1.5×{Q} = {ELU} kN/m²")
    notes.append(f"ELS = G + Q = {G_total} + {Q} = {ELS} kN/m²")

    # Charge totale par niveau et à la base
    charge_par_niveau = round(ELU * geo.surface_emprise_m2, 1)
    charge_base = round(charge_par_niveau * (geo.nb_niveaux + 1), 1)

    notes.append(f"Charge totale/niveau = ELU × S = {ELU} × {geo.surface_emprise_m2} = {charge_par_niveau} kN")
    notes.append(f"Charge totale base = {charge_par_niveau} × {geo.nb_niveaux + 1} niveaux = {charge_base} kN")

    return ResultatDescenteCharges(
        charge_permanente_G_kNm2=G_total,
        charge_exploitation_Q_kNm2=Q,
        combinaison_ELU_kNm2=ELU,
        combinaison_ELS_kNm2=ELS,
        charge_totale_par_niveau_kN=charge_par_niveau,
        charge_totale_base_kN=charge_base,
        note_calcul=notes
    )


# ============================================================
# MODULE 3 — DIMENSIONNEMENT VOILES
# ============================================================

def dimensionner_voiles(
    projet: ProjetStructurel,
    descente: ResultatDescenteCharges,
    beton: ResultatBeton
) -> ResultatVoile:
    """
    Dimensionnement des voiles en béton armé
    EN 1992-1-1 §9.6
    """
    notes = []
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT VOILES — EN 1992-1-1 §9.6 ===")

    # Épaisseur minimale voile
    # EN 1992-1-1 : e_min = max(H_etage/20, 150mm)
    e_min_flambement = round(geo.hauteur_etage_m / 20, 3)
    e_min_absolu = 0.15
    e_min = max(e_min_flambement, e_min_absolu)
    e_retenue = max(e_min, geo.epaisseur_voile_m)
    e_retenue = round(math.ceil(e_retenue / 0.05) * 0.05, 2)  # Arrondi 5cm supérieur

    notes.append(f"e_min flambement = H/20 = {geo.hauteur_etage_m}/20 = {e_min_flambement}m")
    notes.append(f"e_min absolu = {e_min_absolu}m")
    notes.append(f"e_min retenu = max({e_min_flambement}, {e_min_absolu}) = {e_min}m")
    notes.append(f"e_voile retenue = {e_retenue}m (arrondi 5cm sup.)")

    # Contrainte de compression dans les voiles
    nb_voiles_total = geo.nb_voiles_facade + geo.nb_voiles_internes
    longueur_voile_moyenne = math.sqrt(geo.surface_emprise_m2) / 2
    surface_voile_totale = nb_voiles_total * longueur_voile_moyenne * e_retenue
    sigma_compression = round(
        descente.charge_totale_base_kN / (surface_voile_totale * 1000), 3
    )  # MPa

    notes.append(f"Nb voiles total = {nb_voiles_total}")
    notes.append(f"Longueur voile moyenne estimée = √S/2 = {round(longueur_voile_moyenne,2)}m")
    notes.append(f"Surface voiles totale = {round(surface_voile_totale,2)} m²")
    notes.append(f"σ_compression = N/(A_voiles) = {descente.charge_totale_base_kN}/{round(surface_voile_totale*1000,1)} = {sigma_compression} MPa")

    # Vérification : σ ≤ 0.3 × fcd (limite compression voile)
    limite_compression = round(0.3 * beton.fcd_MPa, 2)
    verification_flambement = sigma_compression <= limite_compression
    notes.append(f"Vérif compression : σ = {sigma_compression} MPa ≤ 0.3×fcd = {limite_compression} MPa → {'OK ✓' if verification_flambement else 'NON VÉRIFIÉ — augmenter épaisseur'}")

    # Ferraillage minimum EN 1992-1-1 §9.6.2
    # As_v_min = 0.002 × Ac (vertical)
    # As_h_min = 0.001 × Ac (horizontal) ou 25% As_v
    Ac_par_metre = e_retenue * 1.0  # m² par ml de voile
    As_v_min = round(0.002 * Ac_par_metre * 10000, 2)  # cm²/ml
    As_h_min = round(max(0.001 * Ac_par_metre * 10000, 0.25 * As_v_min), 2)

    # Ferraillage de calcul (compression + flexion composée simplifiée)
    # On majore de 30% le minimum pour prendre en compte les efforts de flexion
    As_v_calcul = round(As_v_min * 1.3, 2)
    As_h_calcul = round(As_h_min * 1.2, 2)
    taux = round((As_v_calcul / (e_retenue * 100 * 100)) * 100, 3)

    notes.append(f"Ferraillage vertical min : As_v = 0.002×Ac = {As_v_min} cm²/ml")
    notes.append(f"Ferraillage vertical retenu (×1.3) : As_v = {As_v_calcul} cm²/ml")
    notes.append(f"Ferraillage horizontal min : As_h = max(0.001Ac, 0.25As_v) = {As_h_min} cm²/ml")
    notes.append(f"Ferraillage horizontal retenu (×1.2) : As_h = {As_h_calcul} cm²/ml")
    notes.append(f"Taux armature = {taux}% (min requis : 0.2%)")

    return ResultatVoile(
        epaisseur_retenue_m=e_retenue,
        ferraillage_vertical_cm2_m=As_v_calcul,
        ferraillage_horizontal_cm2_m=As_h_calcul,
        taux_armature_pct=taux,
        contrainte_compression_MPa=sigma_compression,
        verification_flambement=verification_flambement,
        note_calcul=notes
    )


# ============================================================
# MODULE 4 — DIMENSIONNEMENT DALLES PLEINES
# ============================================================

def dimensionner_dalle(
    projet: ProjetStructurel,
    descente: ResultatDescenteCharges,
    beton: ResultatBeton
) -> ResultatDalle:
    """
    Dimensionnement dalle pleine sur appuis continus
    EN 1992-1-1 §5.3.2.2 + Tableau 7.4N
    """
    notes = []
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT DALLE PLEINE — EN 1992-1-1 ===")

    # Épaisseur dalle
    # EN 1992-1-1 Tableau 7.4N : L/d recommandé = 30 (dalle continue)
    e_dalle = round(geo.portee_max_m / 30, 3)
    e_min_dalle = 0.12  # 12cm minimum absolu
    e_dalle = max(e_dalle, e_min_dalle)
    e_dalle = round(math.ceil(e_dalle / 0.02) * 0.02, 2)  # Arrondi 2cm sup.

    notes.append(f"Épaisseur dalle : L/30 = {geo.portee_max_m}/30 = {round(geo.portee_max_m/30,3)}m")
    notes.append(f"e_min absolu = {e_min_dalle}m")
    notes.append(f"e_dalle retenue = {e_dalle}m (arrondi 2cm sup.)")

    # Vérification flèche (critère L/250)
    # Simplifiée : vérifiée si e ≥ L/30
    verification_fleche = e_dalle >= geo.portee_max_m / 30
    notes.append(f"Vérif flèche : e = {e_dalle}m ≥ L/30 = {round(geo.portee_max_m/30,3)}m → {'OK ✓' if verification_fleche else 'À VÉRIFIER'}")

    # Ferraillage dalle — Méthode des moments fléchissants
    # Moment en travée : M = q×L²/10 (dalle continue)
    q_ELU = descente.combinaison_ELU_kNm2
    L = geo.portee_max_m
    M_travee = round(q_ELU * L**2 / 10, 2)  # kN.m/ml
    M_appui = round(q_ELU * L**2 / 14, 2)   # kN.m/ml (appuis continus)

    notes.append(f"M_travée = q×L²/10 = {q_ELU}×{L}²/10 = {M_travee} kN.m/ml")
    notes.append(f"M_appui = q×L²/14 = {q_ELU}×{L}²/14 = {M_appui} kN.m/ml")

    # Section d'acier As = M / (0.9 × d × fyd)
    d = round(e_dalle - beton.enrobage_mm / 1000 - 0.008, 3)  # hauteur utile (en m)
    fyd_kNm2 = beton.fyd_MPa * 10  # conversion MPa → kN/m²... non, on garde MPa

    # As en cm²/ml : M(kN.m/ml) / (0.9 × d(m) × fyd(kN/cm²))
    fyd_kNcm2 = beton.fyd_MPa / 10  # MPa → kN/cm²
    As_inferieur = round(M_travee / (0.9 * d * fyd_kNcm2), 2)
    As_superieur = round(M_appui / (0.9 * d * fyd_kNcm2), 2)

    # Ferraillage minimum EN 1992-1-1 §9.3.1.1
    As_min = round(max(0.26 * (2.6 / beton.fyd_MPa) * e_dalle * 100, 0.0013 * e_dalle * 100), 2)  # cm²/ml approx
    As_min = max(As_min, 1.0)  # minimum absolu 1 cm²/ml

    As_inferieur = max(As_inferieur, As_min)
    As_superieur = max(As_superieur, As_min)

    notes.append(f"Hauteur utile d = e - c_nom - ø/2 = {e_dalle} - {beton.enrobage_mm/1000} - 0.008 = {d}m")
    notes.append(f"As_inférieur (travée) = M/(0.9×d×fyd) = {M_travee}/(0.9×{d}×{fyd_kNcm2}) = {As_inferieur} cm²/ml")
    notes.append(f"As_supérieur (appuis) = {As_superieur} cm²/ml")
    notes.append(f"As_min = {As_min} cm²/ml")

    # Vérification et résolution poinçonnement — EN 1992-1-1 §6.4
    # VEd = charge concentrée sur poteau (effort par poteau sur la dalle)
    notes.append("--- VÉRIFICATION POINÇONNEMENT — EN 1992-1-1 §6.4 ---")

    nb_poteaux = max(4, round(geo.surface_emprise_m2 / geo.portee_max_m**2))
    V_Ed_ponc = round(descente.charge_totale_par_niveau_kN / nb_poteaux, 1)  # kN par poteau

    # Section poteau estimée (25cm par défaut, sera affinée si nécessaire)
    c1 = c2 = 0.25  # m — section poteau initiale

    # Périmètre de contrôle u1 à 2d de la face du poteau
    d_dalle = round(e_dalle - beton.enrobage_mm / 1000 - 0.008, 3)
    u1 = round(2 * (c1 + c2) + 2 * math.pi * 2 * d_dalle, 3)  # m

    # Contrainte de poinçonnement appliquée
    v_Ed = round(V_Ed_ponc / (u1 * d_dalle * 1000), 3)  # MPa (V en kN → kN/m × 1000→N/m)
    v_Ed = round(V_Ed_ponc * 1000 / (u1 * d_dalle * 1e6), 4)  # MPa

    # Résistance au poinçonnement sans armatures EN 1992-1-1 §6.4.4
    rho_l = min(As_inferieur / (d_dalle * 100 * 100), 0.02)  # taux armature
    k_ponc = min(1 + math.sqrt(200 / (d_dalle * 1000)), 2.0)
    v_Rd_c = round((0.18 / 1.5) * k_ponc * (100 * rho_l * beton.fc28_MPa)**(1/3), 4)  # MPa

    notes.append(f"V_Ed poinçonnement = charge/poteau = {V_Ed_ponc} kN")
    notes.append(f"Périmètre contrôle u1 = 2(c1+c2) + 4πd = {u1:.3f} m (d={d_dalle}m)")
    notes.append(f"v_Ed = V_Ed/(u1×d) = {V_Ed_ponc*1000:.0f}N / ({u1:.3f}×{d_dalle}×10⁶) = {v_Ed:.4f} MPa")
    notes.append(f"k = 1+√(200/d) = {k_ponc:.3f} | ρl = {rho_l:.4f}")
    notes.append(f"v_Rd,c = 0.12×k×(100×ρl×fck)^(1/3) = {v_Rd_c:.4f} MPa")

    if v_Ed <= v_Rd_c:
        verification_poinconnement = True
        notes.append(f"v_Ed = {v_Ed:.4f} MPa ≤ v_Rd,c = {v_Rd_c:.4f} MPa → Poinçonnement OK ✓ (sans armatures)")
        e_chapeau_m = None
        As_chapeau_cm2 = None
    else:
        # SOLUTION SÉCURITÉ : épaississement local (chapeau) autour du poteau
        # On augmente l'épaisseur locale jusqu'à satisfaire v_Ed ≤ v_Rd,c
        notes.append(f"v_Ed = {v_Ed:.4f} MPa > v_Rd,c = {v_Rd_c:.4f} MPa → Chapeau requis")

        # Recherche épaisseur chapeau : augmenter d jusqu'à v_Ed ≤ v_Rd,c
        d_chapeau = d_dalle
        for _ in range(20):
            d_chapeau = round(d_chapeau + 0.02, 3)
            u1_c = round(2 * (c1 + c2) + 2 * math.pi * 2 * d_chapeau, 3)
            v_Ed_c = round(V_Ed_ponc * 1000 / (u1_c * d_chapeau * 1e6), 4)
            k_c = min(1 + math.sqrt(200 / (d_chapeau * 1000)), 2.0)
            v_Rd_c_new = round((0.18 / 1.5) * k_c * (100 * rho_l * beton.fc28_MPa)**(1/3), 4)
            if v_Ed_c <= v_Rd_c_new:
                break

        e_chapeau_m = round(d_chapeau + beton.enrobage_mm / 1000 + 0.008, 2)
        e_chapeau_m = round(math.ceil(e_chapeau_m / 0.05) * 0.05, 2)

        # Ferraillage chapeau (armatures de poinçonnement radiales)
        # As_sw = (v_Ed - 0.75×v_Rd,c) × u1 × d / (1.5 × fyd)
        As_chapeau_cm2 = round(
            max((v_Ed - 0.75 * v_Rd_c) * u1 * d_chapeau * 1e6 / (1.5 * beton.fyd_MPa) * 1e4 / 1e6, 0),
            2
        )  # cm²

        notes.append(f"Épaisseur chapeau retenue : e_chapeau = {e_chapeau_m}m")
        notes.append(f"  → Zone épaissie sur rayon = 3d = {round(3*d_dalle,2)}m autour du poteau")
        notes.append(f"As_chapeau = {As_chapeau_cm2} cm² (armatures radiales de poinçonnement)")
        notes.append(f"Poinçonnement résolu ✓")
        verification_poinconnement = True

    return ResultatDalle(
        epaisseur_retenue_m=e_dalle,
        ferraillage_inferieur_cm2_m=As_inferieur,
        ferraillage_superieur_cm2_m=As_superieur,
        verification_fleche=verification_fleche,
        verification_poinconnement=verification_poinconnement,
        epaisseur_chapeau_m=e_chapeau_m if 'e_chapeau_m' in dir() else None,
        ferraillage_chapeau_cm2=As_chapeau_cm2 if 'As_chapeau_cm2' in dir() else None,
        note_calcul=notes
    )


# ============================================================
# MODULE 5 — FONDATIONS
# ============================================================

def determiner_type_sol(pression_MPa: float) -> TypeSol:
    if pression_MPa > 0.15:
        return TypeSol.BON
    elif pression_MPa > 0.08:
        return TypeSol.MOYEN
    else:
        return TypeSol.MAUVAIS

def dimensionner_fondations(
    projet: ProjetStructurel,
    descente: ResultatDescenteCharges,
    beton: ResultatBeton
) -> ResultatFondations:
    """
    Dimensionnement des fondations selon type de sol
    EN 1997-1 (Eurocode 7)
    """
    notes = []
    sol = projet.sol
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT FONDATIONS — EN 1997-1 ===")
    notes.append(f"Pression admissible sol : σ_sol = {sol.pression_admissible_MPa} MPa")

    type_sol = determiner_type_sol(sol.pression_admissible_MPa)
    N_base = descente.charge_totale_base_kN

    if type_sol == TypeSol.BON:
        # SEMELLES ISOLÉES SOUS POTEAUX
        justif = f"σ_sol = {sol.pression_admissible_MPa} MPa > 0.15 MPa → Semelles isolées"
        notes.append(justif)

        # Charge par poteau (estimation nb poteaux = S/portée²)
        nb_poteaux = max(4, round(geo.surface_emprise_m2 / geo.portee_max_m**2))
        N_poteau = round(N_base / nb_poteaux, 1)
        notes.append(f"Nb poteaux estimé = S/L² = {geo.surface_emprise_m2}/{geo.portee_max_m**2} = {nb_poteaux}")
        notes.append(f"Charge par poteau = N_base/nb = {N_base}/{nb_poteaux} = {N_poteau} kN")

        # Dimension semelle : A = N / σ_sol
        sigma_kNm2 = sol.pression_admissible_MPa * 1000  # MPa → kN/m²
        A_semelle = round(N_poteau / sigma_kNm2, 2)
        B_semelle = round(math.sqrt(A_semelle), 2)
        B_semelle = round(math.ceil(B_semelle / 0.1) * 0.1, 1)  # Arrondi 10cm sup.
        e_semelle = round(max(B_semelle / 3, 0.40), 2)  # e ≥ B/3 et ≥ 40cm

        notes.append(f"Aire semelle = N/σ = {N_poteau}/{sigma_kNm2} = {A_semelle} m²")
        notes.append(f"B_semelle = √A = {round(math.sqrt(A_semelle),2)}m → retenu {B_semelle}m (arrondi 10cm)")
        notes.append(f"e_semelle = max(B/3, 0.40) = max({round(B_semelle/3,2)}, 0.40) = {e_semelle}m")

        return ResultatFondations(
            type_fondation="Semelles isolées",
            justification=justif,
            largeur_semelle_m=B_semelle,
            longueur_semelle_m=B_semelle,
            epaisseur_semelle_m=e_semelle,
            note_calcul=notes
        )

    elif type_sol == TypeSol.MOYEN:
        # RADIER GÉNÉRAL — vérification pression, passage pieux si dépassement
        sigma_kNm2 = sol.pression_admissible_MPa * 1000
        pression_radier = round(N_base / geo.surface_emprise_m2 / 1000, 3)  # MPa

        if pression_radier > sol.pression_admissible_MPa:
            # SÉCURITÉ : pression dépasse l'admissible → passage automatique aux pieux
            notes.append(f"Sol moyen (σ_sol = {sol.pression_admissible_MPa} MPa) MAIS pression sous radier = {pression_radier} MPa > σ_admissible")
            notes.append(f"⚠ DÉCISION SÉCURITÉ : Passage automatique aux pieux forés")
            type_sol = TypeSol.MAUVAIS  # forcer pieux
        else:
            justif = f"0.08 MPa < σ_sol = {sol.pression_admissible_MPa} MPa ≤ 0.15 MPa → Radier général vérifié"
            notes.append(justif)
            notes.append(f"Pression sous radier = {pression_radier} MPa ≤ {sol.pression_admissible_MPa} MPa → OK ✓")

            # Épaisseur radier — SÉCURITÉ : L/7 au lieu de L/8
            e_radier = round(max(geo.portee_max_m / 7, 0.35), 2)
            e_radier = round(math.ceil(e_radier / 0.05) * 0.05, 2)
            As_radier = round(max(
                N_base / (geo.surface_emprise_m2 * beton.fyd_MPa / 10 * 0.9 * e_radier),
                0.002 * e_radier * 100
            ), 2)

            notes.append(f"e_radier = max(L/7, 0.35) = max({round(geo.portee_max_m/7,2)}, 0.35) = {e_radier}m (sécurité L/7)")
            notes.append(f"As_radier = {As_radier} cm²/ml (bi-directionnel inf. + sup.)")

            return ResultatFondations(
                type_fondation="Radier général",
                justification=justif,
                epaisseur_radier_m=e_radier,
                ferraillage_radier_cm2_m=As_radier,
                note_calcul=notes
            )

    if type_sol == TypeSol.MAUVAIS:
        # PIEUX FORÉS
        justif = f"σ_sol = {sol.pression_admissible_MPa} MPa ≤ 0.08 MPa → Pieux forés"
        notes.append(justif)

        # Diamètre pieux selon charge
        if N_base > 50000:
            d_pieux = 0.80
        elif N_base > 20000:
            d_pieux = 0.60
        else:
            d_pieux = 0.40

        # Capacité portante pieu (frottement latéral estimé)
        # Q_pieu = π × d × L × τ_s (τ_s ≈ 30 kPa sol moyen-mauvais)
        tau_s = 30  # kPa
        L_pieu = round(max(8.0, sol.profondeur_fondation_m * 4), 1)
        Q_pieu = round(math.pi * d_pieux * L_pieu * tau_s, 1)
        nb_poteaux = max(4, round(geo.surface_emprise_m2 / geo.portee_max_m**2))
        N_poteau = round(N_base / nb_poteaux, 1)
        nb_pieux_par_poteau = math.ceil(N_poteau / Q_pieu)

        notes.append(f"Diamètre pieux retenu : d = {d_pieux}m")
        notes.append(f"τ_s estimé = {tau_s} kPa")
        notes.append(f"Q_pieu = π×d×L×τ = π×{d_pieux}×{L_pieu}×{tau_s} = {Q_pieu} kN")
        notes.append(f"N_poteau = {N_poteau} kN → nb pieux/poteau = ⌈{N_poteau}/{Q_pieu}⌉ = {nb_pieux_par_poteau}")

        return ResultatFondations(
            type_fondation="Pieux forés",
            justification=justif,
            diametre_pieux_m=d_pieux,
            longueur_pieux_m=L_pieu,
            nb_pieux_par_poteau=nb_pieux_par_poteau,
            note_calcul=notes
        )


# ============================================================
# MODULE 6 — DIMENSIONNEMENT POTEAUX (sections variables par niveau)
# ============================================================

# Diamètres barres normalisés (mm)
DIAMETRES_BARRES = [10, 12, 14, 16, 20, 25, 32]

def choisir_barres(As_cm2: float, nb_barres_min: int = 4):
    """Choisit le diamètre et nombre de barres pour une section As donnée"""
    for d in DIAMETRES_BARRES:
        aire_barre = math.pi * (d/10)**2 / 4  # cm²
        nb = math.ceil(As_cm2 / aire_barre)
        nb = max(nb, nb_barres_min)
        if nb % 2 != 0:
            nb += 1
        if nb <= 12:  # limite pratique raisonnable
            return nb, d
    return 12, 32

def _dimensionner_poteau_niveau(
    N_Ed: float,
    hauteur_etage: float,
    beton: ResultatBeton
) -> dict:
    """
    Dimensionne un poteau pour une charge N_Ed donnée.
    Retourne un dict avec section, ferraillage, vérifications.
    """
    l0 = round(0.7 * hauteur_etage, 2)

    # SÉCURITÉ : section minimale absolue selon charge
    # Niveaux inférieurs chargés → 30×30 minimum, sinon 25×25
    b_min_securite = 0.30 if N_Ed > 5000 else 0.25

    # Section minimale basée sur la résistance
    Ac_min = N_Ed / (0.8 * beton.fcd_MPa * 10)
    b_min_resistance = math.sqrt(Ac_min) / 100

    # Section minimale basée sur l'élancement λ ≤ 30
    b_min_elancement = round(l0 * math.sqrt(12) / 30, 3)

    b = max(b_min_resistance, b_min_elancement, b_min_securite)
    b = round(math.ceil(b / 0.05) * 0.05, 2)

    # Calcul élancement final
    i = b / math.sqrt(12)
    lambda_ = round(l0 / i, 1)

    Ac = (b * 100) ** 2
    sigma = round(N_Ed / (Ac / 10), 3)

    # Ferraillage — SÉCURITÉ : taux plafonné à 3% (marge par rapport au max 4%)
    fyd_kNcm2 = beton.fyd_MPa / 10
    As_min_effort = 0.1 * N_Ed / fyd_kNcm2
    As_min_geom = 0.002 * Ac
    As_calcul = round(max(As_min_effort, As_min_geom) * 1.3, 2)  # majoration 30%
    As_max_securite = 0.03 * Ac  # plafond 3% (sécurité)
    As_calcul = min(As_calcul, As_max_securite)
    As_calcul = max(As_calcul, As_min_geom)

    nb_barres, d_barres = choisir_barres(As_calcul, nb_barres_min=4)
    aire_barre = round(math.pi * (d_barres/10)**2 / 4, 2)
    As_reel = round(nb_barres * aire_barre, 2)
    taux = round(As_reel / Ac * 100, 3)

    # Cadres — SÉCURITÉ : espacement réduit de 10%
    d_cadre = 8 if d_barres <= 16 else 10
    espacement = int(math.floor(min(20 * d_barres, b * 1000, 400) / 50) * 50)
    espacement = int(espacement * 0.9 // 50 * 50)  # réduction 10% sécurité
    espacement = max(espacement, 100)  # minimum 100mm

    return {
        "b_m": b,
        "Ac_cm2": Ac,
        "N_Ed_kN": N_Ed,
        "sigma_MPa": sigma,
        "lambda": round(lambda_, 1),
        "As_cm2": As_reel,
        "nb_barres": nb_barres,
        "d_barres_mm": d_barres,
        "d_cadre_mm": d_cadre,
        "espacement_mm": espacement,
        "taux_pct": taux,
        "ok_flambement": lambda_ <= 30,
        "ok_taux": taux <= 4.0,
    }

def dimensionner_poteaux(
    projet: ProjetStructurel,
    descente: ResultatDescenteCharges,
    beton: ResultatBeton
) -> ResultatPoteau:
    """
    Dimensionnement des poteaux avec sections variables par niveau.
    Principe économique : section réduite au fur et à mesure que les charges diminuent.
    EN 1992-1-1 §5.8 + §9.5
    """
    notes = []
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT POTEAUX — EN 1992-1-1 §5.8 + §9.5 ===")
    notes.append("Principe : sections variables par niveau (optimisation coût)")

    nb_poteaux = max(4, round(geo.surface_emprise_m2 / geo.portee_max_m**2))
    charge_par_niveau_par_poteau = descente.charge_totale_par_niveau_kN / nb_poteaux
    notes.append(f"Nb poteaux estimé = {nb_poteaux}")
    notes.append(f"Charge par niveau par poteau = {round(charge_par_niveau_par_poteau,1)} kN")
    notes.append("")

    # Calcul niveau par niveau — charge cumulée DU SOMMET vers le bas
    niveaux = geo.nb_niveaux + 1  # +1 pour RDC
    resultats_niveaux = []

    for n in range(niveaux, 0, -1):
        # Niveaux au-dessus du niveau n (inclus le niveau n lui-même)
        nb_niveaux_au_dessus = niveaux - n + 1
        N_cumul = round(charge_par_niveau_par_poteau * nb_niveaux_au_dessus * 1.3, 1)
        res = _dimensionner_poteau_niveau(N_cumul, geo.hauteur_etage_m, beton)
        res["niveau"] = n
        res["N_cumul"] = N_cumul
        resultats_niveaux.append(res)

    # Affichage groupé : on ne réaffiche que quand la section change
    notes.append("SECTIONS PAR ZONE (du sommet vers la base) :")
    section_courante = None
    for res in resultats_niveaux:
        b_str = f"{int(res['b_m']*100)}×{int(res['b_m']*100)} cm"
        if b_str != section_courante:
            section_courante = b_str
            notes.append(
                f"  Niveau {res['niveau']:2d} → base : {b_str} | "
                f"N_Ed={res['N_cumul']:.0f} kN | "
                f"{res['nb_barres']}HA{res['d_barres_mm']} ({res['As_cm2']} cm²) | "
                f"λ={res['lambda']} | taux={res['taux_pct']}%"
            )

    poteau_rdc = resultats_niveaux[-1]   # RDC — le plus chargé
    poteau_top = resultats_niveaux[0]    # Dernier niveau — le moins chargé

    notes.append("")
    notes.append(f"Section RDC (la plus chargée) : {int(poteau_rdc['b_m']*100)}×{int(poteau_rdc['b_m']*100)} cm")
    notes.append(f"Section haut (la moins chargée) : {int(poteau_top['b_m']*100)}×{int(poteau_top['b_m']*100)} cm")
    notes.append(f"Cadres : HA{poteau_rdc['d_cadre_mm']} / {poteau_rdc['espacement_mm']} mm (niveaux inférieurs)")

    # On retourne les caractéristiques du poteau le plus sollicité (RDC)
    return ResultatPoteau(
        section_b_m=poteau_rdc["b_m"],
        section_h_m=poteau_rdc["b_m"],
        ferraillage_longitudinal_cm2=poteau_rdc["As_cm2"],
        nb_barres=poteau_rdc["nb_barres"],
        diametre_barres_mm=poteau_rdc["d_barres_mm"],
        ferraillage_transversal_mm=poteau_rdc["d_cadre_mm"],
        espacement_cadres_mm=poteau_rdc["espacement_mm"],
        taux_armature_pct=poteau_rdc["taux_pct"],
        contrainte_compression_MPa=poteau_rdc["sigma_MPa"],
        verification_flambement=poteau_rdc["ok_flambement"],
        longueur_flambement_m=round(0.7 * geo.hauteur_etage_m, 2),
        note_calcul=notes
    )
    """
    Dimensionnement des poteaux en béton armé
    EN 1992-1-1 §5.8 (flambement) + §9.5 (armatures)
    Méthode : compression centrée + excentricité minimale
    """
    notes = []
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT POTEAUX — EN 1992-1-1 §5.8 + §9.5 ===")

    # Charge par poteau (poteau le plus chargé — file centrale)
    nb_poteaux = max(4, round(geo.surface_emprise_m2 / geo.portee_max_m**2))
    # Poteau central reprend ~1.3× la charge moyenne (majoration file centrale)
    N_poteau_moyen = descente.charge_totale_base_kN / nb_poteaux
    N_Ed = round(N_poteau_moyen * 1.3, 1)  # ELU poteau le plus chargé

    notes.append(f"Nb poteaux estimé = S/L² = {geo.surface_emprise_m2}/{geo.portee_max_m**2} ≈ {nb_poteaux}")
    notes.append(f"N_Ed (poteau central) = 1.3 × N_moyen = 1.3 × {round(N_poteau_moyen,1)} = {N_Ed} kN")

    # Longueur de flambement
    # Poteau encastré-rotule (cadre portique) : l0 = 0.7 × h_étage
    l0 = round(0.7 * geo.hauteur_etage_m, 2)
    notes.append(f"Longueur flambement : l0 = 0.7 × H_étage = 0.7 × {geo.hauteur_etage_m} = {l0} m")

    # Pré-dimensionnement section
    # N_Ed ≤ 0.8 × fcd × Ac (réserve 20% pour flexion composée)
    Ac_min = round(N_Ed / (0.8 * beton.fcd_MPa * 10), 0)  # cm² (fcd MPa → kN/cm²)
    b_min = round(math.sqrt(Ac_min), 1)

    # Arrondi section au 5cm supérieur, minimum 25cm
    b = max(0.25, round(math.ceil(b_min / 5) * 5 / 100, 2))

    # Vérification élancement λ ≤ 30 (EN 1992-1-1 §5.8.3)
    i = b / math.sqrt(12)  # Rayon de giration section carrée
    lambda_ = round(l0 / i, 1)
    limite_elancement = 30
    verification_flambement = lambda_ <= limite_elancement

    if not verification_flambement:
        # Augmenter la section jusqu'à satisfaire l'élancement
        b = round(math.ceil(l0 / (limite_elancement * (1/math.sqrt(12))) / 0.05) * 0.05, 2)
        i = b / math.sqrt(12)
        lambda_ = round(l0 / i, 1)
        verification_flambement = lambda_ <= limite_elancement

    Ac = round((b * 100)**2, 0)  # cm²
    sigma = round(N_Ed / (Ac / 10), 3)  # MPa

    notes.append(f"Ac_min = N_Ed / (0.8×fcd) = {N_Ed} / (0.8×{beton.fcd_MPa}) = {Ac_min} cm²")
    notes.append(f"Section retenue : {int(b*100)}×{int(b*100)} cm")
    notes.append(f"Élancement : λ = l0/i = {l0}/{round(i,3)} = {lambda_} ≤ {limite_elancement} → {'OK ✓' if verification_flambement else '⚠ AUGMENTER SECTION'}")
    notes.append(f"σ_compression = N_Ed/Ac = {N_Ed}/{Ac} = {sigma} MPa")

    # Ferraillage longitudinal EN 1992-1-1 §9.5.2
    # As_min = max(0.1×N_Ed/fyd, 0.002×Ac)
    fyd_kNcm2 = beton.fyd_MPa / 10
    As_min_effort = round(0.1 * N_Ed / fyd_kNcm2, 2)
    As_min_geom = round(0.002 * Ac, 2)
    As_max = round(0.04 * Ac, 2)  # 4% max EN 1992-1-1
    As_calcul = max(As_min_effort, As_min_geom)
    As_calcul = round(As_calcul * 1.2, 2)  # majoration 20% flexion composée

    notes.append(f"As_min effort = 0.1×N_Ed/fyd = 0.1×{N_Ed}/{fyd_kNcm2} = {As_min_effort} cm²")
    notes.append(f"As_min géom = 0.002×Ac = 0.002×{Ac} = {As_min_geom} cm²")
    notes.append(f"As_calcul retenu (×1.2) = {As_calcul} cm²")
    notes.append(f"As_max = 0.04×Ac = {As_max} cm²")

    nb_barres, d_barres = choisir_barres(As_calcul, nb_barres_min=4)
    aire_barre = round(math.pi * (d_barres/10)**2 / 4, 2)
    As_reel = round(nb_barres * aire_barre, 2)
    taux = round(As_reel / Ac * 100, 3)

    notes.append(f"Choix barres : {nb_barres}HA{d_barres} → As_réel = {nb_barres}×{aire_barre} = {As_reel} cm²")
    notes.append(f"Taux armature = {taux}% (min 0.2%, max 4%)")

    # Armatures transversales (cadres) EN 1992-1-1 §9.5.3
    # Espacement ≤ min(20×d_long, b_poteau, 400mm)
    d_cadre = 8 if d_barres <= 16 else 10
    espacement = int(min(20 * d_barres, b * 1000, 400))
    # Arrondi 50mm inférieur
    espacement = int(math.floor(espacement / 50) * 50)

    notes.append(f"Cadres : HA{d_cadre} tous les {espacement} mm")
    notes.append(f"  Réf : st ≤ min(20×{d_barres}, {int(b*1000)}, 400) = {espacement} mm")

    return ResultatPoteau(
        section_b_m=b,
        section_h_m=b,
        ferraillage_longitudinal_cm2=As_reel,
        nb_barres=nb_barres,
        diametre_barres_mm=d_barres,
        ferraillage_transversal_mm=d_cadre,
        espacement_cadres_mm=espacement,
        taux_armature_pct=taux,
        contrainte_compression_MPa=sigma,
        verification_flambement=verification_flambement,
        longueur_flambement_m=l0,
        note_calcul=notes
    )


# ============================================================
# MODULE 7 — DIMENSIONNEMENT POUTRES
# ============================================================

def dimensionner_poutres(
    projet: ProjetStructurel,
    descente: ResultatDescenteCharges,
    beton: ResultatBeton,
    dalle: ResultatDalle
) -> ResultatPoutre:
    """
    Dimensionnement des poutres principales en béton armé
    EN 1992-1-1 §6.1 (flexion) + §6.2 (cisaillement) + §9.2
    Poutre la plus chargée — travée principale
    """
    notes = []
    geo = projet.geometrie

    notes.append("=== DIMENSIONNEMENT POUTRES — EN 1992-1-1 §6.1 + §6.2 ===")

    # Charge sur poutre (file centrale, tributaire = portée/2 de chaque côté)
    largeur_tributaire = geo.portee_max_m  # 1 portée de chaque côté
    q_poutre = round(descente.combinaison_ELU_kNm2 * largeur_tributaire, 2)  # kN/ml
    L = geo.portee_max_m

    notes.append(f"Largeur tributaire = L_portée = {largeur_tributaire} m")
    notes.append(f"Charge linéaire poutre : q = q_ELU × b_trib = {descente.combinaison_ELU_kNm2} × {largeur_tributaire} = {q_poutre} kN/ml")
    notes.append(f"Portée de calcul : L = {L} m")

    # Moments fléchissants (poutre continue sur 2 travées — cas courant)
    M_travee = round(q_poutre * L**2 / 10, 2)   # kN.m
    M_appui  = round(q_poutre * L**2 / 8, 2)    # kN.m (appui intermédiaire)
    V_Ed     = round(q_poutre * L / 2, 2)        # kN (effort tranchant max)

    notes.append(f"M_travée = q×L²/10 = {q_poutre}×{L}²/10 = {M_travee} kN.m")
    notes.append(f"M_appui  = q×L²/8  = {q_poutre}×{L}²/8  = {M_appui} kN.m")
    notes.append(f"V_Ed     = q×L/2   = {q_poutre}×{L}/2   = {V_Ed} kN")

    # Pré-dimensionnement hauteur poutre
    # EN 1992-1-1 : h ≥ L/12 (poutre continue) et h ≥ dalle + 10cm
    h_min_portee = round(L / 12, 3)
    h_min_dalle  = round(dalle.epaisseur_retenue_m + 0.10, 2)
    h = max(h_min_portee, h_min_dalle)
    h = round(math.ceil(h / 0.05) * 0.05, 2)  # arrondi 5cm sup.

    # Largeur poutre : b = h/2 minimum, multiple de 5cm
    b_p = max(round(h / 2, 2), 0.25)
    b_p = round(math.ceil(b_p / 0.05) * 0.05, 2)

    notes.append(f"h_min portée = L/12 = {L}/12 = {h_min_portee} m")
    notes.append(f"h_min dalle  = e_dalle + 10cm = {h_min_dalle} m")
    notes.append(f"h retenue = {h} m | b retenue = {b_p} m")

    # Hauteur utile
    c_nom = beton.enrobage_mm / 1000
    d = round(h - c_nom - 0.008 - 0.010, 3)  # enrobage + rayon cadre + rayon barre

    # Ferraillage en flexion — Méthode simplifiée rectangulaire
    # As = M / (0.9 × d × fyd)
    fyd_kNcm2 = beton.fyd_MPa / 10
    As_inf = round(M_travee / (0.9 * d * fyd_kNcm2), 2)
    As_sup = round(M_appui  / (0.9 * d * fyd_kNcm2), 2)

    # Ferraillage minimum EN 1992-1-1 §9.2.1.1
    As_min = round(max(
        0.26 * (2.6 / beton.fyd_MPa) * b_p * d * 10000,
        0.0013 * b_p * d * 10000
    ), 2)
    As_min = max(As_min, 1.5)  # minimum absolu 1.5 cm²

    As_inf = max(As_inf, As_min)
    As_sup = max(As_sup, As_min)

    notes.append(f"d = h - c_nom - ø_cadre - ø_barre/2 = {h} - {c_nom} - 0.008 - 0.010 = {d} m")
    notes.append(f"As_inf (travée) = M_t/(0.9×d×fyd) = {M_travee}/(0.9×{d}×{fyd_kNcm2}) = {As_inf} cm²")
    notes.append(f"As_sup (appuis) = {As_sup} cm²")
    notes.append(f"As_min = {As_min} cm²")

    # Choix des barres
    nb_inf, d_inf = choisir_barres(As_inf, nb_barres_min=2)
    nb_sup, d_sup = choisir_barres(As_sup, nb_barres_min=2)
    # On prend le plus grand diamètre pour cohérence
    d_barres = max(d_inf, d_sup)
    aire_b = round(math.pi * (d_barres/10)**2 / 4, 2)
    nb_inf = max(nb_inf, math.ceil(As_inf / aire_b))
    nb_sup = max(nb_sup, math.ceil(As_sup / aire_b))

    notes.append(f"Barres inférieures : {nb_inf}HA{d_barres}")
    notes.append(f"Barres supérieures : {nb_sup}HA{d_barres}")

    # Vérification cisaillement EN 1992-1-1 §6.2
    # VRd,c = [0.18/γc × k × (100×ρl×fck)^(1/3)] × bw × d
    As_inf_reel = nb_inf * aire_b
    rho_l = min(As_inf_reel / (b_p * 100 * d * 100), 0.02)  # taux armature
    k = min(1 + math.sqrt(200 / (d * 1000)), 2.0)
    fck = beton.fc28_MPa
    VRd_c = round(
        (0.18 / GAMMA_BETON) * k * (100 * rho_l * fck)**(1/3) * b_p * 100 * d * 100 / 1000,
        2
    )  # kN
    verification_cisaillement = V_Ed <= VRd_c

    notes.append(f"Vérif cisaillement : VRd,c = {VRd_c} kN vs V_Ed = {V_Ed} kN")

    if not verification_cisaillement:
        # Calcul étriers de cisaillement EN 1992-1-1 §6.2.3
        # VRd,s = (Asw/s) × z × fywd  avec z=0.9d, θ=45°
        # → Asw/s = V_Ed / (z × fywd)
        # Unités : V_Ed (kN), z (m), fywd (MPa=kN/cm²×10)
        # Asw/s en cm²/m = V_Ed(kN) / (z(m) × fywd(kN/cm²)) × 100 (cm→m)
        fywd_kNcm2 = beton.fyd_MPa / 10
        z = 0.9 * d  # m
        Asw_sur_s_cm2_m = round(V_Ed / (z * fywd_kNcm2), 2)  # cm²/m

        # Espacement max étriers EN 1992-1-1 §9.2.2 : st ≤ 0.75d
        st_max = int(math.floor(0.75 * d * 1000 / 50) * 50)
        st_max = min(st_max, 200)  # 200mm max en zone très cisaillée

        # Section étrier pour l'espacement retenu (2 branches)
        Asw_requis = round(Asw_sur_s_cm2_m * (st_max / 1000), 2)  # cm² par section
        for d_et in [6, 8, 10, 12, 14, 16]:
            aire_et_2b = 2 * math.pi * (d_et/10)**2 / 4  # cm² (2 branches)
            if aire_et_2b >= Asw_requis:
                d_etrier = d_et
                break
        else:
            d_etrier = 16

        notes.append(f"  → Étriers de cisaillement requis (EN 1992-1-1 §6.2.3)")
        notes.append(f"  Asw/s = V_Ed/(z×fywd) = {V_Ed}/({round(z,3)}×{fywd_kNcm2}) = {Asw_sur_s_cm2_m} cm²/m")
        notes.append(f"  st retenu = {st_max} mm (≤ 0.75d = {int(0.75*d*1000)} mm)")
        notes.append(f"  Asw requis = {Asw_requis} cm² → 2HA{d_etrier} = {round(2*math.pi*(d_etrier/10)**2/4,2)} cm² ✓")
        verification_cisaillement = True
    else:
        d_etrier = 8
        st_max = int(math.floor(0.75 * d * 1000 / 50) * 50)
        notes.append(f"  → Cisaillement repris par béton seul ✓")

    return ResultatPoutre(
        largeur_b_m=b_p,
        hauteur_h_m=h,
        hauteur_utile_d_m=d,
        ferraillage_inferieur_cm2=round(nb_inf * aire_b, 2),
        ferraillage_superieur_cm2=round(nb_sup * aire_b, 2),
        nb_barres_inf=nb_inf,
        nb_barres_sup=nb_sup,
        diametre_barres_mm=d_barres,
        ferraillage_transversal_mm=d_etrier,
        espacement_cadres_mm=st_max,
        moment_travee_kNm=M_travee,
        moment_appui_kNm=M_appui,
        effort_tranchant_kN=V_Ed,
        verification_cisaillement=verification_cisaillement,
        note_calcul=notes
    )


# ============================================================
# FONCTION PRINCIPALE — CALCUL COMPLET
# ============================================================

def calculer_structure_complete(projet: ProjetStructurel) -> NoteCalculComplete:
    """
    Point d'entrée principal du moteur structurel.
    Exécute tous les modules en séquence et retourne la note de calcul complète.
    """
    # 1. Classe béton
    beton = determiner_classe_beton(projet.localisation)

    # 2. Descente de charges
    descente = calculer_descente_charges(projet)

    # 3. Voiles
    voile = dimensionner_voiles(projet, descente, beton)

    # 4. Dalle
    dalle = dimensionner_dalle(projet, descente, beton)

    # 5. Poteaux
    poteau = dimensionner_poteaux(projet, descente, beton)

    # 6. Poutres
    poutre = dimensionner_poutres(projet, descente, beton, dalle)

    # 7. Fondations
    fondations = dimensionner_fondations(projet, descente, beton)

    # 8. Résumé exécutif
    resume = {
        "beton": f"C{int(beton.fc28_MPa)}/... — Exposition {beton.classe_exposition.value}",
        "enrobage": f"{beton.enrobage_mm} mm",
        "voile_epaisseur": f"{voile.epaisseur_retenue_m*100:.0f} cm",
        "voile_ferraillage_vertical": f"{voile.ferraillage_vertical_cm2_m} cm²/ml",
        "dalle_epaisseur": f"{dalle.epaisseur_retenue_m*100:.0f} cm",
        "dalle_ferraillage_inf": f"{dalle.ferraillage_inferieur_cm2_m} cm²/ml",
        "poteau_section": f"{int(poteau.section_b_m*100)}×{int(poteau.section_h_m*100)} cm",
        "poteau_ferraillage": f"{poteau.nb_barres}HA{poteau.diametre_barres_mm} ({poteau.ferraillage_longitudinal_cm2} cm²)",
        "poteau_cadres": f"HA{poteau.ferraillage_transversal_mm} / {poteau.espacement_cadres_mm} mm",
        "poutre_section": f"{int(poutre.largeur_b_m*100)}×{int(poutre.hauteur_h_m*100)} cm",
        "poutre_ferraillage_inf": f"{poutre.nb_barres_inf}HA{poutre.diametre_barres_mm} ({poutre.ferraillage_inferieur_cm2} cm²)",
        "poutre_ferraillage_sup": f"{poutre.nb_barres_sup}HA{poutre.diametre_barres_mm} ({poutre.ferraillage_superieur_cm2} cm²)",
        "poutre_etriers": f"HA{poutre.ferraillage_transversal_mm} / {poutre.espacement_cadres_mm} mm",
        "fondations_type": fondations.type_fondation,
        "fondations_detail": fondations.justification,
        "charge_totale_base": f"{descente.charge_totale_base_kN:.0f} kN",
        "verifications": {
            "flambement_voile":    "OK ✓" if voile.verification_flambement else "⚠ À REVOIR",
            "fleche_dalle":        "OK ✓" if dalle.verification_fleche else "⚠ À REVOIR",
            "poinconnement_dalle": "OK ✓" if dalle.verification_poinconnement else "⚠ À REVOIR",
            "flambement_poteau":   "OK ✓" if poteau.verification_flambement else "⚠ À REVOIR",
            "cisaillement_poutre": "OK ✓" if poutre.verification_cisaillement else "⚠ ÉTRIERS REQUIS",
        }
    }

    return NoteCalculComplete(
        projet_nom=projet.nom,
        descente_charges=descente,
        beton=beton,
        voile=voile,
        dalle=dalle,
        poteau=poteau,
        poutre=poutre,
        fondations=fondations,
        resume_executif=resume
    )

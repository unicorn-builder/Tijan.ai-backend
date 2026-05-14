"""
engine_planning.py -- Moteur de planification d'execution Tijan AI
==================================================================
Generates a construction execution schedule with:
  - Phased task breakdown (Structure, MEP, Finitions)
  - Realistic durations for West African construction
  - Critical path dependencies
  - Cost allocation (materiaux vs pose)
  - Monthly cash flow (tresorerie mensuelle)
  - Lot x phase cross-tabulation

References:
  - West African construction practice (6-day work weeks)
  - Duration benchmarks: R+3 residential ~400m2 emprise as baseline
  - Cost split ratios by trade (materiaux / main d'oeuvre)

Author: Tijan AI
Version: 1.0 -- May 2026
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


# ======================================================================
# DATA STRUCTURES
# ======================================================================

@dataclass
class Tache:
    """Single construction task with schedule and cost data."""
    id: str                         # e.g. "STR-1.1"
    lot: str                        # "STRUCTURE", "MEP", "FINITIONS"
    sous_lot: str                   # e.g. "Installation chantier"
    designation: str                # Task name (French, user-facing)
    duree_jours: int                # Duration in working days
    debut_jour: int                 # Start day (from project start, 1-based)
    fin_jour: int                   # End day
    predecesseurs: List[str]        # List of predecessor task IDs
    cout_materiel_fcfa: int         # Material/equipment cost
    cout_pose_fcfa: int             # Installation/labor cost
    cout_total_fcfa: int            # Total cost
    mois_debut: int                 # Starting month (1-based)
    mois_fin: int                   # Ending month


@dataclass
class Phase:
    """Grouped phase for Gantt display."""
    id: str                         # e.g. "PH-1"
    nom: str                        # Phase name (French)
    debut_jour: int
    fin_jour: int
    duree_jours: int
    taches: List[str]               # Task IDs in this phase
    cout_total_fcfa: int


@dataclass
class Planning:
    """Complete construction execution planning."""
    projet_nom: str
    ville: str
    nb_niveaux: int
    surface_batie_m2: float
    duree_totale_jours: int
    duree_totale_mois: int
    taches: List[Tache]
    phases: List[Phase]
    tresorerie_mensuelle: List[dict]     # Monthly cash flow
    tresorerie_lot_phase: List[dict]     # Lot x phase cross-tabulation
    cout_total_fcfa: int


# ======================================================================
# CONSTANTS -- Baseline durations for R+3, ~400m2 emprise
# ======================================================================

# Working days per month (6-day weeks, ~26 working days/month)
JOURS_OUVRES_PAR_MOIS = 26

# Baseline surface for scaling (m2 emprise)
SURFACE_BASELINE_M2 = 400.0

# Baseline number of levels for reference
NIVEAUX_BASELINE = 4  # R+3 = 4 levels (RDC + 3)

# --- Duration baselines (working days) for ~400m2 emprise R+3 ---
DUREE_INSTALLATION_CHANTIER = 15
DUREE_TERRASSEMENT = 20
DUREE_FONDATIONS_SEMELLES = 30
DUREE_FONDATIONS_PIEUX = 45
DUREE_STRUCTURE_BA_PAR_NIVEAU = 28  # coffrage + ferraillage + coulage + cure
DUREE_MACONNERIE_PAR_NIVEAU = 20
DUREE_ETANCHEITE = 10
DUREE_PLOMBERIE_PAR_NIVEAU = 15
DUREE_ELEC_CF_PAR_NIVEAU = 15
DUREE_ELEC_CFA_PAR_NIVEAU = 10
DUREE_CVC_PAR_NIVEAU = 12
DUREE_SECURITE_INCENDIE = 8
DUREE_ASCENSEURS = 30
DUREE_FINITIONS_PAR_NIVEAU = 20

# --- Cost split ratios (materiaux fraction) ---
RATIO_MAT = {
    "terrassement":         0.40,
    "fondations":           0.65,
    "structure_ba":         0.70,
    "maconnerie":           0.55,
    "etancheite":           0.60,
    "plomberie":            0.65,
    "electricite_cf":       0.65,
    "electricite_cfa":      0.65,
    "cvc":                  0.65,
    "securite_incendie":    0.65,
    "ascenseurs":           0.75,
    "finitions_carrelage":  0.50,
    "finitions_menuiserie": 0.50,
    "finitions_peinture":   0.50,
    "finitions_faux_plafond": 0.50,
    "finitions_plomberie_sanitaire": 0.50,
    "finitions_serrurerie": 0.50,
    "installation_chantier": 0.30,
}

# Finitions sub-categories with relative weight (fraction of total finitions cost)
FINITIONS_CATEGORIES = [
    ("Carrelage et revetements de sol", "finitions_carrelage", 0.25),
    ("Menuiserie bois et aluminium", "finitions_menuiserie", 0.20),
    ("Peinture et enduits", "finitions_peinture", 0.20),
    ("Faux-plafonds", "finitions_faux_plafond", 0.10),
    ("Plomberie sanitaire (appareils)", "finitions_plomberie_sanitaire", 0.15),
    ("Serrurerie et metallerie", "finitions_serrurerie", 0.10),
]


# ======================================================================
# HELPER -- Scale duration by surface and complexity
# ======================================================================

def _scale_duration(base_days: int, surface_m2: float, per_level: bool = False) -> int:
    """
    Scale a baseline duration by surface ratio.
    Scaling is sub-linear: uses sqrt ratio to avoid unrealistic durations
    for very large buildings. Minimum 1 day.
    """
    ratio = surface_m2 / SURFACE_BASELINE_M2
    # Sub-linear scaling: more surface -> more time but not proportionally
    factor = math.sqrt(ratio) if ratio > 1.0 else ratio ** 0.7
    scaled = max(1, round(base_days * factor))
    return scaled


def _jour_vers_mois(jour: int) -> int:
    """Convert working day number (1-based) to month number (1-based)."""
    return max(1, math.ceil(jour / JOURS_OUVRES_PAR_MOIS))


# ======================================================================
# COST EXTRACTION -- Pull costs from engine results
# ======================================================================

def _extract_structure_costs(rs_structure) -> dict:
    """
    Extract cost breakdown from ResultatsStructure.boq.
    Returns dict with keys matching task categories.
    """
    boq = rs_structure.boq
    return {
        "terrassement":     int(boq.cout_terr_fcfa),
        "fondations":       int(boq.cout_fond_fcfa),
        "beton_structure":  int(boq.cout_beton_fcfa),
        "acier":            int(boq.cout_acier_fcfa),
        "coffrage":         int(boq.cout_coffrage_fcfa),
        "maconnerie":       int(boq.cout_maco_fcfa),
        "etancheite":       int(boq.cout_etanch_fcfa),
        "divers":           int(boq.cout_divers_fcfa),
        "total_bas":        int(boq.total_bas_fcfa),
        "total_haut":       int(boq.total_haut_fcfa),
    }


def _extract_mep_costs(rs_mep) -> dict:
    """
    Extract cost breakdown from ResultatsMEP.boq.
    Returns dict keyed by lot designation with basic cost.
    """
    costs = {}
    if rs_mep is None or rs_mep.boq is None:
        return costs
    for lot_item in rs_mep.boq.lots:
        key = lot_item.lot.lower().strip()
        cost = int(lot_item.quantite * lot_item.pu_basic_fcfa)
        costs[key] = costs.get(key, 0) + cost
    costs["total_basic"] = int(rs_mep.boq.total_basic_fcfa)
    return costs


def _estimate_finitions_cost(surface_batie_m2: float, nb_niveaux: int) -> int:
    """
    Estimate finitions cost when not provided by engines.
    Uses West African market average: ~45,000-65,000 FCFA/m2 for finitions.
    """
    # Average finitions cost per m2 of built surface
    cout_m2 = 55_000  # FCFA/m2 (mid-range residential)
    return int(surface_batie_m2 * cout_m2)


# ======================================================================
# TASK GENERATION -- Build task list with dependencies
# ======================================================================

def _build_structure_tasks(
    nb_niveaux: int,
    surface_emprise: float,
    fondation_type: str,
    costs: dict,
) -> Tuple[List[Tache], int]:
    """
    Build structure lot tasks and return (tasks, last_day).
    nb_niveaux: total levels including RDC (R+3 = 4 levels).
    """
    taches = []
    jour = 1

    # --- 1. Installation chantier ---
    duree = _scale_duration(DUREE_INSTALLATION_CHANTIER, surface_emprise)
    # Cost: ~2% of structure total or from divers
    cout_install = max(costs.get("divers", 0), int(costs.get("total_bas", 0) * 0.02))
    mat_ratio = RATIO_MAT["installation_chantier"]
    t = Tache(
        id="STR-1.1",
        lot="STRUCTURE",
        sous_lot="Installation chantier",
        designation="Installation de chantier, cloture, base vie",
        duree_jours=duree,
        debut_jour=jour,
        fin_jour=jour + duree - 1,
        predecesseurs=[],
        cout_materiel_fcfa=int(cout_install * mat_ratio),
        cout_pose_fcfa=int(cout_install * (1 - mat_ratio)),
        cout_total_fcfa=cout_install,
        mois_debut=_jour_vers_mois(jour),
        mois_fin=_jour_vers_mois(jour + duree - 1),
    )
    taches.append(t)
    jour += duree

    # --- 2. Terrassement ---
    duree = _scale_duration(DUREE_TERRASSEMENT, surface_emprise)
    cout_terr = costs.get("terrassement", 0)
    mat_ratio = RATIO_MAT["terrassement"]
    t = Tache(
        id="STR-2.1",
        lot="STRUCTURE",
        sous_lot="Terrassement",
        designation="Terrassement general, fouilles, evacuation des terres",
        duree_jours=duree,
        debut_jour=jour,
        fin_jour=jour + duree - 1,
        predecesseurs=["STR-1.1"],
        cout_materiel_fcfa=int(cout_terr * mat_ratio),
        cout_pose_fcfa=int(cout_terr * (1 - mat_ratio)),
        cout_total_fcfa=cout_terr,
        mois_debut=_jour_vers_mois(jour),
        mois_fin=_jour_vers_mois(jour + duree - 1),
    )
    taches.append(t)
    jour += duree

    # --- 3. Fondations ---
    is_pieux = "pieu" in fondation_type.lower()
    duree_base = DUREE_FONDATIONS_PIEUX if is_pieux else DUREE_FONDATIONS_SEMELLES
    duree = _scale_duration(duree_base, surface_emprise)
    cout_fond = costs.get("fondations", 0)
    mat_ratio = RATIO_MAT["fondations"]
    designation = "Fondations profondes (pieux fores)" if is_pieux else "Fondations superficielles (semelles)"
    t = Tache(
        id="STR-3.1",
        lot="STRUCTURE",
        sous_lot="Fondations",
        designation=designation,
        duree_jours=duree,
        debut_jour=jour,
        fin_jour=jour + duree - 1,
        predecesseurs=["STR-2.1"],
        cout_materiel_fcfa=int(cout_fond * mat_ratio),
        cout_pose_fcfa=int(cout_fond * (1 - mat_ratio)),
        cout_total_fcfa=cout_fond,
        mois_debut=_jour_vers_mois(jour),
        mois_fin=_jour_vers_mois(jour + duree - 1),
    )
    taches.append(t)
    jour += duree

    # --- 4. Structure BA per level ---
    # Distribute structure cost (beton + acier + coffrage) across levels
    cout_structure_total = (
        costs.get("beton_structure", 0)
        + costs.get("acier", 0)
        + costs.get("coffrage", 0)
    )
    cout_structure_par_niveau = int(cout_structure_total / max(nb_niveaux, 1))
    mat_ratio = RATIO_MAT["structure_ba"]

    prev_structure_id = "STR-3.1"
    structure_ids_par_niveau = {}

    for i in range(nb_niveaux):
        level_name = "RDC" if i == 0 else f"R+{i}"
        task_id = f"STR-4.{i + 1}"
        duree = _scale_duration(DUREE_STRUCTURE_BA_PAR_NIVEAU, surface_emprise)

        t = Tache(
            id=task_id,
            lot="STRUCTURE",
            sous_lot="Structure beton arme",
            designation=f"Structure BA {level_name} (poteaux, poutres, dalle)",
            duree_jours=duree,
            debut_jour=jour,
            fin_jour=jour + duree - 1,
            predecesseurs=[prev_structure_id],
            cout_materiel_fcfa=int(cout_structure_par_niveau * mat_ratio),
            cout_pose_fcfa=int(cout_structure_par_niveau * (1 - mat_ratio)),
            cout_total_fcfa=cout_structure_par_niveau,
            mois_debut=_jour_vers_mois(jour),
            mois_fin=_jour_vers_mois(jour + duree - 1),
        )
        taches.append(t)
        structure_ids_par_niveau[i] = task_id
        prev_structure_id = task_id
        jour += duree

    dernier_jour_structure = jour - 1

    # --- 5. Maconnerie per level (starts 1 level behind structure) ---
    cout_maco_total = costs.get("maconnerie", 0)
    cout_maco_par_niveau = int(cout_maco_total / max(nb_niveaux, 1))
    mat_ratio = RATIO_MAT["maconnerie"]

    maco_ids_par_niveau = {}
    # Maconnerie for level i can start when structure level i is done
    for i in range(nb_niveaux):
        level_name = "RDC" if i == 0 else f"R+{i}"
        task_id = f"STR-5.{i + 1}"
        duree = _scale_duration(DUREE_MACONNERIE_PAR_NIVEAU, surface_emprise)

        # Maconnerie Ni depends on Structure Ni being done
        pred = [structure_ids_par_niveau[i]]
        # Also depends on previous maconnerie level (sequential within trade)
        if i > 0:
            pred.append(f"STR-5.{i}")

        # Start after all predecessors are done
        pred_ends = [_find_task_end(taches, p) for p in pred]
        debut = max(pred_ends) + 1

        t = Tache(
            id=task_id,
            lot="STRUCTURE",
            sous_lot="Maconnerie",
            designation=f"Maconnerie {level_name} (cloisons, murs de remplissage)",
            duree_jours=duree,
            debut_jour=debut,
            fin_jour=debut + duree - 1,
            predecesseurs=pred,
            cout_materiel_fcfa=int(cout_maco_par_niveau * mat_ratio),
            cout_pose_fcfa=int(cout_maco_par_niveau * (1 - mat_ratio)),
            cout_total_fcfa=cout_maco_par_niveau,
            mois_debut=_jour_vers_mois(debut),
            mois_fin=_jour_vers_mois(debut + duree - 1),
        )
        taches.append(t)
        maco_ids_par_niveau[i] = task_id

    # --- 6. Etancheite (after last structure level) ---
    duree = _scale_duration(DUREE_ETANCHEITE, surface_emprise)
    cout_etanch = costs.get("etancheite", 0)
    mat_ratio = RATIO_MAT["etancheite"]

    debut = _find_task_end(taches, structure_ids_par_niveau[nb_niveaux - 1]) + 1

    t = Tache(
        id="STR-6.1",
        lot="STRUCTURE",
        sous_lot="Etancheite",
        designation="Etancheite terrasse et toiture",
        duree_jours=duree,
        debut_jour=debut,
        fin_jour=debut + duree - 1,
        predecesseurs=[structure_ids_par_niveau[nb_niveaux - 1]],
        cout_materiel_fcfa=int(cout_etanch * mat_ratio),
        cout_pose_fcfa=int(cout_etanch * (1 - mat_ratio)),
        cout_total_fcfa=cout_etanch,
        mois_debut=_jour_vers_mois(debut),
        mois_fin=_jour_vers_mois(debut + duree - 1),
    )
    taches.append(t)

    # Return all tasks and the last day across all structure tasks
    dernier_jour = max(t.fin_jour for t in taches)
    return taches, dernier_jour, maco_ids_par_niveau


def _find_task_end(taches: List[Tache], task_id: str) -> int:
    """Find the end day of a task by its ID."""
    for t in taches:
        if t.id == task_id:
            return t.fin_jour
    return 0


def _build_mep_tasks(
    nb_niveaux: int,
    surface_emprise: float,
    nb_logements: int,
    maco_ids_par_niveau: dict,
    all_taches: List[Tache],
    mep_costs: dict,
    has_ascenseur: bool,
    structure_ids_par_niveau_count: int,
) -> List[Tache]:
    """
    Build MEP lot tasks. MEP per level starts after maconnerie of that level.
    Plomberie, Electricite CF, Electricite CFA, CVC run in parallel per level.
    """
    taches = []

    # Estimate MEP cost distribution if we have a total
    total_mep = mep_costs.get("total_basic", 0)
    if total_mep == 0:
        # Fallback: estimate from surface
        total_mep = int(surface_emprise * nb_niveaux * 35_000)

    # Cost allocation per MEP trade (approximate distribution)
    mep_trade_weights = {
        "plomberie":        0.20,
        "electricite_cf":   0.25,
        "electricite_cfa":  0.10,
        "cvc":              0.25,
        "securite_incendie": 0.05,
        "ascenseurs":       0.15,
    }

    if not has_ascenseur:
        # Redistribute ascenseur weight
        mep_trade_weights["ascenseurs"] = 0.0
        remaining = 0.15
        for k in ["plomberie", "electricite_cf", "cvc"]:
            mep_trade_weights[k] += remaining / 3

    # Use actual costs from BOQ if available, otherwise use weights
    trade_costs = {}
    for trade, weight in mep_trade_weights.items():
        # Try to find matching cost from MEP BOQ
        matched = 0
        for key, val in mep_costs.items():
            if trade.split("_")[0] in key:
                matched = val
                break
        trade_costs[trade] = matched if matched > 0 else int(total_mep * weight)

    # Scaling factor for logements
    logement_factor = max(1.0, math.sqrt(nb_logements / 8.0)) if nb_logements > 0 else 1.0

    # --- Per-level MEP tasks ---
    mep_per_level_trades = [
        ("plomberie", "MEP-1", "Plomberie", "Plomberie {level} (alimentation, evacuation, colonnes)",
         DUREE_PLOMBERIE_PAR_NIVEAU),
        ("electricite_cf", "MEP-2", "Electricite courants forts",
         "Electricite CF {level} (tableau, circuits, prises, eclairage)",
         DUREE_ELEC_CF_PAR_NIVEAU),
        ("electricite_cfa", "MEP-3", "Electricite courants faibles",
         "Electricite CFA {level} (reseau, telephone, TV, interphone)",
         DUREE_ELEC_CFA_PAR_NIVEAU),
        ("cvc", "MEP-4", "CVC", "CVC {level} (climatisation, ventilation)",
         DUREE_CVC_PAR_NIVEAU),
    ]

    mep_end_ids_par_niveau = {}  # track last MEP task per level

    for i in range(nb_niveaux):
        level_name = "RDC" if i == 0 else f"R+{i}"
        level_mep_ids = []

        for trade_key, prefix, sous_lot, designation_tpl, base_duree in mep_per_level_trades:
            task_id = f"{prefix}.{i + 1}"
            duree = _scale_duration(base_duree, surface_emprise)
            # Slight scaling with logements for plomberie and elec
            if trade_key in ("plomberie", "electricite_cf"):
                duree = max(duree, round(duree * logement_factor * 0.8))

            cout_trade_total = trade_costs.get(trade_key, 0)
            cout_par_niveau = int(cout_trade_total / max(nb_niveaux, 1))
            mat_ratio = RATIO_MAT.get(trade_key, 0.65)

            # MEP depends on maconnerie of same level
            pred_id = maco_ids_par_niveau.get(i)
            pred = [pred_id] if pred_id else []
            # Also depends on same trade previous level
            if i > 0:
                prev_id = f"{prefix}.{i}"
                pred.append(prev_id)

            debut = max(
                (_find_task_end(all_taches + taches, p) for p in pred),
                default=0,
            ) + 1

            t = Tache(
                id=task_id,
                lot="MEP",
                sous_lot=sous_lot,
                designation=designation_tpl.format(level=level_name),
                duree_jours=duree,
                debut_jour=debut,
                fin_jour=debut + duree - 1,
                predecesseurs=pred,
                cout_materiel_fcfa=int(cout_par_niveau * mat_ratio),
                cout_pose_fcfa=int(cout_par_niveau * (1 - mat_ratio)),
                cout_total_fcfa=cout_par_niveau,
                mois_debut=_jour_vers_mois(debut),
                mois_fin=_jour_vers_mois(debut + duree - 1),
            )
            taches.append(t)
            level_mep_ids.append(task_id)

        mep_end_ids_par_niveau[i] = level_mep_ids

    # --- Securite incendie (global, after all MEP level tasks) ---
    duree = _scale_duration(DUREE_SECURITE_INCENDIE, surface_emprise)
    # Scale with nb_niveaux
    duree = max(duree, round(duree * math.sqrt(nb_niveaux / NIVEAUX_BASELINE)))
    cout_si = trade_costs.get("securite_incendie", 0)
    mat_ratio = RATIO_MAT["securite_incendie"]

    all_mep_ids = [tid for ids in mep_end_ids_par_niveau.values() for tid in ids]
    last_mep_day = max(
        (_find_task_end(all_taches + taches, tid) for tid in all_mep_ids),
        default=0,
    )

    # Securite incendie depends on last level MEP completion
    last_level_mep_ids = mep_end_ids_par_niveau.get(nb_niveaux - 1, [])
    debut = last_mep_day + 1

    t = Tache(
        id="MEP-5.1",
        lot="MEP",
        sous_lot="Securite incendie",
        designation="Securite incendie (detection, RIA, extincteurs, desenfumage)",
        duree_jours=duree,
        debut_jour=debut,
        fin_jour=debut + duree - 1,
        predecesseurs=last_level_mep_ids,
        cout_materiel_fcfa=int(cout_si * mat_ratio),
        cout_pose_fcfa=int(cout_si * (1 - mat_ratio)),
        cout_total_fcfa=cout_si,
        mois_debut=_jour_vers_mois(debut),
        mois_fin=_jour_vers_mois(debut + duree - 1),
    )
    taches.append(t)

    # --- Ascenseurs (starts after structure N2, ends with finitions) ---
    if has_ascenseur and nb_niveaux >= 3:
        duree = _scale_duration(DUREE_ASCENSEURS, surface_emprise)
        # Scale with height
        duree = max(duree, round(duree * math.sqrt(nb_niveaux / NIVEAUX_BASELINE)))
        cout_asc = trade_costs.get("ascenseurs", 0)
        mat_ratio = RATIO_MAT["ascenseurs"]

        # Ascenseur starts after structure of level 2 (R+1)
        struct_n2_id = f"STR-4.{min(3, structure_ids_par_niveau_count)}"
        debut_asc = _find_task_end(all_taches, struct_n2_id) + 1
        if debut_asc <= 1:
            debut_asc = _find_task_end(all_taches, "STR-4.1") + 1

        t = Tache(
            id="MEP-6.1",
            lot="MEP",
            sous_lot="Ascenseurs",
            designation="Ascenseurs (genie civil, guide rails, cabine, mise en service)",
            duree_jours=duree,
            debut_jour=debut_asc,
            fin_jour=debut_asc + duree - 1,
            predecesseurs=[struct_n2_id],
            cout_materiel_fcfa=int(cout_asc * mat_ratio),
            cout_pose_fcfa=int(cout_asc * (1 - mat_ratio)),
            cout_total_fcfa=cout_asc,
            mois_debut=_jour_vers_mois(debut_asc),
            mois_fin=_jour_vers_mois(debut_asc + duree - 1),
        )
        taches.append(t)

    return taches


def _build_finitions_tasks(
    nb_niveaux: int,
    surface_emprise: float,
    surface_batie: float,
    mep_end_ids_par_niveau: dict,
    all_taches: List[Tache],
    finitions_cost: int,
) -> List[Tache]:
    """
    Build finitions tasks. Per level, starts after MEP of that level is done.
    Finitions sub-categories run sequentially within each level but levels
    can partially overlap.
    """
    taches = []
    task_counter = 0

    cout_par_niveau = int(finitions_cost / max(nb_niveaux, 1))

    for i in range(nb_niveaux):
        level_name = "RDC" if i == 0 else f"R+{i}"

        # Find when MEP for this level ends
        level_mep_ids = mep_end_ids_par_niveau.get(i, [])
        if not level_mep_ids:
            # Fallback: use last known task
            mep_end_day = max((t.fin_jour for t in all_taches), default=0)
        else:
            mep_end_day = max(
                (_find_task_end(all_taches + taches, tid) for tid in level_mep_ids),
                default=0,
            )

        # Also depend on previous level finitions being partially done
        if i > 0:
            # Can start when previous level is ~50% through finitions
            prev_fin_first_id = f"FIN-{(i - 1) * len(FINITIONS_CATEGORIES) + 1}"
            prev_end = _find_task_end(all_taches + taches, prev_fin_first_id)
            mep_end_day = max(mep_end_day, prev_end)

        debut_level = mep_end_day + 1

        for j, (cat_name, cat_key, weight) in enumerate(FINITIONS_CATEGORIES):
            task_counter += 1
            task_id = f"FIN-{task_counter}"
            duree = max(3, _scale_duration(
                round(DUREE_FINITIONS_PAR_NIVEAU * weight * 2),  # scale by category weight
                surface_emprise,
            ))

            cout_cat = int(cout_par_niveau * weight)
            mat_ratio = RATIO_MAT.get(cat_key, 0.50)

            pred = []
            if j == 0:
                # First finitions category depends on MEP
                pred = level_mep_ids[:1] if level_mep_ids else []
            else:
                # Sequential within level
                pred = [f"FIN-{task_counter - 1}"]

            debut = debut_level if j == 0 else _find_task_end(
                all_taches + taches, pred[0] if pred else ""
            ) + 1

            t = Tache(
                id=task_id,
                lot="FINITIONS",
                sous_lot=cat_name,
                designation=f"{cat_name} {level_name}",
                duree_jours=duree,
                debut_jour=debut,
                fin_jour=debut + duree - 1,
                predecesseurs=pred,
                cout_materiel_fcfa=int(cout_cat * mat_ratio),
                cout_pose_fcfa=int(cout_cat * (1 - mat_ratio)),
                cout_total_fcfa=cout_cat,
                mois_debut=_jour_vers_mois(debut),
                mois_fin=_jour_vers_mois(debut + duree - 1),
            )
            taches.append(t)

            if j == 0:
                debut_level = debut  # align subsequent tasks

    return taches


# ======================================================================
# PHASE GROUPING
# ======================================================================

def _group_phases(taches: List[Tache]) -> List[Phase]:
    """Group tasks into construction phases for Gantt display."""
    phase_defs = [
        ("PH-1", "Preparation du chantier", ["STR-1.1", "STR-2.1"]),
        ("PH-2", "Fondations", ["STR-3.1"]),
        ("PH-3", "Gros oeuvre (Structure BA)", None),  # all STR-4.x
        ("PH-4", "Second oeuvre (Maconnerie)", None),   # all STR-5.x
        ("PH-5", "Etancheite", ["STR-6.1"]),
        ("PH-6", "Corps d'etat techniques (MEP)", None),  # all MEP-x
        ("PH-7", "Finitions et amenagements", None),      # all FIN-x
    ]

    phases = []
    for ph_id, ph_nom, explicit_ids in phase_defs:
        if explicit_ids:
            ph_taches = [t for t in taches if t.id in explicit_ids]
        elif "Structure BA" in ph_nom:
            ph_taches = [t for t in taches if t.id.startswith("STR-4.")]
        elif "Maconnerie" in ph_nom:
            ph_taches = [t for t in taches if t.id.startswith("STR-5.")]
        elif "MEP" in ph_nom:
            ph_taches = [t for t in taches if t.lot == "MEP"]
        elif "Finitions" in ph_nom:
            ph_taches = [t for t in taches if t.lot == "FINITIONS"]
        else:
            ph_taches = []

        if not ph_taches:
            continue

        debut = min(t.debut_jour for t in ph_taches)
        fin = max(t.fin_jour for t in ph_taches)
        cout = sum(t.cout_total_fcfa for t in ph_taches)

        phases.append(Phase(
            id=ph_id,
            nom=ph_nom,
            debut_jour=debut,
            fin_jour=fin,
            duree_jours=fin - debut + 1,
            taches=[t.id for t in ph_taches],
            cout_total_fcfa=cout,
        ))

    return phases


# ======================================================================
# CASH FLOW (TRESORERIE)
# ======================================================================

def generer_tresorerie(planning: "Planning") -> dict:
    """
    Generate monthly and lot x phase cash flow from planning.

    Tresorerie mensuelle: for each month, sum costs of all active tasks,
    proportioned by their overlap with that month.

    Tresorerie lot x phase: group by (lot, phase_name) and sum costs.

    Returns dict with keys 'mensuelle' and 'lot_phase'.
    """
    if not planning.taches:
        return {"mensuelle": [], "lot_phase": []}

    # --- Monthly cash flow ---
    nb_mois = planning.duree_totale_mois
    mensuelle = []

    for mois in range(1, nb_mois + 1):
        mois_debut_jour = (mois - 1) * JOURS_OUVRES_PAR_MOIS + 1
        mois_fin_jour = mois * JOURS_OUVRES_PAR_MOIS

        depense_materiel = 0
        depense_pose = 0
        depense_total = 0

        for t in planning.taches:
            if t.fin_jour < mois_debut_jour or t.debut_jour > mois_fin_jour:
                continue  # Task not active this month
            if t.duree_jours <= 0:
                continue

            # Calculate overlap fraction
            overlap_start = max(t.debut_jour, mois_debut_jour)
            overlap_end = min(t.fin_jour, mois_fin_jour)
            overlap_days = max(0, overlap_end - overlap_start + 1)
            fraction = overlap_days / t.duree_jours

            depense_materiel += int(t.cout_materiel_fcfa * fraction)
            depense_pose += int(t.cout_pose_fcfa * fraction)
            depense_total += int(t.cout_total_fcfa * fraction)

        mensuelle.append({
            "mois": mois,
            "depense_materiel_fcfa": depense_materiel,
            "depense_pose_fcfa": depense_pose,
            "depense_total_fcfa": depense_total,
            "cumul_fcfa": 0,  # filled below
        })

    # Compute cumulative
    cumul = 0
    for m in mensuelle:
        cumul += m["depense_total_fcfa"]
        m["cumul_fcfa"] = cumul

    # --- Lot x Phase cross-tabulation ---
    # Map task to phase
    task_to_phase = {}
    for phase in planning.phases:
        for tid in phase.taches:
            task_to_phase[tid] = phase.nom

    lot_phase_map = {}  # (lot, phase_name) -> cost
    for t in planning.taches:
        phase_name = task_to_phase.get(t.id, "Autre")
        key = (t.lot, phase_name)
        if key not in lot_phase_map:
            lot_phase_map[key] = {
                "lot": t.lot,
                "phase": phase_name,
                "cout_materiel_fcfa": 0,
                "cout_pose_fcfa": 0,
                "cout_total_fcfa": 0,
            }
        lot_phase_map[key]["cout_materiel_fcfa"] += t.cout_materiel_fcfa
        lot_phase_map[key]["cout_pose_fcfa"] += t.cout_pose_fcfa
        lot_phase_map[key]["cout_total_fcfa"] += t.cout_total_fcfa

    lot_phase = list(lot_phase_map.values())

    return {"mensuelle": mensuelle, "lot_phase": lot_phase}


# ======================================================================
# MAIN ENTRY POINT
# ======================================================================

def generer_planning(rs_structure, rs_mep, params: dict) -> Planning:
    """
    Generate construction execution planning.

    Args:
        rs_structure: ResultatsStructure from engine_structure_v2.
        rs_mep: ResultatsMEP from engine_mep_v2 (can be None).
        params: dict with keys:
            - nom (str): project name
            - ville (str): city
            - nb_niveaux (int): total levels including RDC
            - surface_emprise_m2 (float): footprint area
            - nb_logements (int, optional): number of housing units
            - usage (str, optional): project usage type

    Returns:
        Planning: complete planning with tasks, phases, cash flow.
    """
    # --- Extract parameters ---
    nom = params.get("nom", "Projet Tijan")
    ville = params.get("ville", "Dakar")
    nb_niveaux = max(1, params.get("nb_niveaux", 1))
    surface_emprise = max(50.0, params.get("surface_emprise_m2", 400.0))
    surface_batie = surface_emprise * nb_niveaux
    nb_logements = params.get("nb_logements", 0)
    usage = params.get("usage", "residentiel")

    # If nb_logements not provided, estimate
    if nb_logements <= 0:
        if usage in ("residentiel", "hotel"):
            # ~1 logement per 80m2 of built surface
            nb_logements = max(1, round(surface_batie / 80))
        else:
            nb_logements = max(1, round(surface_batie / 120))

    # --- Detect foundation type ---
    fondation_type = "semelle"
    if rs_structure is not None:
        try:
            fondation_type = rs_structure.fondation.type.value
        except (AttributeError, TypeError):
            fondation_type = str(getattr(
                getattr(rs_structure, "fondation", None), "type", "semelle"
            ))

    # --- Detect ascenseur ---
    has_ascenseur = nb_niveaux >= 5  # R+4 and above typically have elevator
    if rs_mep is not None:
        try:
            asc = rs_mep.ascenseurs
            if hasattr(asc, "nb_ascenseurs"):
                has_ascenseur = asc.nb_ascenseurs > 0
            elif hasattr(asc, "requis"):
                has_ascenseur = asc.requis
        except (AttributeError, TypeError):
            pass

    # --- Extract costs ---
    structure_costs = {}
    if rs_structure is not None:
        try:
            structure_costs = _extract_structure_costs(rs_structure)
        except (AttributeError, TypeError):
            pass

    # Fallback: estimate structure costs from surface if missing
    if not structure_costs or structure_costs.get("total_bas", 0) == 0:
        # West African average: ~180,000 FCFA/m2 for structure
        total_est = int(surface_batie * 180_000)
        structure_costs = {
            "terrassement":     int(total_est * 0.05),
            "fondations":       int(total_est * 0.15),
            "beton_structure":  int(total_est * 0.35),
            "acier":            int(total_est * 0.20),
            "coffrage":         int(total_est * 0.10),
            "maconnerie":       int(total_est * 0.08),
            "etancheite":       int(total_est * 0.03),
            "divers":           int(total_est * 0.04),
            "total_bas":        total_est,
            "total_haut":       int(total_est * 1.15),
        }

    mep_costs = {}
    if rs_mep is not None:
        try:
            mep_costs = _extract_mep_costs(rs_mep)
        except (AttributeError, TypeError):
            pass

    # --- Build task lists ---
    str_taches, _, maco_ids = _build_structure_tasks(
        nb_niveaux, surface_emprise, fondation_type, structure_costs,
    )

    # Build MEP end IDs per niveau for finitions dependency
    mep_taches = _build_mep_tasks(
        nb_niveaux, surface_emprise, nb_logements,
        maco_ids, str_taches, mep_costs,
        has_ascenseur, nb_niveaux,
    )

    # Collect MEP end IDs per level for finitions
    mep_end_ids_par_niveau = {}
    for i in range(nb_niveaux):
        level_ids = [
            f"MEP-1.{i + 1}",
            f"MEP-2.{i + 1}",
            f"MEP-3.{i + 1}",
            f"MEP-4.{i + 1}",
        ]
        mep_end_ids_par_niveau[i] = level_ids

    all_taches_so_far = str_taches + mep_taches

    # Finitions cost
    finitions_cost = _estimate_finitions_cost(surface_batie, nb_niveaux)

    fin_taches = _build_finitions_tasks(
        nb_niveaux, surface_emprise, surface_batie,
        mep_end_ids_par_niveau, all_taches_so_far,
        finitions_cost,
    )

    # --- Assemble all tasks ---
    all_taches = str_taches + mep_taches + fin_taches

    if not all_taches:
        return Planning(
            projet_nom=nom, ville=ville, nb_niveaux=nb_niveaux,
            surface_batie_m2=surface_batie, duree_totale_jours=0,
            duree_totale_mois=0, taches=[], phases=[],
            tresorerie_mensuelle=[], tresorerie_lot_phase=[],
            cout_total_fcfa=0,
        )

    duree_totale_jours = max(t.fin_jour for t in all_taches)
    duree_totale_mois = _jour_vers_mois(duree_totale_jours)
    cout_total = sum(t.cout_total_fcfa for t in all_taches)

    # --- Group phases ---
    phases = _group_phases(all_taches)

    # --- Build planning object ---
    planning = Planning(
        projet_nom=nom,
        ville=ville,
        nb_niveaux=nb_niveaux,
        surface_batie_m2=surface_batie,
        duree_totale_jours=duree_totale_jours,
        duree_totale_mois=duree_totale_mois,
        taches=all_taches,
        phases=phases,
        tresorerie_mensuelle=[],
        tresorerie_lot_phase=[],
        cout_total_fcfa=cout_total,
    )

    # --- Generate cash flow ---
    tresorerie = generer_tresorerie(planning)
    planning.tresorerie_mensuelle = tresorerie["mensuelle"]
    planning.tresorerie_lot_phase = tresorerie["lot_phase"]

    return planning


# ======================================================================
# SERIALIZATION -- Convert to dict for JSON API response
# ======================================================================

def planning_to_dict(planning: Planning) -> dict:
    """Serialize Planning to a JSON-safe dict for API responses."""
    return {
        "projet_nom": planning.projet_nom,
        "ville": planning.ville,
        "nb_niveaux": planning.nb_niveaux,
        "surface_batie_m2": planning.surface_batie_m2,
        "duree_totale_jours": planning.duree_totale_jours,
        "duree_totale_mois": planning.duree_totale_mois,
        "cout_total_fcfa": planning.cout_total_fcfa,
        "taches": [
            {
                "id": t.id,
                "lot": t.lot,
                "sous_lot": t.sous_lot,
                "designation": t.designation,
                "duree_jours": t.duree_jours,
                "debut_jour": t.debut_jour,
                "fin_jour": t.fin_jour,
                "predecesseurs": t.predecesseurs,
                "cout_materiel_fcfa": t.cout_materiel_fcfa,
                "cout_pose_fcfa": t.cout_pose_fcfa,
                "cout_total_fcfa": t.cout_total_fcfa,
                "mois_debut": t.mois_debut,
                "mois_fin": t.mois_fin,
            }
            for t in planning.taches
        ],
        "phases": [
            {
                "id": p.id,
                "nom": p.nom,
                "debut_jour": p.debut_jour,
                "fin_jour": p.fin_jour,
                "duree_jours": p.duree_jours,
                "taches": p.taches,
                "cout_total_fcfa": p.cout_total_fcfa,
            }
            for p in planning.phases
        ],
        "tresorerie_mensuelle": planning.tresorerie_mensuelle,
        "tresorerie_lot_phase": planning.tresorerie_lot_phase,
    }


# ======================================================================
# STANDALONE TEST
# ======================================================================

if __name__ == "__main__":
    # Test with synthetic parameters (no engine dependencies)
    params = {
        "nom": "Residence Sakho",
        "ville": "Dakar",
        "nb_niveaux": 9,  # R+8
        "surface_emprise_m2": 450.0,
        "nb_logements": 32,
        "usage": "residentiel",
    }

    planning = generer_planning(None, None, params)

    print(f"Projet: {planning.projet_nom}")
    print(f"Ville: {planning.ville}")
    print(f"Niveaux: {planning.nb_niveaux} (R+{planning.nb_niveaux - 1})")
    print(f"Surface batie: {planning.surface_batie_m2:.0f} m2")
    print(f"Duree totale: {planning.duree_totale_jours} jours ({planning.duree_totale_mois} mois)")
    print(f"Cout total: {planning.cout_total_fcfa:,.0f} FCFA")
    print(f"\n--- {len(planning.taches)} taches ---")
    for t in planning.taches:
        print(f"  {t.id:12s} | J{t.debut_jour:4d}-J{t.fin_jour:4d} | {t.duree_jours:3d}j | {t.designation[:55]:55s} | {t.cout_total_fcfa:>14,} FCFA")
    print(f"\n--- {len(planning.phases)} phases ---")
    for p in planning.phases:
        print(f"  {p.id}: {p.nom:40s} | J{p.debut_jour:4d}-J{p.fin_jour:4d} ({p.duree_jours:3d}j) | {p.cout_total_fcfa:>14,} FCFA")
    print(f"\n--- Tresorerie mensuelle ---")
    for m in planning.tresorerie_mensuelle:
        print(f"  Mois {m['mois']:2d}: {m['depense_total_fcfa']:>14,} FCFA | Cumul: {m['cumul_fcfa']:>14,} FCFA")

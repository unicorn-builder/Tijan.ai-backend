"""
extract_project_data.py — Extraction des données projet depuis la géométrie DXF.

1. Identifie les niveaux réels (SS, RDC, R+1..R+8, Terrasse)
2. Associe chaque surface m² à sa pièce nommée (chambre, salon, etc.)
3. Calcule le nombre d'occupants selon les ratios DTU 60.11 / Arrêté du 31 janv. 1986
   - Chambre / Chambre parents : 2 pers
   - Studio (pièce unique < 35 m²) : 1.5 pers
   - Salon / Séjour (> 25 m²) : considéré comme pièce commune, ne rajoute pas d'occupant direct
   - Commerce / Restaurant : 1 pers / 10 m²
   - Bureau : 1 pers / 12 m²
   - Hôtel : 1.5 pers / chambre
4. Retourne un dict utilisable par les moteurs de calcul et les générateurs de plans.
"""
import json, re, os, math

# ══════════════════════════════════════════════════════════════
# LEVELS
# ══════════════════════════════════════════════════════════════

# Mapping fichier → info niveau
LEVEL_FILES = {
    'SOUS_SOL':   {'file': 'sakho_sous_sol_geom.json',    'code': 'SS',   'index': -1, 'alt_m': -2.50},
    'RDC':        {'file': 'sakho_rdc_geom.json',         'code': 'RDC',  'index': 0,  'alt_m': 0.00},
    'ETAGES_1_7': {'file': 'sakho_etages_1_7_geom.json',  'code': 'R+1→R+7', 'index': 1, 'alt_m': 3.00, 'repeat': 7},
    'ETAGE_8':    {'file': 'sakho_etage_8_geom.json',     'code': 'R+8',  'index': 8,  'alt_m': 24.00},
    'TERRASSE':   {'file': 'sakho_terrasse_geom.json',    'code': 'TERRASSE', 'index': 9, 'alt_m': 27.00},
}

# ══════════════════════════════════════════════════════════════
# ROOM TYPE CLASSIFICATION
# ══════════════════════════════════════════════════════════════

def classify_room_type(name):
    """Retourne (type, sous-type) standardisés."""
    n = name.lower().strip()
    if re.match(r'^[\d.,]+', n):
        return ('area', None)
    if any(k in n for k in ['chambre parent', 'ch. parent']):
        return ('chambre_parents', None)
    if any(k in n for k in ['chambre dom', 'ch. dom']):
        return ('chambre_service', None)
    if any(k in n for k in ['chambre']):
        return ('chambre', None)
    if any(k in n for k in ['salon']):
        return ('salon', None)
    if any(k in n for k in ['sejour', 'séjour']):
        return ('sejour', None)
    if 'sam' == n or 'sam' in n:
        return ('sam', None)  # salle à manger
    if any(k in n for k in ['cuisine', 'kitch']):
        return ('cuisine', None)
    if any(k in n for k in ['sdb', 'douche']):
        return ('sdb', None)
    if any(k in n for k in ['wc', 'toil']):
        return ('wc', None)
    if any(k in n for k in ['buanderie']):
        return ('buanderie', None)
    if any(k in n for k in ['dressing']):
        return ('dressing', None)
    if any(k in n for k in ['bureau']):
        return ('bureau', None)
    if any(k in n for k in ['bar']):
        return ('bar', None)
    if any(k in n for k in ['restaurant']):
        return ('restaurant', None)
    if any(k in n for k in ['magasin', 'commerce']):
        return ('commerce', None)
    if any(k in n for k in ['salle de sport', 'gym']):
        return ('salle_sport', None)
    if any(k in n for k in ['salle polyvalente']):
        return ('salle_polyvalente', None)
    if any(k in n for k in ['piscine']):
        return ('piscine', None)
    if any(k in n for k in ['hall', 'palier', 'dgt', 'sas', 'circulation', 'porche']):
        return ('circulation', None)
    if any(k in n for k in ['asc']):
        return ('ascenseur', None)
    if any(k in n for k in ['terrasse', 'balcon', 'jardin', 'vide']):
        return ('exterieur', None)
    if any(k in n for k in ['machinerie']):
        return ('technique', None)
    if any(k in n for k in ['tgbt', 'groupe', 'bache', 'surpresseur', 'local', 'depot', 'dépot', 'vestiaire', 'stationnement']):
        return ('technique', None)
    return ('autre', None)


def parse_area(text):
    """Parse '26.57m²' ou '12.36 m²' en float."""
    m = re.match(r'^([\d.,]+)\s*m', text.strip())
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


# ══════════════════════════════════════════════════════════════
# PAIR AREAS WITH ROOMS
# ══════════════════════════════════════════════════════════════

def pair_rooms_with_areas(rooms):
    """
    Dans le DXF, les labels de surface sont placés à côté des labels de pièce.
    On associe chaque area label à la pièce nommée la plus proche.
    """
    named = []
    areas = []
    for r in rooms:
        rtype, _ = classify_room_type(r['name'])
        if rtype == 'area':
            areas.append(r)
        else:
            named.append({**r, 'room_type': rtype, 'area_m2': None})

    # Pour chaque area label, trouver la pièce nommée la plus proche
    used = set()
    for a in areas:
        area_val = parse_area(a['name'])
        if area_val is None:
            continue
        best_idx = None
        best_dist = float('inf')
        for i, nr in enumerate(named):
            if i in used:
                continue
            d = math.hypot(nr['x'] - a['x'], nr['y'] - a['y'])
            if d < best_dist:
                best_dist = d
                best_idx = i
        if best_idx is not None and best_dist < 5000:  # max 5m de distance
            named[best_idx]['area_m2'] = area_val
            used.add(best_idx)

    return named


# ══════════════════════════════════════════════════════════════
# OCCUPANCY CALCULATION — Ratios DTU
# ══════════════════════════════════════════════════════════════
# DTU 60.11 : débit de base par type de pièce
# Arrêté du 31 janvier 1986 (habitation) :
#   - T1 (studio)    : 1.5 personnes
#   - T2 (1 chambre) : 2 personnes
#   - T3 (2 chambres): 3 personnes
#   - T4 (3 chambres): 4 personnes
#   - T5+ (4+ ch.)   : 5 personnes
# ERP (commerces) : 1 pers / 3-10 m² selon type
# Bureaux : 1 pers / 12 m²

OCCUPANCY_RATES = {
    'chambre':         2.0,   # 2 pers par chambre (couple ou 2 enfants)
    'chambre_parents': 2.0,   # suite parentale
    'chambre_service': 1.0,   # chambre de service / domestique
    'bureau':          None,  # calculé par surface : 1 pers / 12 m²
    'restaurant':      None,  # 1 pers / 3 m² (ERP type N)
    'commerce':        None,  # 1 pers / 5 m² (ERP type M)
    'bar':             None,  # 1 pers / 3 m² (ERP type N)
    'salle_sport':     None,  # 1 pers / 4 m² (ERP type X)
    'salle_polyvalente': None, # 1 pers / 3 m²
}

ERP_DENSITY = {
    'restaurant':       3.0,  # m² par personne
    'commerce':         5.0,
    'bar':              3.0,
    'salle_sport':      4.0,
    'salle_polyvalente': 3.0,
    'bureau':          12.0,
}


def _cluster_rooms_into_apartments(paired_rooms):
    """
    Regroupe les pièces en logements par proximité spatiale.

    Étape 1: Fusionner SAM (salle à manger) avec le salon le plus proche
             — un SAM n'est pas un logement séparé.
    Étape 2: Utiliser les salons restants comme ancres de logement.
    Étape 3: Attribuer chaque chambre au salon le plus proche,
             avec un seuil de distance max (12m ≈ 12000 unités DXF)
             pour éviter les rattachements aberrants.
    """
    salons_raw = [r for r in paired_rooms if r['room_type'] in ('salon', 'sejour')]
    sams = [r for r in paired_rooms if r['room_type'] == 'sam']
    cuisines = [r for r in paired_rooms if r['room_type'] == 'cuisine']
    chambres = [r for r in paired_rooms if r['room_type'] in ('chambre', 'chambre_parents')]

    if not salons_raw and not sams and not cuisines:
        return []

    # Étape 1 : les ancres principales sont les salons/séjours
    anchors = list(salons_raw)

    # Étape 2 : fusionner SAM avec le salon le plus proche (< 10m)
    for sam in sams:
        if anchors:
            nearest = min(anchors, key=lambda s: math.hypot(s['x']-sam['x'], s['y']-sam['y']))
            if math.hypot(nearest['x']-sam['x'], nearest['y']-sam['y']) < 10000:
                continue  # même logement
        anchors.append(sam)  # SAM isolé = logement autonome

    # Étape 3 : les cuisines qui ne sont pas proches d'un salon (> 10m)
    # représentent des logements sans salon identifié (studio, kitchenette)
    for cui in cuisines:
        if anchors:
            nearest = min(anchors, key=lambda s: math.hypot(s['x']-cui['x'], s['y']-cui['y']))
            if math.hypot(nearest['x']-cui['x'], nearest['y']-cui['y']) < 10000:
                continue  # cuisine rattachée à un salon proche
        anchors.append(cui)  # cuisine isolée = logement autonome

    if not anchors:
        return []

    # Étape 4 : créer les logements et rattacher les chambres
    apartments = [{'anchor': s, 'chambres': []} for s in anchors]

    MAX_DIST = 10000  # 10m — seuil réaliste pour un appartement
    for ch in chambres:
        dists = [(i, math.hypot(a['anchor']['x']-ch['x'], a['anchor']['y']-ch['y']))
                 for i, a in enumerate(apartments)]
        dists.sort(key=lambda x: x[1])
        if dists and dists[0][1] < MAX_DIST:
            apartments[dists[0][0]]['chambres'].append(ch)

    # Étape 5 : post-traitement
    filtered = []
    for apt in apartments:
        area = apt['anchor'].get('area_m2') or 0
        nb_ch = len(apt['chambres'])
        # Grand salon (> 40m²) sans chambre = espace commun, pas un studio
        if nb_ch == 0 and area > 40:
            continue
        # Si > 3 chambres, c'est probablement 2 logements fusionnés à tort
        # Split : garder les 2 plus proches, les autres deviennent orphelines
        # qui seront comptées comme chambres dans un logement implicite
        if nb_ch > 3:
            chs_sorted = sorted(apt['chambres'],
                                key=lambda c: math.hypot(c['x']-apt['anchor']['x'],
                                                         c['y']-apt['anchor']['y']))
            apt['chambres'] = chs_sorted[:3]  # garder les 3 plus proches → T4
            # Les chambres restantes forment un logement implicite
            remaining = chs_sorted[3:]
            if remaining:
                # Créer un logement implicite centré sur la première chambre restante
                filtered.append({'anchor': remaining[0], 'chambres': remaining[1:]})
        filtered.append(apt)

    return filtered


def calculate_occupancy_for_level(paired_rooms, level_repeat=1):
    """
    Calcule le nombre d'occupants pour un niveau.
    Regroupe les pièces en logements réels par clustering spatial,
    puis applique les ratios DTU (Arrêté 31 janv. 1986) :
      T1 (studio)  : 1.5 pers
      T2 (1 ch.)   : 2 pers
      T3 (2 ch.)   : 4 pers  (couple + 2 enfants)
      T4 (3 ch.)   : 5 pers
      T5 (4 ch.)   : 6 pers
      T6+ (5+ ch.) : nb_ch + 1
    """
    chambres_service = [r for r in paired_rooms if r['room_type'] == 'chambre_service']
    occupants_residential = 0
    occupants_erp = 0
    nb_logements = 0
    details = []

    apartments = _cluster_rooms_into_apartments(paired_rooms)
    nb_logements = len(apartments)

    # DTU 60.11 / Arrêté 31 janv. 1986
    t_type_map = {0: 1.5, 1: 2.0, 2: 4.0, 3: 5.0, 4: 6.0}
    for apt in apartments:
        nb_ch = len(apt['chambres'])
        pers = t_type_map.get(nb_ch, nb_ch + 1)
        t_label = "Studio" if nb_ch == 0 else f"T{nb_ch+1}"
        occupants_residential += pers
        details.append(f"1× {t_label} ({nb_ch} ch.) → {pers:.0f} pers")

    occupants_residential += len(chambres_service)
    if chambres_service:
        details.append(f"{len(chambres_service)} ch. service → {len(chambres_service)} pers")

    # Count occupants from ERP rooms
    for r in paired_rooms:
        if r['room_type'] in ERP_DENSITY and r.get('area_m2'):
            density = ERP_DENSITY[r['room_type']]
            occ = r['area_m2'] / density
            occupants_erp += occ
            details.append(f"{r['name']} ({r['area_m2']:.0f}m²) → {occ:.0f} pers")

    total = (occupants_residential + occupants_erp) * level_repeat
    nb_logements *= level_repeat

    return total, nb_logements, details


# ══════════════════════════════════════════════════════════════
# MAIN EXTRACTION
# ══════════════════════════════════════════════════════════════

def extract_project_data(geom_dir=None):
    """
    Extract complete project data from DXF geometry files.
    Returns dict with:
      - levels: list of level info
      - total_occupants: int
      - total_logements: int
      - surface_totale_m2: float
      - nb_niveaux: int
      - details: list of strings
    """
    if geom_dir is None:
        geom_dir = os.path.dirname(os.path.abspath(__file__))
    
    project = {
        'levels': [],
        'total_occupants': 0,
        'total_logements': 0,
        'surface_habitable_m2': 0,
        'surface_erp_m2': 0,
        'nb_niveaux': 0,
        'nb_niveaux_detail': '',
        'details': [],
    }
    
    total_occ = 0
    total_log = 0
    
    for lkey, linfo in LEVEL_FILES.items():
        path = os.path.join(geom_dir, linfo['file'])
        if not os.path.exists(path):
            continue
        
        with open(path) as f:
            geom = json.load(f)
        
        rooms = geom.get('rooms', [])
        if not rooms:
            continue
        
        paired = pair_rooms_with_areas(rooms)
        repeat = linfo.get('repeat', 1)
        occ, nb_log, details = calculate_occupancy_for_level(paired, repeat)
        
        # Surface totals
        surface_hab = sum(r.get('area_m2', 0) or 0 for r in paired 
                         if r['room_type'] in ('chambre','chambre_parents','chambre_service',
                                               'salon','sejour','sam','cuisine','sdb','wc',
                                               'buanderie','dressing','bureau')) * repeat
        surface_erp = sum(r.get('area_m2', 0) or 0 for r in paired
                         if r['room_type'] in ('restaurant','commerce','bar','salle_sport',
                                               'salle_polyvalente')) * repeat
        
        level_data = {
            'key': lkey,
            'code': linfo['code'],
            'index': linfo['index'],
            'altitude_m': linfo['alt_m'],
            'repeat': repeat,
            'rooms': len(paired),
            'occupants': occ,
            'logements': nb_log,
            'surface_hab_m2': round(surface_hab, 1),
            'surface_erp_m2': round(surface_erp, 1),
            'details': details,
        }
        project['levels'].append(level_data)
        total_occ += occ
        total_log += nb_log
        project['surface_habitable_m2'] += surface_hab
        project['surface_erp_m2'] += surface_erp
    
    project['total_occupants'] = round(total_occ)
    project['total_logements'] = total_log
    project['surface_habitable_m2'] = round(project['surface_habitable_m2'], 1)
    project['surface_erp_m2'] = round(project['surface_erp_m2'], 1)
    
    # Nombre de niveaux
    nb_niv = 0
    codes = []
    for l in project['levels']:
        if l['key'] == 'SOUS_SOL':
            nb_niv += 1; codes.append('SS')
        elif l['key'] == 'RDC':
            nb_niv += 1; codes.append('RDC')
        elif l['key'] == 'ETAGES_1_7':
            nb_niv += l['repeat']; codes.append(f"R+1→R+{l['repeat']}")
        elif l['key'] == 'ETAGE_8':
            nb_niv += 1; codes.append('R+8')
        elif l['key'] == 'TERRASSE':
            nb_niv += 1; codes.append('Terrasse')
    
    project['nb_niveaux'] = nb_niv
    project['nb_niveaux_detail'] = ' + '.join(codes)
    
    # Summary
    project['details'] = [
        f"Niveaux : {project['nb_niveaux_detail']} = {nb_niv} niveaux",
        f"Occupants : {project['total_occupants']} personnes (DTU 60.11)",
        f"Logements : {project['total_logements']}",
        f"Surface habitable : {project['surface_habitable_m2']} m²",
        f"Surface ERP : {project['surface_erp_m2']} m²",
    ]
    
    return project


# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    data = extract_project_data()
    print("=" * 60)
    print("DONNÉES PROJET EXTRAITES — Résidence SAKHO")
    print("=" * 60)
    for d in data['details']:
        print(f"  {d}")
    print()
    for level in data['levels']:
        print(f"  {level['code']:>12s} : {level['occupants']:>5.0f} pers, {level['logements']:>3d} logts, "
              f"hab={level['surface_hab_m2']:>8.1f}m², erp={level['surface_erp_m2']:>8.1f}m²")
        for detail in level['details']:
            print(f"               {detail}")

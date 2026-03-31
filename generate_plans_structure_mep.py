"""
generate_plans_structure_mep.py — Plans Structure + MEP sur fond architectural
Utilise les résultats réels des moteurs de calcul (engine_structure_v2, engine_mep_v2).
Produit des PDF A3 paysage avec cartouche professionnel + logo.

Appelé par main.py endpoints:
  POST /generate-plans-structure → PDF structure (coffrage, ferraillage, fondations...)
  POST /generate-plans-mep      → PDF MEP par lot (plomberie, électricité, CVC...)
"""
import io, os, math, re, json, tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas

from plan_theme import (draw_border, draw_cartouche, draw_legend, draw_notes,
                        draw_north, draw_axis_label, PAL, LOGO_PATH)

A3L = landscape(A3)
W, H = A3L

# ══════════════════════════════════════════════════════════════
# GEOMETRY HELPERS
# ══════════════════════════════════════════════════════════════

def _get_bounds(walls):
    xs, ys = [], []
    for item in walls:
        if item['type'] == 'line':
            xs += [item['start'][0], item['end'][0]]
            ys += [item['start'][1], item['end'][1]]
        elif item['type'] == 'polyline':
            for p in item['points']:
                xs.append(p[0]); ys.append(p[1])
    if not xs: return 0, 0, 1, 1
    return min(xs), min(ys), max(xs), max(ys)

def _make_tx(geom, margin=18*mm, bottom=42*mm):
    walls = geom.get('walls', []) + geom.get('windows', []) + geom.get('doors', [])
    xn, yn, xx, yx = _get_bounds(walls)
    dw, dh = xx - xn, yx - yn
    aw, ah = W - 2*margin, H - margin - bottom - margin
    sc = min(aw/dw, ah/dh) if dw > 0 and dh > 0 else 1
    ow = margin + (aw - dw*sc)/2
    oh = bottom + (ah - dh*sc)/2
    return lambda x: ow + (x - xn)*sc, lambda y: oh + (y - yn)*sc, sc

def _draw_arch(c, geom, tx, ty):
    c.setStrokeColor(PAL['gris_c']); c.setLineWidth(0.45)
    for item in geom.get('walls', []):
        _draw_item(c, item, tx, ty)
    c.setStrokeColor(colors.HexColor("#90CAF9")); c.setLineWidth(0.25)
    for item in geom.get('windows', []):
        _draw_item(c, item, tx, ty)
    c.setStrokeColor(colors.HexColor("#BCAAA4")); c.setLineWidth(0.2)
    for item in geom.get('doors', []):
        _draw_item(c, item, tx, ty)

def _draw_item(c, item, tx, ty):
    if item['type'] == 'line':
        c.line(tx(item['start'][0]), ty(item['start'][1]),
               tx(item['end'][0]), ty(item['end'][1]))
    elif item['type'] == 'polyline':
        pts = item['points']
        for i in range(len(pts)-1):
            c.line(tx(pts[i][0]), ty(pts[i][1]),
                   tx(pts[i+1][0]), ty(pts[i+1][1]))
        if item.get('closed') and len(pts) > 2:
            c.line(tx(pts[-1][0]), ty(pts[-1][1]),
                   tx(pts[0][0]), ty(pts[0][1]))

def _draw_labels(c, rooms, tx, ty, sz=3):
    c.setFillColor(PAL['gris']); c.setFont("Helvetica", sz)
    for r in rooms:
        if not re.match(r'^\d', r['name']):
            c.drawCentredString(tx(r['x']), ty(r['y']), r['name'])

def _classify(rooms):
    wet, living, service = [], [], []
    for r in rooms:
        n = r['name'].lower().strip()
        if re.match(r'^\d', n): continue
        if any(k in n for k in ['sdb','wc','toil','douche','cuisine','kitch','buanderie']):
            wet.append({**r, 'rt': 'wet'})
        elif any(k in n for k in ['hall','palier','asc','dgt','sas','terrasse','balcon','jardin','piscine','vide','porche','circulation']):
            service.append({**r, 'rt': 'service'})
        else:
            living.append({**r, 'rt': 'living'})
    return wet, living, service


# ══════════════════════════════════════════════════════════════
# STRUCTURE PLAN GENERATOR — uses ResultatsStructure
# ══════════════════════════════════════════════════════════════

def generer_plans_structure(output_path, resultats_structure=None, geom_data=None, params=None):
    """
    Generate structure plans PDF.
    resultats_structure: ResultatsStructure from engine_structure_v2
    geom_data: dict with keys per level, each containing walls/rooms/etc from DXF
    params: dict of project params
    """
    if params is None: params = {}
    p = params if isinstance(params, dict) else params.__dict__
    projet = p.get('nom', 'Projet Tijan')
    ville = p.get('ville', 'Dakar')
    lieu = f"{ville}, {p.get('pays', 'Sénégal')}"

    rs = resultats_structure
    c = pdfcanvas.Canvas(output_path, pagesize=A3L)
    c.setTitle(f"Plans Structure — {projet}")
    c.setAuthor("Tijan AI")

    # Extract real values from calculation engine
    if rs:
        pp = rs.poutre_principale
        ps = rs.poutre_secondaire
        dalle = rs.dalle
        fond = rs.fondation
        beton = rs.classe_beton
        acier = rs.classe_acier
        pot0 = rs.poteaux[0] if rs.poteaux else None

        beam_label = f"PP {pp.b_mm}×{pp.h_mm}" if pp else "PP 25×50"
        beam_rebar = f"{pp.As_inf_cm2:.1f}cm² inf" if pp else ""
        pot_section = f"{pot0.section_mm}×{pot0.section_mm}" if pot0 else "300×300"
        pot_rebar = f"{pot0.nb_barres}HA{pot0.diametre_mm}" if pot0 else "8HA16"
        pot_cadre = f"Cad.HA{pot0.cadre_diam_mm}/{pot0.espacement_cadres_mm//10}" if pot0 else "Cad.HA8/15"
        dalle_ep = f"ep.{dalle.epaisseur_mm}mm" if dalle else "ep.200mm"
        fond_type = fond.type.value.replace('_', ' ').title() if fond else "Semelle Isolée"
        notes_beton = f"Béton {beton} — Acier {acier}"
    else:
        beam_label = "PP 25×50"
        beam_rebar = "3HA16 inf"
        pot_section = "300×300"
        pot_rebar = "8HA16"
        pot_cadre = "Cad.HA8/15"
        dalle_ep = "ep.200mm"
        fond_type = "Semelle Isolée"
        notes_beton = "Béton C30/37 — Acier HA500"

    # If no geometry data, generate placeholder
    if not geom_data:
        # Single page placeholder
        draw_border(c)
        draw_cartouche(c, "PLAN DE COFFRAGE", 1, 1, niveau="Tous niveaux",
                       projet=projet, lieu=lieu, lot="Structure")
        draw_notes(c, [notes_beton, f"Poteau {pot_section} — {pot_rebar}",
                       f"Poutre {beam_label} — Dalle {dalle_ep}",
                       f"Fondation: {fond_type}"])
        c.showPage()
        c.save()
        return output_path

    # With geometry: generate per level
    levels = list(geom_data.items())
    total_pages = len(levels) * 3  # coffrage + ferraillage + voiles per level
    page = 0

    for level_key, geom in levels:
        if len(geom.get('walls', [])) < 5:
            continue
        level_label = geom.get('label', level_key)
        tx, ty, sc = _make_tx(geom)
        wet, living, service = _classify(geom.get('rooms', []))
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]

        # ── Page: Coffrage ──
        page += 1
        draw_border(c)
        draw_cartouche(c, "PLAN DE COFFRAGE", page, total_pages,
                       niveau=level_label, projet=projet, lieu=lieu, lot="Structure")
        draw_north(c)
        _draw_arch(c, geom, tx, ty)
        _draw_labels(c, geom.get('rooms', []), tx, ty, 2.5)

        # Draw poteaux from structure results
        for item in geom.get('structure', []):
            if item['type'] == 'polyline':
                pts = item['points']
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                cx_d = (min(xs)+max(xs))/2; cy_d = (min(ys)+max(ys))/2
                px, py = tx(cx_d), ty(cy_d)
                c.setFillColor(PAL['noir']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.3)
                c.rect(px-2, py-2, 4, 4, fill=1, stroke=1)

        draw_notes(c, [notes_beton,
                       f"Poteau {pot_section}mm — {pot_rebar} — {pot_cadre}",
                       f"Poutre {beam_label}cm — Dalle {dalle_ep}",
                       f"Fondation: {fond_type}"])
        draw_legend(c, [
            (PAL['noir'], f"Poteau BA {pot_section}mm", 'rect'),
            (PAL['noir'], f"Poutre princ. {beam_label}cm", 'line'),
            (PAL['gris'], "Poutre secondaire", 'line'),
            (PAL['gris_c'], f"Dalle BA {dalle_ep}", 'rect'),
        ])
        c.showPage()

        # ── Page: Ferraillage ──
        page += 1
        draw_border(c)
        draw_cartouche(c, "FERRAILLAGE POTEAUX & POUTRES", page, total_pages,
                       niveau=level_label, projet=projet, lieu=lieu, lot="Structure")
        _draw_arch(c, geom, tx, ty)
        _draw_labels(c, geom.get('rooms', []), tx, ty, 2.5)

        # Poteaux with rebar info
        for item in geom.get('structure', []):
            if item['type'] == 'polyline':
                pts = item['points']
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                cx_d = (min(xs)+max(xs))/2; cy_d = (min(ys)+max(ys))/2
                px, py = tx(cx_d), ty(cy_d)
                half = 3.5
                c.setFillColor(PAL['bleu_bg']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.5)
                c.rect(px-half, py-half, 2*half, 2*half, fill=1, stroke=1)
                c.setFillColor(PAL['noir'])
                for dx, dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    c.circle(px+dx*(half-1), py+dy*(half-1), 0.6, fill=1, stroke=0)
                c.setFillColor(PAL['rouge']); c.setFont("Helvetica", 2)
                c.drawCentredString(px, py-half-2.5, pot_rebar)

        draw_notes(c, [notes_beton,
                       f"Poteaux: {pot_rebar} — {pot_cadre}",
                       f"Poutres: {beam_label}cm — {beam_rebar}",
                       "Enrobage 30mm (XC2)"])
        draw_legend(c, [
            (PAL['bleu_bg'], "Section poteau BA", 'rect'),
            (PAL['noir'], "Armatures longitudinales", 'circle'),
            (PAL['rouge'], "Cadres / Étriers", 'line'),
        ])
        c.showPage()

        # ── Page: Voiles ──
        page += 1
        draw_border(c)
        draw_cartouche(c, "VOILES BA & CONTREVENTEMENT", page, total_pages,
                       niveau=level_label, projet=projet, lieu=lieu, lot="Structure")
        _draw_arch(c, geom, tx, ty)
        _draw_labels(c, geom.get('rooms', []), tx, ty, 2.5)

        for r in service:
            if 'asc' in r['name'].lower():
                rx, ry = tx(r['x']), ty(r['y'])
                c.setFillColor(colors.HexColor("#FFCDD2")); c.setStrokeColor(PAL['rouge']); c.setLineWidth(1.5)
                c.rect(rx-10, ry-10, 20, 20, fill=1, stroke=1)
                c.setStrokeColor(PAL['rouge']); c.setLineWidth(0.3)
                c.line(rx-10, ry-10, rx+10, ry+10)
                c.line(rx-10, ry+10, rx+10, ry-10)
                c.setFillColor(PAL['rouge']); c.setFont("Helvetica-Bold", 3)
                c.drawCentredString(rx, ry-13, "VOILE NOYAU ep.20")

        for r in service:
            if 'palier' in r['name'].lower():
                rx, ry = tx(r['x']), ty(r['y'])
                c.setFillColor(colors.HexColor("#FFE0B2")); c.setStrokeColor(PAL['orange']); c.setLineWidth(1)
                c.rect(rx-8, ry-8, 16, 16, fill=1, stroke=1)
                c.setFillColor(PAL['orange']); c.setFont("Helvetica-Bold", 3)
                c.drawCentredString(rx, ry-11, "VOILE CAGE")

        draw_legend(c, [
            (colors.HexColor("#FFCDD2"), "Voile noyau (ascenseur)", 'rect'),
            (colors.HexColor("#FFE0B2"), "Voile cage escalier", 'rect'),
            (PAL['noir'], "Poteau BA", 'rect'),
        ])
        c.showPage()

    c.save()
    return output_path


# ══════════════════════════════════════════════════════════════
# MEP PLAN GENERATOR — uses ResultatsMEP
# ══════════════════════════════════════════════════════════════

def generer_plans_mep(output_path, resultats_mep=None, geom_data=None, params=None):
    """
    Generate MEP plans PDF — all lots.
    resultats_mep: ResultatsMEP from engine_mep_v2
    """
    if params is None: params = {}
    p = params if isinstance(params, dict) else params.__dict__
    projet = p.get('nom', 'Projet Tijan')
    ville = p.get('ville', 'Dakar')
    lieu = f"{ville}, {p.get('pays', 'Sénégal')}"

    rm = resultats_mep

    # Extract real values from MEP engine
    if rm:
        el = rm.electrique
        pl = rm.plomberie
        cv = rm.cvc
        cf = rm.courants_faibles
        si = rm.securite_incendie
        asc = rm.ascenseurs
        auto = rm.automatisation
        transfo = f"Transfo {el.transfo_kva} kVA"
        ge = f"GE {el.groupe_electrogene_kva} kVA"
        citerne = f"Citerne {int(pl.volume_citerne_m3)} m³"
        col_ef = f"CM EF DN{pl.diam_colonne_montante_mm}"
        splits_ch = f"Split {cv.nb_splits_chambre}× chambres"
        splits_sej = f"Split {cv.nb_splits_sejour}× séjours"
        nb_df = f"{si.nb_detecteurs_fumee} DF"
        nb_ext = f"{si.nb_extincteurs_co2 + si.nb_extincteurs_poudre} extincteurs"
        nb_rj45 = f"{cf.nb_prises_rj45} prises RJ45"
        nb_cam = f"{cf.nb_cameras_int + cf.nb_cameras_ext} caméras"
        nb_asc_val = f"{asc.nb_ascenseurs} asc. {asc.capacite_kg}kg"
        gtb_proto = f"Protocole {auto.protocole}"
        gtb_pts = f"{auto.nb_points_controle} points contrôle"
    else:
        transfo = "Transfo 630 kVA"; ge = "GE 400 kVA"
        citerne = "Citerne 30 m³"; col_ef = "CM EF DN50"
        splits_ch = "Split 12000 BTU"; splits_sej = "Split 18000 BTU"
        nb_df = "Détecteurs fumée"; nb_ext = "Extincteurs"
        nb_rj45 = "Prises RJ45"; nb_cam = "Caméras IP"
        nb_asc_val = "Ascenseur 630kg"; gtb_proto = "KNX"
        gtb_pts = "Points contrôle"

    c = pdfcanvas.Canvas(output_path, pagesize=A3L)
    c.setTitle(f"Plans MEP — {projet}")
    c.setAuthor("Tijan AI")

    if not geom_data:
        draw_border(c)
        draw_cartouche(c, "PLANS MEP", 1, 1, niveau="Tous niveaux",
                       projet=projet, lieu=lieu, lot="MEP")
        draw_notes(c, [transfo, ge, citerne, col_ef])
        c.showPage(); c.save()
        return output_path

    levels = [(k, v) for k, v in geom_data.items() if len(v.get('walls', [])) >= 5]
    # 7 lots × N levels
    lots = [
        ("PLOMBERIE — Eau Froide", "Lot 1 — Plomberie"),
        ("PLOMBERIE — Eau Chaude", "Lot 1 — Plomberie"),
        ("PLOMBERIE — Évacuations EU/EP", "Lot 1 — Plomberie"),
        ("ÉLECTRICITÉ — Éclairage", "Lot 2 — Électricité"),
        ("ÉLECTRICITÉ — Prises de courant", "Lot 2 — Électricité"),
        ("ÉLECTRICITÉ — Distribution / TGBT", "Lot 2 — Électricité"),
        ("CVC — Climatisation", "Lot 3 — CVC"),
        ("CVC — Ventilation VMC", "Lot 3 — CVC"),
        ("SÉCURITÉ INCENDIE — Détection", "Lot 4 — Sécurité Incendie"),
        ("SÉCURITÉ INCENDIE — Extinction", "Lot 4 — Sécurité Incendie"),
        ("COURANTS FAIBLES — Réseau VDI", "Lot 5 — Courants Faibles"),
        ("COURANTS FAIBLES — Vidéosurveillance", "Lot 5 — Courants Faibles"),
        ("ASCENSEURS — Implantation", "Lot 6 — Ascenseurs"),
        ("AUTOMATISATION — Bus KNX", "Lot 7 — Automatisation"),
        ("AUTOMATISATION — Capteurs", "Lot 7 — Automatisation"),
    ]
    total_pages = len(lots) * len(levels)
    page = 0

    for lot_titre, lot_name in lots:
        for level_key, geom in levels:
            page += 1
            level_label = geom.get('label', level_key)
            tx, ty, sc = _make_tx(geom)
            wet, living, service = _classify(geom.get('rooms', []))
            shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
            if not shafts:
                shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]

            draw_border(c)
            draw_cartouche(c, lot_titre, page, total_pages,
                           niveau=level_label, projet=projet, lieu=lieu, lot=lot_name)
            draw_north(c)
            _draw_arch(c, geom, tx, ty)
            _draw_labels(c, geom.get('rooms', []), tx, ty, 2.5)

            lot_upper = lot_titre.upper()

            # ── PLOMBERIE EF ──
            if "EAU FROIDE" in lot_upper:
                for sx, sy in shafts:
                    px, py = tx(sx), ty(sy)
                    c.setFillColor(PAL['bleu']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.6)
                    c.circle(px, py, 3.5, fill=1, stroke=1)
                    c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 4)
                    c.drawCentredString(px, py-1.5, "EF")
                    c.setFillColor(PAL['bleu']); c.setFont("Helvetica", 3)
                    c.drawString(px+5, py+2, col_ef)
                for wr in wet:
                    wx, wy = tx(wr['x']), ty(wr['y'])
                    if shafts:
                        ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                        c.setStrokeColor(PAL['bleu']); c.setLineWidth(0.7)
                        c.line(tx(ns[0]), ty(ns[1]), tx(ns[0]), wy)
                        c.line(tx(ns[0]), wy, wx, wy)
                    c.setFillColor(PAL['bleu']); c.circle(wx, wy, 2, fill=1, stroke=0)
                draw_notes(c, [col_ef, citerne, f"Surpresseur {pl.debit_surpresseur_m3h} m³/h" if rm else ""])
                draw_legend(c, [(PAL['bleu'], f"Colonne montante EF", 'circle'),
                                (PAL['bleu'], "Réseau distribution EF", 'line'),
                                (PAL['bleu'], "Point d'eau", 'circle')])

            # ── PLOMBERIE EC ──
            elif "EAU CHAUDE" in lot_upper:
                for sx, sy in shafts:
                    px, py = tx(sx), ty(sy)
                    c.setFillColor(PAL['rouge']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.6)
                    c.circle(px, py, 3.5, fill=1, stroke=1)
                    c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 4)
                    c.drawCentredString(px, py-1.5, "EC")
                for wr in wet:
                    wx, wy = tx(wr['x']), ty(wr['y'])
                    n = wr['name'].lower()
                    if any(k in n for k in ['sdb','douche','cuisine','kitch','buanderie']):
                        if shafts:
                            ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                            c.setStrokeColor(PAL['rouge']); c.setLineWidth(0.5); c.setDash(3,1.5)
                            c.line(tx(ns[0]), ty(ns[1]), tx(ns[0]), wy)
                            c.line(tx(ns[0]), wy, wx, wy); c.setDash()
                        c.setFillColor(PAL['blanc']); c.setStrokeColor(PAL['rouge']); c.setLineWidth(0.5)
                        c.circle(wx, wy, 2.5, fill=1, stroke=1)
                nb_cesi = f"{pl.nb_chauffe_eau_solaire} CESI" if rm else ""
                draw_notes(c, ["CM EC DN32", nb_cesi])
                draw_legend(c, [(PAL['rouge'], "Colonne montante EC", 'circle'),
                                (PAL['rouge'], "Réseau distribution EC", 'dash'),
                                (PAL['rouge'], "Point desserte EC", 'ring')])

            # ── ÉVACUATIONS ──
            elif "VACUATION" in lot_upper:
                for sx, sy in shafts:
                    px, py = tx(sx), ty(sy)
                    c.setFillColor(PAL['marron']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.6)
                    c.circle(px, py, 3.5, fill=1, stroke=1)
                    c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 4)
                    c.drawCentredString(px, py-1.5, "EU")
                for wr in wet:
                    wx, wy = tx(wr['x']), ty(wr['y'])
                    if shafts:
                        ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                        c.setStrokeColor(PAL['marron']); c.setLineWidth(0.5); c.setDash(4,2)
                        c.line(wx, wy, tx(ns[0]), wy); c.line(tx(ns[0]), wy, tx(ns[0]), ty(ns[1]))
                        c.setDash()
                    c.setFillColor(PAL['marron']); c.circle(wx, wy, 2, fill=1, stroke=0)
                draw_legend(c, [(PAL['marron'], "Chute EU DN100", 'circle'),
                                (PAL['marron'], "Collecteur évacuation", 'dash'),
                                (PAL['marron'], "Siphon de sol", 'circle')])

            # ── ÉCLAIRAGE ──
            elif "CLAIRAGE" in lot_upper:
                all_r = wet + living + service
                for r in all_r:
                    rx, ry = tx(r['x']), ty(r['y'])
                    n = r['name'].lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    c.setStrokeColor(PAL['jaune']); c.setFillColor(colors.HexColor("#FFF8E1"))
                    c.setLineWidth(0.4); c.circle(rx, ry+5, 2.5, fill=1, stroke=1)
                    c.setStrokeColor(PAL['jaune']); c.setLineWidth(0.3)
                    c.line(rx-1.5, ry+5, rx+1.5, ry+5); c.line(rx, ry+3.5, rx, ry+6.5)
                draw_legend(c, [(PAL['jaune'], "Luminaire plafonnier", 'circle'),
                                (colors.HexColor("#FFF9C4"), "Interrupteur", 'circle')])

            # ── PRISES ──
            elif "PRISES" in lot_upper:
                all_r = wet + living + service
                for r in all_r:
                    rx, ry = tx(r['x']), ty(r['y'])
                    n = r['name'].lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    c.setFillColor(PAL['orange_c']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.15)
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','restaurant']):
                        for dx,dy in [(-6,-3),(6,-3),(-6,3),(6,3)]:
                            c.rect(rx+dx-1.2,ry+dy-0.8,2.4,1.6,fill=1,stroke=1)
                    elif any(k in n for k in ['cuisine','kitch']):
                        for dx,dy in [(-6,-3),(6,-3),(-6,3),(6,3),(0,-5),(0,5)]:
                            c.rect(rx+dx-1.2,ry+dy-0.8,2.4,1.6,fill=1,stroke=1)
                    else:
                        c.rect(rx+4,ry-0.8,2.4,1.6,fill=1,stroke=1)
                draw_notes(c, [transfo, ge, f"Section colonne {el.section_colonne_mm2}mm²" if rm else ""])
                draw_legend(c, [(PAL['orange_c'], "Prise 2P+T 16A", 'rect'),
                                (PAL['rouge'], "Prise spécialisée 32A", 'rect')])

            # ── DISTRIBUTION TGBT ──
            elif "TGBT" in lot_upper or "DISTRIB" in lot_upper:
                if shafts:
                    px, py = tx(shafts[0][0]), ty(shafts[0][1])
                    c.setFillColor(PAL['vert']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.6)
                    c.rect(px-6, py-12, 12, 8, fill=1, stroke=1)
                    c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 4)
                    c.drawCentredString(px, py-10, "TD")
                draw_notes(c, [transfo, ge, f"{el.nb_compteurs} compteurs" if rm else ""])
                draw_legend(c, [(PAL['vert'], "Tableau divisionnaire", 'rect'),
                                (PAL['orange'], "Chemin de câbles", 'line'),
                                (PAL['orange'], "Circuit terminal", 'dash')])

            # ── CVC CLIMATISATION ──
            elif "CLIMATISATION" in lot_upper:
                for r in living:
                    rx, ry = tx(r['x']), ty(r['y'])
                    n = r['name'].lower()
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','gym','restaurant','salle']):
                        c.setFillColor(PAL['cyan_c']); c.setStrokeColor(PAL['cyan']); c.setLineWidth(0.35)
                        c.rect(rx-4.5,ry+7,9,2.5,fill=1,stroke=1)
                        c.setFillColor(PAL['cyan']); c.setFont("Helvetica",2.2)
                        if 'salon' in n or 'sejour' in n or 'sam' in n:
                            c.drawCentredString(rx,ry+11.5,"18000 BTU")
                        elif 'chambre' in n:
                            c.drawCentredString(rx,ry+11.5,"12000 BTU")
                        else:
                            c.drawCentredString(rx,ry+11.5,"9000 BTU")
                draw_notes(c, [f"Puissance frigo {cv.puissance_frigorifique_kw:.0f} kW" if rm else "",
                               splits_ch, splits_sej])
                draw_legend(c, [(PAL['cyan_c'], "Split mural", 'rect'),
                                (PAL['cyan'], "Ligne frigorifique", 'dash')])

            # ── VMC ──
            elif "VMC" in lot_upper or "VENTILATION" in lot_upper:
                for r in wet:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setStrokeColor(PAL['vert_f']); c.setFillColor(colors.HexColor("#C8E6C9"))
                    c.setLineWidth(0.4); c.circle(rx, ry+4, 2.5, fill=1, stroke=1)
                draw_notes(c, [f"{cv.nb_vmc} VMC {cv.type_vmc}" if rm else "VMC hygroréglable"])
                draw_legend(c, [(PAL['vert_f'], "Bouche extraction VMC", 'circle'),
                                (PAL['vert_f'], "Gaine VMC", 'dash')])

            # ── DÉTECTION INCENDIE ──
            elif "DÉTECTION" in lot_upper or "DETECTION" in lot_upper:
                all_r = wet + living + service
                for r in all_r:
                    rx, ry = tx(r['x']), ty(r['y'])
                    n = r['name'].lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    c.setFillColor(PAL['blanc']); c.setStrokeColor(PAL['rouge']); c.setLineWidth(0.5)
                    c.circle(rx, ry-5, 2.5, fill=1, stroke=1)
                    c.setFillColor(PAL['rouge']); c.setFont("Helvetica-Bold",3)
                    c.drawCentredString(rx, ry-6.5, "DF")
                draw_notes(c, [nb_df, f"Catégorie ERP: {si.categorie_erp}" if rm else "",
                               f"Centrale {si.centrale_zones} zones" if rm else ""])
                draw_legend(c, [(PAL['rouge'], "Détecteur de fumée (DF)", 'ring'),
                                (PAL['rouge'], "Déclencheur manuel (DM)", 'rect'),
                                (PAL['orange'], "Sirène d'alarme", 'circle')])

            # ── EXTINCTION ──
            elif "EXTINCTION" in lot_upper:
                exits = [r for r in service if any(k in r['name'].lower() for k in ['palier','hall','sas'])]
                for r in exits:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(PAL['blanc']); c.setStrokeColor(PAL['rouge']); c.setLineWidth(0.7)
                    c.circle(rx+9, ry+4, 3.5, fill=1, stroke=1)
                    c.setFillColor(PAL['rouge']); c.setFont("Helvetica-Bold",4)
                    c.drawCentredString(rx+9, ry+2.5, "R")
                    c.setFillColor(PAL['vert']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.25)
                    c.rect(rx+4, ry-8, 5, 3, fill=1, stroke=1)
                    c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold",2)
                    c.drawCentredString(rx+6.5, ry-7, "BAES")
                sprink = f"Sprinklers: {'OUI' if si.sprinklers_requis else 'NON'}" if rm else ""
                draw_notes(c, [nb_ext, sprink, f"RIA {si.longueur_ria_ml:.0f} ml" if rm else ""])
                draw_legend(c, [(PAL['rouge'], "RIA", 'ring'),
                                (PAL['rouge'], "Extincteur", 'circle'),
                                (PAL['vert'], "BAES", 'rect')])

            # ── VDI ──
            elif "VDI" in lot_upper:
                all_r = wet + living + service
                for r in all_r:
                    n = r['name'].lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','cuisine','hall','restaurant']):
                        rx, ry = tx(r['x']), ty(r['y'])
                        c.setFillColor(PAL['violet']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.2)
                        c.rect(rx-1.5, ry-4, 3, 2.5, fill=1, stroke=1)
                draw_notes(c, [nb_rj45, f"{cf.baies_serveur} baies serveur" if rm else ""])
                draw_legend(c, [(PAL['violet'], "Prise RJ45 Cat.6", 'rect'),
                                (PAL['violet'], "Baie de brassage", 'rect'),
                                (PAL['violet'], "Câblage VDI", 'dash')])

            # ── VIDÉOSURVEILLANCE ──
            elif "VIDÉO" in lot_upper or "VIDEO" in lot_upper:
                cams = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','sas','porche'])]
                for r in cams:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(PAL['violet_c']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.3)
                    path = c.beginPath()
                    path.moveTo(rx, ry+8); path.lineTo(rx-3, ry+3); path.lineTo(rx+3, ry+3)
                    path.close(); c.drawPath(path, fill=1, stroke=0)
                draw_notes(c, [nb_cam])
                draw_legend(c, [(PAL['violet_c'], "Caméra IP intérieure", 'circle'),
                                (PAL['violet'], "NVR (enregistreur)", 'rect')])

            # ── ASCENSEURS ──
            elif "ASCENSEUR" in lot_upper:
                asc_rooms = [r for r in service if 'asc' in r['name'].lower()]
                for r in asc_rooms:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(PAL['bleu_bg']); c.setStrokeColor(PAL['bleu']); c.setLineWidth(1)
                    c.rect(rx-8, ry-8, 16, 16, fill=1, stroke=1)
                    c.setStrokeColor(PAL['bleu']); c.setLineWidth(0.3)
                    c.line(rx-8,ry-8,rx+8,ry+8); c.line(rx-8,ry+8,rx+8,ry-8)
                    c.setFillColor(PAL['bleu']); c.setFont("Helvetica-Bold",3)
                    c.drawCentredString(rx, ry-11, nb_asc_val if rm else "ASC")
                draw_legend(c, [(PAL['bleu_bg'], "Gaine ascenseur", 'rect'),
                                (PAL['bleu'], "Cabine", 'dash')])

            # ── AUTOMATISATION BUS ──
            elif "BUS" in lot_upper:
                halls = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt'])]
                if len(halls) >= 2:
                    sh = sorted(halls, key=lambda r: r['y'])
                    c.setStrokeColor(PAL['bleu']); c.setLineWidth(1.8)
                    for i in range(len(sh)-1):
                        c.line(tx(sh[i]['x']), ty(sh[i]['y']), tx(sh[i+1]['x']), ty(sh[i+1]['y']))
                draw_notes(c, [gtb_proto, gtb_pts, f"BMS: {'OUI' if auto.bms_requis else 'NON'}" if rm else ""])
                draw_legend(c, [(PAL['bleu'], f"Bus {auto.protocole if rm else 'KNX'}", 'line'),
                                (PAL['gris_f'], "Sous-contrôleur", 'rect')])

            # ── AUTOMATISATION CAPTEURS ──
            elif "CAPTEUR" in lot_upper:
                all_r = wet + living + service
                for r in all_r:
                    n = r['name'].lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    rx, ry = tx(r['x']), ty(r['y'])
                    if any(k in n for k in ['hall','palier','dgt','sas']):
                        c.setFillColor(PAL['orange_c']); c.circle(rx-6, ry+6, 2, fill=1, stroke=0)
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam']):
                        c.setFillColor(PAL['orange_c']); c.rect(rx-7, ry-5, 4, 3, fill=1, stroke=0)
                draw_notes(c, [gtb_pts, f"Gestion éclairage: {'OUI' if auto.gestion_eclairage else 'NON'}" if rm else ""])
                draw_legend(c, [(PAL['orange_c'], "Détecteur présence PIR", 'circle'),
                                (PAL['orange_c'], "Sonde température", 'rect'),
                                (PAL['vert'], "Variateur éclairage", 'rect')])

            c.showPage()

    c.save()
    return output_path

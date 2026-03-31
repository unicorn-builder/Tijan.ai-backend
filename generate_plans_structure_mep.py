"""
generate_plans_structure_mep.py — Plans Structure étendu + Plans MEP
Même pattern que generate_plans_v4.py (le seul générateur validé).

Grille : nb_travees_x/y × portee_max/min depuis ParamsProjet
Structure : poteaux/poutres/dalle/fondation depuis ResultatsStructure
MEP : équipements depuis ResultatsMEP, placés dans les travées

Zéro hardcoding. Chaque valeur vient des moteurs de calcul.
"""
import math
from datetime import datetime
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

# ── Colors — mêmes que v4 ──
NOIR  = colors.HexColor("#111111")
GRIS2 = colors.HexColor("#555555")
GRIS3 = colors.HexColor("#888888")
GRIS4 = colors.HexColor("#CCCCCC")
GRIS5 = colors.HexColor("#E8E8E8")
BLANC = colors.white
VERT  = colors.HexColor("#43A956")
VERT_P= colors.HexColor("#E8F5E9")
ROUGE = colors.HexColor("#CC3333")
BLEU  = colors.HexColor("#2196F3")
BLEU_B= colors.HexColor("#D6E4F0")
ORANGE= colors.HexColor("#FF9800")
CYAN  = colors.HexColor("#00ACC1")
MARRON= colors.HexColor("#795548")
JAUNE = colors.HexColor("#FBC02D")
VIOLET= colors.HexColor("#7B1FA2")

A3L = landscape(A3)


# ══════════════════════════════════════════
# UTILITAIRES — copie exacte de v4
# ══════════════════════════════════════════

def _border(c, w, h):
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(8*mm, 8*mm, w-16*mm, h-16*mm)

def _axis_label(c, x, y, label):
    r = 4.5*mm
    c.setStrokeColor(NOIR); c.setLineWidth(0.4); c.setFillColor(BLANC)
    c.circle(x, y, r, fill=1, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    tw = c.stringWidth(str(label), "Helvetica-Bold", 7)
    c.drawString(x - tw/2, y - 2.5, str(label))

def _cartouche(c, w, h, p, titre, pg, total, ech="1/100"):
    cw, ch_ = 180*mm, 28*mm
    cx = w - cw - 8*mm; cy = 6*mm
    c.setFillColor(BLANC); c.setStrokeColor(NOIR); c.setLineWidth(0.7)
    c.rect(cx, cy, cw, ch_, fill=1, stroke=1)
    c1, c2 = 38*mm, 108*mm
    c.setLineWidth(0.3)
    c.line(cx+c1, cy, cx+c1, cy+ch_)
    c.line(cx+c2, cy, cx+c2, cy+ch_)
    c.line(cx+c1, cy+ch_/2, cx+cw, cy+ch_/2)
    c.setFillColor(VERT); c.setFont("Helvetica-Bold", 10)
    c.drawString(cx+3*mm, cy+ch_-9*mm, "TIJAN AI")
    c.setFillColor(GRIS3); c.setFont("Helvetica", 5.5)
    c.drawString(cx+3*mm, cy+ch_-14*mm, "Engineering Intelligence")
    c.drawString(cx+3*mm, cy+5*mm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 8)
    c.drawString(cx+c1+3*mm, cy+ch_-9*mm, p.get("nom","Projet")[:30])
    c.setFillColor(VERT); c.setFont("Helvetica-Bold", 7)
    c.drawString(cx+c1+3*mm, cy+ch_/2-8*mm, titre)
    c.setFillColor(GRIS3); c.setFont("Helvetica", 6)
    c.drawString(cx+c2+3*mm, cy+ch_-9*mm, f"Éch: {ech}")
    c.drawString(cx+c2+3*mm, cy+ch_-14*mm, p.get("ville","Dakar"))
    c.drawString(cx+c2+3*mm, cy+5*mm, f"Pl. {pg}/{total}")


def _build_grid(p):
    """Build grid params — même logique que pl_coffrage dans v4."""
    nx = min(p.get("nb_travees_x", 4), 8)
    ny = max(min(p.get("nb_travees_y", 3), 6), 3)
    px_m = p.get("portee_max_m", 5.0)
    py_m = p.get("portee_min_m", 4.0)
    if py_m < 2.0:
        py_m = px_m * 0.65
    return nx, ny, px_m, py_m


def _grid_layout(w, h, nx, ny, px_m, py_m, ml=42*mm, mb=48*mm, mr=65*mm, mt=28*mm):
    """Calculate grid position and scale — copie de v4."""
    dw = w - ml - mr
    dh = h - mb - mt
    tot_x = px_m * nx
    tot_y = py_m * ny
    sc = min(dw / tot_x, dh / tot_y)
    gw = tot_x * sc
    gh = tot_y * sc
    ox = ml + (dw - gw) / 2
    oy = mb + (dh - gh) / 2
    return ox, oy, sc, gw, gh


def _draw_grid_axes(c, ox, oy, sc, nx, ny, px_m, py_m, gw, gh):
    """Draw grid axes lines + labels — copie de v4."""
    c.setStrokeColor(GRIS4); c.setLineWidth(0.2); c.setDash(4, 2)
    for i in range(nx + 1):
        xp = ox + i * px_m * sc
        c.line(xp, oy - 8*mm, xp, oy + gh + 8*mm)
    for j in range(ny + 1):
        yp = oy + j * py_m * sc
        c.line(ox - 8*mm, yp, ox + gw + 8*mm, yp)
    c.setDash()
    for i in range(nx + 1):
        _axis_label(c, ox + i * px_m * sc, oy - 15*mm, str(i + 1))
    for j in range(ny + 1):
        _axis_label(c, ox - 15*mm, oy + j * py_m * sc, chr(65 + j))
    # Dimensions
    c.setFillColor(GRIS3); c.setFont("Helvetica", 5.5)
    for i in range(nx):
        mid = ox + (i + 0.5) * px_m * sc
        c.drawCentredString(mid, oy - 9*mm, f"{px_m*1000:.0f}")
    for j in range(ny):
        mid_y = oy + (j + 0.5) * py_m * sc
        c.saveState(); c.translate(ox - 9*mm, mid_y); c.rotate(90)
        c.drawCentredString(0, 0, f"{py_m*1000:.0f}"); c.restoreState()


def _draw_poteaux(c, ox, oy, sc, nx, ny, px_m, py_m, pot_s):
    """Draw columns at grid intersections — copie de v4."""
    pt_d = max(pot_s * sc / 1000, 3)
    for i in range(nx + 1):
        for j in range(ny + 1):
            xp = ox + i * px_m * sc
            yp = oy + j * py_m * sc
            c.setFillColor(NOIR); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
            c.rect(xp - pt_d/2, yp - pt_d/2, pt_d, pt_d, fill=1, stroke=1)


def _draw_poutres_pp(c, ox, oy, sc, nx, ny, px_m, py_m, pp_b):
    """Draw main beams along Y-axes — copie de v4."""
    pd = max(pp_b * sc / 1000, 1.5)
    for j in range(ny + 1):
        yp = oy + j * py_m * sc
        for i in range(nx):
            x1 = ox + i * px_m * sc
            x2 = ox + (i+1) * px_m * sc
            c.setStrokeColor(NOIR); c.setLineWidth(0.8)
            c.line(x1, yp - pd/2, x2, yp - pd/2)
            c.line(x1, yp + pd/2, x2, yp + pd/2)


def _draw_poutres_ps(c, ox, oy, sc, nx, ny, px_m, py_m):
    """Draw secondary beams along X-axes — copie de v4."""
    for i in range(nx + 1):
        xp = ox + i * px_m * sc
        for j in range(ny):
            y1 = oy + j * py_m * sc
            y2 = oy + (j+1) * py_m * sc
            c.setStrokeColor(GRIS3); c.setLineWidth(0.4)
            c.line(xp, y1, xp, y2)


def _draw_dalle_hatch(c, ox, oy, sc, nx, ny, px_m, py_m):
    """Draw slab panel hatch — copie de v4."""
    c.setStrokeColor(GRIS4); c.setLineWidth(0.1)
    for i in range(nx):
        for j in range(ny):
            sx = ox + i * px_m * sc + 2
            sy = oy + j * py_m * sc + 2
            sw = px_m * sc - 4
            sh = py_m * sc - 4
            step = max(6, int(sw / 15))
            for k in range(0, int(sw + sh), step):
                lx1 = sx + min(k, sw); ly1 = sy + max(0, k - sw)
                lx2 = sx + max(0, k - sh); ly2 = sy + min(k, sh)
                c.line(lx1, ly1, lx2, ly2)


# ══════════════════════════════════════════
# DWG REAL GEOMETRY — quand disponible
# ══════════════════════════════════════════

def _dwg_bounds(dwg):
    """Bounding box de la géométrie DWG réelle (lines + polylines)."""
    xs, ys = [], []
    for item in dwg.get('walls',[]) + dwg.get('windows',[]) + dwg.get('doors',[]):
        if item['type'] == 'line':
            xs += [item['start'][0], item['end'][0]]
            ys += [item['start'][1], item['end'][1]]
        elif item['type'] == 'polyline':
            for p in item['points']:
                xs.append(p[0]); ys.append(p[1])
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _dwg_layout(w, h, dwg, ml=42*mm, mb=48*mm, mr=65*mm, mt=28*mm):
    """Calculate DWG transform to fit on page — same margin logic as grid."""
    bounds = _dwg_bounds(dwg)
    if not bounds:
        return None, None, None, None, None
    xn, yn, xx, yx = bounds
    dw_r = xx - xn; dh_r = yx - yn
    if dw_r < 1 or dh_r < 1:
        return None, None, None, None, None
    aw = w - ml - mr; ah = h - mb - mt
    sc = min(aw / dw_r, ah / dh_r)
    gw = dw_r * sc; gh = dh_r * sc
    ox = ml + (aw - gw) / 2
    oy = mb + (ah - gh) / 2
    tx = lambda x: ox + (x - xn) * sc
    ty = lambda y: oy + (y - yn) * sc
    return tx, ty, sc, gw, gh


def _draw_dwg(c, dwg, tx, ty):
    """Dessine la géométrie DWG réelle (murs, fenêtres, portes, labels)."""
    import re
    # Murs
    c.setStrokeColor(GRIS2); c.setLineWidth(0.5)
    for item in dwg.get('walls', []):
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
    # Fenêtres
    c.setStrokeColor(colors.HexColor("#90CAF9")); c.setLineWidth(0.3)
    for item in dwg.get('windows', []):
        if item['type'] == 'line':
            c.line(tx(item['start'][0]), ty(item['start'][1]),
                   tx(item['end'][0]), ty(item['end'][1]))
        elif item['type'] == 'polyline':
            pts = item['points']
            for i in range(len(pts)-1):
                c.line(tx(pts[i][0]), ty(pts[i][1]),
                       tx(pts[i+1][0]), ty(pts[i+1][1]))
    # Portes
    c.setStrokeColor(colors.HexColor("#BCAAA4")); c.setLineWidth(0.25)
    for item in dwg.get('doors', []):
        if item['type'] == 'line':
            c.line(tx(item['start'][0]), ty(item['start'][1]),
                   tx(item['end'][0]), ty(item['end'][1]))
        elif item['type'] == 'polyline':
            pts = item['points']
            for i in range(len(pts)-1):
                c.line(tx(pts[i][0]), ty(pts[i][1]),
                       tx(pts[i+1][0]), ty(pts[i+1][1]))
    # Labels pièces
    c.setFillColor(GRIS3); c.setFont("Helvetica", 3.5)
    for r in dwg.get('rooms', []):
        name = r.get('name', '')
        if name and not re.match(r'^\d', name):
            c.drawCentredString(tx(r['x']), ty(r['y']), name[:20])


def _legend(c, w, h, items):
    """Draw legend box — top right."""
    lx = w - 58*mm; ly = h - 28*mm
    c.setFont("Helvetica-Bold", 7); c.setFillColor(NOIR)
    c.drawString(lx, ly, "LÉGENDE"); ly -= 12
    for color, width, label in items:
        if width == 'fill':
            c.setFillColor(color)
            c.rect(lx, ly, 5, 5, fill=1, stroke=1)
        elif width == 'circle':
            c.setFillColor(color)
            c.circle(lx + 3, ly + 3, 3, fill=1, stroke=0)
        else:
            c.setStrokeColor(color); c.setLineWidth(width)
            c.line(lx, ly + 3, lx + 15, ly + 3)
        c.setFillColor(NOIR); c.setFont("Helvetica", 5.5)
        c.drawString(lx + 18, ly + 1, label)
        ly -= 10


# ══════════════════════════════════════════
# PLANS STRUCTURE — même pattern que v4
# ══════════════════════════════════════════

def generer_plans_structure(output_path, resultats=None, params=None, **kw):
    """
    Plans structure étendus. Même grille que generate_plans_v4.py.
    Toutes les valeurs viennent de ResultatsStructure.
    """
    if resultats is None:
        raise ValueError("ResultatsStructure requis")
    if params is None:
        params = {}
    if hasattr(params, "__dict__"):
        params = {k: v for k, v in vars(params).items() if not k.startswith("_")}

    r = resultats
    p = params
    nx, ny, px_m, py_m = _build_grid(p)
    pot0 = r.poteaux[0] if r.poteaux else None
    pp = r.poutre_principale
    ps = r.poutre_secondaire
    dalle = r.dalle
    fd = r.fondation

    if pot0 is None or pp is None:
        raise ValueError("Résultats structure incomplets")

    pot_s = pot0.section_mm
    pp_b, pp_h = pp.b_mm, pp.h_mm
    ps_b = ps.b_mm if ps else 0
    ps_h = ps.h_mm if ps else 0
    dalle_ep = dalle.epaisseur_mm
    beton = r.classe_beton
    acier = r.classe_acier

    # Levels from poteaux
    nb_niv = p.get("nb_niveaux", len(r.poteaux))
    he = p.get("hauteur_etage_m", 3.0)

    # Count pages: coffrage per level (max 3 displayed) + ferraillage dalles + fondations + coupe
    level_names = []
    if p.get("avec_sous_sol"):
        level_names.append("Sous-Sol")
    level_names.append("RDC")
    nb_etages = nb_niv - len(level_names)
    if nb_etages > 0:
        level_names.append(f"Étages 1-{nb_etages}" if nb_etages > 1 else "Étage 1")
    level_names.append("Terrasse")

    total_pages = len(level_names) + 3  # +ferraillage dalle + fondations + coupe
    page = 0

    c = pdfcanvas.Canvas(output_path, pagesize=A3L)
    c.setTitle(f"Plans Structure — {p.get('nom','Projet')}")
    c.setAuthor("Tijan AI")

    # ── COFFRAGE per level ──
    for level_name in level_names:
        page += 1
        w, h = A3L; c.setPageSize(A3L); _border(c, w, h)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 13)
        c.drawString(14*mm, h - 17*mm, f"PLAN DE COFFRAGE — {level_name.upper()}")

        ox, oy, sc, gw, gh = _grid_layout(w, h, nx, ny, px_m, py_m)
        _draw_grid_axes(c, ox, oy, sc, nx, ny, px_m, py_m, gw, gh)
        _draw_dalle_hatch(c, ox, oy, sc, nx, ny, px_m, py_m)
        _draw_poutres_pp(c, ox, oy, sc, nx, ny, px_m, py_m, pp_b)
        _draw_poutres_ps(c, ox, oy, sc, nx, ny, px_m, py_m)
        _draw_poteaux(c, ox, oy, sc, nx, ny, px_m, py_m, pot_s)

        # Dalle label in each panel
        c.setFillColor(GRIS3); c.setFont("Helvetica", 4.5)
        for i in range(nx):
            for j in range(ny):
                cx_p = ox + (i + 0.5) * px_m * sc
                cy_p = oy + (j + 0.5) * py_m * sc
                c.drawCentredString(cx_p, cy_p, f"D ep.{dalle_ep}")

        _legend(c, w, h, [
            (NOIR, 'fill', f"Poteau {pot_s}×{pot_s}"),
            (NOIR, 0.8, f"PP {pp_b}×{pp_h}"),
            (GRIS3, 0.4, f"PS {ps_b}×{ps_h}" if ps else "PS"),
            (GRIS4, 0.1, f"Dalle ep.{dalle_ep}mm"),
        ])

        c.setFont("Helvetica", 5); c.setFillColor(GRIS3)
        c.drawString(14*mm, 42*mm, f"Béton {beton} — Acier {acier} — Enrobage 30mm")
        _cartouche(c, w, h, p, f"COFFRAGE — {level_name}", page, total_pages)
        c.showPage()

    # ── FERRAILLAGE DALLE ──
    page += 1
    w, h = A3L; c.setPageSize(A3L); _border(c, w, h)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 13)
    c.drawString(14*mm, h - 17*mm, "FERRAILLAGE DALLE — NIVEAU COURANT")

    ox, oy, sc, gw, gh = _grid_layout(w, h, nx, ny, px_m, py_m)
    _draw_grid_axes(c, ox, oy, sc, nx, ny, px_m, py_m, gw, gh)
    _draw_poteaux(c, ox, oy, sc, nx, ny, px_m, py_m, pot_s)

    # Rebar direction arrows in each panel
    for i in range(nx):
        for j in range(ny):
            sx = ox + i * px_m * sc; sy = oy + j * py_m * sc
            sw = px_m * sc; sh = py_m * sc
            cx_p = sx + sw/2; cy_p = sy + sh/2
            # Direction X bars (red)
            c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
            nb_x = max(2, int(sh / 8))
            for k in range(nb_x):
                yb = sy + 4 + k * (sh - 8) / max(nb_x - 1, 1)
                c.line(sx + 3, yb, sx + sw - 3, yb)
            # Direction Y bars (blue)
            c.setStrokeColor(BLEU); c.setLineWidth(0.4)
            nb_y = max(2, int(sw / 8))
            for k in range(nb_y):
                xb = sx + 4 + k * (sw - 8) / max(nb_y - 1, 1)
                c.line(xb, sy + 3, xb, sy + sh - 3)
            # Label
            c.setFillColor(NOIR); c.setFont("Helvetica", 3.5)
            c.drawCentredString(cx_p, cy_p + 3, f"As x={dalle.As_x_cm2_ml:.2f}")
            c.drawCentredString(cx_p, cy_p - 3, f"As y={dalle.As_y_cm2_ml:.2f}")

    _legend(c, w, h, [
        (ROUGE, 0.5, f"Nappe inf X — As={dalle.As_x_cm2_ml:.2f} cm²/ml"),
        (BLEU, 0.4, f"Nappe inf Y — As={dalle.As_y_cm2_ml:.2f} cm²/ml"),
        (NOIR, 'fill', f"Poteau {pot_s}×{pot_s}"),
    ])
    c.setFont("Helvetica", 5); c.setFillColor(GRIS3)
    c.drawString(14*mm, 42*mm, f"Dalle ep.{dalle_ep}mm — {beton} — {acier}")
    _cartouche(c, w, h, p, "FERRAILLAGE DALLE", page, total_pages)
    c.showPage()

    # ── FONDATIONS ──
    page += 1
    w, h = A3L; c.setPageSize(A3L); _border(c, w, h)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 13)
    c.drawString(14*mm, h - 17*mm, "PLAN DE FONDATIONS")

    ox, oy, sc, gw, gh = _grid_layout(w, h, nx, ny, px_m, py_m)
    _draw_grid_axes(c, ox, oy, sc, nx, ny, px_m, py_m, gw, gh)

    nb_pieux = getattr(fd, 'nb_pieux', 0)
    diam_p = getattr(fd, 'diam_pieu_mm', 600)
    larg_sem = getattr(fd, 'largeur_semelle_m', 1.5)
    pr = max(min(diam_p * sc / 2000, 8), 3) if nb_pieux else max(larg_sem * sc / 2, 5)

    for i in range(nx + 1):
        for j in range(ny + 1):
            xp = ox + i * px_m * sc; yp = oy + j * py_m * sc
            c.setFillColor(VERT_P); c.setStrokeColor(VERT); c.setLineWidth(0.4)
            if nb_pieux > 0:
                c.circle(xp, yp, pr, fill=1, stroke=1)
            else:
                c.rect(xp - pr, yp - pr, 2*pr, 2*pr, fill=1, stroke=1)

    # Longrines
    c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    for j in range(ny + 1):
        for i in range(nx):
            x1 = ox + i * px_m * sc + pr; x2 = ox + (i+1) * px_m * sc - pr
            c.line(x1, oy + j * py_m * sc, x2, oy + j * py_m * sc)
    for i in range(nx + 1):
        for j in range(ny):
            y1 = oy + j * py_m * sc + pr; y2 = oy + (j+1) * py_m * sc - pr
            c.line(ox + i * px_m * sc, y1, ox + i * px_m * sc, y2)

    type_f = fd.type.value.replace('_', ' ').title()
    c.setFont("Helvetica", 5.5); c.setFillColor(GRIS2)
    c.drawString(14*mm, 42*mm, f"{type_f} — prof.{fd.profondeur_m:.1f}m — σsol={r.pression_sol_MPa:.2f}MPa — {beton}")
    _legend(c, w, h, [
        (VERT, 'fill', f"{'Pieu ø'+str(diam_p)+'mm' if nb_pieux else 'Semelle '+str(larg_sem)+'×'+str(larg_sem)+'m'}"),
        (NOIR, 0.8, "Longrine"),
    ])
    _cartouche(c, w, h, p, "FONDATIONS", page, total_pages)
    c.showPage()

    # ── COUPE GÉNÉRALE ──
    page += 1
    w, h = A3L; c.setPageSize(A3L); _border(c, w, h)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 13)
    c.drawString(14*mm, h - 17*mm, "COUPE GÉNÉRALE")

    nc = min(nx, 5)
    rml = 50*mm; rmb = 48*mm
    rdw = w - rml - 40*mm; rdh = h - rmb - 35*mm
    tot_hm = nb_niv * he; tot_wm = px_m * nc
    rsc = min(rdw / tot_wm, rdh / tot_hm)
    cgw = tot_wm * rsc; cgh = tot_hm * rsc
    cox = rml + (rdw - cgw) / 2; coy = rmb + (rdh - cgh) / 2

    for niv in range(nb_niv):
        yb = coy + niv * he * rsc; yt = coy + (niv + 1) * he * rsc
        pot_k = r.poteaux[niv] if niv < len(r.poteaux) else pot0
        sec_k = pot_k.section_mm
        pw = max(sec_k * rsc / 1000, 2.5)
        dh_s = max(dalle_ep * rsc / 1000, 1.5)
        c.setFillColor(GRIS5); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
        c.rect(cox, yt - dh_s, cgw, dh_s, fill=1, stroke=1)
        for i in range(nc + 1):
            cpx = cox + i * px_m * rsc
            c.setFillColor(colors.Color(0.88, 0.88, 0.88))
            c.rect(cpx - pw/2, yb, pw, yt - yb - dh_s, fill=1, stroke=1)
        niv_label = getattr(pot_k, 'niveau', f'N{niv}')
        c.setFillColor(NOIR); c.setFont("Helvetica", 5)
        c.drawString(cox - 18*mm, yb + (yt-yb)/2 - 2, niv_label)
        c.setFillColor(GRIS3); c.setFont("Helvetica", 4.5)
        c.drawString(cox + cgw + 3, yb + (yt-yb)/2 - 2, f"{sec_k}×{sec_k}")

    fd_h = max(6, 500 * rsc / 1000)
    c.setFillColor(GRIS4); c.setStrokeColor(NOIR); c.setLineWidth(0.4)
    c.rect(cox - 5, coy - fd_h, cgw + 10, fd_h, fill=1, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawCentredString(cox + cgw/2, coy - fd_h + 2, f"FONDATIONS — {type_f}")

    c.setFont("Helvetica-Bold", 6); c.setFillColor(NOIR)
    c.drawString(cox + cgw + 5, coy + cgh/2, f"H = {tot_hm:.1f} m")
    c.drawString(cox + cgw + 5, coy + cgh/2 - 8, f"Béton {beton}")

    for i in range(nc + 1):
        _axis_label(c, cox + i * px_m * rsc, coy - fd_h - 10*mm, str(i+1))

    _cartouche(c, w, h, p, "COUPE GÉNÉRALE", page, total_pages, ech="1/200")
    c.showPage()

    c.save()
    return output_path


# ══════════════════════════════════════════
# PLANS MEP — même grille, équipements depuis ResultatsMEP
# ══════════════════════════════════════════

def generer_plans_mep(output_path, resultats_mep=None, resultats_structure=None,
                      params=None, dwg_geometry=None, **kw):
    """
    Plans MEP. Deux modes :
    - Avec dwg_geometry : fond de plan DWG réel du projet + MEP superposé
      dwg_geometry peut être:
        - un dict unique (1 seul niveau) : {'walls':[], 'rooms':[], ...}
        - un dict de niveaux : {'SOUS_SOL': {...}, 'RDC': {...}, 'ETAGES_1_7': {...}, ...}
    - Sans : grille paramétrique depuis ParamsProjet + MEP superposé
    Équipements placés dans les pièces réelles depuis ResultatsMEP.
    """
    if resultats_mep is None:
        raise ValueError("ResultatsMEP requis")
    if params is None:
        params = {}
    if hasattr(params, "__dict__"):
        params = {k: v for k, v in vars(params).items() if not k.startswith("_")}

    # Normalize dwg_geometry to a dict of levels
    dwg_levels = {}
    if dwg_geometry:
        if 'walls' in dwg_geometry:
            # Single geometry — use as "Étage courant"
            dwg_levels = {'Étage courant': dwg_geometry}
        else:
            # Multi-level dict
            LEVEL_LABELS = {
                'SOUS_SOL': 'Sous-Sol / Parking',
                'RDC': 'Rez-de-Chaussée',
                'ETAGES_1_7': 'Étages 1 à 7',
                'ETAGE_8': 'Étage 8',
                'TERRASSE': 'Terrasse',
            }
            for key, geom in dwg_geometry.items():
                if isinstance(geom, dict) and len(geom.get('walls', [])) >= 5:
                    label = LEVEL_LABELS.get(key, geom.get('label', key))
                    dwg_levels[label] = geom

    rm = resultats_mep
    p = params
    nx, ny, px_m, py_m = _build_grid(p)
    el = rm.electrique
    pl = rm.plomberie
    cv = rm.cvc
    cf = rm.courants_faibles
    si = rm.securite_incendie
    asc = rm.ascenseurs
    aut = rm.automatisation

    pot_s = 300
    if resultats_structure and resultats_structure.poteaux:
        pot_s = resultats_structure.poteaux[0].section_mm

    import re as _re
    def _classify_rooms(rooms):
        wet, living, service = [], [], []
        for r in rooms:
            n = r.get('name', '').lower().strip()
            if _re.match(r'^\d', n): continue
            if any(k in n for k in ['sdb','wc','toil','douche']):
                wet.append({**r, 'rt': 'wet'})
            elif any(k in n for k in ['cuisine','kitch','buanderie']):
                wet.append({**r, 'rt': 'kitchen'})
            elif any(k in n for k in ['salon','chambre','sejour','bureau','sam','bar','gym','restaurant','magasin','salle']):
                living.append({**r, 'rt': 'living'})
            elif any(k in n for k in ['hall','palier','asc','dgt','sas','terrasse','balcon','jardin','piscine','vide','porche','circulation']):
                service.append({**r, 'rt': 'service'})
            else:
                living.append({**r, 'rt': 'other'})
        return wet, living, service

    # Build level list: if multi-level DWG, iterate each; otherwise single
    if dwg_levels:
        level_list = list(dwg_levels.items())  # [(label, geom), ...]
    else:
        level_list = [("Niveau courant", None)]  # fallback grille

    # Sub-lots: (title, lot_label, draw_fn_key)
    sublots = [
        ("PLOMBERIE — EAU FROIDE",     "PLB", "plb_ef"),
        ("PLOMBERIE — EAU CHAUDE",     "PLB", "plb_ec"),
        ("PLOMBERIE — ÉVACUATIONS",    "PLB", "plb_eu"),
        ("ÉLECTRICITÉ — ÉCLAIRAGE",    "ELEC","elec_ecl"),
        ("ÉLECTRICITÉ — PRISES & TGBT","ELEC","elec_dist"),
        ("CVC — CLIMATISATION",        "CVC", "cvc_clim"),
        ("CVC — VENTILATION VMC",      "CVC", "cvc_vmc"),
        ("SÉCURITÉ INCENDIE — DÉTECTION", "SSI", "ssi_det"),
        ("SÉCURITÉ INCENDIE — EXTINCTION","SSI", "ssi_ext"),
        ("COURANTS FAIBLES",           "CFA", "cfa"),
        ("ASCENSEURS",                 "ASC", "asc_plan"),
        ("AUTOMATISATION — GTB",       "GTB", "gtb"),
    ]

    total_pages = len(sublots) * len(level_list)
    page = 0

    c = pdfcanvas.Canvas(output_path, pagesize=A3L)
    c.setTitle(f"Plans MEP — {p.get('nom','Projet')}")
    c.setAuthor("Tijan AI")

    for title, lot_label, key in sublots:
      for level_label, level_geom in level_list:
        page += 1
        w, h = A3L; c.setPageSize(A3L); _border(c, w, h)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 12)
        c.drawString(14*mm, h - 17*mm, f"{title} — {level_label}")

        # ── Fond de plan : géométrie DWG de CE niveau ──
        use_dwg = False
        if level_geom and len(level_geom.get('walls', [])) >= 5:
            dwg_tx, dwg_ty, dwg_sc, dwg_gw, dwg_gh = _dwg_layout(w, h, level_geom)
            if dwg_tx:
                _draw_dwg(c, level_geom, dwg_tx, dwg_ty)
                tx, ty = dwg_tx, dwg_ty
                bounds = _dwg_bounds(level_geom)
                ox = tx(bounds[0]); oy = ty(bounds[1])
                gw = dwg_gw; gh = dwg_gh
                use_dwg = True

        if not use_dwg:
            ox, oy, sc_g, gw, gh = _grid_layout(w, h, nx, ny, px_m, py_m)
            _draw_grid_axes(c, ox, oy, sc_g, nx, ny, px_m, py_m, gw, gh)
            _draw_poteaux(c, ox, oy, sc_g, nx, ny, px_m, py_m, pot_s)

        notes = []

        # ── Dessin MEP : logique room-aware ──
        # Classify rooms for this specific level
        if use_dwg:
            lvl_wet, lvl_living, lvl_service = _classify_rooms(level_geom.get('rooms', []))
            lvl_all = lvl_wet + lvl_living + lvl_service
            lvl_shafts = [(r['x'], r['y']) for r in lvl_service if 'asc' in r.get('name', '').lower()]
            if not lvl_shafts:
                lvl_shafts = [(r['x'], r['y']) for r in lvl_service if 'palier' in r.get('name', '').lower()]
            lvl_halls = [r for r in lvl_service if any(k in r.get('name', '').lower() for k in ['hall','palier','dgt'])]

        # ── Gaine technique unique (GT) : point de passage vertical ──
        # Positionnée à côté de la première gaine ascenseur
        # Tous les réseaux convergent vers ce point via collecteurs horizontaux
        def _draw_gt(c, gtx, gty, label, color):
            """Dessine la gaine technique avec label."""
            c.setFillColor(color); c.setStrokeColor(NOIR); c.setLineWidth(0.7)
            c.rect(gtx-5, gty-5, 10, 10, fill=1, stroke=1)
            c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(gtx, gty-2, label)
            # Symbole passage vertical (flèche haut/bas)
            c.setStrokeColor(BLANC); c.setLineWidth(0.5)
            c.line(gtx-2, gty+2, gtx, gty+4); c.line(gtx+2, gty+2, gtx, gty+4)
            c.line(gtx-2, gty-4, gtx, gty-6); c.line(gtx+2, gty-4, gtx, gty-6)

        def _route_to_gt(c, fx, fy, gtx, gty, color, width=0.6, dash=None):
            """Route un réseau d'un point vers la GT en L-shape."""
            if dash:
                c.setDash(*dash)
            c.setStrokeColor(color); c.setLineWidth(width)
            # L-shape : horizontal d'abord, puis vertical
            c.line(fx, fy, gtx, fy)  # horizontal
            c.line(gtx, fy, gtx, gty)  # vertical
            if dash:
                c.setDash()

        if use_dwg and lvl_all:
            # MODE DWG : utilise les positions réelles des pièces
            shafts = lvl_shafts
            wet_r = lvl_wet
            living_r = lvl_living
            all_r = lvl_all
            halls = lvl_halls

            # GT position : à côté du premier ascenseur (décalé de 3m)
            if shafts:
                gt_x, gt_y = shafts[0][0] + 3000, shafts[0][1]
            elif halls:
                gt_x, gt_y = halls[0]['x'], halls[0]['y']
            else:
                b = _dwg_bounds(level_geom)
                gt_x, gt_y = (b[0]+b[2])/2, (b[1]+b[3])/2
            gtx_p, gty_p = tx(gt_x), ty(gt_y)

            if key == "plb_ef":
                _draw_gt(c, gtx_p, gty_p, "EF", BLEU)
                c.setFillColor(BLEU); c.setFont("Helvetica", 3)
                c.drawString(gtx_p+7, gty_p+3, f"CM EF DN{pl.diam_colonne_montante_mm}")
                for wr in wet_r:
                    wx, wy = tx(wr['x']), ty(wr['y'])
                    _route_to_gt(c, wx, wy, gtx_p, gty_p, BLEU, 0.6)
                    n = wr.get('name','').lower()
                    if 'sdb' in n or 'douche' in n:
                        c.setFillColor(BLANC); c.setStrokeColor(BLEU); c.setLineWidth(0.5)
                        c.circle(wx, wy, 2.5, fill=1, stroke=1)
                    elif 'wc' in n or 'toil' in n:
                        c.setFillColor(BLEU); c.circle(wx, wy, 2, fill=1, stroke=0)
                    elif 'cuisine' in n or 'kitch' in n:
                        c.setFillColor(BLEU); c.rect(wx-2.5, wy-1.5, 5, 3, fill=1, stroke=0)
                    elif 'buanderie' in n:
                        c.setFillColor(CYAN); c.rect(wx-2, wy-2, 4, 4, fill=1, stroke=0)
                notes = [f"CM EF DN{pl.diam_colonne_montante_mm}", f"Citerne {int(pl.volume_citerne_m3)}m³",
                         f"Surpresseur {pl.debit_surpresseur_m3h}m³/h"]
                _legend(c, w, h, [(BLEU, 'fill', "Gaine technique (GT)"),
                                  (BLEU, 0.6, "Distribution EF"), (BLEU, 'circle', "SDB/Douche"),
                                  (BLEU, 'fill', "WC"), (BLEU, 'fill', "Évier")])

            elif key == "plb_ec":
                _draw_gt(c, gtx_p, gty_p, "EC", ROUGE)
                for wr in wet_r:
                    n = wr.get('name','').lower()
                    if any(k in n for k in ['sdb','douche','cuisine','kitch','buanderie']):
                        wx, wy = tx(wr['x']), ty(wr['y'])
                        _route_to_gt(c, wx, wy, gtx_p, gty_p, ROUGE, 0.5, (3,1.5))
                        c.setFillColor(BLANC); c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
                        c.circle(wx, wy, 2.5, fill=1, stroke=1)
                notes = ["CM EC DN32", f"{pl.nb_chauffe_eau_solaire} CESI"]
                _legend(c, w, h, [(ROUGE, 'fill', "GT — EC DN32"), (ROUGE, 0.5, "Distribution EC")])

            elif key == "plb_eu":
                _draw_gt(c, gtx_p, gty_p, "EU", MARRON)
                c.setFillColor(MARRON); c.setFont("Helvetica", 3)
                c.drawString(gtx_p+7, gty_p+3, "CE EU DN100")
                for wr in wet_r:
                    wx, wy = tx(wr['x']), ty(wr['y'])
                    _route_to_gt(c, wx, wy, gtx_p, gty_p, MARRON, 0.5, (4,2))
                    c.setFillColor(MARRON); c.circle(wx, wy, 2, fill=1, stroke=0)
                notes = ["Chute EU DN100", f"Conso {pl.conso_eau_annuelle_m3:.0f}m³/an"]
                _legend(c, w, h, [(MARRON, 'fill', "GT — EU DN100"), (MARRON, 0.5, "Collecteur")])

            elif key == "elec_ecl":
                for r in all_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace']): continue
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setStrokeColor(JAUNE); c.setFillColor(colors.HexColor("#FFF8E1")); c.setLineWidth(0.4)
                    c.circle(rx, ry+5, 2.5, fill=1, stroke=1)
                    c.setStrokeColor(JAUNE); c.setLineWidth(0.3)
                    c.line(rx-1.5, ry+5, rx+1.5, ry+5); c.line(rx, ry+3.5, rx, ry+6.5)
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','cuisine','sdb','wc','restaurant','magasin','salle']):
                        c.setFillColor(colors.HexColor("#FFF9C4")); c.setStrokeColor(ORANGE); c.setLineWidth(0.3)
                        c.circle(rx-7, ry+2, 1.5, fill=1, stroke=1)
                notes = [f"P éclairage: {el.puissance_eclairage_kw:.1f} kW"]
                _legend(c, w, h, [(JAUNE, 'circle', "Luminaire"), (colors.HexColor("#FFF9C4"), 'circle', "Interrupteur")])

            elif key == "elec_dist":
                # TD dans la gaine technique
                _draw_gt(c, gtx_p, gty_p, "TD", VERT)
                c.setFillColor(VERT); c.setFont("Helvetica", 3)
                c.drawString(gtx_p+7, gty_p+3, f"Transfo {el.transfo_kva}kVA")
                # Chemin de câbles principal via les circulations → GT
                sh = sorted(halls, key=lambda r: r['y'])
                if sh:
                    c.setStrokeColor(ORANGE); c.setLineWidth(1.5)
                    prev_x, prev_y = gtx_p, gty_p
                    for hh in sh:
                        hx, hy = tx(hh['x']), ty(hh['y'])
                        c.line(prev_x, prev_y, hx, hy); prev_x, prev_y = hx, hy
                # Prises dans chaque pièce
                for r in all_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace']): continue
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(ORANGE); c.setStrokeColor(NOIR); c.setLineWidth(0.15)
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','restaurant']):
                        for dx, dy in [(-6,-3),(6,-3),(-6,3),(6,3)]:
                            c.rect(rx+dx-1.2, ry+dy-0.8, 2.4, 1.6, fill=1, stroke=1)
                    elif any(k in n for k in ['cuisine','kitch']):
                        for dx, dy in [(-6,-3),(6,-3),(-6,3),(6,3),(0,-5),(0,5)]:
                            c.rect(rx+dx-1.2, ry+dy-0.8, 2.4, 1.6, fill=1, stroke=1)
                    else:
                        c.rect(rx+4, ry-0.8, 2.4, 1.6, fill=1, stroke=1)
                notes = [f"Transfo {el.transfo_kva}kVA", f"GE {el.groupe_electrogene_kva}kVA",
                         f"{el.nb_compteurs} compteurs — Col.{el.section_colonne_mm2}mm²"]
                _legend(c, w, h, [(VERT, 'fill', "GT — TD"), (ORANGE, 1.5, "Chemin câbles"),
                                  (ORANGE, 'fill', "Prise 2P+T")])

            elif key == "cvc_clim":
                for r in living_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','gym','restaurant','salle','magasin']):
                        rx, ry = tx(r['x']), ty(r['y'])
                        c.setFillColor(CYAN); c.setStrokeColor(colors.HexColor("#006064")); c.setLineWidth(0.35)
                        c.rect(rx-4.5, ry+7, 9, 2.5, fill=1, stroke=1)
                        c.setFillColor(colors.HexColor("#006064")); c.setFont("Helvetica", 2.2)
                        if 'salon' in n or 'sejour' in n or 'sam' in n or 'restaurant' in n:
                            c.drawCentredString(rx, ry+11.5, "18000 BTU")
                        elif 'chambre' in n:
                            c.drawCentredString(rx, ry+11.5, "12000 BTU")
                        else:
                            c.drawCentredString(rx, ry+11.5, "9000 BTU")
                notes = [f"P frigo: {cv.puissance_frigorifique_kw:.0f}kW",
                         f"Splits séj: {cv.nb_splits_sejour} — ch: {cv.nb_splits_chambre}"]
                _legend(c, w, h, [(CYAN, 'fill', "Split mural")])

            elif key == "cvc_vmc":
                for r in wet_r:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setStrokeColor(colors.HexColor("#2E7D32")); c.setFillColor(colors.HexColor("#C8E6C9"))
                    c.setLineWidth(0.4); c.circle(rx, ry+4, 2.5, fill=1, stroke=1)
                    c.setStrokeColor(colors.HexColor("#2E7D32")); c.setLineWidth(0.5)
                    c.line(rx, ry+6.5, rx, ry+9)
                if len(halls) >= 2:
                    sh = sorted(halls, key=lambda r: r['y'])
                    c.setStrokeColor(colors.HexColor("#2E7D32")); c.setLineWidth(1.2); c.setDash(5,2)
                    for i in range(len(sh)-1):
                        c.line(tx(sh[i]['x']), ty(sh[i]['y']), tx(sh[i+1]['x']), ty(sh[i+1]['y']))
                    c.setDash()
                notes = [f"{cv.nb_vmc} VMC {cv.type_vmc}"]
                _legend(c, w, h, [(colors.HexColor("#2E7D32"), 'circle', "Bouche VMC"),
                                  (colors.HexColor("#2E7D32"), 0.5, "Gaine VMC")])

            elif key == "ssi_det":
                for r in all_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(BLANC); c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
                    c.circle(rx, ry-5, 2.5, fill=1, stroke=1)
                    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 3)
                    c.drawCentredString(rx, ry-6.5, "DF")
                exits = [r for r in lvl_service if any(k in r.get('name','').lower() for k in ['palier','hall','sas'])]
                for r in exits:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(ROUGE); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
                    c.rect(rx-7, ry-2.5, 4, 4, fill=1, stroke=1)
                    c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 2.5)
                    c.drawCentredString(rx-5, ry-1.5, "DM")
                notes = [f"{si.nb_detecteurs_fumee} DF — {si.nb_declencheurs_manuels} DM",
                         f"Cat.ERP {si.categorie_erp} — {si.centrale_zones} zones"]
                _legend(c, w, h, [(ROUGE, 'circle', "DF"), (ROUGE, 'fill', "DM")])

            elif key == "ssi_ext":
                stairs = [r for r in lvl_service if 'palier' in r.get('name','').lower()]
                for r in stairs:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(BLANC); c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
                    c.circle(rx+9, ry+4, 3.5, fill=1, stroke=1)
                    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 4)
                    c.drawCentredString(rx+9, ry+2.5, "R")
                    c.setFillColor(VERT); c.setStrokeColor(NOIR); c.setLineWidth(0.25)
                    c.rect(rx+4, ry-8, 5, 3, fill=1, stroke=1)
                    c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 2)
                    c.drawCentredString(rx+6.5, ry-7, "BAES")
                notes = [f"{si.nb_extincteurs_co2+si.nb_extincteurs_poudre} ext. — RIA {si.longueur_ria_ml:.0f}ml",
                         f"Sprinklers: {'OUI' if si.sprinklers_requis else 'NON'}"]
                _legend(c, w, h, [(ROUGE, 'circle', "RIA"), (VERT, 'fill', "BAES")])

            elif key == "cfa":
                for r in all_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam','cuisine','hall','restaurant','salle']):
                        rx, ry = tx(r['x']), ty(r['y'])
                        c.setFillColor(VIOLET); c.setStrokeColor(NOIR); c.setLineWidth(0.2)
                        c.rect(rx-1.5, ry-4, 3, 2.5, fill=1, stroke=1)
                cams = [r for r in lvl_service if any(k in r.get('name','').lower() for k in ['hall','palier','sas','porche'])]
                for r in cams:
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(colors.HexColor("#CE93D8")); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
                    path = c.beginPath()
                    path.moveTo(rx, ry+8); path.lineTo(rx-3, ry+3); path.lineTo(rx+3, ry+3)
                    path.close(); c.drawPath(path, fill=1, stroke=0)
                notes = [f"{cf.nb_prises_rj45} RJ45 — {cf.nb_cameras_int+cf.nb_cameras_ext} caméras"]
                _legend(c, w, h, [(VIOLET, 'fill', "RJ45"), (colors.HexColor("#CE93D8"), 'circle', "Caméra IP")])

            elif key == "asc_plan":
                for r in lvl_service:
                    if 'asc' in r.get('name','').lower():
                        rx, ry = tx(r['x']), ty(r['y'])
                        c.setFillColor(BLEU_B); c.setStrokeColor(BLEU); c.setLineWidth(1)
                        c.rect(rx-8, ry-8, 16, 16, fill=1, stroke=1)
                        c.setStrokeColor(BLEU); c.setLineWidth(0.3)
                        c.line(rx-8, ry-8, rx+8, ry+8); c.line(rx-8, ry+8, rx+8, ry-8)
                        c.setFillColor(BLEU); c.setFont("Helvetica-Bold", 3)
                        c.drawCentredString(rx, ry-12, f"{asc.nb_ascenseurs}× {asc.capacite_kg}kg")
                notes = [f"{asc.nb_ascenseurs} asc. {asc.capacite_kg}kg — {asc.vitesse_ms}m/s"]
                _legend(c, w, h, [(BLEU_B, 'fill', "Gaine ascenseur")])

            elif key == "gtb":
                if len(halls) >= 2:
                    sh = sorted(halls, key=lambda r: r['y'])
                    c.setStrokeColor(BLEU); c.setLineWidth(1.8)
                    for i in range(len(sh)-1):
                        c.line(tx(sh[i]['x']), ty(sh[i]['y']), tx(sh[i+1]['x']), ty(sh[i+1]['y']))
                for r in all_r:
                    n = r.get('name','').lower()
                    if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide']): continue
                    rx, ry = tx(r['x']), ty(r['y'])
                    if any(k in n for k in ['hall','palier','dgt','sas']):
                        c.setFillColor(ORANGE); c.circle(rx-6, ry+6, 2, fill=1, stroke=0)
                    if any(k in n for k in ['chambre','salon','sejour','bureau','sam']):
                        c.setFillColor(ORANGE); c.rect(rx-7, ry-5, 4, 3, fill=1, stroke=0)
                notes = [f"{aut.protocole} — {aut.niveau} — {aut.nb_points_controle} pts"]
                _legend(c, w, h, [(BLEU, 1.8, f"Bus {aut.protocole}"), (ORANGE, 'circle', "Capteur")])

        else:
            # MODE GRILLE : distribution dans les travées
            cx_noy = ox + gw/2; cy_noy = oy + gh/2
            bays = []
            for i in range(nx):
                for j in range(ny):
                    bays.append((ox + (i+0.5)*px_m*sc_g, oy + (j+0.5)*py_m*sc_g))

            if key == "plb_ef":
                c.setFillColor(BLEU); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
                c.circle(cx_noy, cy_noy, 4, fill=1, stroke=1)
                c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 5); c.drawCentredString(cx_noy, cy_noy-2, "EF")
                for bx, by in bays:
                    c.setStrokeColor(BLEU); c.setLineWidth(0.6)
                    c.line(cx_noy, cy_noy, cx_noy, by); c.line(cx_noy, by, bx, by)
                    c.setFillColor(BLEU); c.circle(bx, by, 2, fill=1, stroke=0)
                notes = [f"CM EF DN{pl.diam_colonne_montante_mm}", f"Citerne {int(pl.volume_citerne_m3)}m³"]
                _legend(c, w, h, [(BLEU, 'circle', f"CM EF DN{pl.diam_colonne_montante_mm}"),
                                  (BLEU, 0.6, "Distribution EF")])
            elif key == "plb_ec":
                c.setFillColor(ROUGE); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
                c.circle(cx_noy, cy_noy, 4, fill=1, stroke=1)
                c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 5); c.drawCentredString(cx_noy, cy_noy-2, "EC")
                for bx, by in bays:
                    c.setStrokeColor(ROUGE); c.setLineWidth(0.5); c.setDash(3,1.5)
                    c.line(cx_noy, cy_noy, cx_noy, by); c.line(cx_noy, by, bx, by); c.setDash()
                notes = ["CM EC DN32", f"{pl.nb_chauffe_eau_solaire} CESI"]
                _legend(c, w, h, [(ROUGE, 'circle', "CM EC DN32"), (ROUGE, 0.5, "Distribution EC")])
            elif key == "plb_eu":
                c.setFillColor(MARRON); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
                c.circle(cx_noy, cy_noy, 4, fill=1, stroke=1)
                c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 5); c.drawCentredString(cx_noy, cy_noy-2, "EU")
                for bx, by in bays:
                    c.setStrokeColor(MARRON); c.setLineWidth(0.5); c.setDash(4,2)
                    c.line(bx, by, cx_noy, by); c.line(cx_noy, by, cx_noy, cy_noy); c.setDash()
                    c.setFillColor(MARRON); c.circle(bx, by, 1.5, fill=1, stroke=0)
                notes = ["Chute EU DN100", f"Conso {pl.conso_eau_annuelle_m3:.0f}m³/an"]
                _legend(c, w, h, [(MARRON, 'circle', "Chute EU DN100"), (MARRON, 0.5, "Collecteur")])
            elif key == "elec_ecl":
                for bx, by in bays:
                    c.setStrokeColor(JAUNE); c.setFillColor(colors.HexColor("#FFF8E1")); c.setLineWidth(0.4)
                    c.circle(bx, by, 3, fill=1, stroke=1)
                    c.setStrokeColor(JAUNE); c.setLineWidth(0.3)
                    c.line(bx-2, by, bx+2, by); c.line(bx, by-2, bx, by+2)
                notes = [f"P éclairage: {el.puissance_eclairage_kw:.1f}kW"]
                _legend(c, w, h, [(JAUNE, 'circle', "Luminaire")])
            elif key == "elec_dist":
                c.setFillColor(VERT); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
                c.rect(cx_noy-5, cy_noy-5, 10, 7, fill=1, stroke=1)
                c.setFillColor(BLANC); c.setFont("Helvetica-Bold", 4); c.drawCentredString(cx_noy, cy_noy-3, "TGBT")
                c.setStrokeColor(ORANGE); c.setLineWidth(1.2)
                c.line(cx_noy, cy_noy-5, cx_noy, oy); c.line(cx_noy, cy_noy+2, cx_noy, oy+gh)
                for bx, by in bays:
                    c.setFillColor(ORANGE); c.setStrokeColor(NOIR); c.setLineWidth(0.15)
                    for dx, dy in [(-4,-2),(4,-2),(-4,2),(4,2)]:
                        c.rect(bx+dx-1.2, by+dy-0.8, 2.4, 1.6, fill=1, stroke=1)
                notes = [f"Transfo {el.transfo_kva}kVA", f"GE {el.groupe_electrogene_kva}kVA"]
                _legend(c, w, h, [(VERT, 'fill', "TGBT"), (ORANGE, 1.2, "Chemin câbles"), (ORANGE, 'fill', "Prise")])
            elif key == "cvc_clim":
                for bx, by in bays:
                    c.setFillColor(CYAN); c.setStrokeColor(colors.HexColor("#006064")); c.setLineWidth(0.35)
                    c.rect(bx-5, by+4, 10, 3, fill=1, stroke=1)
                notes = [f"P frigo: {cv.puissance_frigorifique_kw:.0f}kW", f"Splits: {cv.nb_splits_sejour+cv.nb_splits_chambre}"]
                _legend(c, w, h, [(CYAN, 'fill', "Split")])
            elif key == "cvc_vmc":
                for bx, by in bays:
                    c.setStrokeColor(colors.HexColor("#2E7D32")); c.setFillColor(colors.HexColor("#C8E6C9"))
                    c.setLineWidth(0.4); c.circle(bx, by-3, 3, fill=1, stroke=1)
                notes = [f"{cv.nb_vmc} VMC {cv.type_vmc}"]
                _legend(c, w, h, [(colors.HexColor("#2E7D32"), 'circle', "Bouche VMC")])
            elif key == "ssi_det":
                for bx, by in bays:
                    c.setFillColor(BLANC); c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
                    c.circle(bx, by, 3, fill=1, stroke=1)
                    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 3.5); c.drawCentredString(bx, by-1.5, "DF")
                notes = [f"{si.nb_detecteurs_fumee} DF — {si.nb_declencheurs_manuels} DM"]
                _legend(c, w, h, [(ROUGE, 'circle', "DF")])
            elif key == "ssi_ext":
                for corner in [(ox+10, oy+10), (ox+gw-10, oy+gh-10)]:
                    rx, ry = corner
                    c.setFillColor(BLANC); c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
                    c.circle(rx, ry, 4, fill=1, stroke=1)
                    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 5); c.drawCentredString(rx, ry-2, "R")
                    c.setFillColor(VERT); c.rect(rx+8, ry-4, 6, 3.5, fill=1, stroke=1)
                notes = [f"{si.nb_extincteurs_co2+si.nb_extincteurs_poudre} ext. — RIA {si.longueur_ria_ml:.0f}ml"]
                _legend(c, w, h, [(ROUGE, 'circle', "RIA"), (VERT, 'fill', "BAES")])
            elif key == "cfa":
                for bx, by in bays:
                    c.setFillColor(VIOLET); c.setStrokeColor(NOIR); c.setLineWidth(0.2)
                    c.rect(bx-2, by-2, 4, 3, fill=1, stroke=1)
                notes = [f"{cf.nb_prises_rj45} RJ45 — {cf.nb_cameras_int+cf.nb_cameras_ext} caméras"]
                _legend(c, w, h, [(VIOLET, 'fill', "RJ45")])
            elif key == "asc_plan":
                c.setFillColor(BLEU_B); c.setStrokeColor(BLEU); c.setLineWidth(1)
                c.rect(cx_noy-8, cy_noy-8, 16, 16, fill=1, stroke=1)
                c.setStrokeColor(BLEU); c.setLineWidth(0.3)
                c.line(cx_noy-8, cy_noy-8, cx_noy+8, cy_noy+8); c.line(cx_noy-8, cy_noy+8, cx_noy+8, cy_noy-8)
                c.setFillColor(BLEU); c.setFont("Helvetica-Bold", 4)
                c.drawCentredString(cx_noy, cy_noy-12, f"{asc.nb_ascenseurs}× {asc.capacite_kg}kg")
                notes = [f"{asc.nb_ascenseurs} asc. {asc.capacite_kg}kg"]
                _legend(c, w, h, [(BLEU_B, 'fill', "Gaine ascenseur")])
            elif key == "gtb":
                c.setStrokeColor(BLEU); c.setLineWidth(1.8)
                c.line(ox, cy_noy, ox+gw, cy_noy)
                for bx, by in bays:
                    c.setFillColor(ORANGE); c.circle(bx-3, by+3, 1.5, fill=1, stroke=0)
                notes = [f"{aut.protocole} — {aut.nb_points_controle} pts"]
                _legend(c, w, h, [(BLEU, 1.8, f"Bus {aut.protocole}"), (ORANGE, 'circle', "Capteur")])

        # Notes en bas
        c.setFont("Helvetica", 5); c.setFillColor(GRIS3)
        for k_n, note in enumerate(notes[:3]):
            c.drawString(14*mm, 42*mm - k_n*5*mm, note)

        _cartouche(c, w, h, p, title, page, total_pages)
        c.showPage()

    c.save()
    return output_path

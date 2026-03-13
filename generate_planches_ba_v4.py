"""
Tijan AI — Planches BA v4
8 planches A3 paysage — charte sobre Tijan v4
Clipping systématique, pas de débordement, palette minimaliste.
Géométrie depuis DXF parsé OU paramètres Sakho en fallback.
"""
import math
import io
from datetime import datetime
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pypdf import PdfWriter, PdfReader

import sys
sys.path.insert(0, '/home/claude')
from tijan_theme import *

# ── Données Sakho (fallback sans DXF) ───────────────────────
PROJET_SAKHO = {
    "nom":   "Résidence Papa Oumar Sakho",
    "ref":   "1711-STR",
    "ville": "Dakar, Sénégal",
    "beton": "C30/37",
    "acier": "HA500",
    "norme": "EN 1992-1-1 (Eurocodes)",
}

GRILLE_SAKHO = {
    "px": [6180, 6180, 5180, 6180, 5180, 6180, 5180, 6180],
    "py": [5180, 4130, 5180, 4130, 5180],
}

POTEAUX_SAKHO = [
    {"label": "RDC",      "b": 500, "nb": 12, "diam": 20, "cd": 10, "ce": 150, "NEd": 5585},
    {"label": "Niveau 2", "b": 500, "nb":  8, "diam": 16, "cd":  8, "ce": 115, "NEd": 4897},
    {"label": "Niveau 3", "b": 450, "nb":  8, "diam": 16, "cd":  8, "ce": 115, "NEd": 4200},
    {"label": "Niveau 4", "b": 450, "nb":  8, "diam": 16, "cd":  8, "ce": 115, "NEd": 3500},
    {"label": "Niveau 5", "b": 400, "nb":  8, "diam": 14, "cd":  8, "ce": 130, "NEd": 2800},
    {"label": "Niveau 6", "b": 350, "nb":  8, "diam": 14, "cd":  8, "ce": 140, "NEd": 2200},
    {"label": "Niveau 7", "b": 300, "nb":  8, "diam": 12, "cd":  8, "ce": 150, "NEd": 1600},
    {"label": "Niveau 8", "b": 250, "nb":  8, "diam": 12, "cd":  8, "ce": 160, "NEd": 1050},
    {"label": "Toiture",  "b": 200, "nb":  4, "diam": 12, "cd":  8, "ce": 180, "NEd":  500},
]

POUTRE_SAKHO = {
    "b": 250, "h": 450,
    "As_inf": 3.83, "As_sup": 4.85,
    "etrier_d": 8, "etrier_e": 300,
    "portee": 6180,
}

FOND_SAKHO = {
    "type": "Pieux forés", "nb": 4,
    "diam": 800, "L": 10.0,
    "As_cm2": 39.27, "cerce_d": 12, "cerce_e": 200,
}


# ════════════════════════════════════════════════════════════
# MOTEUR DE GRILLE — echelle + positions axes
# ════════════════════════════════════════════════════════════

# Zone dessin effective (sous le bandeau titre)
ZX = DX + 2*mm
ZY = DY + 2*mm
ZW = DW - 4*mm
ZH = DH - TITRE_H - 4*mm


def calcul_grille(portees_x=None, portees_y=None, marge=8*mm):
    """Calcule scale + positions axes pour tenir dans la zone dessin"""
    px = portees_x or GRILLE_SAKHO["px"]
    py = portees_y or GRILLE_SAKHO["py"]
    Lx, Ly = sum(px), sum(py)
    sx = (ZW - 2*marge) / Lx
    sy = (ZH - 2*marge) / Ly
    scale = min(sx, sy)
    ox = ZX + marge + (ZW - 2*marge - Lx*scale) / 2
    oy = ZY + marge + (ZH - 2*marge - Ly*scale) / 2
    axes_x = [ox]
    for p in px:
        axes_x.append(axes_x[-1] + p * scale)
    axes_y = [oy]
    for p in py:
        axes_y.append(axes_y[-1] + p * scale)
    return scale, ox, oy, axes_x, axes_y


# ════════════════════════════════════════════════════════════
# HELPERS DESSIN BA
# ════════════════════════════════════════════════════════════

def fond_plan(c, axes_x, axes_y):
    """Fond neutre de la dalle"""
    c.setFillColor(GRIS_FOND)
    c.setStrokeColor(GRIS_CLAIR)
    c.setLineWidth(LW_FIN)
    c.rect(axes_x[0], axes_y[0],
           axes_x[-1]-axes_x[0], axes_y[-1]-axes_y[0],
           fill=1, stroke=1)


def tracer_axes(c, axes_x, axes_y, r_bulle=3.5*mm):
    """Axes tiretés + bulles"""
    lettres = "ABCDEFGHIJKLM"
    x0, y0 = axes_x[0], axes_y[0]
    x1, y1 = axes_x[-1], axes_y[-1]

    set_trait(c, LW_FIN, GRIS_MOY, ([5, 2], 0))
    for x in axes_x:
        c.line(x, y0 - 6*mm, x, y1 + 6*mm)
    for y in axes_y:
        c.line(x0 - 6*mm, y, x1 + 6*mm, y)
    c.setDash()

    for i, x in enumerate(axes_x):
        bulle_axe(c, x, y1 + r_bulle + 1.5*mm, r_bulle, str(i+1))
        bulle_axe(c, x, y0 - r_bulle - 1.5*mm, r_bulle, str(i+1))
    for j, y in enumerate(axes_y):
        bulle_axe(c, x0 - r_bulle - 1.5*mm, y, r_bulle, lettres[j])
        bulle_axe(c, x1 + r_bulle + 1.5*mm, y, r_bulle, lettres[j])


def cotations_grille(c, axes_x, axes_y, portees_x, portees_y, scale):
    """Cotations portées sous et à gauche"""
    y_cote = axes_y[0] - 10*mm
    x_cote = axes_x[0] - 10*mm

    set_trait(c, LW_FIN, GRIS_FORT)

    # Portées X
    for i, p in enumerate(portees_x):
        x1, x2 = axes_x[i], axes_x[i+1]
        c.line(x1, axes_y[0], x1, y_cote - 1*mm)
        c.line(x2, axes_y[0], x2, y_cote - 1*mm)
        c.line(x1, y_cote, x2, y_cote)
        _fleche_cote(c, x1, y_cote, "d")
        _fleche_cote(c, x2, y_cote, "g")
        c.setFillColor(NOIR); c.setFont(FONT_SOUS, 5)
        c.drawCentredString((x1+x2)/2, y_cote - 4*mm, f"{p/1000:.2f}m")

    # Total X
    c.setFont(FONT_TITRE, 5.5); c.setFillColor(TIJAN_VERT_F)
    total_x = sum(portees_x)
    c.drawCentredString((axes_x[0]+axes_x[-1])/2, y_cote - 8.5*mm,
                        f"L = {total_x/1000:.2f} m")

    # Portées Y
    for j, p in enumerate(portees_y):
        y1, y2 = axes_y[j], axes_y[j+1]
        c.setFillColor(NOIR); c.setFont(FONT_SOUS, 5)
        c.drawCentredString(x_cote - 2*mm, (y1+y2)/2 - 2, f"{p/1000:.2f}")

    # Total Y
    c.setFont(FONT_TITRE, 5.5); c.setFillColor(TIJAN_VERT_F)
    c.drawCentredString(x_cote - 2*mm, (axes_y[0]+axes_y[-1])/2 + 6*mm,
                        f"{sum(portees_y)/1000:.2f}m")


def _fleche_cote(c, x, y, direction, s=1.8*mm):
    c.setFillColor(GRIS_FORT)
    p = c.beginPath()
    if direction == "d":
        p.moveTo(x, y); p.lineTo(x+s, y+s*0.4); p.lineTo(x+s, y-s*0.4)
    else:
        p.moveTo(x, y); p.lineTo(x-s, y+s*0.4); p.lineTo(x-s, y-s*0.4)
    p.close(); c.drawPath(p, fill=1, stroke=0)


def poteau_coffrage(c, cx, cy, b_s, label_section=None):
    """Poteau vue de dessus — coffrage"""
    hachures(c, cx-b_s/2, cy-b_s/2, b_s, b_s)
    set_trait(c, LW_GROS, NOIR)
    c.rect(cx-b_s/2, cy-b_s/2, b_s, b_s, fill=0, stroke=1)
    if label_section:
        c.setFillColor(TIJAN_VERT_F); c.setFont(FONT_TITRE, 4.5)
        c.drawCentredString(cx, cy - b_s/2 - 3.5, label_section)


def poteau_ferraille(c, cx, cy, b_s, nb_barres, diam_mm, cd_mm, ce_mm):
    """Coupe poteau avec armatures individuelles"""
    enrob = 3*mm

    # Béton
    c.setFillColor(GRIS_FOND)
    set_trait(c, LW_GROS, NOIR)
    c.rect(cx-b_s/2, cy-b_s/2, b_s, b_s, fill=1, stroke=1)
    hachures(c, cx-b_s/2, cy-b_s/2, b_s, b_s)

    # Cadre
    offset = enrob + max(3, cd_mm * 0.35)
    set_trait(c, LW_FIN * 1.5, GRIS_FORT)
    c.rect(cx-b_s/2+offset, cy-b_s/2+offset,
           b_s-2*offset, b_s-2*offset, fill=0, stroke=1)

    # Barres longitudinales
    r_b = max(1.5, diam_mm * 0.35)
    positions = _positions_barres(b_s, nb_barres, enrob + max(3, cd_mm*0.35) + r_b)
    for px_b, py_b in positions:
        c.setFillColor(NOIR)
        c.circle(cx + px_b, cy + py_b, r_b, fill=1, stroke=0)


def _positions_barres(b_s, nb, offset):
    """Positions des barres dans la section"""
    pos = []
    inner = b_s - 2*offset
    barres_cote = max(2, nb // 4)
    n_tot = barres_cote * 4 - 4
    # 4 coins
    coins = [(-inner/2, -inner/2), (inner/2, -inner/2),
             (inner/2, inner/2), (-inner/2, inner/2)]
    pos.extend(coins)
    # Barres intermédiaires
    if nb > 4:
        extra = nb - 4
        par_cote = extra // 4
        for k in range(1, par_cote+1):
            t = k / (par_cote+1)
            pos.append((-inner/2 + t*inner, -inner/2))
            pos.append((-inner/2 + t*inner,  inner/2))
            pos.append((-inner/2, -inner/2 + t*inner))
            pos.append(( inner/2, -inner/2 + t*inner))
    return pos[:nb]


def poutre_coupe(c, cx, cy, b_s, h_s, As_inf, As_sup, etrier_d, etrier_e):
    """Coupe poutre T — vue de côté simplifiée"""
    enrob = 3*mm
    # Béton
    c.setFillColor(GRIS_FOND)
    set_trait(c, LW_GROS, NOIR)
    c.rect(cx-b_s/2, cy-h_s/2, b_s, h_s, fill=1, stroke=1)
    hachures(c, cx-b_s/2, cy-h_s/2, b_s, h_s)

    # Étriers
    off_et = enrob + max(2, etrier_d*0.3)
    set_trait(c, LW_FIN * 1.5, GRIS_FORT)
    c.rect(cx-b_s/2+off_et, cy-h_s/2+off_et,
           b_s-2*off_et, h_s-2*off_et, fill=0, stroke=1)

    # Barres inf
    r_b = max(1.5, 16*0.35)
    n_inf = max(2, round(As_inf / (math.pi*(16/2)**2/100)))
    espacement = (b_s - 2*(enrob + off_et)) / max(n_inf-1, 1)
    for i in range(n_inf):
        bx = cx - b_s/2 + enrob + off_et + i*espacement
        c.setFillColor(NOIR)
        c.circle(bx, cy-h_s/2+enrob+off_et+r_b, r_b, fill=1, stroke=0)

    # Barres sup
    n_sup = max(2, round(As_sup / (math.pi*(16/2)**2/100)))
    for i in range(n_sup):
        bx = cx - b_s/2 + enrob + off_et + i*(b_s-2*(enrob+off_et))/max(n_sup-1,1)
        c.setFillColor(NOIR)
        c.circle(bx, cy+h_s/2-enrob-off_et-r_b, r_b, fill=1, stroke=0)


# ════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE PAGES
# ════════════════════════════════════════════════════════════

def nouvelle_page(proj):
    buf = io.BytesIO()
    cv = canvas.Canvas(buf, pagesize=A3L)
    bordure_page(cv)
    return cv, buf


def finaliser(cv, buf):
    cv.save(); buf.seek(0)
    return PdfReader(buf).pages[0]


def _cartouche_ba(cv, num, titre, sous_titre, proj, echelle="1/200"):
    cartouche(cv, num, 8, titre, sous_titre,
              "STRUCTURE BA", echelle,
              proj["nom"], proj["ref"], proj["ville"],
              datetime.now().strftime("%d/%m/%Y"))


# ── Pl.1 — Plan de coffrage ──────────────────────────────────
def planche_1_coffrage(proj=None, portees_x=None, portees_y=None,
                       poteaux=None, poutre=None):
    proj = proj or PROJET_SAKHO
    px = portees_x or GRILLE_SAKHO["px"]
    py = portees_y or GRILLE_SAKHO["py"]
    poteaux = poteaux or POTEAUX_SAKHO
    poutre = poutre or POUTRE_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 1, "PLAN DE COFFRAGE", "Vue de dessus — Grille structurelle", proj)
    bandeau_titre(cv, "Pl.1 — PLAN DE COFFRAGE",
                  f"Béton {proj['beton']} — Acier {proj['acier']}")

    scale, ox, oy, axes_x, axes_y = calcul_grille(px, py)

    # Clipping zone dessin
    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    fond_plan(cv, axes_x, axes_y)

    # Poutres (lignes entre poteaux)
    b_pou = max(3*mm, scale * poutre["b"])
    cv.setFillColor(GRIS_ALT)
    set_trait(cv, LW_MOYEN, GRIS_FORT)
    for i in range(len(axes_x)-1):
        for j in range(len(axes_y)):
            x1, x2 = axes_x[i], axes_x[i+1]
            y = axes_y[j]
            cv.rect(x1, y-b_pou/2, x2-x1, b_pou, fill=1, stroke=1)
    for j in range(len(axes_y)-1):
        for i in range(len(axes_x)):
            x = axes_x[i]
            y1, y2 = axes_y[j], axes_y[j+1]
            cv.rect(x-b_pou/2, y1, b_pou, y2-y1, fill=1, stroke=1)

    # Poteaux (section RDC)
    b_s = max(4*mm, scale * poteaux[0]["b"])
    for i in range(len(axes_x)):
        for j in range(len(axes_y)):
            poteau_coffrage(cv, axes_x[i], axes_y[j], b_s)

    cv.restoreState()

    tracer_axes(cv, axes_x, axes_y)
    cotations_grille(cv, axes_x, axes_y, px, py, scale)

    # Nomenclature poteaux (tableau sobre en bas à droite de la zone)
    tx = ZX + ZW - 55*mm; ty = ZY + 2*mm
    tw = 53*mm; th = min(50*mm, ZH * 0.4)
    lignes = [("SECTION RDC", f"{poteaux[0]['b']//10}×{poteaux[0]['b']//10} cm")]
    lignes += [("---",)]
    lignes += [(p["label"], f"{p['b']//10}×{p['b']//10}cm / {p['nb']}HA{p['diam']}")
               for p in poteaux]
    tableau_donnees(cv, tx, ty, tw, th, "SECTIONS POTEAUX", lignes)

    return finaliser(cv, buf)


# ── Pl.2 — Ferraillage poteaux ───────────────────────────────
def planche_2_poteaux(proj=None, poteaux=None):
    proj = proj or PROJET_SAKHO
    poteaux = poteaux or POTEAUX_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 2, "FERRAILLAGE POTEAUX", "Coupes A-A — sections variables", proj, "1/20")
    bandeau_titre(cv, "Pl.2 — FERRAILLAGE POTEAUX",
                  "Sections variables RDC → Toiture — Eurocodes EN1992")

    n = len(poteaux)
    cols = min(4, n)
    rows = math.ceil(n / cols)
    cell_w = ZW / cols
    cell_h = ZH / rows

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    for idx, p in enumerate(poteaux):
        col = idx % cols
        row = idx // cols
        cx = ZX + col * cell_w + cell_w / 2
        cy = ZY + ZH - (row + 0.5) * cell_h

        size = min(cell_w * 0.6, cell_h * 0.6)
        b_s = max(12*mm, size * p["b"] / 500)

        # Coupe
        poteau_ferraille(cv, cx, cy, b_s,
                         p["nb"], p["diam"], p["cd"], p["ce"])

        # Label niveau — au-dessus
        cv.setFillColor(NOIR); cv.setFont(FONT_TITRE, 6.5)
        cv.drawCentredString(cx, cy + b_s/2 + 4*mm, p["label"])

        # Section — dessous
        cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 6)
        cv.drawCentredString(cx, cy - b_s/2 - 4*mm,
                             f"{p['b']//10}×{p['b']//10} cm")

        # Armatures
        cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
        cv.drawCentredString(cx, cy - b_s/2 - 8.5*mm,
                             f"{p['nb']}HA{p['diam']} — cadre ø{p['cd']}/{p['ce']}")

        # NEd
        cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 4.5)
        cv.drawCentredString(cx, cy - b_s/2 - 12.5*mm,
                             f"NEd = {p['NEd']} kN")

    cv.restoreState()

    return finaliser(cv, buf)


# ── Pl.3 — Poutres ───────────────────────────────────────────
def planche_3_poutres(proj=None, poutre=None, poteaux=None):
    proj = proj or PROJET_SAKHO
    poutre = poutre or POUTRE_SAKHO
    poteaux = poteaux or POTEAUX_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 3, "FERRAILLAGE POUTRES", "Élévation + Coupe A-A — portée type", proj, "1/20")
    bandeau_titre(cv, "Pl.3 — FERRAILLAGE POUTRES",
                  f"Portée type {poutre['portee']/1000:.2f}m — {proj['beton']}")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # ── Élévation poutre sur toute la largeur
    el_h = ZH * 0.38
    el_y = ZY + ZH * 0.52
    el_x = ZX + 10*mm
    el_w = ZW - 20*mm
    b_s_pou = max(6*mm, el_h * 0.6)
    h_s_pou = el_h

    # Poteaux supports
    b_s_pot = max(8*mm, el_w * 0.04)
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_GROS, NOIR)
    for xp in [el_x, el_x + el_w]:
        cv.rect(xp - b_s_pot/2, el_y, b_s_pot, h_s_pou * 1.3, fill=1, stroke=1)
        hachures(cv, xp-b_s_pot/2, el_y, b_s_pot, h_s_pou*1.3)

    # Corps poutre
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_GROS, NOIR)
    cv.rect(el_x, el_y, el_w, h_s_pou, fill=1, stroke=1)
    hachures(cv, el_x, el_y, el_w, h_s_pou)

    enrob = 3*mm
    r_b = max(2*mm, 0.4*mm * poutre["etrier_d"] * 10)

    # Étriers (représentation schématique verticale)
    n_etriers = int(el_w / max(8*mm, scale_etrier(poutre["etrier_e"])))
    set_trait(cv, LW_FIN * 1.5, GRIS_FORT)
    for k in range(1, n_etriers+1):
        xe = el_x + el_w * k / (n_etriers+1)
        cv.rect(xe - 1.5, el_y + enrob, 3, h_s_pou - 2*enrob, fill=0, stroke=1)

    # Barres inf (As_inf)
    r_l = max(1.8*mm, poutre["etrier_d"] * 0.09 * mm * 10)
    n_inf = max(2, round(poutre["As_inf"] / 2.01))
    esp_inf = (el_w - 2*(enrob + 6*mm)) / max(n_inf-1, 1)
    for i in range(n_inf):
        bx = el_x + enrob + 6*mm + i * esp_inf
        cv.setFillColor(NOIR)
        cv.circle(bx, el_y + enrob + r_l, r_l, fill=1, stroke=0)

    # Barres sup (As_sup)
    n_sup = max(2, round(poutre["As_sup"] / 2.01))
    esp_sup = (el_w - 2*(enrob + 6*mm)) / max(n_sup-1, 1)
    for i in range(n_sup):
        bx = el_x + enrob + 6*mm + i * esp_sup
        cv.setFillColor(NOIR)
        cv.circle(bx, el_y + h_s_pou - enrob - r_l, r_l, fill=1, stroke=0)

    # Cotations élévation
    set_trait(cv, LW_FIN, GRIS_FORT)
    # Portée
    cv.line(el_x, el_y - 6*mm, el_x + el_w, el_y - 6*mm)
    cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 6.5)
    cv.drawCentredString(el_x + el_w/2, el_y - 10.5*mm,
                         f"L = {poutre['portee']/1000:.2f} m")
    # Hauteur
    cv.line(el_x - 6*mm, el_y, el_x - 6*mm, el_y + h_s_pou)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(el_x - 16*mm, el_y + h_s_pou/2 - 2,
                  f"h={poutre['h']//10}cm")

    # ── Coupe A-A (en bas)
    cp_y = ZY + 4*mm
    cp_h = ZH * 0.38
    cp_w = min(cp_h, ZW * 0.25)
    cp_x = ZX + ZW/2 - cp_w/2
    b_s_cp = max(8*mm, cp_w * 0.7)
    h_s_cp = min(cp_h * 0.8, b_s_cp * (poutre["h"]/poutre["b"]))

    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_GROS, NOIR)
    cv.rect(cp_x + cp_w/2 - b_s_cp/2, cp_y + cp_h/2 - h_s_cp/2,
            b_s_cp, h_s_cp, fill=1, stroke=1)
    hachures(cv, cp_x + cp_w/2 - b_s_cp/2, cp_y + cp_h/2 - h_s_cp/2, b_s_cp, h_s_cp)

    cx_cp = cp_x + cp_w/2
    cy_cp = cp_y + cp_h/2

    # Cadre
    off_et = 4*mm
    set_trait(cv, LW_FIN * 1.5, GRIS_FORT)
    cv.rect(cx_cp - b_s_cp/2 + off_et, cy_cp - h_s_cp/2 + off_et,
            b_s_cp - 2*off_et, h_s_cp - 2*off_et, fill=0, stroke=1)

    r_b2 = max(1.5*mm, 16*0.35*mm*0.5)
    # Barres inf
    for i in range(n_inf):
        bx = cx_cp - b_s_cp/2 + off_et + r_b2 + \
             i * (b_s_cp - 2*off_et - 2*r_b2) / max(n_inf-1, 1)
        cv.setFillColor(NOIR)
        cv.circle(bx, cy_cp - h_s_cp/2 + off_et + r_b2, r_b2, fill=1, stroke=0)
    # Barres sup
    for i in range(n_sup):
        bx = cx_cp - b_s_cp/2 + off_et + r_b2 + \
             i * (b_s_cp - 2*off_et - 2*r_b2) / max(n_sup-1, 1)
        cv.setFillColor(NOIR)
        cv.circle(bx, cy_cp + h_s_cp/2 - off_et - r_b2, r_b2, fill=1, stroke=0)

    # Label coupe
    cv.setFillColor(NOIR); cv.setFont(FONT_TITRE, 6.5)
    cv.drawCentredString(cx_cp, cp_y + cp_h + 3*mm, "COUPE A-A")

    # Tableau récap
    tx = ZX + 2*mm; ty = ZY + 2*mm; tw = 55*mm; th = 36*mm
    tableau_donnees(cv, tx, ty, tw, th, "POUTRE TYPE", [
        ("b × h", f"{poutre['b']//10} × {poutre['h']//10} cm"),
        ("As inf.", f"{poutre['As_inf']} cm²"),
        ("As sup.", f"{poutre['As_sup']} cm²"),
        ("Étriers", f"HA{poutre['etrier_d']}/{poutre['etrier_e']} mm"),
        ("Portée", f"{poutre['portee']/1000:.2f} m"),
        ("Béton", proj["beton"]),
    ])

    cv.restoreState()
    return finaliser(cv, buf)


def scale_etrier(esp_mm):
    return esp_mm * 0.05


# ── Pl.4 — Dalle + fondations ────────────────────────────────
def planche_4_dalle_fond(proj=None, portees_x=None, portees_y=None, fond=None):
    proj = proj or PROJET_SAKHO
    px = portees_x or GRILLE_SAKHO["px"]
    py = portees_y or GRILLE_SAKHO["py"]
    fond = fond or FOND_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 4, "DALLE + FONDATIONS", "Armatures dalle — Plan fondations", proj)
    bandeau_titre(cv, "Pl.4 — DALLE ET FONDATIONS",
                  f"Pieux forés ø{fond['diam']} — L={fond['L']}m")

    scale, ox, oy, axes_x, axes_y = calcul_grille(px, py)

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    fond_plan(cv, axes_x, axes_y)

    # Treillis dalle (réseau de lignes fines)
    pas_tr = max(3*mm, scale * 200)
    set_trait(cv, LW_TRES_FIN + 0.1, GRIS_MOY)
    x0, y0, x1, y1 = axes_x[0], axes_y[0], axes_x[-1], axes_y[-1]
    for x in [x0 + i*pas_tr for i in range(int((x1-x0)/pas_tr)+1)]:
        if x0 <= x <= x1:
            cv.line(x, y0, x, y1)
    for y in [y0 + j*pas_tr for j in range(int((y1-y0)/pas_tr)+1)]:
        if y0 <= y <= y1:
            cv.line(x0, y, x1, y)

    # Semelles / pieux sous chaque nœud
    for i in range(len(axes_x)):
        for j in range(len(axes_y)):
            cx, cy = axes_x[i], axes_y[j]
            r_pieu = max(3*mm, scale * fond["diam"] / 2)
            # Groupe de pieux (4 pieux)
            offsets = [(-r_pieu*1.2, -r_pieu*1.2), (r_pieu*1.2, -r_pieu*1.2),
                       (r_pieu*1.2,  r_pieu*1.2), (-r_pieu*1.2,  r_pieu*1.2)]
            for dx, dy in offsets:
                cv.setFillColor(GRIS_CLAIR)
                set_trait(cv, LW_FIN, GRIS_FORT)
                cv.circle(cx+dx, cy+dy, r_pieu*0.5, fill=1, stroke=1)

    # Poteaux RDC
    b_s = max(4*mm, scale * POTEAUX_SAKHO[0]["b"])
    for i in range(len(axes_x)):
        for j in range(len(axes_y)):
            poteau_coffrage(cv, axes_x[i], axes_y[j], b_s)

    cv.restoreState()

    tracer_axes(cv, axes_x, axes_y)
    cotations_grille(cv, axes_x, axes_y, px, py, scale)

    # Tableau fondations
    tx = ZX + ZW - 60*mm; ty = ZY + 2*mm; tw = 58*mm; th = 40*mm
    tableau_donnees(cv, tx, ty, tw, th, "FONDATIONS — PIEUX FORÉS", [
        ("Type", fond["type"]),
        ("Nb pieux/poteau", str(fond["nb"])),
        ("Diamètre", f"ø{fond['diam']} mm"),
        ("Longueur", f"{fond['L']} m"),
        ("As longit.", f"{fond['As_cm2']} cm²"),
        ("Armature anneau", f"ø{fond['cerce_d']}/{fond['cerce_e']}mm"),
        ("Béton", proj["beton"]),
    ])

    return finaliser(cv, buf)


# ── Pl.5 — Façonnage armatures ───────────────────────────────
def planche_5_faconnage(proj=None, poteaux=None, poutre=None):
    proj = proj or PROJET_SAKHO
    poteaux = poteaux or POTEAUX_SAKHO
    poutre = poutre or POUTRE_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 5, "FAÇONNAGE ARMATURES", "Nomenclature barres — Schémas façonnage", proj, "NTS")
    bandeau_titre(cv, "Pl.5 — FAÇONNAGE ET NOMENCLATURE",
                  "Repères par barre — Longueurs développées")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # Tableau nomenclature complet
    col_w = ZW / 2 - 3*mm

    # Colonne gauche : poteaux
    lignes_pot = [("Repère", "Section / Armatures")]
    lignes_pot.append(("---",))
    for p in poteaux:
        # Longueur développée approximative
        L_dev = (p["b"] - 2*30) * 4 + 2 * 300  # mm (boucle + crochets)
        lignes_pot.append((
            f"{p['label']} — {p['nb']}HA{p['diam']}",
            f"Ld={L_dev//10}cm / cadre ø{p['cd']}"
        ))
    tableau_donnees(cv, ZX, ZY + ZH*0.5, col_w, ZH*0.48,
                    "NOMENCLATURE POTEAUX", lignes_pot)

    # Colonne droite : poutres + fondations
    lignes_pou = [
        ("Poutre b×h", f"{poutre['b']//10}×{poutre['h']//10} cm"),
        ("As inf. HA16", f"{poutre['As_inf']} cm² — Ld ≈ {poutre['portee']//10}cm"),
        ("As sup. HA16", f"{poutre['As_sup']} cm² — chapeau L/4"),
        ("Étriers HA8", f"ø{poutre['etrier_d']}/{poutre['etrier_e']}mm courant"),
        ("---",),
        ("Pieux HA20", f"{FOND_SAKHO['As_cm2']} cm²"),
        ("Cerces HA12", f"ø{FOND_SAKHO['cerce_d']}/{FOND_SAKHO['cerce_e']}mm"),
    ]
    tableau_donnees(cv, ZX + col_w + 3*mm, ZY + ZH*0.5,
                    col_w, ZH*0.48, "NOMENCLATURE POUTRES + PIEUX", lignes_pou)

    # Schémas façonnage (bas de planche)
    _schema_faconnage_poteau(cv, ZX + 10*mm, ZY + 2*mm, ZH*0.45)
    _schema_faconnage_poutre(cv, ZX + ZW*0.4, ZY + 2*mm, ZW*0.55, ZH*0.45, poutre)

    cv.restoreState()
    return finaliser(cv, buf)


def _schema_faconnage_poteau(cv, x, y, h):
    """Schéma façonnage barre longitudinale poteau"""
    w = ZW * 0.32
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(x, y, w, h, fill=1, stroke=1)

    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6)
    cv.drawCentredString(x + w/2, y + h - 5*mm, "FAÇONNAGE BARRE POTEAU")

    # Barre droite avec crochets
    yb = y + h/2
    marge = 8*mm
    cv.setStrokeColor(NOIR); cv.setLineWidth(LW_GROS)
    cv.line(x + marge + 5*mm, yb, x + w - marge - 5*mm, yb)
    # Crochets
    for xc, sens in [(x + marge, 1), (x + w - marge, -1)]:
        cv.line(xc, yb, xc + sens*5*mm, yb)
        cv.arc(xc + sens*5*mm - 2*mm, yb - 2*mm,
               xc + sens*5*mm + 2*mm, yb + 2*mm, 0, 90*sens)

    # Cotes
    set_trait(cv, LW_FIN, GRIS_FORT)
    L_tot = w - 2*marge
    cv.line(x+marge, y+h*0.3, x+w-marge, y+h*0.3)
    cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 5.5)
    cv.drawCentredString(x+w/2, y+h*0.3 - 5*mm, "Ld = L étage + 2 × ancrage")


def _schema_faconnage_poutre(cv, x, y, w, h, poutre):
    """Schéma façonnage armatures poutre"""
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(x, y, w, h, fill=1, stroke=1)

    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6)
    cv.drawCentredString(x+w/2, y+h-5*mm, "SCHÉMA ARMATURES POUTRE")

    # Épure schématique
    margin = 10*mm
    yb_inf = y + h*0.3
    yb_sup = y + h*0.7
    x0, x1 = x+margin, x+w-margin

    # Béton outline
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_MOYEN, GRIS_FORT)
    cv.rect(x0, yb_inf - 4*mm, x1-x0, yb_sup - yb_inf + 8*mm, fill=1, stroke=1)

    # Barre inférieure
    set_trait(cv, LW_GROS, NOIR)
    cv.line(x0+3*mm, yb_inf, x1-3*mm, yb_inf)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(x0, yb_inf-4.5*mm, f"As inf = {poutre['As_inf']} cm²")

    # Barre supérieure (avec chapeaux)
    cv.line(x0+3*mm, yb_sup, x0 + (x1-x0)*0.35, yb_sup)
    cv.line(x1-(x1-x0)*0.35, yb_sup, x1-3*mm, yb_sup)
    cv.setFont(FONT_SOUS, 5)
    cv.drawString(x0, yb_sup+2*mm, f"As sup = {poutre['As_sup']} cm² (chapeaux L/4)")


# ── Pl.6 — Plan fondations ───────────────────────────────────
def planche_6_plan_fondations(proj=None, portees_x=None, portees_y=None, fond=None):
    proj = proj or PROJET_SAKHO
    px = portees_x or GRILLE_SAKHO["px"]
    py = portees_y or GRILLE_SAKHO["py"]
    fond = fond or FOND_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 6, "PLAN FONDATIONS", "Vue en plan — Pieux forés", proj)
    bandeau_titre(cv, "Pl.6 — PLAN DE FONDATIONS",
                  f"{fond['nb']} pieux ø{fond['diam']}mm / poteau — L={fond['L']}m")

    scale, ox, oy, axes_x, axes_y = calcul_grille(px, py)

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # Fond sol (teinte terre)
    cv.setFillColor(colors.HexColor("#EDE9E0"))
    cv.setStrokeColor(GRIS_CLAIR); cv.setLineWidth(LW_FIN)
    cv.rect(axes_x[0]-8*mm, axes_y[0]-8*mm,
            axes_x[-1]-axes_x[0]+16*mm,
            axes_y[-1]-axes_y[0]+16*mm, fill=1, stroke=1)

    # Fond dalle radier
    cv.setFillColor(GRIS_FOND)
    cv.rect(axes_x[0], axes_y[0],
            axes_x[-1]-axes_x[0], axes_y[-1]-axes_y[0], fill=1, stroke=0)

    # Pieux par groupe
    r_pieu = max(3.5*mm, scale * fond["diam"] / 2)
    groupe_off = r_pieu * 1.5
    offsets = [(-groupe_off, -groupe_off), (groupe_off, -groupe_off),
               (groupe_off,  groupe_off), (-groupe_off,  groupe_off)]

    for i in range(len(axes_x)):
        for j in range(len(axes_y)):
            cx, cy = axes_x[i], axes_y[j]
            # Longrines (lignes de liaison)
            if i < len(axes_x)-1:
                set_trait(cv, LW_MOYEN, GRIS_FORT)
                cv.line(cx+groupe_off, cy, axes_x[i+1]-groupe_off, cy)
            if j < len(axes_y)-1:
                cv.line(cx, cy+groupe_off, cx, axes_y[j+1]-groupe_off)

            # Pieux
            for dx, dy in offsets:
                cv.setFillColor(GRIS_CLAIR)
                set_trait(cv, LW_MOYEN, NOIR)
                cv.circle(cx+dx, cy+dy, r_pieu, fill=1, stroke=1)
                hachures(cv, cx+dx-r_pieu, cy+dy-r_pieu, r_pieu*2, r_pieu*2)
                # Redessiner cercle par-dessus
                cv.setFillColor(colors.transparent if hasattr(colors, 'transparent') else BLANC)
                set_trait(cv, LW_MOYEN, NOIR)
                cv.circle(cx+dx, cy+dy, r_pieu, fill=0, stroke=1)

            # Poteau
            b_s = max(4*mm, scale * POTEAUX_SAKHO[0]["b"])
            poteau_coffrage(cv, cx, cy, b_s)

    cv.restoreState()

    tracer_axes(cv, axes_x, axes_y)
    cotations_grille(cv, axes_x, axes_y, px, py, scale)

    # Coupe pieu (encart)
    tx = ZX + ZW - 50*mm; ty = ZY + ZH*0.4
    tw = 48*mm; th = ZH*0.55
    _coupe_pieu(cv, tx, ty, tw, th, fond)

    return finaliser(cv, buf)


def _coupe_pieu(cv, x, y, w, h, fond):
    """Coupe verticale schématique d'un pieu"""
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(x, y, w, h, fill=1, stroke=1)

    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6)
    cv.drawCentredString(x+w/2, y+h-5*mm, "COUPE PIEU FORÉ")

    marge = 6*mm
    r_p = min(w/4, 8*mm)
    xp = x + w/2
    y_top = y + h - 12*mm
    y_bot = y + marge + 5*mm
    h_pieu = y_top - y_bot

    # Sol (fond)
    cv.setFillColor(colors.HexColor("#EDE9E0"))
    cv.rect(x+marge, y_bot, w-2*marge, h_pieu, fill=1, stroke=0)

    # Pieu (béton)
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_MOYEN, NOIR)
    cv.rect(xp-r_p, y_bot, r_p*2, h_pieu, fill=1, stroke=1)
    hachures(cv, xp-r_p, y_bot, r_p*2, h_pieu)

    # Armatures
    r_b = 1.2*mm
    for xb in [xp-r_p+3*mm, xp+r_p-3*mm]:
        cv.setFillColor(NOIR)
        cv.line(xb, y_bot+2*mm, xb, y_top-2*mm)

    # Cerces schématiques
    set_trait(cv, LW_TRES_FIN*1.5, GRIS_FORT)
    for yc in [y_bot + h_pieu*k/6 for k in range(1,6)]:
        cv.line(xp-r_p+2*mm, yc, xp+r_p-2*mm, yc)

    # Cotes
    cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 5.5)
    cv.drawString(xp+r_p+2*mm, y_bot + h_pieu/2 - 2,
                  f"L={fond['L']}m")
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawCentredString(xp, y_bot-4*mm, f"ø{fond['diam']}mm")


# ── Pl.7 — Escaliers ─────────────────────────────────────────
def planche_7_escaliers(proj=None):
    proj = proj or PROJET_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 7, "ESCALIERS", "Plan + coupe + ferraillage", proj, "1/50")
    bandeau_titre(cv, "Pl.7 — ESCALIERS",
                  "Dalle inclinée armée — Giron 28cm — Contre-marche 17cm")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # Zone gauche : plan escalier
    zg_w = ZW * 0.45
    _plan_escalier(cv, ZX + 5*mm, ZY + 5*mm, zg_w - 5*mm, ZH - 5*mm)

    # Zone droite : coupe + ferraillage
    _coupe_escalier(cv, ZX + zg_w + 5*mm, ZY + 5*mm, ZW - zg_w - 10*mm, ZH - 5*mm)

    cv.restoreState()
    return finaliser(cv, buf)


def _plan_escalier(cv, x, y, w, h):
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(x, y, w, h, fill=1, stroke=1)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6.5)
    cv.drawCentredString(x+w/2, y+h-5*mm, "PLAN ESCALIER — 1/50")

    # Paillasse (rectangle incliné représenté en plan)
    marge = 8*mm
    pw = w - 2*marge; ph = h * 0.7
    px0 = x + marge; py0 = y + marge

    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_MOYEN, NOIR)
    cv.rect(px0, py0, pw, ph, fill=1, stroke=1)

    # Marches (lignes horizontales)
    n_marches = 12
    for i in range(1, n_marches):
        y_m = py0 + ph * i / n_marches
        set_trait(cv, LW_FIN, GRIS_FORT)
        cv.line(px0, y_m, px0+pw, y_m)

    # Flèche de montée
    set_trait(cv, LW_MOYEN, TIJAN_VERT)
    cv.line(px0+pw/2, py0+ph*0.1, px0+pw/2, py0+ph*0.9)
    cv.setFillColor(TIJAN_VERT)
    p = cv.beginPath()
    p.moveTo(px0+pw/2, py0+ph*0.9)
    p.lineTo(px0+pw/2-2*mm, py0+ph*0.8)
    p.lineTo(px0+pw/2+2*mm, py0+ph*0.8)
    p.close(); cv.drawPath(p, fill=1, stroke=0)

    cv.setFillColor(TIJAN_VERT); cv.setFont(FONT_TITRE, 5.5)
    cv.drawCentredString(px0+pw/2+5*mm, py0+ph*0.5, "MONTÉE")

    # Cotations
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(px0, py0-5*mm, f"Larg. = {pw/mm*10:.0f}mm (approx)")
    cv.drawString(px0, py0-9*mm, f"12 marches × G=28cm / H=17cm")


def _coupe_escalier(cv, x, y, w, h, giron=280, contre_marche=170, n=12):
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(x, y, w, h, fill=1, stroke=1)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6.5)
    cv.drawCentredString(x+w/2, y+h-5*mm, "COUPE LONGITUDINALE — FERRAILLAGE")

    marge = 10*mm
    ep_dall = max(3*mm, h*0.06)
    w_draw = w - 2*marge
    h_draw = h * 0.75

    # Angle paillasse
    angle = math.atan2(contre_marche * n, giron * n)
    L_horiz = w_draw

    # Dessiner les marches
    x0 = x + marge; y0 = y + marge + 5*mm
    step_w = L_horiz / n
    step_h = step_w * math.tan(angle)

    cv.setFillColor(GRIS_FOND)
    p_marche = cv.beginPath()
    p_marche.moveTo(x0, y0)
    cx_m, cy_m = x0, y0
    for i in range(n):
        p_marche.lineTo(cx_m + step_w, cy_m)
        p_marche.lineTo(cx_m + step_w, cy_m + step_h)
        cx_m += step_w; cy_m += step_h
    # Fermer par le bas
    p_marche.lineTo(x0, cy_m)
    p_marche.close()
    set_trait(cv, LW_MOYEN, NOIR)
    cv.drawPath(p_marche, fill=1, stroke=1)

    # Dalle inclinée (dessous)
    p_dalle = cv.beginPath()
    p_dalle.moveTo(x0, y0)
    p_dalle.lineTo(x0 + L_horiz, y0 + step_h*n)
    p_dalle.lineTo(x0 + L_horiz, y0 + step_h*n - ep_dall/math.cos(angle))
    p_dalle.lineTo(x0, y0 - ep_dall/math.cos(angle))
    p_dalle.close()
    cv.setFillColor(GRIS_ALT)
    set_trait(cv, LW_FIN, GRIS_FORT)
    cv.drawPath(p_dalle, fill=1, stroke=1)

    # Armatures (ligne dans la dalle)
    y_arm = y0 - ep_dall*0.35
    set_trait(cv, LW_MOYEN, NOIR)
    cv.line(x0 + 2*mm, y_arm,
            x0 + L_horiz - 2*mm,
            y_arm + (step_h*n) * (L_horiz-4*mm)/L_horiz)

    # Cotes
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(x0, y0 - ep_dall - 5*mm,
                  f"ep. dalle = {ep_dall/mm*5:.0f}cm (typ.)")
    cv.drawString(x0, y0 - ep_dall - 9.5*mm,
                  f"G={giron}mm / CH={contre_marche}mm — {n} marches")


# ── Pl.8 — Façades + acrotères ───────────────────────────────
def planche_8_facades(proj=None, portees_x=None, poteaux=None):
    proj = proj or PROJET_SAKHO
    px = portees_x or GRILLE_SAKHO["px"]
    poteaux = poteaux or POTEAUX_SAKHO

    cv, buf = nouvelle_page(proj)
    _cartouche_ba(cv, 8, "FAÇADES — ACROTÈRES", "Élévation structurelle — sections variables", proj, "1/200")
    bandeau_titre(cv, "Pl.8 — FAÇADES ET ACROTÈRES",
                  f"R+{len(poteaux)-1} — H tot = {len(poteaux)*3:.0f}m")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # Façade principale (vue de côté — élévation)
    n_niv = len(poteaux)
    h_etage = ZH * 0.78 / n_niv
    w_facade = ZW * 0.85
    x0_fac = ZX + (ZW - w_facade) / 2
    y0_fac = ZY + 5*mm
    Lx_facade = sum(px)

    # Nbre de travées
    n_travees = len(px)
    w_travee = [p / Lx_facade * w_facade for p in px]

    # Sous-sol / fondation (hachures sol)
    cv.setFillColor(colors.HexColor("#E8E0D0"))
    cv.rect(x0_fac - 5*mm, y0_fac - 8*mm, w_facade + 10*mm, 8*mm, fill=1, stroke=0)

    # Étages
    for niv_idx in range(n_niv):
        y_niv = y0_fac + niv_idx * h_etage
        p_niv = poteaux[niv_idx]
        b_s = max(2.5*mm, p_niv["b"] / Lx_facade * w_facade * 3)

        # Dalle
        cv.setFillColor(GRIS_ALT)
        set_trait(cv, LW_FIN, GRIS_CLAIR)
        cv.rect(x0_fac, y_niv + h_etage - 2*mm, w_facade, 2*mm, fill=1, stroke=1)

        # Poteaux (section variable)
        x_cur = x0_fac
        for ti in range(n_travees):
            # Poteau gauche
            cv.setFillColor(GRIS_FOND)
            set_trait(cv, LW_MOYEN, NOIR)
            cv.rect(x_cur - b_s/2, y_niv, b_s, h_etage, fill=1, stroke=1)
            hachures(cv, x_cur-b_s/2, y_niv, b_s, h_etage)
            x_cur += w_travee[ti]

        # Poteau droit (dernier)
        cv.setFillColor(GRIS_FOND)
        set_trait(cv, LW_MOYEN, NOIR)
        cv.rect(x_cur - b_s/2, y_niv, b_s, h_etage, fill=1, stroke=1)
        hachures(cv, x_cur-b_s/2, y_niv, b_s, h_etage)

        # Poutre
        b_pou = max(1.5*mm, POUTRE_SAKHO["b"] / Lx_facade * w_facade * 0.8)
        set_trait(cv, LW_MOYEN, GRIS_FORT)
        cv.line(x0_fac, y_niv + h_etage - 2*mm - b_pou,
                x0_fac + w_facade, y_niv + h_etage - 2*mm - b_pou)

        # Label niveau
        cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 5)
        cv.drawString(x0_fac + w_facade + 2*mm, y_niv + h_etage/2 - 2,
                      p_niv["label"])
        # Côte de niveau
        h_m = niv_idx * 3.0
        cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 4.5)
        cv.drawString(x0_fac - 18*mm, y_niv + h_etage/2 - 2,
                      f"+{h_m:.2f}m")

    # Acrotère (toiture)
    y_top = y0_fac + n_niv * h_etage
    ep_acr = max(1.5*mm, 0.15 / Lx_facade * w_facade * 3)
    h_acr = h_etage * 0.4
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_MOYEN, NOIR)
    for xp in [x0_fac, x0_fac + w_facade]:
        cv.rect(xp - ep_acr/2, y_top, ep_acr, h_acr, fill=1, stroke=1)
    # Acrotère continu
    cv.rect(x0_fac, y_top + h_acr - 1.5*mm, w_facade, 1.5*mm, fill=1, stroke=1)

    cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 5)
    cv.drawString(x0_fac + w_facade + 2*mm, y_top + h_acr/2 - 2, "Acrotère")

    # Cotation hauteur totale
    y_total_bot = y0_fac; y_total_top = y0_fac + n_niv * h_etage
    set_trait(cv, LW_FIN, GRIS_FORT)
    cv.line(x0_fac - 12*mm, y_total_bot, x0_fac - 12*mm, y_total_top)
    cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_TITRE, 6)
    cv.drawString(x0_fac - 28*mm, (y_total_bot+y_total_top)/2 - 3,
                  f"H={n_niv*3:.0f}m")

    cv.restoreState()
    return finaliser(cv, buf)


# ════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════

def generer_dossier_ba(output_path: str, proj=None,
                       portees_x=None, portees_y=None,
                       poteaux=None, poutre=None, fond=None):
    print("Génération dossier BA v4 — charte sobre Tijan")
    writer = PdfWriter()

    planches = [
        ("Pl.1 — Plan de coffrage",
         lambda: planche_1_coffrage(proj, portees_x, portees_y, poteaux, poutre)),
        ("Pl.2 — Ferraillage poteaux",
         lambda: planche_2_poteaux(proj, poteaux)),
        ("Pl.3 — Ferraillage poutres",
         lambda: planche_3_poutres(proj, poutre, poteaux)),
        ("Pl.4 — Dalle et fondations",
         lambda: planche_4_dalle_fond(proj, portees_x, portees_y, fond)),
        ("Pl.5 — Façonnage armatures",
         lambda: planche_5_faconnage(proj, poteaux, poutre)),
        ("Pl.6 — Plan de fondations",
         lambda: planche_6_plan_fondations(proj, portees_x, portees_y, fond)),
        ("Pl.7 — Escaliers",
         lambda: planche_7_escaliers(proj)),
        ("Pl.8 — Façades et acrotères",
         lambda: planche_8_facades(proj, portees_x, poteaux)),
    ]

    for titre, fn in planches:
        writer.add_page(fn())
        print(f"  ✓ {titre}")

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"\n✓ Dossier BA v4 — 8 planches : {output_path}")


if __name__ == "__main__":
    generer_dossier_ba("/mnt/user-data/outputs/tijan_dossier_ba_v4_sakho.pdf")

"""
Tijan AI — Planches MEP v4
Nombre et contenu définis selon pertinence APD marché Dakar :

Pl.1 — Schéma unifilaire électrique (TGBT + tableaux divisionnaires)
Pl.2 — Plan type étage — Électricité (éclairage + prises + détection)
Pl.3 — Plan type étage — Plomberie (EF/EC + évacuations)
Pl.4 — Plan type étage — HVAC (climatisation + VMC)
Pl.5 — Schéma vertical plomberie (colonne montante + chutes)
Pl.6 — Bilan MEP + EDGE (récapitulatif puissances + débits + certif.)
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

# ── Données Sakho ────────────────────────────────────────────
PROJET_MEP = {
    "nom":   "Résidence Papa Oumar Sakho",
    "ref":   "1711-MEP",
    "ville": "Dakar, Sénégal",
    "usage": "Résidentiel R+8 — 32 unités",
    "norme": "NF C 15-100 / DTU 60.11",
}

GRILLE = {
    "px": [6180, 6180, 5180, 6180, 5180, 6180, 5180, 6180],
    "py": [5180, 4130, 5180, 4130, 5180],
}

NB_NIVEAUX = 9
H_ETAGE = 3.00

ELEC = {
    "P_totale_kVA": 386,
    "tension": "400V TN-S",
    "tgbt": "4P 630A",
    "tableaux": [
        {"id": "TGBT",  "P_kVA": 386, "I_A": 558, "disj": "4P 630A"},
        {"id": "TD-A",  "P_kVA":  80, "I_A": 116, "disj": "3P 125A"},
        {"id": "TD-B",  "P_kVA":  80, "I_A": 116, "disj": "3P 125A"},
        {"id": "TD-C",  "P_kVA":  80, "I_A": 116, "disj": "3P 125A"},
        {"id": "TD-D",  "P_kVA":  60, "I_A":  87, "disj": "3P 100A"},
        {"id": "HVAC",  "P_kVA": 145, "I_A": 210, "disj": "3P 250A"},
        {"id": "GE",    "P_kVA": 200, "I_A": 289, "disj": "4P 400A"},
    ],
}

PLOMBERIE = {
    "conso_m3_j": 30,
    "pression_bar": 3.5,
    "reservoir_m3": 20,
    "pompe_kW": 5.5,
    "d_col_ef": 63,
    "d_col_ec": 50,
    "d_chute_eu": 100,
    "d_chute_ep": 100,
    "nb_apts": 32,
}

HVAC = {
    "P_kW": 145,
    "systeme": "VRV 4 fils",
    "UE": "RXYQ18T",
    "COP": 3.8,
    "EER": 3.5,
    "nb_UI": 32,
    "VMC_debit_m3h": 90,
    "solaire_kWc": 12,
}

# Positions colonnes plomberie (indices dans la grille)
COL_EF = [(1,1), (1,4), (7,1), (7,4)]
CHUTES_EU = [(2,2), (6,2), (2,3), (6,3)]


# ════════════════════════════════════════════════════════════
# MOTEUR GRILLE
# ════════════════════════════════════════════════════════════

ZX = DX + 2*mm
ZY = DY + 2*mm
ZW = DW - 4*mm
ZH = DH - TITRE_H - 4*mm


def calcul_grille(marge=8*mm):
    px, py = GRILLE["px"], GRILLE["py"]
    Lx, Ly = sum(px), sum(py)
    sx = (ZW - 2*marge) / Lx
    sy = (ZH - 2*marge) / Ly
    scale = min(sx, sy)
    ox = ZX + marge + (ZW - 2*marge - Lx*scale)/2
    oy = ZY + marge + (ZH - 2*marge - Ly*scale)/2
    axes_x = [ox] + [ox + sum(px[:i+1])*scale for i in range(len(px))]
    axes_y = [oy] + [oy + sum(py[:j+1])*scale for j in range(len(py))]
    return scale, ox, oy, axes_x, axes_y


def fond_etage(cv, axes_x, axes_y, scale):
    """Fond plan d'étage : dalle + poteaux + axes"""
    # Dalle
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    cv.rect(axes_x[0], axes_y[0],
            axes_x[-1]-axes_x[0], axes_y[-1]-axes_y[0],
            fill=1, stroke=1)

    # Cloisons simplifiées (traits fins)
    ep = max(1.2*mm, scale*150)
    cv.setFillColor(GRIS_ALT)
    for j in range(1, len(axes_y)-1):
        y = axes_y[j]
        for i in range(len(axes_x)-1):
            x0, x1 = axes_x[i], axes_x[i+1]
            # Cloison partielle (60% de la travée)
            cv.rect(x0, y-ep/2, (x1-x0)*0.6, ep, fill=1, stroke=0)

    # Poteaux
    b_s = max(3*mm, scale*500)
    for i in range(len(axes_x)):
        for j in range(len(axes_y)):
            cx, cy = axes_x[i], axes_y[j]
            cv.setFillColor(BLANC)
            set_trait(cv, LW_MOYEN, NOIR)
            cv.rect(cx-b_s/2, cy-b_s/2, b_s, b_s, fill=1, stroke=1)
            hachures(cv, cx-b_s/2, cy-b_s/2, b_s, b_s)

    # Axes
    set_trait(cv, LW_FIN, GRIS_CLAIR, ([4,2],0))
    for x in axes_x:
        cv.line(x, axes_y[0]-4*mm, x, axes_y[-1]+4*mm)
    for y in axes_y:
        cv.line(axes_x[0]-4*mm, y, axes_x[-1]+4*mm, y)
    cv.setDash()

    # Bulles axes
    r = 3*mm; lettres = "ABCDEF"
    for i, x in enumerate(axes_x):
        bulle_axe(cv, x, axes_y[-1]+r+1.5*mm, r, str(i+1))
    for j, y in enumerate(axes_y):
        bulle_axe(cv, axes_x[0]-r-1.5*mm, y, r, lettres[j])


# ════════════════════════════════════════════════════════════
# HELPERS SYMBOLES MEP
# ════════════════════════════════════════════════════════════

def spot_eclairage(cv, cx, cy, r):
    """Downlight — cercle avec 4 traits"""
    cv.setFillColor(BLANC)
    set_trait(cv, 0.6, NOIR)
    cv.circle(cx, cy, r, fill=1, stroke=1)
    set_trait(cv, 0.4, GRIS_MOY)
    for a in [0, 90, 180, 270]:
        aa = math.radians(a)
        cv.line(cx+r*math.cos(aa), cy+r*math.sin(aa),
                cx+r*1.5*math.cos(aa), cy+r*1.5*math.sin(aa))


def prise_elec(cv, cx, cy, r):
    """Prise — demi-cercle"""
    cv.setFillColor(BLANC)
    set_trait(cv, 0.6, NOIR)
    p = cv.beginPath()
    p.arc(cx-r, cy-r, cx+r, cy+r, 0, 180)
    p.lineTo(cx-r, cy); p.close()
    cv.drawPath(p, fill=1, stroke=1)


def detecteur_fumee(cv, cx, cy, r):
    """Détecteur — cercle avec D"""
    cv.setFillColor(GRIS_ALT)
    set_trait(cv, 0.5, NOIR)
    cv.circle(cx, cy, r, fill=1, stroke=1)
    cv.setFillColor(NOIR); cv.setFont(FONT_TITRE, max(4, r*0.9/mm))
    cv.drawCentredString(cx, cy-r*0.35, "D")


def symbole_colonne(cv, cx, cy, r, label):
    """Colonne montante — cercle plein + label"""
    cv.setFillColor(GRIS_FORT)
    set_trait(cv, 0.5, NOIR)
    cv.circle(cx, cy, r, fill=1, stroke=1)
    cv.setFillColor(BLANC); cv.setFont(FONT_TITRE, max(4, r*0.8/mm))
    cv.drawCentredString(cx, cy-r*0.35, label[:2])


def symbole_chute(cv, cx, cy, r, label):
    """Chute EU/EP — cercle vide + label"""
    cv.setFillColor(BLANC)
    set_trait(cv, 0.8, GRIS_FORT)
    cv.circle(cx, cy, r, fill=1, stroke=1)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, max(4, r*0.7/mm))
    cv.drawCentredString(cx, cy-r*0.35, label[:2])


def cassette_vrv(cv, cx, cy, s):
    """Unité intérieure VRV — carré avec 4 flèches"""
    cv.setFillColor(BLANC)
    set_trait(cv, 0.6, GRIS_FORT)
    cv.roundRect(cx-s/2, cy-s/2, s, s, 1*mm, fill=1, stroke=1)
    # 4 soufflages
    set_trait(cv, 0.4, GRIS_MOY)
    for a in [0, 90, 180, 270]:
        aa = math.radians(a)
        cv.line(cx, cy, cx+s*0.38*math.cos(aa), cy+s*0.38*math.sin(aa))


def bouche_vmc(cv, cx, cy, r):
    """Bouche VMC — carré barré"""
    cv.setFillColor(GRIS_ALT)
    set_trait(cv, 0.5, GRIS_FORT)
    cv.rect(cx-r, cy-r, 2*r, 2*r, fill=1, stroke=1)
    cv.line(cx-r, cy-r, cx+r, cy+r)


def tuyau(cv, x1, y1, x2, y2, color, lw=1.0, dash=None):
    set_trait(cv, lw, color, dash)
    cv.line(x1, y1, x2, y2)
    cv.setDash()


def tableau_elec_symbole(cv, cx, cy, w, h, label, color=NOIR):
    """Tableau électrique — rectangle + label"""
    cv.setFillColor(BLANC)
    set_trait(cv, LW_MOYEN, color)
    cv.rect(cx-w/2, cy-h/2, w, h, fill=1, stroke=1)
    cv.setFillColor(color); cv.setFont(FONT_TITRE, 5.5)
    cv.drawCentredString(cx, cy-2, label)


# ════════════════════════════════════════════════════════════
# PAGES
# ════════════════════════════════════════════════════════════

def nouvelle_page():
    buf = io.BytesIO()
    cv = canvas.Canvas(buf, pagesize=A3L)
    bordure_page(cv)
    return cv, buf


def finaliser(cv, buf):
    cv.save(); buf.seek(0)
    return PdfReader(buf).pages[0]


def _cart(cv, num, titre, sous_titre, lot, echelle="1/200"):
    cartouche(cv, num, 6, titre, sous_titre, lot,
              echelle, PROJET_MEP["nom"], PROJET_MEP["ref"],
              PROJET_MEP["ville"], datetime.now().strftime("%d/%m/%Y"))


def _legende(cv, items, x=None, y=None):
    """Légende sobre en bas gauche"""
    x = x or ZX + 2*mm
    y = y or ZY + 2*mm
    cv.setFillColor(BLANC)
    set_trait(cv, LW_FIN, GRIS_CLAIR)
    item_h = 5.5*mm
    w_leg = 70*mm
    h_leg = len(items) * item_h + 8*mm
    cv.rect(x, y, w_leg, h_leg, fill=1, stroke=1)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_TITRE, 6)
    cv.drawString(x+3*mm, y+h_leg-5.5*mm, "LÉGENDE")
    for i, (color, lw, dash, label) in enumerate(items):
        yi = y + h_leg - 8*mm - i*item_h
        legende_item(cv, x+3*mm, yi, color, lw, dash, label)


# ── Pl.1 — Schéma unifilaire ─────────────────────────────────
def planche_1_unifilaire():
    cv, buf = nouvelle_page()
    _cart(cv, 1, "SCHÉMA UNIFILAIRE", f"{ELEC['P_totale_kVA']} kVA — {ELEC['tension']}", "ÉLEC", "NTS")
    bandeau_titre(cv, "Pl.1 — SCHÉMA UNIFILAIRE ÉLECTRIQUE",
                  f"TGBT {ELEC['tgbt']} — {len(ELEC['tableaux'])} tableaux")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    tds = ELEC["tableaux"]
    n = len(tds)

    # Zone schéma
    sx = ZX + 5*mm; sy = ZY + 5*mm
    sw = ZW - 10*mm; sh = ZH - 5*mm

    # ── Barre SENELEC / GE en haut
    y_src = sy + sh - 20*mm
    # SENELEC
    _bloc_source_sobre(cv, sx+5*mm, y_src, "SENELEC", "BT 400V")
    # GE
    _bloc_source_sobre(cv, sx+50*mm, y_src, "GE 200kVA", "Secours")
    # Inverseur
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawCentredString(sx+32*mm, y_src+5*mm, "ATS")
    set_trait(cv, 0.5, GRIS_MOY)
    cv.circle(sx+32*mm, y_src+8*mm, 2*mm, fill=1, stroke=0)

    # Jeu de barres
    y_jdb = y_src - 10*mm
    set_trait(cv, 2.0, NOIR)
    cv.line(sx+5*mm, y_jdb, sx+sw*0.82, y_jdb)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(sx+sw*0.83, y_jdb-1.5, "JdB 400V")

    # Liaisons sources → JdB
    set_trait(cv, 1.2, NOIR)
    cv.line(sx+15*mm, y_src, sx+15*mm, y_jdb)
    cv.line(sx+60*mm, y_src, sx+60*mm, y_jdb)

    # TGBT
    y_tgbt = y_jdb - 14*mm
    _disjoncteur_sobre(cv, sx+sw*0.35, y_jdb, y_tgbt+6*mm, ELEC["tgbt"])
    tableau_elec_symbole(cv, sx+sw*0.35, y_tgbt, 20*mm, 8*mm, "TGBT")

    # Tableaux divisionnaires
    espacement = sw / (n+1)
    y_td = y_tgbt - 22*mm

    for idx, td in enumerate(tds):
        xtd = sx + (idx+1)*espacement
        # Colonne
        set_trait(cv, 0.8, NOIR)
        cv.line(xtd, y_tgbt-1*mm, xtd, y_td+12*mm)
        # Disjoncteur
        _disjoncteur_sobre(cv, xtd, y_td+12*mm, y_td+6*mm, td["disj"])
        # Bloc
        tableau_elec_symbole(cv, xtd, y_td, 18*mm, 7*mm, td["id"])
        # Puissance
        cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 4.5)
        cv.drawCentredString(xtd, y_td-4*mm, f"{td['P_kVA']}kVA")
        cv.drawCentredString(xtd, y_td-7.5*mm, f"In={td['I_A']}A")

    # Note EDGE (sobre)
    _note_sobre(cv, sx+sw-60*mm, sy+2*mm, 58*mm, 10*mm,
                "EDGE : comptage par tableau — monitoring consommation/niveau")

    cv.restoreState()
    return finaliser(cv, buf)


def _bloc_source_sobre(cv, x, y, titre, detail):
    w, h = 22*mm, 14*mm
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_FIN, NOIR)
    cv.rect(x, y-h, w, h, fill=1, stroke=1)
    cv.setFillColor(NOIR); cv.setFont(FONT_TITRE, 5.5)
    cv.drawCentredString(x+w/2, y-4*mm, titre)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
    cv.drawCentredString(x+w/2, y-9*mm, detail)


def _disjoncteur_sobre(cv, x, y_haut, y_bas, label):
    set_trait(cv, 0.8, NOIR)
    cv.line(x, y_haut, x, y_bas+3*mm)
    r = 2*mm; ym = (y_haut+y_bas)/2
    cv.setFillColor(BLANC)
    cv.rect(x-r, ym-r, 2*r, 2*r, fill=1, stroke=1)
    cv.line(x-r*0.7, ym-r*0.7, x+r*0.7, ym+r*0.7)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
    cv.drawCentredString(x, ym-r-3, label)


def _note_sobre(cv, x, y, w, h, texte):
    cv.setFillColor(GRIS_FOND)
    set_trait(cv, LW_TRES_FIN, GRIS_MOY)
    cv.rect(x, y, w, h, fill=1, stroke=1)
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
    # Découper texte pour ne pas dépasser
    max_c = int(w / (4.5*0.55))
    t = texte[:max_c] if len(texte) > max_c else texte
    cv.drawString(x+2*mm, y+3.5*mm, t)


# ── Pl.2 — Plan type étage — Électricité ─────────────────────
def planche_2_elec_etage():
    cv, buf = nouvelle_page()
    _cart(cv, 2, "PLAN ÉTAGE TYPE — ÉLEC", "Éclairage / Prises / Détection", "ÉLEC")
    bandeau_titre(cv, "Pl.2 — PLAN ÉTAGE TYPE — ÉLECTRICITÉ",
                  "Circuits C1→C7 — NF C 15-100")

    scale, ox, oy, axes_x, axes_y = calcul_grille()

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    fond_etage(cv, axes_x, axes_y, scale)

    r_spot = max(2*mm, scale*280)
    r_prise = max(1.5*mm, scale*200)
    r_det = max(1.8*mm, scale*250)

    for i in range(len(axes_x)-1):
        for j in range(len(axes_y)-1):
            mx = (axes_x[i]+axes_x[i+1])/2
            my = (axes_y[j]+axes_y[j+1])/2
            surf = (GRILLE["px"][i]/1000) * (GRILLE["py"][j]/1000)
            n_spots = max(1, round(surf/7))

            if n_spots == 1:
                spot_eclairage(cv, mx, my, r_spot)
            else:
                n_cols = min(3, n_spots)
                n_rows = math.ceil(n_spots/n_cols)
                dx_s = (axes_x[i+1]-axes_x[i])/(n_cols+1)
                dy_s = (axes_y[j+1]-axes_y[j])/(n_rows+1)
                for ci in range(n_cols):
                    for ri in range(n_rows):
                        spot_eclairage(cv,
                            axes_x[i]+(ci+1)*dx_s,
                            axes_y[j]+(ri+1)*dy_s, r_spot)

            # Prise sur mur
            prise_elec(cv, axes_x[i]+2.5*mm,
                       (axes_y[j]+axes_y[j+1])/2, r_prise)

    # Détecteurs incendie (un par deux travées)
    for i in range(1, len(axes_x)-1, 2):
        for j in range(1, len(axes_y)-1, 2):
            detecteur_fumee(cv,
                (axes_x[i]+axes_x[i+1])/2,
                (axes_y[j]+axes_y[j+1])/2, r_det)

    # Tableau DB
    tableau_elec_symbole(cv, axes_x[1]+3*mm, axes_y[1]+3*mm,
                         14*mm, 7*mm, "DB-B")

    cv.restoreState()

    _legende(cv, [
        (NOIR, 0.6, None, "Downlight / spot éclairage"),
        (NOIR, 0.6, None, "Prise 16A"),
        (GRIS_FORT, 0.5, None, "Détecteur fumée"),
    ])

    return finaliser(cv, buf)


# ── Pl.3 — Plan type étage — Plomberie ───────────────────────
def planche_3_plomberie_etage():
    cv, buf = nouvelle_page()
    _cart(cv, 3, "PLAN ÉTAGE TYPE — PLOMBERIE", "EF/EC/EU/EP — DTU 60.11", "PLOMBERIE")
    bandeau_titre(cv, "Pl.3 — PLAN ÉTAGE TYPE — PLOMBERIE",
                  f"EF DN{PLOMBERIE['d_col_ef']} / EC DN{PLOMBERIE['d_col_ec']} / EU DN{PLOMBERIE['d_chute_eu']}")

    scale, ox, oy, axes_x, axes_y = calcul_grille()

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    fond_etage(cv, axes_x, axes_y, scale)

    r_col = max(2.5*mm, scale*300)
    r_chute = max(2*mm, scale*250)

    # Distribution EF (tirets) et EC (traits-points)
    for i in range(len(axes_x)-1):
        for j in range(len(axes_y)-1):
            xg = axes_x[i]+3*mm
            xd = axes_x[i+1]-3*mm
            ym_ef = axes_y[j] + (axes_y[j+1]-axes_y[j])*0.3
            ym_ec = axes_y[j] + (axes_y[j+1]-axes_y[j])*0.55

            tuyau(cv, xg, ym_ef, xg+(xd-xg)*0.6, ym_ef,
                  MEP_EF, 0.9, ([5,2],0))
            tuyau(cv, xg, ym_ec, xg+(xd-xg)*0.5, ym_ec,
                  MEP_EC, 0.9, ([3,1,1,1],0))

            # Appareils sanitaires (WC + lavabo schématique)
            xs = xg+(xd-xg)*0.65
            ys = axes_y[j]+(axes_y[j+1]-axes_y[j])*0.5
            s_san = max(3*mm, scale*600)
            # WC
            cv.setFillColor(BLANC)
            set_trait(cv, 0.5, GRIS_FORT)
            cv.ellipse(xs-s_san*0.35, ys-s_san*0.5,
                       xs+s_san*0.35, ys, fill=1, stroke=1)
            # Lavabo
            cv.arc(xs+s_san*0.5, ys-s_san*0.25,
                   xs+s_san*1.0, ys+s_san*0.25, 0, 360)

    # Colonnes EF
    for ci, cj in COL_EF:
        if ci < len(axes_x) and cj < len(axes_y):
            symbole_colonne(cv, axes_x[ci], axes_y[cj], r_col, "EF")
            symbole_colonne(cv, axes_x[ci]+r_col*2.2, axes_y[cj], r_col, "EC")

    # Chutes EU
    for ci, cj in CHUTES_EU:
        if ci < len(axes_x) and cj < len(axes_y):
            symbole_chute(cv, axes_x[ci], axes_y[cj], r_chute, "EU")

    # Chutes EP (coins)
    for ci, cj in [(0,0),(8,0),(0,5),(8,5)]:
        if ci < len(axes_x) and cj < len(axes_y):
            symbole_chute(cv, axes_x[ci], axes_y[cj], r_chute, "EP")

    cv.restoreState()

    _legende(cv, [
        (MEP_EF, 0.9, ([5,2],0), f"Eau Froide DN{PLOMBERIE['d_col_ef']} — PPR"),
        (MEP_EC, 0.9, ([3,1,1,1],0), f"Eau Chaude DN{PLOMBERIE['d_col_ec']} — PPR"),
        (GRIS_FORT, 0.8, None, f"Chute EU DN{PLOMBERIE['d_chute_eu']} — PVC"),
        (GRIS_MOY, 0.8, None, f"Chute EP DN{PLOMBERIE['d_chute_ep']} — PVC"),
    ])

    return finaliser(cv, buf)


# ── Pl.4 — Plan type étage — HVAC ────────────────────────────
def planche_4_hvac_etage():
    cv, buf = nouvelle_page()
    _cart(cv, 4, "PLAN ÉTAGE TYPE — HVAC", f"VRV {HVAC['systeme']} — VMC DF", "HVAC")
    bandeau_titre(cv, "Pl.4 — PLAN ÉTAGE TYPE — CLIMATISATION + VMC",
                  f"{HVAC['UE']} — COP {HVAC['COP']} / EER {HVAC['EER']}")

    scale, ox, oy, axes_x, axes_y = calcul_grille()

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZH, ZH)
    clip_rect(cv, ZX, ZY, ZW, ZH)

    fond_etage(cv, axes_x, axes_y, scale)

    # Cassettes VRV
    for i in range(len(axes_x)-1):
        for j in range(len(axes_y)-1):
            mx = (axes_x[i]+axes_x[i+1])/2
            my = (axes_y[j]+axes_y[j+1])/2
            s_cas = max(5*mm, scale*900)
            cassette_vrv(cv, mx, my, s_cas)
            cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
            cv.drawCentredString(mx, my-s_cas/2-3.5,
                                 f"{HVAC['P_kW']//HVAC['nb_UI']}kW")

    # Réseau frigorifique (tuyaux gaz — tirets)
    y_reseau = axes_y[2]
    tuyau(cv, axes_x[1], y_reseau, axes_x[7], y_reseau,
          MEP_HVAC, 1.2, ([6,2],0))
    cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5)
    cv.drawString(axes_x[4]+1*mm, y_reseau+1.5*mm,
                  "Réseau frigo ø15.9/9.5mm")

    # VMC (gaine — pointillés)
    y_vmc = axes_y[1]
    tuyau(cv, axes_x[2], y_vmc, axes_x[6], y_vmc,
          MEP_HVAC, 0.8, ([2,2],0))
    for i in range(2, 7):
        bx = axes_x[i]+(axes_x[i+1]-axes_x[i])*0.4 if i < len(axes_x)-1 else axes_x[i]
        by = y_vmc
        bouche_vmc(cv, bx, by, max(2*mm, scale*300))

    cv.restoreState()

    _legende(cv, [
        (GRIS_FORT, 0.6, None, "Cassette VRV 4 voies"),
        (MEP_HVAC, 1.2, ([6,2],0), "Réseau frigorifique"),
        (MEP_HVAC, 0.8, ([2,2],0), "Gaine VMC"),
        (GRIS_FORT, 0.5, None, "Bouche VMC extraction"),
    ])

    return finaliser(cv, buf)


# ── Pl.5 — Schéma vertical plomberie ─────────────────────────
def planche_5_schema_vertical():
    cv, buf = nouvelle_page()
    _cart(cv, 5, "SCHÉMA VERTICAL PLOMBERIE", "Colonne montante + chutes", "PLOMBERIE", "NTS")
    bandeau_titre(cv, "Pl.5 — SCHÉMA VERTICAL PLOMBERIE",
                  f"R+{NB_NIVEAUX-1} — H={NB_NIVEAUX*H_ETAGE:.0f}m — {PLOMBERIE['conso_m3_j']}m³/j")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    # Paramètres schéma
    marge_g = 18*mm; marge_d = 5*mm
    sw = ZW - marge_g - marge_d
    h_niv = (ZH - 8*mm) / (NB_NIVEAUX + 1)
    x0 = ZX + marge_g
    y0 = ZY + 4*mm

    niveaux_labels = (["Sous-sol"] + ["RDC"] +
                      [f"N{i}" for i in range(1, NB_NIVEAUX-1)] + ["Toiture"])

    # Lignes de planchers
    for idx in range(NB_NIVEAUX+1):
        y_niv = y0 + idx * h_niv
        set_trait(cv, LW_TRES_FIN, GRIS_CLAIR)
        cv.line(x0, y_niv, x0+sw, y_niv)

        # Nom niveau
        cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 5.5)
        cv.drawRightString(x0-2*mm, y_niv+1*mm,
                           niveaux_labels[idx] if idx < len(niveaux_labels) else "")

        # Cote
        h_m = idx * H_ETAGE
        cv.setFillColor(TIJAN_VERT_F); cv.setFont(FONT_SOUS, 4.5)
        cv.drawString(x0+sw+2*mm, y_niv+1*mm, f"+{h_m:.2f}m")

    # Colonnes verticales
    cols = [
        ("EF", MEP_EF, f"DN{PLOMBERIE['d_col_ef']}", "PPR", 1.2, None),
        ("EC", MEP_EC, f"DN{PLOMBERIE['d_col_ec']}", "PPR", 1.2, ([4,1,1,1],0)),
        ("EU", MEP_EU, f"DN{PLOMBERIE['d_chute_eu']}", "PVC", 1.0, ([5,2],0)),
        ("EP", MEP_EP, f"DN{PLOMBERIE['d_chute_ep']}", "PVC", 1.0, ([3,3],0)),
    ]
    n_cols = len(cols)
    x_cols = [x0 + sw*(i+1)/(n_cols+1) for i in range(n_cols)]

    for xcol, (nom, color, diam, mat, lw, dash) in zip(x_cols, cols):
        # Tuyau vertical
        tuyau(cv, xcol, y0, xcol, y0+NB_NIVEAUX*h_niv, color, lw, dash)

        # En-tête
        cv.setFillColor(NOIR); cv.setFont(FONT_TITRE, 6)
        cv.drawCentredString(xcol, y0+NB_NIVEAUX*h_niv+3*mm, nom)
        cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 5)
        cv.drawCentredString(xcol, y0+NB_NIVEAUX*h_niv+0.5*mm, f"{diam} {mat}")

        # Piquages
        for idx in range(1, NB_NIVEAUX):
            y_niv = y0 + idx*h_niv
            cv.setFillColor(BLANC)
            set_trait(cv, 0.6, color)
            cv.circle(xcol, y_niv, 1.5*mm, fill=1, stroke=1)
            if nom in ("EF", "EC"):
                debit = PLOMBERIE["conso_m3_j"] / NB_NIVEAUX
                cv.setFillColor(GRIS_MOY); cv.setFont(FONT_SOUS, 4)
                cv.drawString(xcol+2*mm, y_niv-1.5,
                              f"Q={debit:.1f}m³/j")

        # Bas
        if nom in ("EF", "EC"):
            tuyau(cv, xcol-6*mm, y0, xcol, y0, color, lw)
            cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
            cv.drawRightString(xcol-7*mm, y0-1.5, "ARRIVÉE")
        else:
            tuyau(cv, xcol, y0, xcol-6*mm, y0, color, lw)
            cv.setFillColor(GRIS_FORT); cv.setFont(FONT_SOUS, 4.5)
            cv.drawRightString(xcol-8*mm, y0-1.5, "→ FOSSE")

    # Bilan hydraulique (encart droit)
    bx = x0+sw-52*mm; by = y0+5*mm
    tableau_donnees(cv, bx, by, 50*mm, 50*mm, "BILAN HYDRAULIQUE", [
        ("Conso totale", f"{PLOMBERIE['conso_m3_j']} m³/j"),
        ("Conso/apt/j", f"{PLOMBERIE['conso_m3_j']/PLOMBERIE['nb_apts']*1000:.0f} L"),
        ("Réservoir", f"{PLOMBERIE['reservoir_m3']} m³"),
        ("Pression", f"{PLOMBERIE['pression_bar']} bar"),
        ("Pompe", f"{PLOMBERIE['pompe_kW']} kW"),
        ("Fosse septique", "15 m³ béton armé"),
    ])

    cv.restoreState()
    return finaliser(cv, buf)


# ── Pl.6 — Bilan MEP + EDGE ──────────────────────────────────
def planche_6_bilan():
    cv, buf = nouvelle_page()
    _cart(cv, 6, "BILAN MEP + EDGE", "Puissances / Débits / Certification IFC", "BILAN", "—")
    bandeau_titre(cv, "Pl.6 — BILAN MEP — RÉCAPITULATIF + EDGE BASIC",
                  "Critères IFC/World Bank : −20% énergie / eau / énergie grise")

    cv.saveState()
    clip_rect(cv, ZX, ZY, ZW, ZH)

    col_w = (ZW - 8*mm) / 3

    # Colonne 1 — Électricité
    tableau_donnees(cv,
        ZX, ZY + ZH*0.02, col_w - 2*mm, ZH*0.96,
        "BILAN ÉLECTRIQUE", [
            ("Puissance totale", f"{ELEC['P_totale_kVA']} kVA"),
            ("Éclairage", "32 kW"),
            ("Prises / force", "96 kW"),
            ("Climatisation", f"{HVAC['P_kW']} kW"),
            ("Pompes", f"{PLOMBERIE['pompe_kW']} kW"),
            ("Communs", "85 kW"),
            ("---",),
            ("TGBT", ELEC["tgbt"]),
            ("Tension", ELEC["tension"]),
            ("GE secours", "200 kVA"),
            ("Onduleur", "15 kVA — 1h"),
            ("Solaire PV", f"{HVAC['solaire_kWc']} kWc"),
            ("---",),
            ("EDGE énergie", "LED + VRV COP3.8 + PV"),
            ("Économie", "≥ 20% vs référence"),
        ]
    )

    # Colonne 2 — Plomberie
    tableau_donnees(cv,
        ZX + col_w + 2*mm, ZY + ZH*0.02, col_w - 2*mm, ZH*0.96,
        "BILAN PLOMBERIE", [
            ("Conso totale", f"{PLOMBERIE['conso_m3_j']} m³/j"),
            ("Conso/apt", f"{PLOMBERIE['conso_m3_j']/PLOMBERIE['nb_apts']*1000:.0f} L/j"),
            ("Réservoir", f"{PLOMBERIE['reservoir_m3']} m³"),
            ("Pression", f"{PLOMBERIE['pression_bar']} bar"),
            ("Pompe", f"{PLOMBERIE['pompe_kW']} kW"),
            ("---",),
            ("Colonnes EF", f"4 × DN{PLOMBERIE['d_col_ef']} PPR"),
            ("Colonnes EC", f"4 × DN{PLOMBERIE['d_col_ec']} PPR"),
            ("Chutes EU", f"4 × DN{PLOMBERIE['d_chute_eu']} PVC"),
            ("Chutes EP", f"6 × DN{PLOMBERIE['d_chute_ep']} PVC"),
            ("Fosse", "15 m³ béton armé"),
            ("---",),
            ("EDGE eau", "Robinets débit réduit"),
            ("ECS solaire", "60% apport solaire"),
            ("Économie eau", "≥ 20% vs référence"),
        ]
    )

    # Colonne 3 — HVAC + récap EDGE
    tableau_donnees(cv,
        ZX + 2*(col_w+2*mm), ZY + ZH*0.02, col_w - 2*mm, ZH*0.96,
        "BILAN HVAC + EDGE", [
            ("Système", HVAC["systeme"]),
            ("Modèle UE", HVAC["UE"]),
            ("Puissance", f"{HVAC['P_kW']} kW"),
            ("Nb unités int.", str(HVAC["nb_UI"])),
            ("COP", str(HVAC["COP"])),
            ("EER", str(HVAC["EER"])),
            ("---",),
            ("VMC double flux", f"{HVAC['VMC_debit_m3h']} m³/h/apt"),
            ("Rendement éch.", "80%"),
            ("Solaire PV", f"{HVAC['solaire_kWc']} kWc"),
            ("Capteurs ECS", "24 m² — 8 capteurs"),
            ("---",),
            ("EDGE enveloppe", "Vitrage double — isolation"),
            ("EDGE bilan", "Certifiable EDGE Basic"),
            ("Économie glob.", "≥ 20% énergie + eau"),
        ]
    )

    cv.restoreState()
    return finaliser(cv, buf)


# ════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════

def generer_dossier_mep(output_path: str):
    print("Génération dossier MEP v4 — charte sobre Tijan")
    writer = PdfWriter()

    planches = [
        ("Pl.1 — Schéma unifilaire électrique",   planche_1_unifilaire),
        ("Pl.2 — Plan étage type — Électricité",   planche_2_elec_etage),
        ("Pl.3 — Plan étage type — Plomberie",     planche_3_plomberie_etage),
        ("Pl.4 — Plan étage type — HVAC",          planche_4_hvac_etage),
        ("Pl.5 — Schéma vertical plomberie",       planche_5_schema_vertical),
        ("Pl.6 — Bilan MEP + EDGE",                planche_6_bilan),
    ]

    for titre, fn in planches:
        writer.add_page(fn())
        print(f"  ✓ {titre}")

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"\n✓ Dossier MEP v4 — 6 planches : {output_path}")


if __name__ == "__main__":
    generer_dossier_mep("/mnt/user-data/outputs/tijan_dossier_mep_v4_sakho.pdf")

"""
plan_theme.py — Charte graphique unifiée pour plans Tijan AI
Cartouche professionnel, légendes, bordures, annotations
"""
import os
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime

def _get_logo_path():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ['tijan_logo_crop.png', 'tijan_logo.png']:
        p = os.path.join(here, name)
        if os.path.exists(p):
            return p
    return None

LOGO_PATH = _get_logo_path()

A3L = landscape(A3)
W, H = A3L

# ══════════════════════════════════════════════════════════════
# PALETTE
# ══════════════════════════════════════════════════════════════
PAL = {
    'noir':      colors.HexColor("#1A1A1A"),
    'gris_f':    colors.HexColor("#444444"),
    'gris':      colors.HexColor("#888888"),
    'gris_c':    colors.HexColor("#BBBBBB"),
    'gris_cc':   colors.HexColor("#DDDDDD"),
    'gris_bg':   colors.HexColor("#F5F5F5"),
    'blanc':     colors.white,
    'vert':      colors.HexColor("#2E8B57"),
    'vert_t':    colors.HexColor("#43A956"),
    'vert_bg':   colors.HexColor("#E8F5E9"),
    'bleu':      colors.HexColor("#1565C0"),
    'bleu_c':    colors.HexColor("#42A5F5"),
    'bleu_bg':   colors.HexColor("#E3F2FD"),
    'rouge':     colors.HexColor("#C62828"),
    'rouge_c':   colors.HexColor("#EF5350"),
    'orange':    colors.HexColor("#E65100"),
    'orange_c':  colors.HexColor("#FF9800"),
    'cyan':      colors.HexColor("#00838F"),
    'cyan_c':    colors.HexColor("#00BCD4"),
    'violet':    colors.HexColor("#6A1B9A"),
    'violet_c':  colors.HexColor("#AB47BC"),
    'marron':    colors.HexColor("#5D4037"),
    'jaune':     colors.HexColor("#F9A825"),
    'jaune_c':   colors.HexColor("#FFC107"),
    'vert_f':    colors.HexColor("#1B5E20"),
}

# ══════════════════════════════════════════════════════════════
# BORDER — Double cadre avec filet intérieur fin
# ══════════════════════════════════════════════════════════════
def draw_border(c):
    m = 8*mm
    # Cadre extérieur épais
    c.setStrokeColor(PAL['noir']); c.setLineWidth(1.2)
    c.rect(m, m, W-2*m, H-2*m)
    # Filet intérieur fin
    c.setStrokeColor(PAL['gris_c']); c.setLineWidth(0.25)
    c.rect(m+1.5, m+1.5, W-2*m-3, H-2*m-3)

# ══════════════════════════════════════════════════════════════
# CARTOUCHE — Design professionnel BET
# ══════════════════════════════════════════════════════════════
def draw_cartouche(c, titre, page, total, niveau="", echelle="1/100",
                   projet="Résidence SAKHO", lieu="Dakar, Sénégal",
                   maitre_ouvrage="Famille SAKHO", lot=""):
    """
    Cartouche BET professionnel en bas à droite.
    6 cellules : Logo | Projet+Titre | Niveau | Échelle+Date | Pl.
    """
    cw = 210*mm
    ch = 36*mm
    cx = W - cw - 8*mm
    cy = 8*mm

    # ── Fond blanc ──
    c.setFillColor(PAL['blanc']); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.8)
    c.rect(cx, cy, cw, ch, fill=1, stroke=1)

    # ── Colonnes ──
    c1 = 42*mm    # Logo
    c2 = 90*mm    # Projet + Titre (large)
    c3 = 42*mm    # Niveau + Lot
    c4 = 36*mm    # Infos (échelle, date, pl.)
    
    # Lignes verticales
    c.setLineWidth(0.4)
    c.line(cx+c1, cy, cx+c1, cy+ch)
    c.line(cx+c1+c2, cy, cx+c1+c2, cy+ch)
    c.line(cx+c1+c2+c3, cy, cx+c1+c2+c3, cy+ch)

    # Ligne horizontale médiane dans colonnes 2, 3, 4
    c.setLineWidth(0.25)
    c.line(cx+c1, cy+ch/2, cx+cw, cy+ch/2)
    # Sous-ligne dans colonne 4 (3 zones)
    c.line(cx+c1+c2+c3, cy+ch*2/3, cx+cw, cy+ch*2/3)
    c.line(cx+c1+c2+c3, cy+ch/3, cx+cw, cy+ch/3)

    # ── Zone 1 : Logo TIJAN AI ──
    logo_cx = cx + c1/2
    # Bande verte derrière le logo
    c.setFillColor(PAL['vert']); c.setStrokeColor(PAL['vert'])
    c.rect(cx+0.5, cy+0.5, c1-1, ch-1, fill=1, stroke=0)
    # Vrai logo PNG si disponible
    if LOGO_PATH:
        try:
            logo_w = c1 - 6*mm
            logo_h = logo_w * 768 / 1376  # aspect ratio du logo
            logo_y = cy + (ch - logo_h) / 2
            c.drawImage(LOGO_PATH, cx + 3*mm, logo_y,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback texte
            c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(logo_cx, cy+ch-14*mm, "TIJAN")
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(logo_cx, cy+ch-20*mm, "AI")
    else:
        c.setFillColor(PAL['blanc']); c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(logo_cx, cy+ch-14*mm, "TIJAN")
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(logo_cx, cy+ch-20*mm, "AI")

    # ── Zone 2 haut : Projet ──
    z2x = cx + c1 + 4*mm
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 9)
    c.drawString(z2x, cy+ch-10*mm, projet)
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 6)
    c.drawString(z2x, cy+ch-16*mm, f"Maître d'ouvrage : {maitre_ouvrage}")

    # ── Zone 2 bas : Titre du plan ──
    c.setFillColor(PAL['vert']); c.setFont("Helvetica-Bold", 8)
    c.drawString(z2x, cy+ch/2-9*mm, titre)
    if lot:
        c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 5.5)
        c.drawString(z2x, cy+2*mm, f"Lot : {lot}")

    # ── Zone 3 haut : Niveau ──
    z3x = cx + c1 + c2 + 3*mm
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(z3x, cy+ch-10*mm, "NIVEAU")
    c.setFillColor(PAL['bleu']); c.setFont("Helvetica-Bold", 7)
    c.drawString(z3x, cy+ch-17*mm, niveau if niveau else "—")

    # ── Zone 3 bas : Lieu ──
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 5.5)
    c.drawString(z3x, cy+ch/2-8*mm, lieu)
    c.drawString(z3x, cy+2*mm, f"BET : Tijan AI")

    # ── Zone 4 : Échelle / Date / Planche ──
    z4x = cx + c1 + c2 + c3 + 3*mm
    z4cx = cx + c1 + c2 + c3 + c4/2

    # Échelle (haut)
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 5)
    c.drawString(z4x, cy+ch-8*mm, "Échelle")
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(z4cx, cy+ch-15*mm, echelle)

    # Date (milieu)
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 5)
    c.drawString(z4x, cy+ch*2/3-7*mm, "Date")
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(z4cx, cy+ch*2/3-13*mm, datetime.now().strftime('%d/%m/%Y'))

    # Planche (bas)
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 5)
    c.drawString(z4x, cy+ch/3-7*mm, "Planche")
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(z4cx, cy+ch/3-14*mm, f"{page}/{total}")

# ══════════════════════════════════════════════════════════════
# LÉGENDE — Cadre propre, titre souligné, symboles alignés
# ══════════════════════════════════════════════════════════════
def draw_legend(c, items, x=10*mm, y=None):
    """
    items: list of (color, label, style)
    style: 'line', 'dash', 'circle', 'rect', 'ring'
    """
    if y is None:
        y = H - 10*mm
    lw = 62*mm
    row_h = 6*mm
    lh = (len(items)+1)*row_h + 5*mm

    # Fond avec ombre légère
    c.setFillColor(colors.Color(0.92,0.92,0.92,0.5))
    c.rect(x+0.8, y-lh-0.8, lw, lh, fill=1, stroke=0)
    # Cadre principal
    c.setFillColor(colors.Color(1,1,1,0.95)); c.setStrokeColor(PAL['gris_f']); c.setLineWidth(0.4)
    c.rect(x, y-lh, lw, lh, fill=1, stroke=1)

    # Titre
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x+4*mm, y-6*mm, "LÉGENDE")
    # Filet sous titre
    c.setStrokeColor(PAL['vert']); c.setLineWidth(0.8)
    c.line(x+3*mm, y-7.5*mm, x+lw-3*mm, y-7.5*mm)

    sym_x1 = x + 4*mm
    sym_x2 = x + 14*mm
    sym_cx = (sym_x1 + sym_x2) / 2
    txt_x = x + 16*mm

    for i, (col, label, style) in enumerate(items):
        iy = y - (i+2)*row_h + 1*mm

        if style == 'line':
            c.setStrokeColor(col); c.setLineWidth(2)
            c.line(sym_x1, iy+2.5, sym_x2, iy+2.5)
        elif style == 'dash':
            c.setStrokeColor(col); c.setLineWidth(1.5); c.setDash(3.5, 2)
            c.line(sym_x1, iy+2.5, sym_x2, iy+2.5)
            c.setDash()
        elif style == 'circle':
            c.setFillColor(col); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.2)
            c.circle(sym_cx, iy+2.5, 2.8, fill=1, stroke=1)
        elif style == 'rect':
            c.setFillColor(col); c.setStrokeColor(PAL['noir']); c.setLineWidth(0.2)
            c.rect(sym_x1, iy+0.5, sym_x2-sym_x1, 4, fill=1, stroke=1)
        elif style == 'ring':
            c.setFillColor(PAL['blanc']); c.setStrokeColor(col); c.setLineWidth(0.8)
            c.circle(sym_cx, iy+2.5, 2.8, fill=1, stroke=1)

        c.setFillColor(PAL['noir']); c.setFont("Helvetica", 5.5)
        c.drawString(txt_x, iy+1, label)

# ══════════════════════════════════════════════════════════════
# AXIS LABEL — Cercle propre avec lettre/numéro
# ══════════════════════════════════════════════════════════════
def draw_axis_label(c, x, y, label):
    r = 5*mm
    c.setStrokeColor(PAL['noir']); c.setLineWidth(0.5)
    c.setFillColor(PAL['blanc'])
    c.circle(x, y, r, fill=1, stroke=1)
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 8)
    tw = c.stringWidth(str(label), "Helvetica-Bold", 8)
    c.drawString(x - tw/2, y - 3, str(label))

# ══════════════════════════════════════════════════════════════
# NOTES — Bloc de notes en bas à gauche
# ══════════════════════════════════════════════════════════════
def draw_notes(c, lines, x=12*mm, y=50*mm):
    """Affiche un bloc de notes techniques"""
    # Fond subtil
    max_w = max(c.stringWidth(l, "Helvetica", 4.5) for l in lines) + 8*mm
    bh = len(lines)*5.5*mm + 6*mm
    c.setFillColor(colors.Color(1,1,1,0.85)); c.setStrokeColor(PAL['gris_c']); c.setLineWidth(0.25)
    c.rect(x-2*mm, y-3*mm, max_w, bh, fill=1, stroke=1)
    # Titre
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica-Bold", 5)
    c.drawString(x, y+bh-7*mm, "NOTES TECHNIQUES")
    c.setStrokeColor(PAL['gris_c']); c.setLineWidth(0.3)
    c.line(x, y+bh-8.5*mm, x+max_w-6*mm, y+bh-8.5*mm)
    # Lignes
    c.setFillColor(PAL['gris_f']); c.setFont("Helvetica", 4.5)
    for i, line in enumerate(lines):
        c.drawString(x, y+bh-13*mm-i*5.5*mm, line)

# ══════════════════════════════════════════════════════════════
# NORTH ARROW
# ══════════════════════════════════════════════════════════════
def draw_north(c, x=None, y=None):
    if x is None: x = W - 25*mm
    if y is None: y = H - 25*mm
    r = 6*mm
    # Circle
    c.setStrokeColor(PAL['gris_f']); c.setLineWidth(0.4)
    c.setFillColor(PAL['blanc'])
    c.circle(x, y, r, fill=1, stroke=1)
    # Arrow
    c.setFillColor(PAL['noir'])
    path = c.beginPath()
    path.moveTo(x, y+r-1.5*mm)
    path.lineTo(x-2.5*mm, y-r+3*mm)
    path.lineTo(x, y-r+5*mm)
    path.lineTo(x+2.5*mm, y-r+3*mm)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    # N
    c.setFillColor(PAL['noir']); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x, y+r+2*mm, "N")

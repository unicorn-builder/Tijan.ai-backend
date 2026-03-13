"""
Tijan AI — Charte graphique v4
Sobre, minimaliste, professionnelle.
Une seule couleur d'accent (vert Tijan).
Tout le reste : noir, blanc, gris.
"""
from reportlab.lib import colors
from reportlab.lib.units import mm

# ── Palette ─────────────────────────────────────────────────
TIJAN_VERT    = colors.HexColor("#3A8C4E")   # accent principal — utilisé avec parcimonie
TIJAN_VERT_F  = colors.HexColor("#2A6438")   # variante foncée (titres)
NOIR          = colors.HexColor("#111111")
GRIS_FORT     = colors.HexColor("#444444")
GRIS_MOY      = colors.HexColor("#888888")
GRIS_CLAIR    = colors.HexColor("#CCCCCC")
GRIS_FOND     = colors.HexColor("#F4F4F2")
GRIS_ALT      = colors.HexColor("#EBEBEB")   # alternance lignes tableau
BLANC         = colors.white

# Couleurs MEP — discrètes, monochromes différenciés par épaisseur + tirets
MEP_EF        = colors.HexColor("#2255AA")   # eau froide — bleu foncé
MEP_EC        = colors.HexColor("#AA4422")   # eau chaude — brun
MEP_EU        = colors.HexColor("#666666")   # eaux usées — gris
MEP_EP        = colors.HexColor("#444488")   # eaux pluviales — ardoise
MEP_ELEC      = colors.HexColor("#111111")   # électricité — noir
MEP_HVAC      = colors.HexColor("#336666")   # climatisation — gris-vert

# ── Traits ──────────────────────────────────────────────────
LW_GROS       = 1.4    # contours béton, murs
LW_MOYEN      = 0.8    # éléments principaux
LW_FIN        = 0.4    # axes, cotes, secondaires
LW_TRES_FIN   = 0.2    # hachures

# ── Typographie ─────────────────────────────────────────────
FONT_TITRE    = "Helvetica-Bold"
FONT_SOUS     = "Helvetica"
FONT_MONO     = "Courier"

FS_GRAND      = 9
FS_NORMAL     = 7
FS_PETIT      = 6
FS_MICRO      = 5

# ── Layout A3 paysage ────────────────────────────────────────
from reportlab.lib.pagesizes import A3, landscape
A3L = landscape(A3)
W, H = A3L   # 841.9 × 595.3 pts

# Marges
ML = 14*mm; MR = 8*mm; MT = 8*mm; MB = 14*mm

# Cartouche droite
CART_W = 64*mm
CART_H = H - MT - MB

# Zone dessin
DX = ML
DY = MB
DW = W - ML - MR - CART_W - 4*mm
DH = H - MT - MB

# Bandeau titre (dans la zone dessin, haut)
TITRE_H = 10*mm


def set_trait(c, lw, color=NOIR, dash=None):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    if dash:
        c.setDash(dash[0], dash[1])
    else:
        c.setDash()


def clip_rect(c, x, y, w, h):
    """Activer le clipping sur un rectangle — tout ce qui est dessiné ensuite est clipé"""
    p = c.beginPath()
    p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)


def texte_clippe(c, texte, x, y, x_max, font=FONT_SOUS, size=FS_PETIT, color=NOIR):
    """Dessine un texte tronqué avec '…' s'il dépasse x_max"""
    c.setFont(font, size)
    c.setFillColor(color)
    # Estimer largeur (approx 0.55 × size par caractère Helvetica)
    char_w = size * 0.55
    max_chars = max(3, int((x_max - x) / char_w))
    if len(texte) > max_chars:
        texte = texte[:max_chars-1] + "…"
    c.drawString(x, y, texte)


def cartouche(c, pl_num, pl_total, titre, sous_titre, lot, echelle,
              projet_nom, projet_ref, ville, date_str):
    """
    Cartouche droit — sobre, Tijan.
    Bandeau vert haut (logo) + infos structurées dessous.
    """
    x = W - MR - CART_W
    y = MB
    cw = CART_W
    ch = CART_H

    # Fond blanc + bordure gris clair
    c.setFillColor(BLANC)
    c.setStrokeColor(GRIS_CLAIR)
    c.setLineWidth(0.5)
    c.rect(x, y, cw, ch, fill=1, stroke=1)

    # Bandeau vert — logo Tijan
    bh = 18*mm
    c.setFillColor(TIJAN_VERT)
    c.rect(x, y + ch - bh, cw, bh, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont(FONT_TITRE, 11)
    c.drawCentredString(x + cw/2, y + ch - bh/2 - 4, "TIJAN AI")
    c.setFont(FONT_SOUS, 5.5)
    c.drawCentredString(x + cw/2, y + ch - bh + 3.5*mm, "Bureau d'études automatisé")

    # Numéro de planche — grand, sobre
    c.setFillColor(TIJAN_VERT)
    c.setFont(FONT_TITRE, 22)
    c.drawCentredString(x + cw/2, y + ch - bh - 14*mm, f"{pl_num:02d}")
    c.setFillColor(GRIS_MOY)
    c.setFont(FONT_SOUS, 6)
    c.drawCentredString(x + cw/2, y + ch - bh - 18*mm, f"/{pl_total}")

    # Séparateur
    c.setStrokeColor(GRIS_CLAIR); c.setLineWidth(0.4)
    c.line(x + 4*mm, y + ch - bh - 20*mm, x + cw - 4*mm, y + ch - bh - 20*mm)

    # Bloc infos projet
    infos = [
        ("PROJET",   projet_nom),
        ("RÉF.",     projet_ref),
        ("VILLE",    ville),
        ("LOT",      lot),
        ("TITRE",    titre),
        ("ÉCHELLE",  echelle),
        ("DATE",     date_str),
    ]

    yi = y + ch - bh - 22*mm
    rh = 8.5*mm
    for label, val in infos:
        yi -= rh
        # Label
        c.setFillColor(GRIS_MOY)
        c.setFont(FONT_SOUS, 4.5)
        c.drawString(x + 3*mm, yi + rh*0.65, label)
        # Valeur — tronquée si trop longue
        c.setFillColor(NOIR)
        c.setFont(FONT_TITRE, 5.5)
        texte_clippe(c, str(val), x + 3*mm, yi + rh*0.2,
                     x + cw - 3*mm, FONT_TITRE, 5.5, NOIR)
        # Ligne séparatrice légère
        c.setStrokeColor(GRIS_ALT); c.setLineWidth(0.3)
        c.line(x + 3*mm, yi, x + cw - 3*mm, yi)

    # Pied de cartouche — sous_titre
    c.setFillColor(GRIS_FOND)
    c.rect(x, y, cw, 8*mm, fill=1, stroke=0)
    c.setFillColor(GRIS_FORT)
    c.setFont(FONT_SOUS, 4.5)
    # Découper sous_titre si trop long
    max_c = int(cw / (4.5 * 0.55))
    st = sous_titre[:max_c] if len(sous_titre) > max_c else sous_titre
    c.drawCentredString(x + cw/2, y + 3*mm, st)

    # Bordure extérieure cartouche
    c.setStrokeColor(GRIS_FORT); c.setLineWidth(0.8)
    c.rect(x, y, cw, ch, fill=0, stroke=1)


def bandeau_titre(c, titre, sous_titre=""):
    """Bandeau titre en haut de la zone dessin — sobre"""
    c.setFillColor(NOIR)
    c.rect(DX, DY + DH - TITRE_H, DW, TITRE_H, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont(FONT_TITRE, 8)
    # Tronquer si trop long
    texte_clippe(c, titre, DX + 4*mm, DY + DH - TITRE_H/2 - 3,
                 DX + DW*0.75, FONT_TITRE, 8, BLANC)
    if sous_titre:
        c.setFont(FONT_SOUS, 6)
        texte_clippe(c, sous_titre,
                     DX + DW*0.76, DY + DH - TITRE_H/2 - 2.5,
                     DX + DW - 3*mm, FONT_SOUS, 6, GRIS_CLAIR)


def bordure_page(c):
    """Bordure fine de la page"""
    c.setStrokeColor(GRIS_FORT)
    c.setLineWidth(1.0)
    c.rect(6*mm, 6*mm, W - 12*mm, H - 12*mm, fill=0, stroke=1)


def tableau_donnees(c, x, y, w, h, titre, lignes, col_split=0.55):
    """
    Tableau de données sobre — 2 colonnes (label / valeur).
    Clipping strict dans les limites x,y,w,h.
    lignes : list of (label, valeur) ou ("---",) pour séparateur
    """
    # Fond
    c.setFillColor(BLANC)
    c.setStrokeColor(GRIS_CLAIR)
    c.setLineWidth(0.4)
    c.rect(x, y, w, h, fill=1, stroke=1)

    # Titre bandeau
    th = 7*mm
    c.setFillColor(NOIR)
    c.rect(x, y + h - th, w, th, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont(FONT_TITRE, 6.5)
    texte_clippe(c, titre, x + 3*mm, y + h - th/2 - 2.5,
                 x + w - 3*mm, FONT_TITRE, 6.5, BLANC)

    # Lignes
    zone_h = h - th
    n = max(len(lignes), 1)
    rh = min(zone_h / n, 7*mm)

    for i, ligne in enumerate(lignes):
        yy = y + h - th - (i + 1) * rh
        if yy < y:
            break  # ne pas dépasser le bas

        # Alternance fond
        if i % 2 == 0:
            c.setFillColor(GRIS_ALT)
            c.rect(x, yy, w, rh, fill=1, stroke=0)

        if len(ligne) == 1 and ligne[0] == "---":
            # Séparateur
            c.setStrokeColor(TIJAN_VERT); c.setLineWidth(0.5)
            c.line(x + 2*mm, yy + rh/2, x + w - 2*mm, yy + rh/2)
            c.setDash()
            continue

        label, val = ligne[0], ligne[1] if len(ligne) > 1 else ""
        x_split = x + w * col_split

        # Label
        c.setFillColor(GRIS_FORT)
        c.setFont(FONT_SOUS, 5.2)
        texte_clippe(c, label, x + 2.5*mm, yy + rh*0.3,
                     x_split - 1*mm, FONT_SOUS, 5.2, GRIS_FORT)

        # Valeur
        c.setFillColor(NOIR)
        c.setFont(FONT_TITRE, 5.5)
        texte_clippe(c, str(val), x_split + 1*mm, yy + rh*0.3,
                     x + w - 2*mm, FONT_TITRE, 5.5, NOIR)

    # Bordure finale
    c.setStrokeColor(GRIS_CLAIR); c.setLineWidth(0.4)
    c.rect(x, y, w, h, fill=0, stroke=1)


def legende_item(c, x, y, color, lw, dash, label):
    """Item de légende sobre — ligne + texte"""
    set_trait(c, lw, color, dash)
    c.line(x, y + 2.5*mm, x + 8*mm, y + 2.5*mm)
    c.setDash()
    c.setFillColor(NOIR)
    c.setFont(FONT_SOUS, 5.5)
    c.drawString(x + 10*mm, y + 1*mm, label)


def bulle_axe(c, cx, cy, r, texte):
    """Bulle d'axe minimaliste"""
    c.setFillColor(BLANC)
    c.setStrokeColor(GRIS_FORT)
    c.setLineWidth(0.5)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(NOIR)
    c.setFont(FONT_TITRE, 6)
    c.drawCentredString(cx, cy - 2.2, texte[:2])


def hachures(c, x, y, w, h, pas=3*mm, angle=45):
    """Hachures béton clippées dans un rectangle"""
    c.saveState()
    p = c.beginPath()
    p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)
    c.setStrokeColor(GRIS_CLAIR)
    c.setLineWidth(LW_TRES_FIN)
    diag = math.hypot(w, h) + pas
    cx_h, cy_h = x + w/2, y + h/2
    n = int(diag / pas) + 2
    import math as _math
    a = _math.radians(angle)
    ca, sa = _math.cos(a), _math.sin(a)
    for i in range(-n, n):
        d = i * pas
        ox, oy = d * _math.cos(a + _math.pi/2), d * _math.sin(a + _math.pi/2)
        c.line(cx_h + ox - diag*ca, cy_h + oy - diag*sa,
               cx_h + ox + diag*ca, cy_h + oy + diag*sa)
    c.restoreState()


import math

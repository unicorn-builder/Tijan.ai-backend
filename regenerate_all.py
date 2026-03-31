"""
Regenerate all plans with improved theme.
Patches mep_generator.py and structure generators to use plan_theme.
"""
import sys, os
sys.path.insert(0, '/Users/serignetall/tijan-repo')

# Monkey-patch: replace old drawing functions with themed versions
from plan_theme import (draw_border, draw_cartouche, draw_legend, draw_notes,
                        draw_north, draw_axis_label, PAL, W, H)
from reportlab.lib.units import mm

# ── Patch mep_generator ──
import mep_generator as mep

def _patched_border(c):
    draw_border(c)

def _patched_cartouche(c, titre, page, total, niveau="", pw=None):
    lot_name = ""
    t_upper = titre.upper()
    if "PLOMB" in t_upper: lot_name = "Lot 1 — Plomberie"
    elif "ELECTRI" in t_upper: lot_name = "Lot 2 — Électricité"
    elif "CVC" in t_upper: lot_name = "Lot 3 — CVC"
    elif "SECURI" in t_upper: lot_name = "Lot 4 — Sécurité Incendie"
    elif "COURANT" in t_upper: lot_name = "Lot 5 — Courants Faibles"
    elif "ASCENS" in t_upper: lot_name = "Lot 6 — Ascenseurs"
    elif "AUTOM" in t_upper: lot_name = "Lot 7 — Automatisation"
    draw_cartouche(c, titre, page, total, niveau=niveau, lot=lot_name)

def _patched_legend(c, items, x=10*mm, y=None, pw=None):
    draw_legend(c, items, x, y)

mep.border = _patched_border
mep.cartouche = _patched_cartouche
mep.legend_box = _patched_legend

# ── Patch structure_generator ──
import structure_generator as struc

def _struc_cartouche(c, titre, page, total, niveau="", pw=None):
    lot_name = ""
    t_upper = titre.upper()
    if "COFFRAGE" in t_upper: lot_name = "Lot 8 — Coffrage"
    elif "POTEAU" in t_upper: lot_name = "Lot 9 — Ferraillage Poteaux"
    elif "POUTRE" in t_upper: lot_name = "Lot 10 — Ferraillage Poutres"
    elif "FONDATION" in t_upper: lot_name = "Lot 11 — Fondations"
    elif "VOILE" in t_upper: lot_name = "Lot 12 — Voiles"
    draw_cartouche(c, titre, page, total, niveau=niveau, lot=lot_name)

struc.border = _patched_border
struc.cartouche = _struc_cartouche
struc.legend_box = _patched_legend
struc.draw_axis_label = draw_axis_label

# ── Patch structure_generator_v2 ──
import structure_generator_v2 as struc2

def _struc2_cartouche(c, titre, page, total, niveau="", pw=None):
    lot_name = ""
    t_upper = titre.upper()
    if "DALLE" in t_upper: lot_name = "Lot 13 — Ferraillage Dalles"
    elif "ESCAL" in t_upper: lot_name = "Lot 14 — Escaliers"
    elif "COUPE" in t_upper: lot_name = "Lot 15 — Coupes Générales"
    elif "NOMENCL" in t_upper or "RÉCAP" in t_upper: lot_name = "Lot 16 — Nomenclature"
    elif "DÉTAIL" in t_upper or "DETAIL" in t_upper: lot_name = "Lot 17 — Détails Constructifs"
    draw_cartouche(c, titre, page, total, niveau=niveau, lot=lot_name)

struc2.border = _patched_border
struc2.cartouche = _struc2_cartouche
struc2.legend_box = _patched_legend
struc2.draw_axis_label = draw_axis_label

# ── Run everything ──
print("=" * 60)
print("RÉGÉNÉRATION COMPLÈTE — Nouveau thème")
print("=" * 60)

# MEP
mep.generate_plomberie()
mep.generate_electricite()
mep.generate_cvc()
mep.generate_securite_incendie()
mep.generate_courants_faibles()
mep.generate_ascenseurs()
mep.generate_automatisation()

# Structure v1
struc.generate_coffrage()
struc.generate_ferraillage_poteaux()
struc.generate_ferraillage_poutres()
struc.generate_fondations()
struc.generate_voiles()

# Structure v2
struc2.generate_ferraillage_dalles()
struc2.generate_escaliers()
struc2.generate_coupes()
struc2.generate_nomenclature()
struc2.generate_details()

print("\n" + "=" * 60)
print("RÉGÉNÉRATION TERMINÉE")
print("=" * 60)

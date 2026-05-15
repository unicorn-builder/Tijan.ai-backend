"""
gen_boq_xlsx.py — BOQ Structure as Excel (.xlsx) — Bilingual FR/EN
Tijan AI — same data as gen_boq_structure.py, Excel output via openpyxl
Columns: Lot | Designation | Qty | Unit | Supply | Labour | Total | Notes
"""
import io, math
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers


VERT_FILL = PatternFill(start_color="43A956", end_color="43A956", fill_type="solid")
GRIS_FILL = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
NORMAL_FONT = Font(name="Calibri", size=10)
NUM_FMT = '#,##0'
THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin'),
)

# ── Supply / labour split ratios ──────────────────────────────
SPLIT_RATIOS = {
    'beton':              (0.75, 0.25),
    'acier':              (0.60, 0.40),
    'coffrage_bois':      (0.30, 0.70),
    'coffrage_metal':     (0.40, 0.60),
    'terr_mecanique':     (0.35, 0.65),
    'terr_manuel':        (0.15, 0.85),
    'remblai':            (0.50, 0.50),
    'evacuation':         (0.50, 0.50),
    'sable':              (0.50, 0.50),
    'pieux':              (0.55, 0.45),
    'fondation':          (0.55, 0.45),
    'maconnerie':         (0.50, 0.50),
    'enduits':            (0.35, 0.65),
    'etanch_sbs':         (0.60, 0.40),
    'etanch_pvc':         (0.60, 0.40),
    'etanch_liquide':     (0.55, 0.45),
    'ba13':               (0.45, 0.55),
    'escalier':           (0.65, 0.35),
    'forfait':            (0.50, 0.50),
    'honoraires':         (0.00, 1.00),
}


def _split(montant, ratio_key):
    """Split a total amount into (fourniture, pose) using predefined ratios."""
    r_f, r_p = SPLIT_RATIOS.get(ratio_key, (0.50, 0.50))
    f = int(montant * r_f)
    p_ = montant - f  # ensure fourn + pose = montant exactly
    return f, p_


# Translation helpers
def _t(fr, en, lang='fr'):
    return en if lang == 'en' else fr


def _add_header_row(ws, row, headers):
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = HEADER_FONT
        cell.fill = VERT_FILL
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = THIN_BORDER


def _add_row(ws, row, values, bold=False, subtotal=False):
    font = BOLD_FONT if bold or subtotal else NORMAL_FONT
    fill = GRIS_FILL if subtotal else None
    for col, val in enumerate(values, 1):
        cell = ws.cell(row=row, column=col, value=val)
        cell.font = font
        cell.border = THIN_BORDER
        if fill:
            cell.fill = fill
        if isinstance(val, (int, float)) and val != 0:
            cell.number_format = NUM_FMT
            cell.alignment = Alignment(horizontal='right')


def generer_boq_structure_xlsx(rs, params: dict, lang: str = "fr") -> bytes:
    """Generate BOQ Structure as Excel. Returns xlsx bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = "BOQ Structure"

    d = rs.params
    boq = rs.boq
    poteaux = rs.poteaux
    poutre = rs.poutre_principale
    dalle = rs.dalle
    fond = rs.fondation

    # Pricing
    try:
        from prix_marche import get_prix_structure
        px = get_prix_structure(d.ville)
    except:
        class _PX:
            beton_c2530_m3=170000; beton_c3037_m3=185000; beton_c3545_m3=210000
            acier_ha400_kg=750; acier_ha500_kg=810; coffrage_bois_m2=18000
            coffrage_metal_m2=25000; terr_mecanique_m3=8500; terr_manuel_m3=5000
            remblai_m3=6500; pieu_fore_d600_ml=220000; pieu_fore_d800_ml=285000
            pieu_fore_d1000_ml=360000; semelle_filante_ml=85000; radier_m2=95000
            agglo_creux_10_m2=18000; agglo_creux_15_m2=24000; agglo_creux_20_m2=30000
            mo_chef_chantier_j=35000; mo_macon_j=18000; mo_ferrailleur_j=20000
            mo_manœuvre_j=8000
        px = _PX()

    prix_beton = {
        'C25/30': px.beton_c2530_m3, 'C30/37': px.beton_c3037_m3,
        'C35/45': px.beton_c3545_m3, 'C40/50': getattr(px, 'beton_c4050_m3', px.beton_c3545_m3),
    }.get(rs.classe_beton, px.beton_c3037_m3)
    prix_acier = px.acier_ha400_kg if rs.classe_acier == 'HA400' else px.acier_ha500_kg

    nb_pot = (d.nb_travees_x + 1) * (d.nb_travees_y + 1)
    surf_batie = boq.surface_batie_m2

    # Title rows
    ws.merge_cells('A1:H1')
    ws['A1'] = d.nom
    ws['A1'].font = Font(name="Calibri", size=14, bold=True)
    ws.merge_cells('A2:H2')
    ws['A2'] = f'{"BOQ Structure" if lang == "en" else "BOQ Structure"} — {d.ville} — R+{d.nb_niveaux-1} — {d.usage.value.capitalize()}'
    ws['A2'].font = Font(name="Calibri", size=11)
    ws.merge_cells('A3:H3')
    built_area_label = _t('Surface bâtie', 'Built area', lang)
    ws['A3'] = f'{built_area_label}: {surf_batie:,.0f} m² — {_t("Béton", "Concrete", lang)} {rs.classe_beton} — {_t("Acier", "Steel", lang)} {rs.classe_acier} — {_t("Prix 2026", "Pricing 2026", lang)}'
    ws['A3'].font = Font(name="Calibri", size=10, italic=True)

    # Column widths — 8 columns
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 45
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 16
    ws.column_dimensions['F'].width = 16
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 30

    if lang == 'en':
        headers = ['Lot', 'Description', 'Qty', 'Unit', 'Materials (FCFA)', 'Installation (FCFA)', 'Total (FCFA)', 'Notes']
    else:
        headers = ['Lot', 'Désignation', 'Qté', 'Unité', 'Matériaux (FCFA)', 'Installation (FCFA)', 'Total (FCFA)', 'Observations']
    row = 5
    _add_header_row(ws, row, headers)
    row += 1

    grand_total = 0
    grand_fourn = 0
    grand_pose = 0

    # LOT 1 — Installation
    m_cloture = int(4*math.sqrt(d.surface_emprise_m2)*15000)
    m_base = int(surf_batie*800)
    m_branch = int(surf_batie*500)
    m_secu = int(surf_batie*300)
    m_repli = int(surf_batie*600)
    inst_forfait = m_cloture + m_base + m_branch + m_secu + m_repli

    f_clot, p_clot = _split(m_cloture, 'forfait')
    f_base, p_base = _split(m_base, 'forfait')
    f_bran, p_bran = _split(m_branch, 'forfait')
    f_secu, p_secu = _split(m_secu, 'forfait')
    f_repl, p_repl = _split(m_repli, 'forfait')
    f_inst = f_clot + f_base + f_bran + f_secu + f_repl
    p_inst = inst_forfait - f_inst

    lot1_rows = [
        ('1.1', _t('Clôture de chantier', 'Site fence', lang), int(4*math.sqrt(d.surface_emprise_m2)), 'ml', f_clot, p_clot, m_cloture, ''),
        ('1.2', _t('Base vie chantier', 'Temporary site facilities', lang), 1, _t('forfait', 'lump sum', lang), f_base, p_base, m_base, _t('Modulaires', 'Modular units', lang)),
        ('1.3', _t('Branchements provisoires eau + élec', 'Temporary water + power connections', lang), 1, _t('forfait', 'lump sum', lang), f_bran, p_bran, m_branch, ''),
        ('1.4', _t('Signalétique sécurité + EPI', 'Safety signage + PPE', lang), 1, _t('forfait', 'lump sum', lang), f_secu, p_secu, m_secu, ''),
        ('1.5', _t('Repli et nettoyage', 'Demobilization & cleanup', lang), 1, _t('forfait', 'lump sum', lang), f_repl, p_repl, m_repli, ''),
    ]
    for vals in lot1_rows:
        _add_row(ws, row, vals)
        row += 1
    _add_row(ws, row, ('', _t('SOUS-TOTAL LOT 1', 'SUBTOTAL LOT 1', lang), '', '', f_inst, p_inst, inst_forfait, ''), subtotal=True)
    grand_total += inst_forfait
    grand_fourn += f_inst
    grand_pose += p_inst
    row += 1

    # LOT 2 — Terrassement / Earthwork
    V_decap = d.surface_emprise_m2 * 0.30
    V_fouilles = d.surface_emprise_m2 * (fond.profondeur_m + 0.50)
    V_remblai = V_fouilles * 0.30
    V_evacu = V_fouilles * 0.70

    m_decap = int(V_decap*px.terr_mecanique_m3)
    m_fouilles = int(V_fouilles*px.terr_mecanique_m3)
    m_remblai = int(V_remblai*px.remblai_m3)
    m_evacu = int(V_evacu*5000)
    c_terr = m_decap + m_fouilles + m_remblai + m_evacu

    f_decap, p_decap = _split(m_decap, 'terr_mecanique')
    f_fouil, p_fouil = _split(m_fouilles, 'terr_mecanique')
    f_rembl, p_rembl = _split(m_remblai, 'remblai')
    f_evacu, p_evacu = _split(m_evacu, 'evacuation')
    f_terr = f_decap + f_fouil + f_rembl + f_evacu
    p_terr = c_terr - f_terr

    lot2_rows = [
        ('2.1', _t('Décapage terre végétale e=30cm', 'Topsoil removal d=30cm', lang), int(V_decap), 'm³', f_decap, p_decap, m_decap, ''),
        ('2.2', _t('Fouilles générales mécaniques', 'Mechanical excavation', lang), int(V_fouilles), 'm³', f_fouil, p_fouil, m_fouilles, ''),
        ('2.3', _t('Remblai compacté', 'Compacted backfill', lang), int(V_remblai), 'm³', f_rembl, p_rembl, m_remblai, ''),
        ('2.4', _t('Évacuation terres', 'Soil evacuation', lang), int(V_evacu), 'm³', f_evacu, p_evacu, m_evacu, ''),
    ]
    for vals in lot2_rows:
        _add_row(ws, row, vals)
        row += 1
    _add_row(ws, row, ('', _t('SOUS-TOTAL LOT 2', 'SUBTOTAL LOT 2', lang), '', '', f_terr, p_terr, c_terr, ''), subtotal=True)
    grand_total += c_terr
    grand_fourn += f_terr
    grand_pose += p_terr
    row += 1

    # LOT 3 — Fondations / Foundations
    if fond.nb_pieux > 0:
        prix_pieu = {600: px.pieu_fore_d600_ml, 800: px.pieu_fore_d800_ml,
                     1000: px.pieu_fore_d1000_ml}.get(fond.diam_pieu_mm, px.pieu_fore_d800_ml)
        c_pieux = int(fond.nb_pieux * fond.longueur_pieu_m * prix_pieu)
        c_longr = int(nb_pot * 6 * 85000)
        c_fond = c_pieux + c_longr
        f_pieux, p_pieux = _split(c_pieux, 'pieux')
        f_longr, p_longr = _split(c_longr, 'fondation')
        f_fond = f_pieux + f_longr
        p_fond = c_fond - f_fond
        piles_label = _t('pieux', 'piles', lang)
        lot3_rows = [
            ('3.1', _t(f'Pieux forés Ø{fond.diam_pieu_mm}mm L={fond.longueur_pieu_m}m', f'Bored piles Ø{fond.diam_pieu_mm}mm L={fond.longueur_pieu_m}m', lang), int(fond.nb_pieux * fond.longueur_pieu_m), 'ml', f_pieux, p_pieux, c_pieux, f'{fond.nb_pieux} {piles_label}'),
            ('3.2', _t('Longrines BA 30×50cm', 'Concrete pile caps 30×50cm', lang), int(nb_pot * 6), 'ml', f_longr, p_longr, c_longr, ''),
        ]
    else:
        m_proprete = int(d.surface_emprise_m2*0.10*120000)
        m_semelles = int(fond.beton_semelle_m3*0.6*prix_beton)
        m_arm_sem = int(fond.beton_semelle_m3*100*prix_acier)
        c_fond = int(fond.beton_semelle_m3 * prix_beton * 1.6)
        f_prop, p_prop = _split(m_proprete, 'beton')
        f_sem, p_sem = _split(m_semelles, 'beton')
        f_arm, p_arm = _split(m_arm_sem, 'acier')
        f_fond = f_prop + f_sem + f_arm
        p_fond = c_fond - f_fond
        lot3_rows = [
            ('3.1', _t('Béton de propreté e=10cm', 'Blinding concrete d=10cm', lang), int(d.surface_emprise_m2*0.10), 'm³', f_prop, p_prop, m_proprete, ''),
            ('3.2', _t(f'Semelles BA {rs.classe_beton}', f'Concrete footings {rs.classe_beton}', lang), int(fond.beton_semelle_m3*0.6), 'm³', f_sem, p_sem, m_semelles, ''),
            ('3.3', _t(f'Armatures semelles {rs.classe_acier}', f'Footing reinforcement {rs.classe_acier}', lang), int(fond.beton_semelle_m3*100), 'kg', f_arm, p_arm, m_arm_sem, ''),
        ]
    for vals in lot3_rows:
        _add_row(ws, row, vals)
        row += 1
    _add_row(ws, row, ('', _t('SOUS-TOTAL LOT 3', 'SUBTOTAL LOT 3', lang), '', '', f_fond, p_fond, c_fond, ''), subtotal=True)
    grand_total += c_fond
    grand_fourn += f_fond
    grand_pose += p_fond
    row += 1

    # LOT 4 — Structure BA / Reinforced Concrete Structure
    ep_dalle_m = dalle.epaisseur_mm / 1000
    c_struct = 0
    f_struct = 0

    # 4.1 — Poteaux / Columns (per level)
    for i, pt in enumerate(poteaux):
        b = pt.section_mm / 1000
        V_niv = b**2 * d.hauteur_etage_m * nb_pot
        As_niv = pt.nb_barres * math.pi * pt.diametre_mm**2 / 400 * nb_pot * d.hauteur_etage_m * 7850 / 10000
        c_b = int(V_niv * prix_beton)
        c_a = int(As_niv * prix_acier)
        f_b, p_b = _split(c_b, 'beton')
        f_a, p_a = _split(c_a, 'acier')
        cols_desc = _t(f'Poteaux béton {pt.section_mm}×{pt.section_mm} — {pt.niveau}',
                       f'Column concrete {pt.section_mm}×{pt.section_mm} — {pt.niveau}', lang)
        _add_row(ws, row, (f'4.1.{i*2+1}', cols_desc, f'{V_niv:.1f}', 'm³', f_b, p_b, c_b, ''))
        row += 1
        steel_desc = _t(f'Armatures poteaux {pt.niveau} — {pt.nb_barres}HA{pt.diametre_mm}',
                        f'Column reinforcement {pt.niveau} — {pt.nb_barres}HA{pt.diametre_mm}', lang)
        _add_row(ws, row, (f'4.1.{i*2+2}', steel_desc, f'{As_niv:.0f}', 'kg', f_a, p_a, c_a, f'{nb_pot} {_t("poteaux", "columns", lang)}'))
        row += 1
        c_struct += c_b + c_a
        f_struct += f_b + f_a

    # 4.2 — Poutres / Beams
    pp_b = poutre.b_mm / 1000
    pp_h = poutre.h_mm / 1000
    px_m = getattr(d, 'portee_x_m', d.portee_max_m)
    py_m = getattr(d, 'portee_y_m', d.portee_max_m)
    V_pp_x = pp_b * pp_h * px_m * (d.nb_travees_y + 1) * d.nb_travees_x * d.nb_niveaux
    V_pp_y = pp_b * pp_h * py_m * (d.nb_travees_x + 1) * d.nb_travees_y * d.nb_niveaux
    V_pp = V_pp_x + V_pp_y
    As_pp_cm2 = (poutre.As_inf_cm2 + poutre.As_sup_cm2) if hasattr(poutre, 'As_inf_cm2') else 10.0
    L_pp_total = (px_m * (d.nb_travees_y + 1) * d.nb_travees_x + py_m * (d.nb_travees_x + 1) * d.nb_travees_y) * d.nb_niveaux
    As_pp_kg = As_pp_cm2 / 10000 * L_pp_total * 7850
    c_pp_b = int(V_pp * prix_beton)
    c_pp_a = int(As_pp_kg * prix_acier)
    f_pp_b, p_pp_b = _split(c_pp_b, 'beton')
    f_pp_a, p_pp_a = _split(c_pp_a, 'acier')
    beams_desc = _t(f'Poutres principales béton {poutre.b_mm}×{poutre.h_mm}',
                    f'Main beams concrete {poutre.b_mm}×{poutre.h_mm}', lang)
    _add_row(ws, row, ('4.2.1', beams_desc, f'{V_pp:.1f}', 'm³', f_pp_b, p_pp_b, c_pp_b, ''))
    row += 1
    beams_steel = _t(f'Armatures poutres', f'Beam reinforcement', lang)
    _add_row(ws, row, ('4.2.2', beams_steel, f'{As_pp_kg:.0f}', 'kg', f_pp_a, p_pp_a, c_pp_a, f'As={As_pp_cm2:.1f}cm²'))
    row += 1
    c_struct += c_pp_b + c_pp_a
    f_struct += f_pp_b + f_pp_a

    # 4.3 — Dalle / Slab
    V_dalle = ep_dalle_m * surf_batie
    c_dalle = int(V_dalle * prix_beton)
    As_dalle_cm2 = (dalle.As_x_cm2_ml + dalle.As_y_cm2_ml) if hasattr(dalle, 'As_x_cm2_ml') else 8.0
    As_dalle_kg = As_dalle_cm2 / 10000 * surf_batie * 7850
    c_dalle_a = int(As_dalle_kg * prix_acier)
    f_dalle, p_dalle = _split(c_dalle, 'beton')
    f_dalle_a, p_dalle_a = _split(c_dalle_a, 'acier')
    slab_desc = _t(f'Dalle pleine ep.{dalle.epaisseur_mm}mm', f'Solid slab t={dalle.epaisseur_mm}mm', lang)
    _add_row(ws, row, ('4.3.1', slab_desc, f'{V_dalle:.1f}', 'm³', f_dalle, p_dalle, c_dalle, ''))
    row += 1
    slab_steel = _t('Armatures dalle (nappe inf. + sup.)', 'Slab reinforcement (top + bottom)', lang)
    _add_row(ws, row, ('4.3.2', slab_steel, f'{As_dalle_kg:.0f}', 'kg', f_dalle_a, p_dalle_a, c_dalle_a, f'As={As_dalle_cm2:.1f}cm²/ml'))
    row += 1
    c_struct += c_dalle + c_dalle_a
    f_struct += f_dalle + f_dalle_a

    # 4.4 — Coffrage / Formwork
    coff_pot = 4 * (poteaux[0].section_mm / 1000) * d.hauteur_etage_m * nb_pot * d.nb_niveaux
    coff_pp = (2 * pp_h + pp_b) * L_pp_total
    coff_dalle = surf_batie * d.nb_niveaux
    coff_total = coff_pot + coff_pp + coff_dalle
    c_coff = int(coff_total * px.coffrage_bois_m2)
    f_coff, p_coff = _split(c_coff, 'coffrage_bois')
    coff_desc = _t('Coffrage bois (poteaux + poutres + dalle)', 'Formwork (columns + beams + slab)', lang)
    _add_row(ws, row, ('4.4', coff_desc, f'{coff_total:.0f}', 'm²', f_coff, p_coff, c_coff,
                       _t(f'Pot:{coff_pot:.0f} + Poutr:{coff_pp:.0f} + Dalle:{coff_dalle:.0f}',
                          f'Col:{coff_pot:.0f} + Beam:{coff_pp:.0f} + Slab:{coff_dalle:.0f}', lang)))
    row += 1
    c_struct += c_coff
    f_struct += f_coff
    p_struct = c_struct - f_struct

    _add_row(ws, row, ('', _t('SOUS-TOTAL LOT 4', 'SUBTOTAL LOT 4', lang), '', '', f_struct, p_struct, c_struct, ''), subtotal=True)
    grand_total += c_struct
    grand_fourn += f_struct
    grand_pose += p_struct
    row += 2

    # GRAND TOTAL
    grand_pose = grand_total - grand_fourn  # ensure exact match
    total_label = _t('TOTAL GÉNÉRAL STRUCTURE', 'TOTAL STRUCTURAL COST', lang)
    unit_label = _t('FCFA/m²', 'FCFA/m²', lang)
    _add_row(ws, row, ('', total_label, '', '', grand_fourn, grand_pose, grand_total, f'{grand_total/surf_batie:,.0f} {unit_label}'), bold=True)
    ws.cell(row=row, column=7).font = Font(name="Calibri", size=12, bold=True, color="43A956")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

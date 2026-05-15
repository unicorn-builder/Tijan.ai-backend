"""
gen_boq_structure_en.py — English Structural BOQ
Complete translation of gen_boq_structure.py with identical structure, layout, and calculations.
Columns: Lot | Description | Qty | Unit | Supply | Labour | Total | Notes
Uses tijan_theme.py for consistent PDF design.
Signature: generer_boq_structure(rs, params_dict) → bytes
"""
import io, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                  Spacer, PageBreak, KeepTogether)
from tijan_theme import *


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
    """Split a total amount into (supply, labour) using predefined ratios."""
    r_f, r_p = SPLIT_RATIOS.get(ratio_key, (0.50, 0.50))
    f = int(montant * r_f)
    p_ = montant - f  # ensure supply + labour = montant exactly
    return f, p_


def generer_boq_structure(rs, params: dict, lang: str = "en") -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rs.params.nom, 'BOQ Structure — Detailed')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    doc.build(_build(rs), onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _row(lot, desig, qte, unite, fourn, pose, total, note='', bold=False):
    st = 'td_b' if bold else 'td'
    st_r = 'td_b_r' if bold else 'td_r'
    st_g = 'td_g_r' if bold else 'td_r'
    return [p(lot, st), p(desig, st), p(str(qte) if qte != '' else '—', st_r),
            p(unite, st),
            p(fmt_fcfa(fourn) if fourn else '—', st_r),
            p(fmt_fcfa(pose) if pose else '—', st_r),
            p(fmt_fcfa(total) if total else '—', st_g),
            p(note, 'small')]

def _sous_total(desig, fourn, pose, total):
    return [p(''), p(desig, 'td_b'), p(''), p(''),
            p(fmt_fcfa(fourn), 'td_r'),
            p(fmt_fcfa(pose), 'td_r'),
            p(fmt_fcfa(total), 'td_g_r'), p('')]

def _build(rs):
    story = []
    d = rs.params
    boq = rs.boq
    poteaux = rs.poteaux
    poutre = rs.poutre_principale
    dalle = rs.dalle
    fond = rs.fondation
    cl = rs.cloisons

    # Try to import pricing
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
            agglo_plein_25_m2=38000; ba13_simple_m2=28000; ba13_double_m2=42000
            etanch_sbs_m2=18500; etanch_pvc_m2=22000; etanch_liquide_m2=12000
            mo_chef_chantier_j=35000; mo_macon_j=18000; mo_ferrailleur_j=20000
            mo_manœuvre_j=8000
        px = _PX()

    # Select concrete price by class
    prix_beton = {
        'C25/30': px.beton_c2530_m3, 'C30/37': px.beton_c3037_m3,
        'C35/45': px.beton_c3545_m3, 'C40/50': getattr(px,'beton_c4050_m3', 240000),
    }.get(rs.classe_beton, px.beton_c3037_m3)

    prix_acier = px.acier_ha400_kg if rs.classe_acier == 'HA400' else px.acier_ha500_kg

    nb_pot = (d.nb_travees_x + 1) * (d.nb_travees_y + 1)
    ep_dalle_m = dalle.epaisseur_mm / 1000
    surf_batie = boq.surface_batie_m2

    # ── HEADER ───────────────────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(d.nom, S['titre']))
    story.append(Paragraph(
        f'Bill of Quantities and Prices — Structure — {d.ville} {rs.params.pays}',
        S['sous_titre']))
    story.append(Paragraph(
        f'R+{d.nb_niveaux-1} — {d.usage.value.capitalize()} — '
        f'Built area: {fmt_n(surf_batie,0,"m²")} — '
        f'Concrete {rs.classe_beton} — Steel {rs.classe_acier}',
        S['body']))
    story.append(Paragraph(
        'Unit prices local market 2026. Materials and installation columns separated. Margin ±15%. '
        'Document suitable for contractor tender.',
        S['note']))
    story.append(Spacer(1, 3*mm))

    # BOQ Columns — 8 columns with supply / labour split
    CW_COLS = [CW*w for w in [0.04, 0.30, 0.06, 0.05, 0.13, 0.13, 0.13, 0.16]]
    dl = devise_label()
    HEADERS = [p(h,'th') for h in [
        'Lot', 'Description', 'Qty', 'Unit',
        f'Materials ({dl})', f'Installation ({dl})', f'Total ({dl})', 'Notes']]

    def make_table(rows):
        t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
        ts = table_style()
        t.setStyle(ts)
        return t

    # Tracking supply / labour totals for recap
    recap_fourn = {}
    recap_pose = {}

    # ══════════════════════════════════════════════════════════
    # LOT 1 — SITE INSTALLATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 1', 'SITE INSTALLATION AND MANAGEMENT')

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

    rows_inst = [
        _row('1.1', 'Site fence (wood palisade or corrugated metal)', int(4*math.sqrt(d.surface_emprise_m2)), 'lm', f_clot, p_clot, m_cloture),
        _row('1.2', 'Site office, changing rooms, sanitary facilities', 1, 'lump sum', f_base, p_base, m_base, 'Modular removable'),
        _row('1.3', 'Provisional water + electricity connections', 1, 'lump sum', f_bran, p_bran, m_branch),
        _row('1.4', 'Safety signage + PPE supply', 1, 'lump sum', f_secu, p_secu, m_secu),
        _row('1.5', 'Site decommissioning and cleanup', 1, 'lump sum', f_repl, p_repl, m_repli),
        _sous_total('SUBTOTAL LOT 1', f_inst, p_inst, inst_forfait),
    ]
    story.append(make_table(rows_inst))
    recap_fourn['lot1'] = f_inst
    recap_pose['lot1'] = p_inst

    # ══════════════════════════════════════════════════════════
    # LOT 2 — EARTHWORKS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 2', 'EARTHWORKS — GENERAL')
    V_decap = d.surface_emprise_m2 * 0.30
    V_fouilles = d.surface_emprise_m2 * (fond.profondeur_m + 0.50)
    V_remblai  = V_fouilles * 0.30
    V_evacu    = V_fouilles * 0.70

    m_decap = int(V_decap*px.terr_mecanique_m3)
    m_fouilles = int(V_fouilles*px.terr_mecanique_m3)
    m_fouilles_man = int(V_fouilles*0.10*px.terr_manuel_m3)
    m_remblai = int(V_remblai*px.remblai_m3)
    m_evacu = int(V_evacu*5000)
    m_sable = int(d.surface_emprise_m2*0.10*12000)

    f_decap, p_decap = _split(m_decap, 'terr_mecanique')
    f_fouil, p_fouil = _split(m_fouilles, 'terr_mecanique')
    f_fman, p_fman = _split(m_fouilles_man, 'terr_manuel')
    f_rembl, p_rembl = _split(m_remblai, 'remblai')
    f_evacu, p_evacu = _split(m_evacu, 'evacuation')
    f_sable, p_sable = _split(m_sable, 'sable')

    c_terr = m_decap + m_fouilles + m_fouilles_man + m_remblai + m_evacu + m_sable
    f_terr = f_decap + f_fouil + f_fman + f_rembl + f_evacu + f_sable
    p_terr = c_terr - f_terr

    rows_terr = [
        _row('2.1', 'Topsoil stripping e=30cm', int(V_decap), 'm³', f_decap, p_decap, m_decap),
        _row('2.2', 'Mechanical excavation general', int(V_fouilles), 'm³', f_fouil, p_fouil, m_fouilles, 'Mechanical equipment'),
        _row('2.3', 'Manual excavation at bottom of holes', int(V_fouilles*0.10), 'm³', f_fman, p_fman, m_fouilles_man, 'Manual finishing'),
        _row('2.4', 'Compacted backfill (selected material)', int(V_remblai), 'm³', f_rembl, p_rembl, m_remblai),
        _row('2.5', 'Excess soil disposal', int(V_evacu), 'm³', f_evacu, p_evacu, m_evacu, 'Transport + authorized dumping'),
        _row('2.6', 'Sand bed under flooring e=10cm', int(d.surface_emprise_m2*0.10), 'm³', f_sable, p_sable, m_sable),
        _sous_total('SUBTOTAL LOT 2', f_terr, p_terr, c_terr),
    ]
    story.append(make_table(rows_terr))
    recap_fourn['lot2'] = f_terr
    recap_pose['lot2'] = p_terr

    # ══════════════════════════════════════════════════════════
    # LOT 3 — FOUNDATIONS
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 3', 'FOUNDATIONS')
    story.append(Paragraph(
        f'Type: {fond.type.value} — Admissible soil pressure: {d.pression_sol_MPa} MPa — '
        f'Justification: {fond.justification}', S['note']))
    story.append(Spacer(1, 2*mm))

    rows_fond = []
    c_fond = 0
    f_fond_total = 0

    if fond.nb_pieux > 0:
        prix_pieu = {600: px.pieu_fore_d600_ml, 800: px.pieu_fore_d800_ml,
                     1000: px.pieu_fore_d1000_ml}.get(fond.diam_pieu_mm, px.pieu_fore_d800_ml)
        V_fond_beton = fond.nb_pieux * math.pi*(fond.diam_pieu_mm/1000/2)**2 * fond.longueur_pieu_m
        kg_fond_acier = fond.nb_pieux * fond.As_cm2/10000 * 7850 * fond.longueur_pieu_m
        c_pieux = int(fond.nb_pieux * fond.longueur_pieu_m * prix_pieu)
        c_longr = int(nb_pot * 6 * 85000)
        c_fond  = c_pieux + c_longr

        f_pieux, p_pieux = _split(c_pieux, 'pieux')
        f_acier_f, p_acier_f = _split(int(kg_fond_acier*prix_acier), 'acier')
        m_proprete = int(nb_pot*0.5*0.5*0.10*120000)
        f_prop, p_prop = _split(m_proprete, 'beton')
        f_longr, p_longr = _split(c_longr, 'fondation')
        m_tetes = int(nb_pot*120000)
        f_tetes, p_tetes = _split(m_tetes, 'fondation')

        f_fond_total = f_pieux + f_acier_f + f_prop + f_longr + f_tetes
        p_fond_total = c_fond - f_fond_total

        rows_fond = [
            _row('3.1', f'RC bored piles Ø{fond.diam_pieu_mm}mm — L={fond.longueur_pieu_m}m', int(fond.nb_pieux * fond.longueur_pieu_m), 'lm', f_pieux, p_pieux, c_pieux, f'{fond.nb_pieux} piles × {fond.longueur_pieu_m}m'),
            _row('3.2', f'Pile reinforcement HA500B — cage Ø{fond.diam_pieu_mm}mm', int(kg_fond_acier), 'kg', f_acier_f, p_acier_f, int(kg_fond_acier*prix_acier), f'As={fond.As_cm2}cm² per pile'),
            _row('3.3', f'Blinding concrete e=10cm under tie beams', int(nb_pot*0.5*0.5*0.10), 'm³', f_prop, p_prop, m_proprete),
            _row('3.4', f'RC tie beams {rs.classe_beton} — 30×50cm section', int(nb_pot * 6), 'lm', f_longr, p_longr, c_longr, 'Links between piles'),
            _row('3.5', 'Pile heads + RC capitals', nb_pot, 'ea', f_tetes, p_tetes, m_tetes, 'Pile-structure connection'),
            _sous_total('SUBTOTAL LOT 3', f_fond_total, p_fond_total, c_fond),
        ]
        story.append(Paragraph(
            f'ℹ Foundations represent {c_fond/boq.total_bas_fcfa*100:.0f}% of structure budget — '
            f'critical item requiring prior geotechnical study.',
            S['note']))
    elif fond.beton_semelle_m3 > 0:
        c_fond = int(fond.beton_semelle_m3 * prix_beton * 1.6)
        m_prop = int(d.surface_emprise_m2*0.10*120000)
        m_sem = int(fond.beton_semelle_m3*0.6*prix_beton)
        m_arm = int(fond.beton_semelle_m3*100*prix_acier)
        m_coff_f = int(fond.beton_semelle_m3*2*px.coffrage_bois_m2)

        f_prop, p_prop = _split(m_prop, 'beton')
        f_sem, p_sem = _split(m_sem, 'beton')
        f_arm, p_arm = _split(m_arm, 'acier')
        f_coff, p_coff = _split(m_coff_f, 'coffrage_bois')

        f_fond_total = f_prop + f_sem + f_arm + f_coff
        p_fond_total = c_fond - f_fond_total

        rows_fond = [
            _row('3.1', 'Blinding concrete e=10cm', int(d.surface_emprise_m2*0.10), 'm³', f_prop, p_prop, m_prop),
            _row('3.2', f'RC footings {rs.classe_beton}', int(fond.beton_semelle_m3*0.6), 'm³', f_sem, p_sem, m_sem),
            _row('3.3', f'Footing reinforcement {rs.classe_acier}', int(fond.beton_semelle_m3*100), 'kg', f_arm, p_arm, m_arm),
            _row('3.4', 'Footing formwork (lost forms)', int(fond.beton_semelle_m3*2), 'm²', f_coff, p_coff, m_coff_f),
            _sous_total('SUBTOTAL LOT 3', f_fond_total, p_fond_total, c_fond),
        ]

    story.append(make_table(rows_fond))
    recap_fourn['lot3'] = f_fond_total
    recap_pose['lot3'] = c_fond - f_fond_total

    # ══════════════════════════════════════════════════════════
    # LOT 4 — REINFORCED CONCRETE STRUCTURE
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 4', f'REINFORCED CONCRETE STRUCTURE — {rs.classe_beton} / {rs.classe_acier}')

    # 4.1 Columns by level
    story.append(Paragraph('4.1 — Columns', S['h2']))
    rows_pot = [HEADERS]
    c_pot_total = 0
    f_pot_total = 0
    for i, pt in enumerate(poteaux):
        b = pt.section_mm / 1000
        V_niv = b**2 * d.hauteur_etage_m * nb_pot
        As_niv = pt.nb_barres * math.pi * pt.diametre_mm**2 / 400 * nb_pot * d.hauteur_etage_m * 7850 / 10000
        c_beton_niv = int(V_niv * prix_beton)
        c_acier_niv = int(As_niv * prix_acier)
        c_coff_niv  = int(4 * b * d.hauteur_etage_m * nb_pot * px.coffrage_bois_m2)
        c_pot_niv   = c_beton_niv + c_acier_niv + c_coff_niv

        f_b, p_b = _split(c_beton_niv, 'beton')
        f_a, p_a = _split(c_acier_niv, 'acier')
        f_c, p_c = _split(c_coff_niv, 'coffrage_bois')
        f_niv = f_b + f_a + f_c

        c_pot_total += c_pot_niv
        f_pot_total += f_niv
        rows_pot.append([
            p(f'4.1.{i+1}'),
            p(f'Columns {pt.niveau} — {pt.section_mm}×{pt.section_mm}mm — {pt.nb_barres}HA{pt.diametre_mm}'),
            p(f'{nb_pot}', 'td_r'), p('ea'),
            p(fmt_fcfa(f_niv), 'td_r'),
            p(fmt_fcfa(c_pot_niv - f_niv), 'td_r'),
            p(fmt_fcfa(c_pot_niv), 'td_r'),
            p(f'NEd={pt.NEd_kN:.0f}kN | ρ={pt.taux_armature_pct:.1f}%', 'small'),
        ])
    rows_pot.append(_sous_total('Subtotal columns', f_pot_total, c_pot_total - f_pot_total, c_pot_total))

    t_pot = Table(rows_pot, colWidths=CW_COLS, repeatRows=1)
    t_pot.setStyle(table_style())
    story.append(t_pot)

    # 4.2 Beams
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.2 — Beams', S['h2']))
    b_p = poutre.b_mm/1000; h_p = poutre.h_mm/1000
    L_px = d.nb_travees_x * d.portee_max_m * (d.nb_travees_y+1) * d.nb_niveaux
    L_py = d.nb_travees_y * d.portee_min_m * (d.nb_travees_x+1) * d.nb_niveaux
    V_pout = (L_px + L_py) * b_p * (h_p - ep_dalle_m)
    kg_pout = V_pout * 100
    c_pout_beton = int(V_pout * prix_beton)
    c_pout_acier = int(kg_pout * prix_acier)
    c_pout_coff  = int((L_px+L_py) * (b_p + 2*(h_p-ep_dalle_m)) * px.coffrage_bois_m2 * 0.6)
    c_pout_total = c_pout_beton + c_pout_acier + c_pout_coff

    f_pb, p_pb = _split(c_pout_beton, 'beton')
    f_pa, p_pa = _split(c_pout_acier, 'acier')
    f_pc, p_pc = _split(c_pout_coff, 'coffrage_bois')
    f_pout_total = f_pb + f_pa + f_pc

    f_pb_x = int(f_pb * L_px / (L_px + L_py)) if (L_px + L_py) > 0 else 0
    p_pb_x = int(c_pout_beton * L_px / (L_px + L_py)) - f_pb_x if (L_px + L_py) > 0 else 0
    m_pb_x = int(c_pout_beton * L_px / (L_px + L_py)) if (L_px + L_py) > 0 else 0
    f_pb_y = f_pb - f_pb_x
    p_pb_y = (c_pout_beton - m_pb_x) - f_pb_y
    m_pb_y = c_pout_beton - m_pb_x

    rows_pout = [
        HEADERS,
        _row('4.2.1', f'Main beams {poutre.b_mm}×{poutre.h_mm}mm — max span {d.portee_max_m}m', int(L_px), 'lm', f_pb_x, p_pb_x, m_pb_x, f'As bottom={poutre.As_inf_cm2}cm² / As top={poutre.As_sup_cm2}cm²'),
        _row('4.2.2', f'Secondary beams {poutre.b_mm}×{poutre.h_mm}mm — min span {d.portee_min_m}m', int(L_py), 'lm', f_pb_y, p_pb_y, m_pb_y),
        _row('4.2.3', f'Beam reinforcement {rs.classe_acier} (shaped + placed)', int(kg_pout), 'kg', f_pa, p_pa, c_pout_acier, f'Stirrups HA{poutre.etrier_diam_mm} e={poutre.etrier_esp_mm}mm'),
        _row('4.2.4', 'Beam formwork (wood + props)', int((L_px+L_py)*(b_p+2*(h_p-ep_dalle_m))*0.6), 'm²', f_pc, p_pc, c_pout_coff),
        _sous_total('Subtotal beams', f_pout_total, c_pout_total - f_pout_total, c_pout_total),
    ]
    t_pout = Table(rows_pout, colWidths=CW_COLS, repeatRows=1)
    t_pout.setStyle(table_style())
    story.append(t_pout)

    # 4.3 Slabs
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.3 — Slabs', S['h2']))
    V_dalles = surf_batie * ep_dalle_m * 0.85
    kg_dalles = V_dalles * 80
    c_dalle_beton = int(V_dalles * prix_beton)
    c_dalle_acier = int(kg_dalles * prix_acier)
    c_dalle_coff  = int(surf_batie * 0.85 * px.coffrage_bois_m2)
    c_dalle_total = c_dalle_beton + c_dalle_acier + c_dalle_coff

    f_db, p_db = _split(c_dalle_beton, 'beton')
    f_da, p_da = _split(c_dalle_acier, 'acier')
    f_dc, p_dc = _split(c_dalle_coff, 'coffrage_bois')
    m_etai = int(surf_batie*0.85*3500)
    f_etai, p_etai = _split(m_etai, 'coffrage_bois')
    m_reserv = int(surf_batie*500)
    f_reserv, p_reserv = _split(m_reserv, 'forfait')
    f_dalle_total = f_db + f_da + f_dc + f_etai + f_reserv
    c_dalle_total_full = c_dalle_total + m_etai + m_reserv

    rows_dalles = [
        HEADERS,
        _row('4.3.1', f'RC slab concrete {rs.classe_beton} BPE e={dalle.epaisseur_mm}mm', int(V_dalles), 'm³', f_db, p_db, c_dalle_beton, f'As_x={dalle.As_x_cm2_ml}cm²/lm / As_y={dalle.As_y_cm2_ml}cm²/lm'),
        _row('4.3.2', f'Slab reinforcement {rs.classe_acier} — HA10 both directions', int(kg_dalles), 'kg', f_da, p_da, c_dalle_acier, 'Welded mesh + reinforcement'),
        _row('4.3.3', 'Slab formwork (metal plates)', int(surf_batie*0.85), 'm²', f_dc, p_dc, c_dalle_coff),
        _row('4.3.4', 'Temporary shoring (scaffolding)', int(surf_batie*0.85), 'm²', f_etai, p_etai, m_etai, 'Rental + labor'),
        _row('4.3.5', 'Openings and chases (shafts, stairs)', 1, 'lump sum', f_reserv, p_reserv, m_reserv, 'Estimate 0.5% of built area'),
        _sous_total('Subtotal slabs', f_dalle_total, c_dalle_total_full - f_dalle_total, c_dalle_total_full),
    ]
    t_dalles = Table(rows_dalles, colWidths=CW_COLS, repeatRows=1)
    t_dalles.setStyle(table_style())
    story.append(t_dalles)

    # 4.4 Stairs
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.4 — Stairs', S['h2']))
    nb_esc = max(1, int(surf_batie/1500))
    c_esc_vol = int(nb_esc * d.nb_niveaux * 450000)
    c_esc_garde = int(nb_esc*d.nb_niveaux*3*45000)
    c_esc = c_esc_vol + c_esc_garde
    f_esc_v, p_esc_v = _split(c_esc_vol, 'escalier')
    f_esc_g, p_esc_g = _split(c_esc_garde, 'escalier')
    f_esc = f_esc_v + f_esc_g

    rows_esc = [
        HEADERS,
        _row('4.4.1', f'RC stairs {rs.classe_beton} — flights + landings', nb_esc * d.nb_niveaux, 'flight', f_esc_v, p_esc_v, c_esc_vol, f'{nb_esc} staircase(s) × {d.nb_niveaux} levels'),
        _row('4.4.2', 'Stair handrail (RC/metal)', nb_esc * d.nb_niveaux * 3, 'lm', f_esc_g, p_esc_g, c_esc_garde),
        _sous_total('Subtotal stairs', f_esc, c_esc - f_esc, c_esc),
    ]
    t_esc = Table(rows_esc, colWidths=CW_COLS, repeatRows=1)
    t_esc.setStyle(table_style())
    story.append(t_esc)

    recap_fourn['lot4'] = f_pot_total + f_pout_total + f_dalle_total + f_esc
    recap_pose['lot4'] = (c_pot_total + c_pout_total + c_dalle_total_full + c_esc) - recap_fourn['lot4']

    # ══════════════════════════════════════════════════════════
    # LOT 5 — MASONRY AND PARTITIONS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 5', 'MASONRY, PARTITIONS AND FINISHES')
    cl = rs.cloisons
    opt_rec = next((o for o in cl.options if o.type == cl.option_recommandee), cl.options[0])

    rows_maco = [HEADERS]
    c_maco_total = 0
    f_maco_total = 0

    # Exterior facades
    surf_facades = 4 * math.sqrt(d.surface_emprise_m2) * d.nb_niveaux * d.hauteur_etage_m * 0.70
    c_fac = int(surf_facades * px.agglo_plein_25_m2)
    f_fac, p_fac = _split(c_fac, 'maconnerie')
    rows_maco.append(_row('5.1', 'Exterior facade masonry — solid blocks 25cm',
        int(surf_facades), 'm²', f_fac, p_fac, c_fac, 'Perimeter walls finished 2 sides'))
    c_maco_total += c_fac
    f_maco_total += f_fac

    # Separative partitions
    c_sep = int(cl.surface_separative_m2 * opt_rec.prix_fcfa_m2)
    f_sep, p_sep = _split(c_sep, 'maconnerie')
    rows_maco.append(_row('5.2', f'Separative partitions — {opt_rec.materiau[:40]}',
        int(cl.surface_separative_m2), 'm²', f_sep, p_sep, c_sep,
        f'Recommended option — {opt_rec.usage_recommande[:35]}'))
    c_maco_total += c_sep
    f_maco_total += f_sep

    # Light interior partitions
    prix_leger = px.ba13_simple_m2
    c_leg = int(cl.surface_legere_m2 * prix_leger)
    f_leg, p_leg = _split(c_leg, 'ba13')
    rows_maco.append(_row('5.3', 'Light interior partitions — simple BA13 rail',
        int(cl.surface_legere_m2), 'm²', f_leg, p_leg, c_leg, 'Non-separative interior partitions'))
    c_maco_total += c_leg
    f_maco_total += f_leg

    # Technical shafts
    c_gaines = int(cl.surface_gaines_m2 * px.beton_c3037_m3 * 0.20)
    f_gaines, p_gaines = _split(c_gaines, 'beton')
    rows_maco.append(_row('5.4', 'Technical shafts — cast RC 20cm',
        int(cl.surface_gaines_m2), 'm²', f_gaines, p_gaines, c_gaines,
        'Lift shafts + riser columns'))
    c_maco_total += c_gaines
    f_maco_total += f_gaines

    # Renders/finishes
    surf_enduit = (surf_facades + cl.surface_separative_m2) * 2
    c_end = int(surf_enduit * 8500)
    f_end, p_end = _split(c_end, 'enduits')
    rows_maco.append(_row('5.5', 'Cement + plaster finishes interior/exterior',
        int(surf_enduit), 'm²', f_end, p_end, c_end, 'Finishing of masonry surfaces'))
    c_maco_total += c_end
    f_maco_total += f_end

    # Parapets
    perim = 4 * math.sqrt(d.surface_emprise_m2)
    c_acrot = int(perim * 35000)
    f_acrot, p_acrot = _split(c_acrot, 'beton')
    rows_maco.append(_row('5.6', 'RC parapets h=60cm on roof',
        int(perim), 'lm', f_acrot, p_acrot, c_acrot))
    c_maco_total += c_acrot
    f_maco_total += f_acrot

    p_maco_total = c_maco_total - f_maco_total
    rows_maco.append(_sous_total('SUBTOTAL LOT 5', f_maco_total, p_maco_total, c_maco_total))
    recap_fourn['lot5'] = f_maco_total
    recap_pose['lot5'] = p_maco_total

    # Note on partition options
    story.append(Paragraph(
        'ℹ Several partition options available based on budget and use. '
        'See structure calculation note for detailed comparison.',
        S['note']))
    t_maco = Table(rows_maco, colWidths=CW_COLS, repeatRows=1)
    t_maco.setStyle(table_style())
    story.append(t_maco)

    # ══════════════════════════════════════════════════════════
    # LOT 6 — WATERPROOFING AND INSULATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 6', 'WATERPROOFING AND INSULATION')
    surf_etanch = d.surface_emprise_m2
    c_sbs  = int(surf_etanch * px.etanch_sbs_m2)
    c_prot = int(surf_etanch * 5000)
    c_dallettes = int(surf_etanch * 0.40 * 8000)
    c_ss_sol = int(d.surface_emprise_m2 * 0.30 * px.etanch_pvc_m2) if d.avec_sous_sol else 0
    c_salles = int(surf_batie * 0.08 * px.etanch_liquide_m2)
    c_etanch_total = c_sbs + c_prot + c_dallettes + c_salles + c_ss_sol

    f_sbs, p_sbs = _split(c_sbs, 'etanch_sbs')
    f_prot, p_prot = _split(c_prot, 'forfait')
    f_dall, p_dall = _split(c_dallettes, 'forfait')
    f_sal, p_sal = _split(c_salles, 'etanch_liquide')
    f_etanch = f_sbs + f_prot + f_dall + f_sal

    rows_etanch = [
        HEADERS,
        _row('6.1', 'Flat roof waterproofing SBS bitumen (primer + 2 coats)', int(surf_etanch), 'm²', f_sbs, p_sbs, c_sbs, 'Torch applied — DTU 43.1'),
        _row('6.2', 'Waterproofing protection — 5cm protection screed', int(surf_etanch), 'm²', f_prot, p_prot, c_prot),
        _row('6.3', 'Concrete tiles on supports (accessible roof)', int(surf_etanch*0.40), 'm²', f_dall, p_dall, c_dallettes, '40% accessible roof'),
        _row('6.4', 'Wet room waterproofing (bathrooms, kitchens)', int(surf_batie*0.08), 'm²', f_sal, p_sal, c_salles, 'Single component resin'),
    ]
    if d.avec_sous_sol:
        f_ss, p_ss = _split(c_ss_sol, 'etanch_pvc')
        rows_etanch.append(_row('6.5', 'Basement waterproofing (PVC membrane)', int(d.surface_emprise_m2), 'm²', f_ss, p_ss, c_ss_sol, 'Internal tanking'))
        f_etanch += f_ss

    p_etanch = c_etanch_total - f_etanch
    rows_etanch.append(_sous_total('SUBTOTAL LOT 6', f_etanch, p_etanch, c_etanch_total))
    recap_fourn['lot6'] = f_etanch
    recap_pose['lot6'] = p_etanch

    t_etanch = Table(rows_etanch, colWidths=CW_COLS, repeatRows=1)
    t_etanch.setStyle(table_style())
    story.append(t_etanch)

    # ══════════════════════════════════════════════════════════
    # LOT 7 — MISCELLANEOUS AND CONTINGENCIES
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 7', 'MISCELLANEOUS, CONTINGENCIES AND ENGINEERING FEES')
    sous_tot_travaux = (inst_forfait + c_terr + c_fond + c_pot_total +
                        c_pout_total + c_dalle_total_full + c_maco_total + c_etanch_total)
    c_impr  = int(sous_tot_travaux * 0.05)
    c_bet   = int(sous_tot_travaux * 0.04)
    c_ctrl  = int(sous_tot_travaux * 0.015)
    m_joints = int(surf_batie/500*850000)
    m_reserv7 = int(surf_batie*800)

    f_joints, p_joints = _split(m_joints, 'forfait')
    f_reserv7, p_reserv7 = _split(m_reserv7, 'forfait')
    f_impr, p_impr = _split(c_impr, 'forfait')
    f_bet, p_bet = _split(c_bet, 'honoraires')
    f_ctrl, p_ctrl = _split(c_ctrl, 'honoraires')

    c_div_total = m_joints + m_reserv7 + c_impr + c_bet + c_ctrl
    f_div = f_joints + f_reserv7 + f_impr + f_bet + f_ctrl
    p_div = c_div_total - f_div

    rows_div = [
        HEADERS,
        _row('7.1', 'Expansion joints (all levels)', int(surf_batie/500), 'ea', f_joints, p_joints, m_joints, '1 joint per 500m² approx.'),
        _row('7.2', 'Miscellaneous reservations and sealants', 1, 'lump sum', f_reserv7, p_reserv7, m_reserv7, 'Electrical and plumbing sleeves'),
        _row('7.3', 'Site contingencies (5% works)', 1, 'lump sum', f_impr, p_impr, c_impr, 'Variations and adaptations'),
        _row('7.4', 'Engineer design fees (4% works)', 1, 'lump sum', f_bet, p_bet, c_bet, 'Execution plans + supervision'),
        _row('7.5', 'Technical inspection (1.5% works)', 1, 'lump sum', f_ctrl, p_ctrl, c_ctrl, 'Approved body required'),
        _sous_total('SUBTOTAL LOT 7', f_div, p_div, c_div_total),
    ]
    recap_fourn['lot7'] = f_div
    recap_pose['lot7'] = p_div

    t_div = Table(rows_div, colWidths=CW_COLS, repeatRows=1)
    t_div.setStyle(table_style())
    story.append(t_div)

    # ══════════════════════════════════════════════════════════
    # GENERAL SUMMARY
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('RECAP', 'GENERAL SUMMARY')

    total_ht  = (inst_forfait + c_terr + c_fond + c_pot_total +
                 c_pout_total + c_dalle_total_full + c_maco_total +
                 c_etanch_total + c_div_total)
    total_fourn = sum(recap_fourn.values())
    total_pose = total_ht - total_fourn
    total_bas = int(total_ht * 0.95)
    total_haut = int(total_ht * 1.15)

    recap_rows = [
        [p('LOT','th'), p('DESCRIPTION','th_l'), p(f'SUPPLY ({dl})','th'), p(f'LABOUR ({dl})','th'), p(f'AMOUNT ({dl})','th'), p('% TOTAL','th')],
        [p('1','td_b'), p('Site Installation'), p(fmt_fcfa(recap_fourn.get('lot1',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot1',0)),'td_r'), p(fmt_fcfa(inst_forfait),'td_r'), p(f'{inst_forfait/total_ht*100:.1f}%','td_r')],
        [p('2','td_b'), p('Earthworks'), p(fmt_fcfa(recap_fourn.get('lot2',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot2',0)),'td_r'), p(fmt_fcfa(c_terr),'td_r'), p(f'{c_terr/total_ht*100:.1f}%','td_r')],
        [p('3','td_b'), p('Foundations'), p(fmt_fcfa(recap_fourn.get('lot3',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot3',0)),'td_r'), p(fmt_fcfa(c_fond),'td_r'), p(f'{c_fond/total_ht*100:.1f}%','td_r')],
        [p('4','td_b'), p('RC Structure (columns + beams + slabs + stairs)'), p(fmt_fcfa(recap_fourn.get('lot4',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot4',0)),'td_r'), p(fmt_fcfa(c_pot_total+c_pout_total+c_dalle_total_full+c_esc),'td_r'), p(f'{(c_pot_total+c_pout_total+c_dalle_total_full+c_esc)/total_ht*100:.1f}%','td_r')],
        [p('5','td_b'), p('Masonry and Partitions'), p(fmt_fcfa(recap_fourn.get('lot5',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot5',0)),'td_r'), p(fmt_fcfa(c_maco_total),'td_r'), p(f'{c_maco_total/total_ht*100:.1f}%','td_r')],
        [p('6','td_b'), p('Waterproofing and Insulation'), p(fmt_fcfa(recap_fourn.get('lot6',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot6',0)),'td_r'), p(fmt_fcfa(c_etanch_total),'td_r'), p(f'{c_etanch_total/total_ht*100:.1f}%','td_r')],
        [p('7','td_b'), p('Miscellaneous + Engineering Fees'), p(fmt_fcfa(recap_fourn.get('lot7',0)),'td_r'), p(fmt_fcfa(recap_pose.get('lot7',0)),'td_r'), p(fmt_fcfa(c_div_total),'td_r'), p(f'{c_div_total/total_ht*100:.1f}%','td_r')],
    ]
    recap_rows.append([p('','td_b'), p('ESTIMATED TOTAL HT','td_b'), p(fmt_fcfa(total_fourn),'td_g_r'), p(fmt_fcfa(total_pose),'td_g_r'), p(fmt_fcfa(total_ht),'td_g_r'), p('100%','td_b')])
    recap_rows.append([p('','td_b'), p('LOW ESTIMATE (-5%)','td_b'), p('','td_r'), p('','td_r'), p(fmt_fcfa(total_bas),'td_g_r'), p('','td_b')])
    recap_rows.append([p('','td_b'), p('HIGH ESTIMATE (+15%)','td_b'), p('','td_r'), p('','td_r'), p(fmt_fcfa(total_haut),'td_g_r'), p('','td_b')])

    CW_RECAP = [CW*w for w in [0.06, 0.34, 0.16, 0.16, 0.18, 0.10]]
    tr = Table(recap_rows, colWidths=CW_RECAP, repeatRows=1)
    ts_r = table_style(zebra=False)
    ts_r.add('BACKGROUND', (0,-3), (-1,-1), VERT_LIGHT)
    ts_r.add('FONTNAME',   (0,-3), (-1,-1), 'Helvetica-Bold')
    ts_r.add('LINEABOVE',  (0,-3), (-1,-3), 1.5, VERT)
    tr.setStyle(ts_r)
    story.append(tr)

    # Cost ratios
    story.append(Spacer(1, 3*mm))
    rat_data = [
        [p('INDICATOR','th'), p('VALUE','th'), p('MARKET REFERENCE','th')],
        [p('Total built area','td_b'), p(f'{fmt_n(surf_batie,0)} m²'), p(f'Footprint {int(d.surface_emprise_m2)} m² × {d.nb_niveaux} levels')],
        [p('Total cost / m² built','td_b'), p(f'{int(total_ht/surf_batie):,} FCFA/m²'.replace(',', ' ')), p('Residential Dakar: 80 000–160 000 FCFA/m²')],
        [p('Materials / Installation ratio','td_b'), p(f'{total_fourn/total_ht*100:.0f}% / {total_pose/total_ht*100:.0f}%'), p('Reference: 55% materials / 45% installation')],
        [p('Foundations / total structure','td_b'), p(f'{c_fond/total_ht*100:.1f}%'), p('Normal: 15–25% (deep foundations)')],
        [p('Steel ratio','td_b'), p(f'{int(boq.acier_kg/surf_batie)} kg/m²'), p('EDGE reference: 40 kg/m²')],
    ]
    tr2 = Table(rat_data, colWidths=[CW*0.35, CW*0.25, CW*0.40], repeatRows=1)
    tr2.setStyle(table_style())
    story.append(tr2)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '* This BOQ is a pre-project estimate (±15%). Quantities are calculated from '
        'EC2/EC8 dimensioning and ratios validated for local market. '
        'A detailed take-off from execution drawings is required before tender.',
        S['disc']))

    return story

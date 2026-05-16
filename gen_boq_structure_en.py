"""
gen_boq_structure_en.py — English Structural BOQ
Format BPU: No. | Description | Unit | Qty | Unit Price | Amount | Notes
Complete translation of gen_boq_structure.py with identical structure and calculations.
"""
import io, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                  Spacer, PageBreak, KeepTogether)
from tijan_theme import *


def generer_boq_structure(rs, params: dict, lang: str = "en") -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rs.params.nom, 'BOQ Structure — Detailed')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    doc.build(_build(rs), onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _pu(montant, qte):
    """Compute unit price from total and quantity."""
    return int(montant / qte) if qte and qte > 0 else 0


def _row(lot, desig, unite, qte, pu, montant, note='', bold=False):
    st = 'td_b' if bold else 'td'
    st_r = 'td_b_r' if bold else 'td_r'
    st_g = 'td_g_r' if bold else 'td_r'
    return [p(lot, st), p(desig, st),
            p(unite, st),
            p(str(qte) if qte != '' else '—', st_r),
            p(fmt_fcfa(pu) if pu else '—', st_r),
            p(fmt_fcfa(montant) if montant else '—', st_g),
            p(note, 'small')]

def _sous_total(desig, total):
    return [p(''), p(desig, 'td_b'), p(''), p(''),
            p('', 'td_r'),
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
        f'Bill of Quantities and Unit Prices — Structure — {d.ville} {rs.params.pays}',
        S['sous_titre']))
    story.append(Paragraph(
        f'R+{d.nb_niveaux-1} — {d.usage.value.capitalize()} — '
        f'Built area: {fmt_n(surf_batie,0,"m²")} — '
        f'Concrete {rs.classe_beton} — Steel {rs.classe_acier}',
        S['body']))
    story.append(Paragraph(
        'Unit prices local market 2026. Margin ±15%. '
        'Document suitable for contractor tender.',
        S['note']))
    story.append(Spacer(1, 3*mm))

    # BPU Columns — 7 columns
    CW_COLS = [CW*w for w in [0.05, 0.30, 0.06, 0.07, 0.14, 0.15, 0.23]]
    dl = devise_label()
    HEADERS = [p(h,'th') for h in [
        'No.', 'Description', 'Unit', 'Qty',
        f'Unit Price ({dl})', f'Amount ({dl})', 'Notes']]

    def make_table(rows):
        t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
        ts = table_style()
        t.setStyle(ts)
        return t

    # Tracking totals per lot for recap
    recap = {}

    # ══════════════════════════════════════════════════════════
    # LOT 1 — SITE INSTALLATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 1', 'SITE INSTALLATION AND MANAGEMENT')

    q_cloture = int(4*math.sqrt(d.surface_emprise_m2))
    m_cloture = int(q_cloture*15000)
    m_base = int(surf_batie*800)
    m_branch = int(surf_batie*500)
    m_secu = int(surf_batie*300)
    m_repli = int(surf_batie*600)
    inst_forfait = m_cloture + m_base + m_branch + m_secu + m_repli

    rows_inst = [
        _row('1.1', 'Site fence (wood palisade or corrugated metal)', 'lm', q_cloture, 15000, m_cloture),
        _row('1.2', 'Site office, changing rooms, sanitary facilities', 'lump sum', 1, m_base, m_base, 'Modular removable'),
        _row('1.3', 'Provisional water + electricity connections', 'lump sum', 1, m_branch, m_branch),
        _row('1.4', 'Safety signage + PPE supply', 'lump sum', 1, m_secu, m_secu),
        _row('1.5', 'Site decommissioning and cleanup', 'lump sum', 1, m_repli, m_repli),
        _sous_total('SUBTOTAL LOT 1', inst_forfait),
    ]
    story.append(make_table(rows_inst))
    recap['lot1'] = inst_forfait

    # ══════════════════════════════════════════════════════════
    # LOT 2 — EARTHWORKS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 2', 'EARTHWORKS — GENERAL')
    V_decap = d.surface_emprise_m2 * 0.30
    V_fouilles = d.surface_emprise_m2 * (fond.profondeur_m + 0.50)
    V_remblai  = V_fouilles * 0.30
    V_evacu    = V_fouilles * 0.70
    V_sable    = d.surface_emprise_m2 * 0.10

    m_decap = int(V_decap*px.terr_mecanique_m3)
    m_fouilles = int(V_fouilles*px.terr_mecanique_m3)
    q_fouilles_man = int(V_fouilles*0.10)
    m_fouilles_man = int(q_fouilles_man*px.terr_manuel_m3)
    m_remblai = int(V_remblai*px.remblai_m3)
    m_evacu = int(V_evacu*5000)
    m_sable = int(V_sable*12000)
    c_terr = m_decap + m_fouilles + m_fouilles_man + m_remblai + m_evacu + m_sable

    rows_terr = [
        _row('2.1', 'Topsoil stripping e=30cm', 'm³', int(V_decap), px.terr_mecanique_m3, m_decap),
        _row('2.2', 'Mechanical excavation general', 'm³', int(V_fouilles), px.terr_mecanique_m3, m_fouilles, 'Mechanical equipment'),
        _row('2.3', 'Manual excavation at bottom of holes', 'm³', q_fouilles_man, px.terr_manuel_m3, m_fouilles_man, 'Manual finishing'),
        _row('2.4', 'Compacted backfill (selected material)', 'm³', int(V_remblai), px.remblai_m3, m_remblai),
        _row('2.5', 'Excess soil disposal', 'm³', int(V_evacu), 5000, m_evacu, 'Transport + authorized dumping'),
        _row('2.6', 'Sand bed under flooring e=10cm', 'm³', int(V_sable), 12000, m_sable),
        _sous_total('SUBTOTAL LOT 2', c_terr),
    ]
    story.append(make_table(rows_terr))
    recap['lot2'] = c_terr

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

    if fond.nb_pieux > 0:
        prix_pieu = {600: px.pieu_fore_d600_ml, 800: px.pieu_fore_d800_ml,
                     1000: px.pieu_fore_d1000_ml}.get(fond.diam_pieu_mm, px.pieu_fore_d800_ml)
        kg_fond_acier = fond.nb_pieux * fond.As_cm2/10000 * 7850 * fond.longueur_pieu_m
        q_pieux_ml = int(fond.nb_pieux * fond.longueur_pieu_m)
        c_pieux = int(q_pieux_ml * prix_pieu)
        q_longr = int(nb_pot * 6)
        c_longr = int(q_longr * 85000)
        m_acier_fond = int(kg_fond_acier*prix_acier)
        q_proprete = int(nb_pot*0.5*0.5*0.10)
        m_proprete = int(q_proprete*120000) if q_proprete > 0 else int(nb_pot*0.5*0.5*0.10*120000)
        m_tete = int(nb_pot*120000)
        c_fond = c_pieux + c_longr + m_acier_fond + m_proprete + m_tete

        rows_fond = [
            _row('3.1', f'RC bored piles Ø{fond.diam_pieu_mm}mm — L={fond.longueur_pieu_m}m', 'lm', q_pieux_ml, prix_pieu, c_pieux, f'{fond.nb_pieux} piles × {fond.longueur_pieu_m}m'),
            _row('3.2', f'Pile reinforcement HA500B — cage Ø{fond.diam_pieu_mm}mm', 'kg', int(kg_fond_acier), prix_acier, m_acier_fond, f'As={fond.As_cm2}cm² per pile'),
            _row('3.3', f'Blinding concrete e=10cm under tie beams', 'm³', max(1, q_proprete), _pu(m_proprete, max(1, q_proprete)), m_proprete),
            _row('3.4', f'RC tie beams {rs.classe_beton} — 30×50cm section', 'lm', q_longr, 85000, c_longr, 'Links between piles'),
            _row('3.5', 'Pile heads + RC capitals', 'ea', nb_pot, 120000, m_tete, 'Pile-structure connection'),
            _sous_total('SUBTOTAL LOT 3', c_fond),
        ]
        story.append(Paragraph(
            f'Foundations represent {c_fond/boq.total_bas_fcfa*100:.0f}% of structure budget — '
            f'critical item requiring prior geotechnical study.',
            S['note']))
    elif fond.beton_semelle_m3 > 0:
        q_proprete2 = int(d.surface_emprise_m2*0.10)
        m_proprete2 = int(q_proprete2*120000) if q_proprete2 > 0 else int(d.surface_emprise_m2*0.10*120000)
        q_sem_bet = int(fond.beton_semelle_m3*0.6)
        m_semelle_bet = int(q_sem_bet*prix_beton) if q_sem_bet > 0 else int(fond.beton_semelle_m3*0.6*prix_beton)
        q_sem_acier = int(fond.beton_semelle_m3*100)
        m_semelle_acier = int(q_sem_acier*prix_acier)
        q_sem_coff = int(fond.beton_semelle_m3*2)
        m_semelle_coff = int(q_sem_coff*px.coffrage_bois_m2) if q_sem_coff > 0 else int(fond.beton_semelle_m3*2*px.coffrage_bois_m2)
        c_fond = m_proprete2 + m_semelle_bet + m_semelle_acier + m_semelle_coff

        rows_fond = [
            _row('3.1', 'Blinding concrete e=10cm', 'm³', max(1, q_proprete2), _pu(m_proprete2, max(1, q_proprete2)), m_proprete2),
            _row('3.2', f'RC footings {rs.classe_beton}', 'm³', max(1, q_sem_bet), prix_beton, m_semelle_bet),
            _row('3.3', f'Footing reinforcement {rs.classe_acier}', 'kg', q_sem_acier, prix_acier, m_semelle_acier),
            _row('3.4', 'Footing formwork (lost forms)', 'm²', max(1, q_sem_coff), px.coffrage_bois_m2, m_semelle_coff),
            _sous_total('SUBTOTAL LOT 3', c_fond),
        ]

    story.append(make_table(rows_fond))
    recap['lot3'] = c_fond

    # ══════════════════════════════════════════════════════════
    # LOT 4 — REINFORCED CONCRETE STRUCTURE
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 4', f'REINFORCED CONCRETE STRUCTURE — {rs.classe_beton} / {rs.classe_acier}')

    # 4.1 Columns by level
    story.append(Paragraph('4.1 — Columns', S['h2']))
    rows_pot = [HEADERS]
    c_pot_total = 0
    for i, pt in enumerate(poteaux):
        b = pt.section_mm / 1000
        V_niv = b**2 * d.hauteur_etage_m * nb_pot
        As_niv = pt.nb_barres * math.pi * pt.diametre_mm**2 / 400 * nb_pot * d.hauteur_etage_m * 7850 / 10000
        c_beton_niv = int(V_niv * prix_beton)
        c_acier_niv = int(As_niv * prix_acier)
        c_coff_niv  = int(4 * b * d.hauteur_etage_m * nb_pot * px.coffrage_bois_m2)
        c_pot_niv   = c_beton_niv + c_acier_niv + c_coff_niv
        pu_pot_niv  = _pu(c_pot_niv, nb_pot)

        c_pot_total += c_pot_niv
        rows_pot.append([
            p(f'4.1.{i+1}'),
            p(f'Columns {pt.niveau} — {pt.section_mm}×{pt.section_mm}mm — {pt.nb_barres}HA{pt.diametre_mm}'),
            p('ea'),
            p(f'{nb_pot}', 'td_r'),
            p(fmt_fcfa(pu_pot_niv), 'td_r'),
            p(fmt_fcfa(c_pot_niv), 'td_r'),
            p(f'NEd={pt.NEd_kN:.0f}kN | ρ={pt.taux_armature_pct:.1f}%', 'small'),
        ])
    rows_pot.append(_sous_total('Subtotal columns', c_pot_total))

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
    q_pout_coff = int((L_px+L_py)*(b_p+2*(h_p-ep_dalle_m))*0.6)
    c_pout_coff  = int(q_pout_coff * px.coffrage_bois_m2) if q_pout_coff > 0 else int((L_px+L_py) * (b_p + 2*(h_p-ep_dalle_m)) * px.coffrage_bois_m2 * 0.6)
    c_pout_total = c_pout_beton + c_pout_acier + c_pout_coff

    m_pout_princ = int(c_pout_beton*L_px/(L_px+L_py)) if (L_px+L_py) > 0 else 0
    m_pout_sec = c_pout_beton - m_pout_princ

    rows_pout = [
        HEADERS,
        _row('4.2.1', f'Main beams {poutre.b_mm}×{poutre.h_mm}mm — max span {d.portee_max_m}m', 'lm', int(L_px), _pu(m_pout_princ, int(L_px)), m_pout_princ, f'As bottom={poutre.As_inf_cm2}cm² / As top={poutre.As_sup_cm2}cm²'),
        _row('4.2.2', f'Secondary beams {poutre.b_mm}×{poutre.h_mm}mm — min span {d.portee_min_m}m', 'lm', int(L_py), _pu(m_pout_sec, int(L_py)), m_pout_sec),
        _row('4.2.3', f'Beam reinforcement {rs.classe_acier} (shaped + placed)', 'kg', int(kg_pout), prix_acier, c_pout_acier, f'Stirrups HA{poutre.etrier_diam_mm} e={poutre.etrier_esp_mm}mm'),
        _row('4.2.4', 'Beam formwork (wood + props)', 'm²', q_pout_coff, _pu(c_pout_coff, q_pout_coff), c_pout_coff),
        _sous_total('Subtotal beams', c_pout_total),
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
    q_dalle_coff = int(surf_batie * 0.85)
    c_dalle_coff  = int(q_dalle_coff * px.coffrage_bois_m2)
    m_etai = int(q_dalle_coff*3500)
    m_reserv = int(surf_batie*500)
    c_dalle_total = c_dalle_beton + c_dalle_acier + c_dalle_coff + m_etai + m_reserv

    rows_dalles = [
        HEADERS,
        _row('4.3.1', f'RC slab concrete {rs.classe_beton} BPE e={dalle.epaisseur_mm}mm', 'm³', int(V_dalles), prix_beton, c_dalle_beton, f'As_x={dalle.As_x_cm2_ml}cm²/lm / As_y={dalle.As_y_cm2_ml}cm²/lm'),
        _row('4.3.2', f'Slab reinforcement {rs.classe_acier} — HA10 both directions', 'kg', int(kg_dalles), prix_acier, c_dalle_acier, 'Welded mesh + reinforcement'),
        _row('4.3.3', 'Slab formwork (metal plates)', 'm²', q_dalle_coff, px.coffrage_bois_m2, c_dalle_coff),
        _row('4.3.4', 'Temporary shoring (scaffolding)', 'm²', q_dalle_coff, 3500, m_etai, 'Rental + labor'),
        _row('4.3.5', 'Openings and chases (shafts, stairs)', 'lump sum', 1, m_reserv, m_reserv, 'Estimate 0.5% of built area'),
        _sous_total('Subtotal slabs', c_dalle_total),
    ]
    t_dalles = Table(rows_dalles, colWidths=CW_COLS, repeatRows=1)
    t_dalles.setStyle(table_style())
    story.append(t_dalles)

    # 4.4 Stairs
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.4 — Stairs', S['h2']))
    nb_esc = max(1, int(surf_batie/1500))
    q_esc = nb_esc * d.nb_niveaux
    c_esc = int(q_esc * 450000)
    q_garde = nb_esc * d.nb_niveaux * 3
    m_garde = int(q_garde*45000)
    c_esc_total = c_esc + m_garde

    rows_esc = [
        HEADERS,
        _row('4.4.1', f'RC stairs {rs.classe_beton} — flights + landings', 'flight', q_esc, 450000, c_esc, f'{nb_esc} staircase(s) × {d.nb_niveaux} levels'),
        _row('4.4.2', 'Stair handrail (RC/metal)', 'lm', q_garde, 45000, m_garde),
        _sous_total('Subtotal stairs', c_esc_total),
    ]
    t_esc = Table(rows_esc, colWidths=CW_COLS, repeatRows=1)
    t_esc.setStyle(table_style())
    story.append(t_esc)

    # Lot 4 total
    c_lot4 = c_pot_total + c_pout_total + c_dalle_total + c_esc_total
    recap['lot4'] = c_lot4

    # ══════════════════════════════════════════════════════════
    # LOT 5 — MASONRY AND PARTITIONS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 5', 'MASONRY, PARTITIONS AND FINISHES')
    cl = rs.cloisons
    opt_rec = next((o for o in cl.options if o.type == cl.option_recommandee), cl.options[0])

    rows_maco = [HEADERS]
    c_maco_total = 0

    # Exterior facades
    surf_facades = 4 * math.sqrt(d.surface_emprise_m2) * d.nb_niveaux * d.hauteur_etage_m * 0.70
    q_fac = int(surf_facades)
    c_fac = int(q_fac * px.agglo_plein_25_m2)
    rows_maco.append(_row('5.1', 'Exterior facade masonry — solid blocks 25cm',
        'm²', q_fac, px.agglo_plein_25_m2, c_fac, 'Perimeter walls finished 2 sides'))
    c_maco_total += c_fac

    # Separative partitions
    q_sep = int(cl.surface_separative_m2)
    c_sep = int(q_sep * opt_rec.prix_fcfa_m2)
    rows_maco.append(_row('5.2', f'Separative partitions — {opt_rec.materiau[:40]}',
        'm²', q_sep, opt_rec.prix_fcfa_m2, c_sep,
        f'Recommended option — {opt_rec.usage_recommande[:35]}'))
    c_maco_total += c_sep

    # Light interior partitions
    q_leg = int(cl.surface_legere_m2)
    c_leg = int(q_leg * px.ba13_simple_m2)
    rows_maco.append(_row('5.3', 'Light interior partitions — simple BA13 rail',
        'm²', q_leg, px.ba13_simple_m2, c_leg, 'Non-separative interior partitions'))
    c_maco_total += c_leg

    # Technical shafts
    q_gaines = int(cl.surface_gaines_m2)
    pu_gaines = int(px.beton_c3037_m3 * 0.20)
    c_gaines = int(q_gaines * pu_gaines)
    rows_maco.append(_row('5.4', 'Technical shafts — cast RC 20cm',
        'm²', q_gaines, pu_gaines, c_gaines,
        'Lift shafts + riser columns'))
    c_maco_total += c_gaines

    # Renders
    surf_enduit = int((surf_facades + cl.surface_separative_m2) * 2)
    c_end = int(surf_enduit * 8500)
    rows_maco.append(_row('5.5', 'Cement + plaster finishes interior/exterior',
        'm²', surf_enduit, 8500, c_end, 'Finishing of masonry surfaces'))
    c_maco_total += c_end

    # Parapets
    perim = int(4 * math.sqrt(d.surface_emprise_m2))
    c_acrot = int(perim * 35000)
    rows_maco.append(_row('5.6', 'RC parapets h=60cm on roof',
        'lm', perim, 35000, c_acrot))
    c_maco_total += c_acrot

    rows_maco.append(_sous_total('SUBTOTAL LOT 5', c_maco_total))

    story.append(Paragraph(
        'Several partition options available based on budget and use. '
        'See structure calculation note for detailed comparison.',
        S['note']))
    t_maco = Table(rows_maco, colWidths=CW_COLS, repeatRows=1)
    t_maco.setStyle(table_style())
    story.append(t_maco)
    recap['lot5'] = c_maco_total

    # ══════════════════════════════════════════════════════════
    # LOT 6 — WATERPROOFING AND INSULATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 6', 'WATERPROOFING AND INSULATION')
    surf_etanch = int(d.surface_emprise_m2)
    c_sbs  = int(surf_etanch * px.etanch_sbs_m2)
    c_prot = int(surf_etanch * 5000)
    q_dallettes = int(surf_etanch * 0.40)
    c_dallettes = int(q_dallettes * 8000)
    c_ss_sol = int(d.surface_emprise_m2 * 0.30 * px.etanch_pvc_m2) if d.avec_sous_sol else 0
    q_salles = int(surf_batie * 0.08)
    c_salles = int(q_salles * px.etanch_liquide_m2)
    c_etanch_total = c_sbs + c_prot + c_dallettes + c_salles + c_ss_sol

    rows_etanch = [
        HEADERS,
        _row('6.1', 'Flat roof waterproofing SBS bitumen (primer + 2 coats)', 'm²', surf_etanch, px.etanch_sbs_m2, c_sbs, 'Torch applied — DTU 43.1'),
        _row('6.2', 'Waterproofing protection — 5cm protection screed', 'm²', surf_etanch, 5000, c_prot),
        _row('6.3', 'Concrete tiles on supports (accessible roof)', 'm²', q_dallettes, 8000, c_dallettes, '40% accessible roof'),
        _row('6.4', 'Wet room waterproofing (bathrooms, kitchens)', 'm²', q_salles, px.etanch_liquide_m2, c_salles, 'Single component resin'),
    ]
    if d.avec_sous_sol:
        q_ss = int(d.surface_emprise_m2)
        rows_etanch.append(_row('6.5', 'Basement waterproofing (PVC membrane)', 'm²', q_ss, int(px.etanch_pvc_m2*0.30), c_ss_sol, 'Internal tanking'))
    rows_etanch.append(_sous_total('SUBTOTAL LOT 6', c_etanch_total))

    t_etanch = Table(rows_etanch, colWidths=CW_COLS, repeatRows=1)
    t_etanch.setStyle(table_style())
    story.append(t_etanch)
    recap['lot6'] = c_etanch_total

    # ══════════════════════════════════════════════════════════
    # LOT 7 — MISCELLANEOUS AND CONTINGENCIES
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 7', 'MISCELLANEOUS, CONTINGENCIES AND ENGINEERING FEES')
    sous_tot_travaux = (inst_forfait + c_terr + c_fond + c_lot4 +
                        c_maco_total + c_etanch_total)
    q_joints = int(surf_batie/500)
    m_joints = int(q_joints*850000) if q_joints > 0 else int(surf_batie/500*850000)
    m_reserv7 = int(surf_batie*800)
    c_impr  = int(sous_tot_travaux * 0.05)
    c_bet   = int(sous_tot_travaux * 0.04)
    c_ctrl  = int(sous_tot_travaux * 0.015)
    c_div_total = m_joints + m_reserv7 + c_impr + c_bet + c_ctrl

    rows_div = [
        HEADERS,
        _row('7.1', 'Expansion joints (all levels)', 'ea', max(1, q_joints), _pu(m_joints, max(1, q_joints)), m_joints, '1 joint per 500m² approx.'),
        _row('7.2', 'Miscellaneous reservations and sealants', 'lump sum', 1, m_reserv7, m_reserv7, 'Electrical and plumbing sleeves'),
        _row('7.3', 'Site contingencies (5% works)', 'lump sum', 1, c_impr, c_impr, 'Variations and adaptations'),
        _row('7.4', 'Engineer design fees (4% works)', 'lump sum', 1, c_bet, c_bet, 'Execution plans + supervision'),
        _row('7.5', 'Technical inspection (1.5% works)', 'lump sum', 1, c_ctrl, c_ctrl, 'Approved body required'),
        _sous_total('SUBTOTAL LOT 7', c_div_total),
    ]

    t_div = Table(rows_div, colWidths=CW_COLS, repeatRows=1)
    t_div.setStyle(table_style())
    story.append(t_div)
    recap['lot7'] = c_div_total

    # ══════════════════════════════════════════════════════════
    # GENERAL SUMMARY
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('RECAP', 'GENERAL SUMMARY')

    total_ht  = sum(recap.values())
    total_bas = int(total_ht * 0.95)
    total_haut = int(total_ht * 1.15)

    recap_rows = [
        [p('LOT','th'), p('DESCRIPTION','th_l'),
         p(f'AMOUNT ({dl})','th'), p('% TOTAL','th')],
    ]
    lot_labels = [
        ('1', 'Site Installation', recap.get('lot1', 0)),
        ('2', 'Earthworks', recap.get('lot2', 0)),
        ('3', 'Foundations', recap.get('lot3', 0)),
        ('4', 'RC Structure (columns + beams + slabs + stairs)', recap.get('lot4', 0)),
        ('5', 'Masonry and Partitions', recap.get('lot5', 0)),
        ('6', 'Waterproofing and Insulation', recap.get('lot6', 0)),
        ('7', 'Miscellaneous + Engineering Fees', recap.get('lot7', 0)),
    ]
    for num, desig, total_lot in lot_labels:
        recap_rows.append([
            p(num, 'td_b'), p(desig),
            p(fmt_fcfa(total_lot), 'td_r'),
            p(f'{total_lot/total_ht*100:.1f}%', 'td_r'),
        ])

    recap_rows.append([p('','td_b'), p('ESTIMATED TOTAL HT','td_b'),
                       p(fmt_fcfa(total_ht),'td_g_r'), p('100%','td_b')])
    recap_rows.append([p('','td_b'), p('LOW ESTIMATE (-5%)','td_b'),
                       p(fmt_fcfa(total_bas),'td_g_r'), p('','td_b')])
    recap_rows.append([p('','td_b'), p('HIGH ESTIMATE (+15%)','td_b'),
                       p(fmt_fcfa(total_haut),'td_g_r'), p('','td_b')])

    tr = Table(recap_rows, colWidths=[CW*0.08, CW*0.52, CW*0.28, CW*0.12], repeatRows=1)
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
        [p('RC cost / m² built','td_b'), p(f'{int(c_lot4/surf_batie):,} FCFA/m²'.replace(',', ' ')), p('Concrete + steel + formwork ratio')],
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

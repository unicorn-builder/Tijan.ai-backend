"""
gen_boq_structure_en.py — English Structural BOQ
Complete translation of gen_boq_structure.py with identical structure, layout, and calculations.
Uses tijan_theme.py for consistent PDF design.
Signature: generer_boq_structure(rs, params_dict) → bytes
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


def _row(lot, desig, qte, unite, pu, montant, note='', bold=False):
    st = 'td_b' if bold else 'td'
    st_r = 'td_b_r' if bold else 'td_r'
    st_g = 'td_g_r' if bold else 'td_r'
    return [p(lot, st), p(desig, st), p(str(qte) if qte != '' else '—', st_r),
            p(unite, st), p(fmt_n(pu) if pu else '—', st_r),
            p(fmt_fcfa(montant) if montant else '—', st_g),
            p(note, 'small')]

def _sous_total(desig, montant):
    return [p(''), p(desig, 'td_b'), p(''), p(''), p(''),
            p(fmt_fcfa(montant), 'td_g_r'), p('')]

def _build(rs):
    story = []
    d = rs.params
    boq = rs.boq
    poteaux = rs.poteaux
    poutre = rs.poutre_principale
    dalle = rs.dalle
    fond = rs.fondation
    cl = rs.cloisons

    # Tenter import prix
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
        'Unit prices local market 2026 (supply and install). Margin ±15%. '
        'Document suitable for contractor tender.',
        S['note']))
    story.append(Spacer(1, 3*mm))

    # BOQ Columns
    CW_COLS = [CW*w for w in [0.05, 0.36, 0.07, 0.06, 0.12, 0.14, 0.20]]
    HEADERS = [p(h,'th') for h in ['Lot','Description','Qty','Unit',f"U.P. ({devise_label()})",f"Amount ({devise_label()})",'Notes']]

    def make_table(rows):
        t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
        ts = table_style()
        t.setStyle(ts)
        return t

    # ══════════════════════════════════════════════════════════
    # LOT 1 — SITE INSTALLATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 1', 'SITE INSTALLATION AND MANAGEMENT')
    inst_forfait = int(surf_batie * 2500)
    rows_inst = [
        _row('1.1', 'Site fence (wood palisade or corrugated metal)', int(4*math.sqrt(d.surface_emprise_m2)), 'lm', 15000, int(4*math.sqrt(d.surface_emprise_m2)*15000)),
        _row('1.2', 'Site office, changing rooms, sanitary facilities', 1, 'lump sum', 0, int(surf_batie*800), 'Modular removable'),
        _row('1.3', 'Provisional water + electricity connections', 1, 'lump sum', 0, int(surf_batie*500)),
        _row('1.4', 'Safety signage + PPE supply', 1, 'lump sum', 0, int(surf_batie*300)),
        _row('1.5', 'Site decommissioning and cleanup', 1, 'lump sum', 0, int(surf_batie*600)),
        _sous_total('SUBTOTAL LOT 1', inst_forfait),
    ]
    story.append(make_table(rows_inst))

    # ══════════════════════════════════════════════════════════
    # LOT 2 — EARTHWORKS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 2', 'EARTHWORKS — GENERAL')
    V_decap = d.surface_emprise_m2 * 0.30
    V_fouilles = d.surface_emprise_m2 * (fond.profondeur_m + 0.50)
    V_remblai  = V_fouilles * 0.30
    V_evacu    = V_fouilles * 0.70
    c_terr = int(V_decap*px.terr_mecanique_m3 + V_fouilles*px.terr_mecanique_m3 +
                  V_remblai*px.remblai_m3 + V_evacu*5000)
    rows_terr = [
        _row('2.1', 'Topsoil stripping e=30cm', int(V_decap), 'm³', px.terr_mecanique_m3, int(V_decap*px.terr_mecanique_m3)),
        _row('2.2', 'Mechanical excavation general', int(V_fouilles), 'm³', px.terr_mecanique_m3, int(V_fouilles*px.terr_mecanique_m3), 'Mechanical equipment'),
        _row('2.3', 'Manual excavation at bottom of holes', int(V_fouilles*0.10), 'm³', px.terr_manuel_m3, int(V_fouilles*0.10*px.terr_manuel_m3), 'Manual finishing'),
        _row('2.4', 'Compacted backfill (selected material)', int(V_remblai), 'm³', px.remblai_m3, int(V_remblai*px.remblai_m3)),
        _row('2.5', 'Excess soil disposal', int(V_evacu), 'm³', 5000, int(V_evacu*5000), 'Transport + authorized dumping'),
        _row('2.6', 'Sand bed under flooring e=10cm', int(d.surface_emprise_m2*0.10), 'm³', 12000, int(d.surface_emprise_m2*0.10*12000)),
        _sous_total('SUBTOTAL LOT 2', c_terr),
    ]
    story.append(make_table(rows_terr))

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
        V_fond_beton = fond.nb_pieux * math.pi*(fond.diam_pieu_mm/1000/2)**2 * fond.longueur_pieu_m
        kg_fond_acier = fond.nb_pieux * fond.As_cm2/10000 * 7850 * fond.longueur_pieu_m
        c_pieux = int(fond.nb_pieux * fond.longueur_pieu_m * prix_pieu)
        c_longr = int(nb_pot * 6 * 85000)  # tie beams
        c_fond  = c_pieux + c_longr
        rows_fond = [
            _row('3.1', f'RC bored piles Ø{fond.diam_pieu_mm}mm — L={fond.longueur_pieu_m}m', int(fond.nb_pieux * fond.longueur_pieu_m), 'lm', prix_pieu, c_pieux, f'{fond.nb_pieux} piles × {fond.longueur_pieu_m}m'),
            _row('3.2', f'Pile reinforcement HA500B — cage Ø{fond.diam_pieu_mm}mm', int(kg_fond_acier), 'kg', prix_acier, int(kg_fond_acier*prix_acier), f'As={fond.As_cm2}cm² per pile'),
            _row('3.3', f'Blinding concrete e=10cm under tie beams', int(nb_pot*0.5*0.5*0.10), 'm³', 120000, int(nb_pot*0.5*0.5*0.10*120000)),
            _row('3.4', f'RC tie beams {rs.classe_beton} — 30×50cm section', int(nb_pot * 6), 'lm', 85000, c_longr, 'Links between piles'),
            _row('3.5', 'Pile heads + RC capitals', nb_pot, 'ea', 120000, int(nb_pot*120000), 'Pile-structure connection'),
            _sous_total('SUBTOTAL LOT 3', c_fond),
        ]
        story.append(Paragraph(
            f'ℹ Foundations represent {c_fond/boq.total_bas_fcfa*100:.0f}% of structure budget — '
            f'critical item requiring prior geotechnical study.',
            S['note']))
    elif fond.beton_semelle_m3 > 0:
        c_fond = int(fond.beton_semelle_m3 * prix_beton * 1.6)
        rows_fond = [
            _row('3.1', 'Blinding concrete e=10cm', int(d.surface_emprise_m2*0.10), 'm³', 120000, int(d.surface_emprise_m2*0.10*120000)),
            _row('3.2', f'RC footings {rs.classe_beton}', int(fond.beton_semelle_m3*0.6), 'm³', prix_beton, int(fond.beton_semelle_m3*0.6*prix_beton)),
            _row('3.3', f'Footing reinforcement {rs.classe_acier}', int(fond.beton_semelle_m3*100), 'kg', prix_acier, int(fond.beton_semelle_m3*100*prix_acier)),
            _row('3.4', 'Footing formwork (lost forms)', int(fond.beton_semelle_m3*2), 'm²', px.coffrage_bois_m2, int(fond.beton_semelle_m3*2*px.coffrage_bois_m2)),
            _sous_total('SUBTOTAL LOT 3', c_fond),
        ]

    story.append(make_table(rows_fond))

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
        c_pot_total += c_pot_niv
        rows_pot.append([
            p(f'4.1.{i+1}'),
            p(f'Columns {pt.niveau} — {pt.section_mm}×{pt.section_mm}mm — {pt.nb_barres}HA{pt.diametre_mm}'),
            p(f'{nb_pot}', 'td_r'), p('ea'),
            p(fmt_n(c_pot_niv//nb_pot), 'td_r'),
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
    c_pout_coff  = int((L_px+L_py) * (b_p + 2*(h_p-ep_dalle_m)) * px.coffrage_bois_m2 * 0.6)
    c_pout_total = c_pout_beton + c_pout_acier + c_pout_coff
    rows_pout = [
        HEADERS,
        _row('4.2.1', f'Main beams {poutre.b_mm}×{poutre.h_mm}mm — max span {d.portee_max_m}m', int(L_px), 'lm', int(c_pout_beton//(L_px+1)), int(c_pout_beton*L_px/(L_px+L_py)), f'As bottom={poutre.As_inf_cm2}cm² / As top={poutre.As_sup_cm2}cm²'),
        _row('4.2.2', f'Secondary beams {poutre.b_mm}×{poutre.h_mm}mm — min span {d.portee_min_m}m', int(L_py), 'lm', int(c_pout_beton//(L_py+1)), int(c_pout_beton*L_py/(L_px+L_py))),
        _row('4.2.3', f'Beam reinforcement {rs.classe_acier} (shaped + placed)', int(kg_pout), 'kg', prix_acier, c_pout_acier, f'Stirrups HA{poutre.etrier_diam_mm} e={poutre.etrier_esp_mm}mm'),
        _row('4.2.4', 'Beam formwork (wood + props)', int((L_px+L_py)*(b_p+2*(h_p-ep_dalle_m))*0.6), 'm²', px.coffrage_bois_m2, c_pout_coff),
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
    c_dalle_coff  = int(surf_batie * 0.85 * px.coffrage_bois_m2)
    c_dalle_total = c_dalle_beton + c_dalle_acier + c_dalle_coff
    rows_dalles = [
        HEADERS,
        _row('4.3.1', f'RC slab concrete {rs.classe_beton} BPE e={dalle.epaisseur_mm}mm', int(V_dalles), 'm³', prix_beton, c_dalle_beton, f'As_x={dalle.As_x_cm2_ml}cm²/lm / As_y={dalle.As_y_cm2_ml}cm²/lm'),
        _row('4.3.2', f'Slab reinforcement {rs.classe_acier} — HA10 both directions', int(kg_dalles), 'kg', prix_acier, c_dalle_acier, 'Welded mesh + reinforcement'),
        _row('4.3.3', 'Slab formwork (metal plates)', int(surf_batie*0.85), 'm²', px.coffrage_bois_m2, c_dalle_coff),
        _row('4.3.4', 'Temporary shoring (scaffolding)', int(surf_batie*0.85), 'm²', 3500, int(surf_batie*0.85*3500), 'Rental + labor'),
        _row('4.3.5', 'Openings and chases (shafts, stairs)', 1, 'lump sum', 0, int(surf_batie*500), 'Estimate 0.5% of built area'),
        _sous_total('Subtotal slabs', c_dalle_total),
    ]
    t_dalles = Table(rows_dalles, colWidths=CW_COLS, repeatRows=1)
    t_dalles.setStyle(table_style())
    story.append(t_dalles)

    # 4.4 Stairs
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.4 — Stairs', S['h2']))
    nb_esc = max(1, int(surf_batie/1500))
    c_esc = int(nb_esc * d.nb_niveaux * 450000)
    rows_esc = [
        HEADERS,
        _row('4.4.1', f'RC stairs {rs.classe_beton} — flights + landings', nb_esc * d.nb_niveaux, 'flight', 450000, c_esc, f'{nb_esc} staircase(s) × {d.nb_niveaux} levels'),
        _row('4.4.2', 'Stair handrail (RC/metal)', nb_esc * d.nb_niveaux * 3, 'lm', 45000, int(nb_esc*d.nb_niveaux*3*45000)),
        _sous_total('Subtotal stairs', c_esc + int(nb_esc*d.nb_niveaux*3*45000)),
    ]
    t_esc = Table(rows_esc, colWidths=CW_COLS, repeatRows=1)
    t_esc.setStyle(table_style())
    story.append(t_esc)

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
    c_fac = int(surf_facades * px.agglo_plein_25_m2)
    rows_maco.append(_row('5.1', 'Exterior facade masonry — solid blocks 25cm',
        int(surf_facades), 'm²', px.agglo_plein_25_m2, c_fac, 'Perimeter walls finished 2 sides'))
    c_maco_total += c_fac

    # Separative partitions
    c_sep = int(cl.surface_separative_m2 * opt_rec.prix_fcfa_m2)
    rows_maco.append(_row('5.2', f'Separative partitions — {opt_rec.materiau[:40]}',
        int(cl.surface_separative_m2), 'm²', int(opt_rec.prix_fcfa_m2), c_sep,
        f'Recommended option — {opt_rec.usage_recommande[:35]}'))
    c_maco_total += c_sep

    # Light interior partitions
    prix_leger = px.ba13_simple_m2
    c_leg = int(cl.surface_legere_m2 * prix_leger)
    rows_maco.append(_row('5.3', 'Light interior partitions — simple BA13 rail',
        int(cl.surface_legere_m2), 'm²', prix_leger, c_leg, 'Non-separative interior partitions'))
    c_maco_total += c_leg

    # Technical shafts
    c_gaines = int(cl.surface_gaines_m2 * px.beton_c3037_m3 * 0.20)
    rows_maco.append(_row('5.4', 'Technical shafts — cast RC 20cm',
        int(cl.surface_gaines_m2), 'm²', int(px.beton_c3037_m3 * 0.20), c_gaines,
        'Lift shafts + riser columns'))
    c_maco_total += c_gaines

    # Renders/finishes
    surf_enduit = (surf_facades + cl.surface_separative_m2) * 2
    c_end = int(surf_enduit * 8500)
    rows_maco.append(_row('5.5', 'Cement + plaster finishes interior/exterior',
        int(surf_enduit), 'm²', 8500, c_end, 'Finishing of masonry surfaces'))
    c_maco_total += c_end

    # Parapets
    perim = 4 * math.sqrt(d.surface_emprise_m2)
    c_acrot = int(perim * 35000)
    rows_maco.append(_row('5.6', 'RC parapets h=60cm on roof',
        int(perim), 'lm', 35000, c_acrot))
    c_maco_total += c_acrot

    rows_maco.append(_sous_total('SUBTOTAL LOT 5', c_maco_total))

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
    c_dallettes = int(surf_etanch * 8000)
    c_ss_sol = int(d.surface_emprise_m2 * 0.30 * px.etanch_pvc_m2) if d.avec_sous_sol else 0
    c_salles = int(surf_batie * 0.08 * px.etanch_liquide_m2)
    c_etanch_total = c_sbs + c_prot + c_dallettes + c_ss_sol + c_salles

    rows_etanch = [
        HEADERS,
        _row('6.1', 'Flat roof waterproofing SBS bitumen (primer + 2 coats)', int(surf_etanch), 'm²', px.etanch_sbs_m2, c_sbs, 'Torch applied — DTU 43.1'),
        _row('6.2', 'Waterproofing protection — 5cm protection screed', int(surf_etanch), 'm²', 5000, c_prot),
        _row('6.3', 'Concrete tiles on supports (accessible roof)', int(surf_etanch*0.40), 'm²', 8000, int(surf_etanch*0.40*8000), '40% accessible roof'),
        _row('6.4', 'Wet room waterproofing (bathrooms, kitchens)', int(surf_batie*0.08), 'm²', px.etanch_liquide_m2, c_salles, 'Single component resin'),
    ]
    if d.avec_sous_sol:
        rows_etanch.append(_row('6.5', 'Basement waterproofing (PVC membrane)', int(d.surface_emprise_m2), 'm²', px.etanch_pvc_m2, c_ss_sol, 'Internal tanking'))
    rows_etanch.append(_sous_total('SUBTOTAL LOT 6', c_etanch_total))

    t_etanch = Table(rows_etanch, colWidths=CW_COLS, repeatRows=1)
    t_etanch.setStyle(table_style())
    story.append(t_etanch)

    # ══════════════════════════════════════════════════════════
    # LOT 7 — MISCELLANEOUS AND CONTINGENCIES
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 7', 'MISCELLANEOUS, CONTINGENCIES AND ENGINEERING FEES')
    sous_tot_travaux = (inst_forfait + c_terr + c_fond + c_pot_total +
                        c_pout_total + c_dalle_total + c_maco_total + c_etanch_total)
    c_impr  = int(sous_tot_travaux * 0.05)
    c_bet   = int(sous_tot_travaux * 0.04)
    c_ctrl  = int(sous_tot_travaux * 0.015)

    rows_div = [
        HEADERS,
        _row('7.1', 'Expansion joints (all levels)', int(surf_batie/500), 'ea', 850000, int(surf_batie/500*850000), '1 joint per 500m² approx.'),
        _row('7.2', 'Miscellaneous reservations and sealants', 1, 'lump sum', 0, int(surf_batie*800), 'Electrical and plumbing sleeves'),
        _row('7.3', 'Site contingencies (5% works)', 1, 'lump sum', 0, c_impr, 'Variations and adaptations'),
        _row('7.4', 'Engineer design fees (4% works)', 1, 'lump sum', 0, c_bet, 'Execution plans + supervision'),
        _row('7.5', 'Technical inspection (1.5% works)', 1, 'lump sum', 0, c_ctrl, 'Approved body required'),
        _sous_total('SUBTOTAL LOT 7', c_impr + c_bet + c_ctrl + int(surf_batie*800) + int(surf_batie/500*850000)),
    ]
    c_div_total = c_impr + c_bet + c_ctrl + int(surf_batie*800) + int(surf_batie/500*850000)

    t_div = Table(rows_div, colWidths=CW_COLS, repeatRows=1)
    t_div.setStyle(table_style())
    story.append(t_div)

    # ══════════════════════════════════════════════════════════
    # GENERAL SUMMARY
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('RECAP', 'GENERAL SUMMARY')

    total_ht  = (inst_forfait + c_terr + c_fond + c_pot_total +
                 c_pout_total + c_dalle_total + c_maco_total +
                 c_etanch_total + c_div_total)
    total_bas = int(total_ht * 0.95)
    total_haut = int(total_ht * 1.15)

    recap_rows = [
        [p('LOT','th'), p('DESCRIPTION','th_l'), p('AMOUNT (FCFA)','th'), p('% TOTAL','th')],
        [p('1','td_b'), p('Site Installation'), p(fmt_fcfa(inst_forfait),'td_r'), p(f'{inst_forfait/total_ht*100:.1f}%','td_r')],
        [p('2','td_b'), p('Earthworks'), p(fmt_fcfa(c_terr),'td_r'), p(f'{c_terr/total_ht*100:.1f}%','td_r')],
        [p('3','td_b'), p('Foundations'), p(fmt_fcfa(c_fond),'td_r'), p(f'{c_fond/total_ht*100:.1f}%','td_r')],
        [p('4','td_b'), p('RC Structure (columns + beams + slabs + stairs)'), p(fmt_fcfa(c_pot_total+c_pout_total+c_dalle_total),'td_r'), p(f'{(c_pot_total+c_pout_total+c_dalle_total)/total_ht*100:.1f}%','td_r')],
        [p('5','td_b'), p('Masonry and Partitions'), p(fmt_fcfa(c_maco_total),'td_r'), p(f'{c_maco_total/total_ht*100:.1f}%','td_r')],
        [p('6','td_b'), p('Waterproofing and Insulation'), p(fmt_fcfa(c_etanch_total),'td_r'), p(f'{c_etanch_total/total_ht*100:.1f}%','td_r')],
        [p('7','td_b'), p('Miscellaneous + Engineering Fees'), p(fmt_fcfa(c_div_total),'td_r'), p(f'{c_div_total/total_ht*100:.1f}%','td_r')],
    ]
    recap_rows.append([p('','td_b'), p('ESTIMATED TOTAL HT','td_b'), p(fmt_fcfa(total_ht),'td_g_r'), p('100%','td_b')])
    recap_rows.append([p('','td_b'), p('LOW ESTIMATE (-5%)','td_b'), p(fmt_fcfa(total_bas),'td_g_r'), p('','td_b')])
    recap_rows.append([p('','td_b'), p('HIGH ESTIMATE (+15%)','td_b'), p(fmt_fcfa(total_haut),'td_g_r'), p('','td_b')])

    tr = Table(recap_rows, colWidths=[CW*0.07, CW*0.50, CW*0.25, CW*0.18], repeatRows=1)
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
        [p('RC structure cost / m² built','td_b'), p(f'{int((c_pot_total+c_pout_total+c_dalle_total)/surf_batie):,} FCFA/m²'.replace(',', ' ')), p('Concrete + steel + formwork')],
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

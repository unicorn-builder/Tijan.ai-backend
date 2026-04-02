"""
gen_note_structure_en.py — English Structural Calculation Note (9 pages)
Uses tijan_theme.py for identical design to FR version.
Labels/headers in English. Dynamic engine text passed through p() which
calls pdf_translate when lang='en'.
Signature: generer(rs, params_dict) → bytes
"""
import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, Spacer, PageBreak
from tijan_theme import *

logger = logging.getLogger(__name__)


def generer(rs, params: dict) -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rs.params.nom, 'Structural Calculation Note', lang='en')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    story = _build(rs)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _build(rs):
    story = []
    d = rs.params
    boq = rs.boq
    ana = rs.analyse
    surf_batie_estimee = not hasattr(d, 'surface_batie_plans') or not d.surface_batie_plans

    # ── PAGE 1 — PROJECT SHEET ─────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(p(d.nom, 'titre'))
    story.append(p(f'{d.ville} — {d.usage.value.capitalize()} R+{d.nb_niveaux-1} ({d.nb_niveaux} levels)', 'sous_titre'))
    story.append(p('Indicative calculations ±15% — Must be verified by a licensed structural engineer.', 'disc'))
    story.append(Spacer(1, 3*mm))

    story += section_title('1', 'PROJECT DATA')
    note_surf = '' if not surf_batie_estimee else ' *'
    cw4 = [CW*0.28, CW*0.22, CW*0.28, CW*0.22]
    fiche = [
        [p('PARAMETER','th'), p('VALUE','th'), p('PARAMETER','th'), p('VALUE','th')],
        [p('Project','td_b'), p(d.nom), p('Location','td_b'), p(d.ville)],
        [p('Use','td_b'), p(d.usage.value.capitalize()), p('Levels','td_b'), p(f'R+{d.nb_niveaux-1} ({d.nb_niveaux})')],
        [p(f'Built area{note_surf}','td_b'), p(fmt_n(boq.surface_batie_m2,'','m²')), p('Habitable area','td_b'), p(fmt_n(boq.surface_habitable_m2,'','m²'))],
        [p('Spans','td_b'), p(f'{d.portee_min_m}–{d.portee_max_m} m'), p('Bays','td_b'), p(f'{d.nb_travees_x}×{d.nb_travees_y}')],
        [p('Concrete','td_b'), p(f'{rs.classe_beton} — fck={rs.fck_MPa:.0f} MPa'), p('Steel','td_b'), p(f'{rs.classe_acier} — fyk={rs.fyk_MPa:.0f} MPa')],
        [p('Bearing pressure','td_b'), p(f'{rs.pression_sol_MPa} MPa'), p('Distance to sea','td_b'), p(f'{rs.distance_mer_km:.1f} km')],
        [p('Loads G / Q','td_b'), p(f'{rs.charge_G_kNm2} / {rs.charge_Q_kNm2} kN/m²'), p('Seismic zone','td_b'), p(f'Zone {rs.zone_sismique} — ag={rs.sismique.ag_g}g')],
    ]
    t = Table(fiche, colWidths=cw4, repeatRows=1)
    t.setStyle(table_style())
    story.append(t)
    if surf_batie_estimee:
        story.append(p('* Built area estimated (footprint × levels) — to be confirmed with final drawings.', 'small'))

    story.append(Spacer(1, 2*mm))
    story.append(p(f'ℹ {ana.justification_materiaux}', 'note'))

    # ── PAGE 2 — DESIGN ASSUMPTIONS ───────────────────────────
    story += section_title('2', 'DESIGN ASSUMPTIONS AND APPLICABLE CODES')
    hyp = [
        [p('DOMAIN','th'), p('STANDARD','th'), p('VALUE','th')],
        [p('Reinforced concrete','td_b'), p('Eurocode 2 — NF EN 1992-1-1'), p(f'γc=1.5 — fcd={rs.fck_MPa/1.5:.1f} MPa')],
        [p('Seismic','td_b'), p('Eurocode 8 — NF EN 1998-1'), p(f'Zone {rs.zone_sismique} — ag={rs.sismique.ag_g}g — DCL')],
        [p('Dead load G','td_b'), p('EC1 — NF EN 1991-1-1'), p(f'{rs.charge_G_kNm2} kN/m² ({d.usage.value})')],
        [p('Live load Q','td_b'), p('EC1 — NF EN 1991-1-1'), p(f'{rs.charge_Q_kNm2} kN/m² ({d.usage.value})')],
        [p('ULS combination','td_b'), p('1.35G + 1.5Q'), p(f'{1.35*rs.charge_G_kNm2+1.5*rs.charge_Q_kNm2:.1f} kN/m²')],
        [p('Foundations','td_b'), p('EC7 + DTU 13.2'), p(f'qadm={rs.pression_sol_MPa} MPa — {rs.fondation.type.value}')],
        [p('Durability','td_b'), p(f'Exposure {"XS1" if rs.distance_mer_km<5 else "XC2"} — EN 206'), p(f'Cover {30 if rs.distance_mer_km>=5 else 40}mm')],
    ]
    t2 = Table(hyp, colWidths=[CW*0.20, CW*0.55, CW*0.25], repeatRows=1)
    t2.setStyle(table_style())
    story.append(t2)

    # ── PAGE 3 — COLUMNS ─────────────────────────────────────
    story.append(PageBreak())
    story += section_title('3', 'LOAD TAKEDOWN — COLUMNS (EC2/EC8)')
    story.append(p(f'Spans {d.portee_min_m}–{d.portee_max_m} m — grid {d.nb_travees_x}×{d.nb_travees_y} — ULS combination: {1.35*rs.charge_G_kNm2+1.5*rs.charge_Q_kNm2:.1f} kN/m².', 'body_j'))

    cw_p = [CW*w for w in [0.09, 0.10, 0.12, 0.08, 0.08, 0.08, 0.10, 0.09, 0.10, 0.10, 0.06]]
    rows = [[p(h,'th') for h in ['Level','NEd (kN)','Section','Bars','Ø (mm)','Tie Ø','Tie sp.','ρ (%)','NRd (kN)','NEd/NRd','Check']]]
    for pt in rs.poteaux:
        rows.append([
            p(pt.niveau),
            p(fmt_n(pt.NEd_kN,1), 'td_r'),
            p(f'{pt.section_mm}×{pt.section_mm}'),
            p(str(pt.nb_barres),'td_r'),
            p(str(pt.diametre_mm),'td_r'),
            p(str(pt.cadre_diam_mm),'td_r'),
            p(str(pt.espacement_cadres_mm),'td_r'),
            p(f'{pt.taux_armature_pct:.2f}','td_r'),
            p(fmt_n(pt.NRd_kN,1),'td_r'),
            p(f'{pt.ratio_NEd_NRd:.2f}','td_r'),
            p('✓','ok') if pt.verif_ok else p('✗','nok'),
        ])
    t3 = Table(rows, colWidths=cw_p, repeatRows=1)
    ts3 = table_style()
    for i, pt in enumerate(rs.poteaux):
        if pt.taux_armature_pct > 2.5:
            ts3.add('TEXTCOLOR', (7,i+1), (7,i+1), ORANGE)
        if not pt.verif_ok:
            ts3.add('BACKGROUND', (0,i+1), (-1,i+1), ORANGE_LT)
    t3.setStyle(ts3)
    story.append(t3)
    story.append(p('ρ = reinforcement ratio (EC2: 0.1% ≤ ρ ≤ 4%) | NEd/NRd < 1 required', 'small'))

    # ── PAGE 4 — BEAMS + SLAB ─────────────────────────────────
    story.append(PageBreak())
    story += section_title('4', 'BEAM DESIGN (EC2)')
    for pout in [rs.poutre_principale, rs.poutre_secondaire]:
        if pout is None: continue
        beam_type = 'Main beam' if pout.type == 'principale' else 'Secondary beam'
        story.append(p(f'{beam_type} — span {pout.portee_m} m', 'h2'))
        cw_po = [CW*0.13]*7
        rows_po = [[p(h,'th') for h in ['b (mm)','h (mm)','As bot (cm²)','As top (cm²)','Stirrups','Stirrup sp.','Span (m)']]]
        rows_po.append([
            p(str(pout.b_mm),'td_r'), p(str(pout.h_mm),'td_r'),
            p(f'{pout.As_inf_cm2:.1f}','td_r'), p(f'{pout.As_sup_cm2:.1f}','td_r'),
            p(f'HA{pout.etrier_diam_mm}'), p(f's={pout.etrier_esp_mm}mm'),
            p(f'{pout.portee_m:.2f}','td_r'),
        ])
        tpo = Table(rows_po, colWidths=cw_po, repeatRows=1)
        tpo.setStyle(table_style(zebra=False))
        story.append(tpo)
        vf = '✓ OK' if pout.verif_fleche else '⚠ To be checked'
        vt = '✓ OK' if pout.verif_effort_t else '⚠ To be checked'
        story.append(p(f'Deflection check: {vf} | Shear check: {vt}', 'small'))
        story.append(Spacer(1, 2*mm))

    story += section_title('5', 'SLAB DESIGN (EC2)')
    dalle = rs.dalle
    dalle_data = [
        [p('PARAMETER','th'), p('VALUE','th'), p('JUSTIFICATION','th')],
        [p('Thickness','td_b'), p(f'{dalle.epaisseur_mm} mm'), p(f'e ≥ L/35 = {rs.params.portee_min_m/35*1000:.0f} mm')],
        [p('As x (cm²/ml)','td_b'), p(f'{dalle.As_x_cm2_ml:.1f}','td_r'), p('Main span reinforcement')],
        [p('As y (cm²/ml)','td_b'), p(f'{dalle.As_y_cm2_ml:.1f}','td_r'), p('Transverse reinforcement')],
        [p('Max. deflection','td_b'), p(f'{dalle.fleche_admissible_mm:.1f} mm'), p(f'L/250 = {rs.params.portee_min_m/250*1000:.1f} mm')],
        [p('Verification','td_b'), p('✓ Compliant' if dalle.verif_ok else '⚠ To be checked', 'td_g' if dalle.verif_ok else 'td_o'), p('')],
    ]
    td = Table(dalle_data, colWidths=[CW*0.28, CW*0.22, CW*0.50], repeatRows=1)
    td.setStyle(table_style())
    story.append(td)

    # ── PAGE 5 — PARTITIONS ──────────────────────────────────
    story.append(PageBreak())
    story += section_title('6', 'PARTITIONS AND MASONRY')
    cl = rs.cloisons
    story.append(p(f'Total partition area: {int(cl.surface_totale_m2)} m² (separating {int(cl.surface_separative_m2)} m² | lightweight {int(cl.surface_legere_m2)} m² | shafts {int(cl.surface_gaines_m2)} m²)', 'body'))
    story.append(p(f'Recommended option: {cl.option_recommandee.value} — design load: {cl.charge_dalle_kn_m2} kN/m²', 'body'))
    story.append(Spacer(1, 2*mm))

    cw_cl = [CW*0.20, CW*0.08, CW*0.12, CW*0.10, CW*0.12, CW*0.38]
    rows_cl = [[p(h,'th') for h in ['Option','Thk (cm)','Load (kN/m²)','U.P. (FCFA/m²)','Recommended','Key advantages']]]
    for opt in cl.options:
        est_rec = opt.type == cl.option_recommandee
        rows_cl.append([
            p(opt.materiau[:35], 'td_b' if est_rec else 'td'),
            p(str(opt.epaisseur_cm),'td_r'),
            p(str(opt.charge_kn_m2),'td_r'),
            p(fmt_n(opt.prix_fcfa_m2),'td_r'),
            p('★ Recommended','td_g') if est_rec else p('—'),
            p(' | '.join(opt.avantages[:2])),
        ])
    tcl = Table(rows_cl, colWidths=cw_cl, repeatRows=1)
    ts_cl = table_style()
    for i, opt in enumerate(cl.options):
        if opt.type == cl.option_recommandee:
            ts_cl.add('BACKGROUND', (0,i+1), (-1,i+1), VERT_LIGHT)
    tcl.setStyle(ts_cl)
    story.append(tcl)
    story.append(Paragraph(
        'ℹ If multiple options have significant cost impacts, '
        'submit to the owner for approval before proceeding.',
        S['note']))

    # ── PAGE 6 — FOUNDATIONS ─────────────────────────────────
    story.append(PageBreak())
    story += section_title('7', 'FOUNDATION DESIGN (EC7 + DTU 13.2)')
    fond = rs.fondation
    story.append(p(f'Justification: {fond.justification}', 'body_j'))
    story.append(Spacer(1, 2*mm))

    fond_data = [
        [p('PARAMETER','th'), p('VALUE','th'), p('REMARK','th')],
        [p('Type','td_b'), p(fond.type.value), p('Adapted to soil conditions and building height')],
    ]
    if fond.nb_pieux > 0:
        fond_data += [
            [p('Pile diameter','td_b'), p(f'Ø{fond.diam_pieu_mm} mm'), p('Continuous flight auger')],
            [p('Pile length','td_b'), p(f'{fond.longueur_pieu_m:.1f} m'), p('Down to bearing stratum')],
            [p('Reinforcement','td_b'), p(f'As = {fond.As_cm2:.1f} cm²'), p('B500B cage, full length')],
            [p('Total piles','td_b'), p(str(fond.nb_pieux)), p('Estimate — to be confirmed by geotechnical engineer')],
        ]
        try:
            from prix_marche import get_prix_structure
            px = get_prix_structure(rs.params.ville)
            cout_pieux = fond.nb_pieux * fond.longueur_pieu_m * px.pieu_fore_d800_ml
            story.append(Spacer(1, 2*mm))
            story.append(p(f'ℹ Foundation cost impact: {fmt_fcfa(cout_pieux)} estimated ({cout_pieux/boq.total_bas_fcfa*100:.0f}% of structural budget). Deep foundations = highest cost item after superstructure.', 'note'))
        except Exception as e:
            logger.warning(f"Foundation cost calculation failed: {e}")
    else:
        fond_data += [
            [p('Footing width','td_b'), p(f'{fond.largeur_semelle_m:.2f} m'), p('Square section')],
            [p('Depth','td_b'), p(f'{fond.profondeur_m:.1f} m'), p('Below frost + bearing stratum')],
        ]

    tf = Table(fond_data, colWidths=[CW*0.28, CW*0.22, CW*0.50], repeatRows=1)
    tf.setStyle(table_style())
    story.append(tf)

    # ── PAGE 7 — SEISMIC ─────────────────────────────────────
    story.append(PageBreak())
    story += section_title('8', 'SEISMIC ANALYSIS (EC8 — NF EN 1998-1)')
    sism = rs.sismique
    story.append(p(f'Seismic zone {sism.zone} — ag = {sism.ag_g}g — T1 = {sism.T1_s}s — Fb = {sism.Fb_kN:.0f} kN', 'body'))
    story.append(Spacer(1, 2*mm))

    sism_data = [
        [p('PARAMETER','th'), p('VALUE','th'), p('REFERENCE','th')],
        [p('Acceleration ag'), p(f'{sism.ag_g}g = {sism.ag_g*9.81:.2f} m/s²'), p('National annex')],
        [p('Soil factor S'), p('1.15'), p('Soil type C — EC8 Table 3.2')],
        [p('Behaviour factor q'), p('1.5 (DCL)'), p('EC8 §5.2.2.2')],
        [p('Period T1'), p(f'{sism.T1_s} s'), p('EC8 §4.3.3.2 — approximate method')],
        [p('Base shear Fb'), p(f'{sism.Fb_kN:.0f} kN'), p('Fb = Sd(T1) × m × λ')],
        [p('DCL compliance'), p('✓ Compliant' if sism.conforme_DCL else '⚠ Further analysis needed', 'td_g' if sism.conforme_DCL else 'td_o'), p('')],
    ]
    ts_ = Table(sism_data, colWidths=[CW*0.35, CW*0.35, CW*0.30], repeatRows=1)
    ts_.setStyle(table_style())
    story.append(ts_)
    story.append(Spacer(1, 3*mm))
    for disp in sism.dispositions:
        prefix = '⚠' if '⚠' in disp else '•'
        style = 'note' if '⚠' in disp else 'body'
        story.append(p(f'{prefix} {disp.replace("⚠ ","")}', style))

    # ── PAGE 8 — ANALYSIS ────────────────────────────────────
    story.append(PageBreak())
    story += section_title('9', 'ENGINEERING ANALYSIS AND RECOMMENDATIONS')

    story.append(p('Engineering Summary:', 'h2'))
    story.append(p(ana.note_ingenieur, 'bleu'))
    story.append(Spacer(1, 3*mm))

    if ana.points_forts or ana.alertes:
        col1, col2 = [], []
        if ana.points_forts:
            col1.append(p('✅ Strengths', 'h2'))
            for f in ana.points_forts:
                col1.append(p(f'• {f}', 'body'))
                col1.append(Spacer(1,1*mm))
        if ana.alertes:
            col2.append(p('⚠ Attention Points', 'h2'))
            for a in ana.alertes:
                col2.append(p(f'• {a}', 'note'))
                col2.append(Spacer(1,1*mm))
        tfa = Table([[col1, col2]], colWidths=[CW*0.50, CW*0.50])
        tfa.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]))
        story.append(tfa)
        story.append(Spacer(1, 3*mm))

    if ana.recommandations:
        story.append(p('Recommendations:', 'h2'))
        rec_data = [[p('#','th'), p('RECOMMENDATION','th_l')]]
        for i, r in enumerate(ana.recommandations):
            rec_data.append([p(str(i+1),'td_r'), p(r)])
        tr = Table(rec_data, colWidths=[CW*0.06, CW*0.94], repeatRows=1)
        tr.setStyle(table_style())
        story.append(tr)

    # ── PAGE 9 — BOQ ─────────────────────────────────────────
    story.append(PageBreak())
    story += section_title('10', 'BILL OF QUANTITIES AND PRICES — STRUCTURE')
    story.append(p(f'Unit prices based on {rs.params.ville} 2026 market (supply and install). Margin ±15%.', 'small'))
    story.append(Spacer(1, 2*mm))

    cw_b = [CW*w for w in [0.05, 0.37, 0.09, 0.07, 0.13, 0.14, 0.15]]
    boq_rows = [[p(h,'th') for h in ['Lot','Description','Qty','Unit','U.P. (FCFA)','Low est.','High est.']]]

    lots_data = [
        ('1',  'Earthworks — clearing + mechanical excavation',
         fmt_n(boq.terrassement_m3), 'm³', fmt_n(8500),
         fmt_fcfa(boq.cout_terr_fcfa), fmt_fcfa(int(boq.cout_terr_fcfa*1.10))),
        ('2',  'Foundations — piles/footings/raft RC',
         '—', 'lump sum', '—',
         fmt_fcfa(boq.cout_fond_fcfa), fmt_fcfa(int(boq.cout_fond_fcfa*1.20))),
        ('3a', f'Concrete {rs.classe_beton} RMC — structure ({fmt_n(boq.beton_structure_m3,0)} m³)',
         fmt_n(boq.beton_structure_m3,0), 'm³', '185 000',
         fmt_fcfa(boq.cout_beton_fcfa), fmt_fcfa(int(boq.cout_beton_fcfa*1.10))),
        ('3b', f'Steel {rs.classe_acier} supply+fix ({fmt_n(boq.acier_kg,0)} kg)',
         fmt_n(boq.acier_kg,0), 'kg', '810',
         fmt_fcfa(boq.cout_acier_fcfa), fmt_fcfa(int(boq.cout_acier_fcfa*1.10))),
        ('3c', f'Formwork all faces ({fmt_n(boq.coffrage_m2,0)} m²)',
         fmt_n(boq.coffrage_m2,0), 'm²', '18 000',
         fmt_fcfa(boq.cout_coffrage_fcfa), fmt_fcfa(int(boq.cout_coffrage_fcfa*1.10))),
        ('4',  'Masonry — 15cm blocks plastered both sides',
         fmt_n(boq.maconnerie_m2,0), 'm²', '24 000',
         fmt_fcfa(boq.cout_maco_fcfa), fmt_fcfa(int(boq.cout_maco_fcfa*1.15))),
        ('5',  f'Roof waterproofing ({fmt_n(boq.etancheite_m2,0)} m²)',
         fmt_n(boq.etancheite_m2,0), 'm²', '18 500',
         fmt_fcfa(boq.cout_etanch_fcfa), fmt_fcfa(int(boq.cout_etanch_fcfa*1.10))),
        ('6',  'Miscellaneous — joints, parapets, openings',
         '—', 'lump sum', '—',
         fmt_fcfa(boq.cout_divers_fcfa), fmt_fcfa(int(boq.cout_divers_fcfa*1.10))),
    ]
    for lot in lots_data:
        boq_rows.append([p(lot[0]), p(lot[1]), p(lot[2],'td_r'), p(lot[3]),
                          p(lot[4],'td_r'), p(lot[5],'td_r'), p(lot[6],'td_r')])
    boq_rows.append([
        p('','td_b'), p('TOTAL STRUCTURE','td_b'), p('','td_r'), p(''), p('','td_r'),
        p(fmt_fcfa(boq.total_bas_fcfa),'td_g_r'), p(fmt_fcfa(boq.total_haut_fcfa),'td_g_r'),
    ])
    tboq = Table(boq_rows, colWidths=cw_b, repeatRows=1)
    ts_boq = table_style()
    total_row_style(ts_boq)
    tboq.setStyle(ts_boq)
    story.append(tboq)

    story.append(Spacer(1, 3*mm))
    rat_data = [
        [p(h,'th') for h in ['INDICATOR','LOW VALUE','HIGH VALUE','NOTE']],
        [p('Total built area','td_b'), p(fmt_n(boq.surface_batie_m2,'','m²')), p('—'),
         p(f'Footprint {int(d.surface_emprise_m2)} m² × {d.nb_niveaux} levels', 'small')],
        [p('Cost / m² built','td_b'), p(f'{boq.ratio_fcfa_m2_bati:,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(f'{int(boq.ratio_fcfa_m2_bati*1.15):,} FCFA/m²'.replace(',', ' '),'td_r'),
         p('Structure only — excl. MEP, finishes, ext. works', 'small')],
        [p('Cost / m² habitable','td_b'), p(f'{boq.ratio_fcfa_m2_habitable:,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(f'{int(boq.ratio_fcfa_m2_habitable*1.15):,} FCFA/m²'.replace(',', ' '),'td_r'),
         p('Habitable area ≈ 78% of built area', 'small')],
        [p('TOTAL STRUCTURAL COST','td_b'),
         p(fmt_fcfa(boq.total_bas_fcfa),'td_g_r'), p(fmt_fcfa(boq.total_haut_fcfa),'td_g_r'),
         p('Estimate ±15%', 'small')],
    ]
    tr2 = Table(rat_data, colWidths=[CW*0.32, CW*0.20, CW*0.20, CW*0.28], repeatRows=1)
    ts_r = table_style()
    total_row_style(ts_r)
    tr2.setStyle(ts_r)
    story.append(tr2)

    return story

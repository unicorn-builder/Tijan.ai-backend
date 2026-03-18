"""
gen_note_structure.py — Note de calcul structure
Tijan AI — données 100% issues du moteur engine_structure_v2
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer, PageBreak, KeepTogether
from tijan_theme import *
from pdf_strings import get_strings

def generer(rs, params: dict, lang: str = "fr") -> bytes:
    """
    rs : ResultatsStructure (output de engine_structure_v2.calculer_structure)
    params : dict avec nom, ville, etc.
    """
    buf = io.BytesIO()
    s_h = get_strings(lang)
    hf = HeaderFooter(rs.params.nom, s_h['note_structure_title'], lang=lang)
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)

    story = _build(rs, lang=lang)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _build(rs, lang="fr"):
    s = get_strings(lang)
    story = []
    d = rs.params
    boq = rs.boq
    ana = rs.analyse
    surf_batie_estimee = not hasattr(d, 'surface_batie_plans') or not d.surface_batie_plans

    # ── PAGE 1 — FICHE PROJET ──────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(d.nom, S['titre']))
    story.append(Paragraph(f'{d.ville} — {d.usage.value.capitalize()} R+{d.nb_niveaux-1} ({d.nb_niveaux} niveaux)', S['sous_titre']))
    story.append(Paragraph(
        s['subtitle_structure'],
        S['disc']))
    story.append(Spacer(1, 3*mm))

    # Fiche projet
    story += section_title('1', s['project_data'])
    note_surf = '' if not surf_batie_estimee else ' *'
    cw4 = [CW*0.28, CW*0.22, CW*0.28, CW*0.22]
    fiche = [
        [p('PARAMÈTRE','th'), p('VALEUR','th'), p('PARAMÈTRE','th'), p('VALEUR','th')],
        [p(s['project'],'td_b'), p(d.nom), p(s['location'],'td_b'), p(d.ville)],
        [p(s['usage_label'],'td_b'), p(d.usage.value.capitalize()), p(s['levels_label'],'td_b'), p(f'R+{d.nb_niveaux-1} ({d.nb_niveaux})')],
        [p(f"{s['built_surface']}{note_surf}",'td_b'), p(fmt_n(boq.surface_batie_m2,'','m²')), p(s['hab_surface'],'td_b'), p(fmt_n(boq.surface_habitable_m2,'','m²'))],
        [p(s['spans'],'td_b'), p(f'{d.portee_min_m}–{d.portee_max_m} m'), p(s['bays'],'td_b'), p(f'{d.nb_travees_x}×{d.nb_travees_y}')],
        [p(s['concrete'],'td_b'), p(f'{rs.classe_beton} — fck={rs.fck_MPa:.0f} MPa'), p(s['steel'],'td_b'), p(f'{rs.classe_acier} — fyk={rs.fyk_MPa:.0f} MPa')],
        [p(s['soil'],'td_b'), p(f'{rs.pression_sol_MPa} MPa'), p(s['sea_dist'],'td_b'), p(f'{rs.distance_mer_km:.1f} km')],
        [p(s['loads'],'td_b'), p(f'{rs.charge_G_kNm2} / {rs.charge_Q_kNm2} kN/m²'), p(s['seismic_zone'],'td_b'), p(f'Zone {rs.zone_sismique} — ag={rs.sismique.ag_g}g')],
    ]
    t = Table(fiche, colWidths=cw4, repeatRows=1)
    t.setStyle(table_style())
    story.append(t)
    if surf_batie_estimee:
        story.append(Paragraph('* Surface bâtie estimée (emprise × niveaux) — à confirmer avec plans définitifs.', S['small']))

    # Justification matériaux
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f'ℹ {ana.justification_materiaux}', S['note']))

    # ── PAGE 2 — HYPOTHÈSES ───────────────────────────────────
    story += section_title('2', s['hypotheses'])
    hyp = [
        [p('DOMAINE','th'), p('NORME','th'), p('VALEUR','th')],
        [p(s['rc_label'],'td_b'), p('Eurocode 2 — NF EN 1992-1-1'), p(f'γc=1.5 — fcd={rs.fck_MPa/1.5:.1f} MPa')],
        [p(s['seismic_label'],'td_b'), p('Eurocode 8 — NF EN 1998-1'), p(f'Zone {rs.zone_sismique} — ag={rs.sismique.ag_g}g — DCL')],
        [p(s['perm_loads'],'td_b'), p('EC1 — NF EN 1991-1-1'), p(f'{rs.charge_G_kNm2} kN/m² ({d.usage.value})')],
        [p(s['var_loads'],'td_b'), p('EC1 — NF EN 1991-1-1'), p(f'{rs.charge_Q_kNm2} kN/m² ({d.usage.value})')],
        [p(s['elu_combo'],'td_b'), p('1.35G + 1.5Q'), p(f'{1.35*rs.charge_G_kNm2+1.5*rs.charge_Q_kNm2:.1f} kN/m²')],
        [p(s['foundations_label'],'td_b'), p('EC7 + DTU 13.2'), p(f'qadm={rs.pression_sol_MPa} MPa — {rs.fondation.type.value}')],
        [p(s['durability'],'td_b'), p(f'Exposition {"XS1" if rs.distance_mer_km<5 else "XC2"} — EN 206'), p(f'Enrobage {30 if rs.distance_mer_km>=5 else 40}mm')],
    ]
    t2 = Table(hyp, colWidths=[CW*0.20, CW*0.55, CW*0.25], repeatRows=1)
    t2.setStyle(table_style())
    story.append(t2)

    # ── PAGE 3 — POTEAUX ─────────────────────────────────────
    story.append(PageBreak())
    story += section_title('3', s['columns'])
    story.append(Paragraph(
        f'Portées {d.portee_min_m}–{d.portee_max_m} m — grille {d.nb_travees_x}×{d.nb_travees_y} — '
        f'combinaison ELU : {1.35*rs.charge_G_kNm2+1.5*rs.charge_Q_kNm2:.1f} kN/m².',
        S['body_j']))

    cw_p = [CW*w for w in [0.09, 0.10, 0.12, 0.08, 0.08, 0.08, 0.10, 0.09, 0.10, 0.10, 0.06]]
    rows = [[p(h,'th') for h in [s['level'],s['ned'],s['section_h'],s['nb_bars'],s['diam'],s['stirrup_d'],s['stirrup_s'],s['ratio'],s['nrd'],s['ratio_check'],s['verif']]]]
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
    story.append(Paragraph(s['rho_note'], S['small']))

    # ── PAGE 4 — POUTRES + DALLE ─────────────────────────────
    story.append(PageBreak())
    story += section_title('4', s['beams'])
    for pout in [rs.poutre_principale, rs.poutre_secondaire]:
        if pout is None: continue
        story.append(Paragraph(f'Poutre {pout.type} — portée {pout.portee_m} m', S['h2']))
        cw_po = [CW*0.13]*7
        rows_po = [[p(h,'th') for h in [s['b_mm'],s['h_mm'],s['as_inf'],s['as_sup'],s['stirrups'],s['stir_sp'],s['span_m']]]]
        rows_po.append([
            p(str(pout.b_mm),'td_r'), p(str(pout.h_mm),'td_r'),
            p(f'{pout.As_inf_cm2:.1f}','td_r'), p(f'{pout.As_sup_cm2:.1f}','td_r'),
            p(f'HA{pout.etrier_diam_mm}'), p(f'e={pout.etrier_esp_mm}mm'),
            p(f'{pout.portee_m:.2f}','td_r'),
        ])
        tpo = Table(rows_po, colWidths=cw_po, repeatRows=1)
        tpo.setStyle(table_style(zebra=False))
        story.append(tpo)
        vf = '✓ OK' if pout.verif_fleche else '⚠ À vérifier'
        vt = '✓ OK' if pout.verif_effort_t else '⚠ À vérifier'
        story.append(Paragraph(f"{s['defl_check']} : {vf} | {s['shear_check']} : {vt}", S['small']))
        story.append(Spacer(1, 2*mm))

    story += section_title('5', s['slab'])
    dalle = rs.dalle
    dalle_data = [
        [p('PARAMÈTRE','th'), p('VALEUR','th'), p('JUSTIFICATION','th')],
        [p(s['thickness'],'td_b'), p(f'{dalle.epaisseur_mm} mm'), p(f'e ≥ L/35 = {rs.params.portee_min_m/35*1000:.0f} mm')],
        [p(s['as_x'],'td_b'), p(f'{dalle.As_x_cm2_ml:.1f}','td_r'), p(s['rebar_main'])],
        [p(s['as_y'],'td_b'), p(f'{dalle.As_y_cm2_ml:.1f}','td_r'), p(s['rebar_sec'])],
        [p(s['adm_defl'],'td_b'), p(f'{dalle.fleche_admissible_mm:.1f} mm'), p(f'L/250 = {rs.params.portee_min_m/250*1000:.1f} mm')],
        [p(s['verif_label'],'td_b'), p(s['compliant'] if dalle.verif_ok else s['to_verify'], 'td_g' if dalle.verif_ok else 'td_o'), p('')],
    ]
    td = Table(dalle_data, colWidths=[CW*0.28, CW*0.22, CW*0.50], repeatRows=1)
    td.setStyle(table_style())
    story.append(td)

    # ── PAGE 5 — CLOISONS ────────────────────────────────────
    story.append(PageBreak())
    story += section_title('6', s['partitions'])
    cl = rs.cloisons
    story.append(Paragraph(
        f'Surface totale cloisons estimée : {int(cl.surface_totale_m2)} m² '
        f'(séparatives {int(cl.surface_separative_m2)} m² | légères {int(cl.surface_legere_m2)} m² | gaines {int(cl.surface_gaines_m2)} m²)',
        S['body']))
    story.append(Paragraph(f'Option recommandée : {cl.option_recommandee.value} — charge retenue : {cl.charge_dalle_kn_m2} kN/m²', S['body']))
    story.append(Spacer(1, 2*mm))

    # Tableau options
    cw_cl = [CW*0.20, CW*0.08, CW*0.12, CW*0.10, CW*0.12, CW*0.38]
    rows_cl = [[p(h,'th') for h in ['Option','Ép. (cm)','Charge (kN/m²)','P.U. (FCFA/m²)','Recommandé','Avantages principaux']]]
    for opt in cl.options:
        est_rec = opt.type == cl.option_recommandee
        rows_cl.append([
            p(opt.materiau[:35], 'td_b' if est_rec else 'td'),
            p(str(opt.epaisseur_cm),'td_r'),
            p(str(opt.charge_kn_m2),'td_r'),
            p(fmt_n(opt.prix_fcfa_m2),'td_r'),
            p('★ Recommandé','td_g') if est_rec else p('—'),
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
        'ℹ Si plusieurs options ont des impacts prix significatifs, '
        'les soumettre au maître d\'ouvrage avant validation.',
        S['note']))

    # ── PAGE 6 — FONDATIONS ──────────────────────────────────
    story.append(PageBreak())
    story += section_title('7', s['foundations'])
    fond = rs.fondation
    story.append(Paragraph(f'Justification : {fond.justification}', S['body_j']))
    story.append(Spacer(1, 2*mm))

    fond_data = [
        [p('PARAMÈTRE','th'), p('VALEUR','th'), p('REMARQUE','th')],
        [p('Type','td_b'), p(fond.type.value), p('Adapté aux conditions de sol et à la hauteur')],
    ]
    if fond.nb_pieux > 0:
        fond_data += [
            [p(s['pile_diam'],'td_b'), p(f'Ø{fond.diam_pieu_mm} mm'), p(s['drilled'])],
            [p(s['pile_length'],'td_b'), p(f'{fond.longueur_pieu_m:.1f} m'), p(s['bearing_layer'])],
            [p(s['reinf'],'td_b'), p(f'As = {fond.As_cm2:.1f} cm²'), p(s['full_cage'])],
            [p(s['nb_piles_label'],'td_b'), p(str(fond.nb_pieux)), p(s['est_geotech'])],
        ]
        # Note impact prix
        try:
            from prix_marche import get_prix_structure
            px = get_prix_structure(rs.params.ville)
            cout_pieux = fond.nb_pieux * fond.longueur_pieu_m * px.pieu_fore_d800_ml
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(
                f'ℹ Impact prix fondations : {fmt_fcfa(cout_pieux)} estimés '
                f'({cout_pieux/boq.total_bas_fcfa*100:.0f}% du budget structure). '
                f'Fondations profondes = poste le plus coûteux après gros œuvre.',
                S['note']))
        except: pass
    else:
        fond_data += [
            [p(s['footing_width'],'td_b'), p(f'{fond.largeur_semelle_m:.2f} m'), p(s['square_sec'])],
            [p(s['depth'],'td_b'), p(f'{fond.profondeur_m:.1f} m'), p(s['below_frost'])],
        ]

    tf = Table(fond_data, colWidths=[CW*0.28, CW*0.22, CW*0.50], repeatRows=1)
    tf.setStyle(table_style())
    story.append(tf)

    # ── PAGE 7 — SÉISMIQUE ───────────────────────────────────
    story.append(PageBreak())
    story += section_title('8', s['seismic'])
    sism = rs.sismique
    story.append(Paragraph(
        f'Zone sismique {sism.zone} — ag = {sism.ag_g}g — T₁ = {sism.T1_s}s — Fb = {sism.Fb_kN:.0f} kN',
        S['body']))
    story.append(Spacer(1, 2*mm))

    sism_data = [
        [p('PARAMÈTRE','th'), p('VALEUR','th'), p('RÉFÉRENCE','th')],
        [p(s['accel']), p(f'{sism.ag_g}g = {sism.ag_g*9.81:.2f} m/s²'), p(s['nat_annex'])],
        [p(s['soil_factor']), p('1.15'), p(s['soil_c'])],
        [p(s['q_factor']), p('1.5 (DCL)'), p('EC8 §5.2.2.2')],
        [p(s['period']), p(f'{sism.T1_s} s'), p('EC8 §4.3.3.2 — méthode approchée')],
        [p(s['base_force']), p(f'{sism.Fb_kN:.0f} kN'), p('Fb = Sd(T₁) × m × λ')],
        [p(s['dcl_comp']), p(s['compliant'] if sism.conforme_DCL else s['add_analysis'], 'td_g' if sism.conforme_DCL else 'td_o'), p('')],
    ]
    ts_ = Table(sism_data, colWidths=[CW*0.35, CW*0.35, CW*0.30], repeatRows=1)
    ts_.setStyle(table_style())
    story.append(ts_)
    story.append(Spacer(1, 3*mm))
    for disp in sism.dispositions:
        prefix = '⚠' if '⚠' in disp else '•'
        style = 'note' if '⚠' in disp else 'body'
        story.append(Paragraph(f'{prefix} {disp.replace("⚠ ","")}', S[style]))

    # ── PAGE 8 — ANALYSE ─────────────────────────────────────
    story.append(PageBreak())
    story += section_title('9', s['analysis'])

    # Note ingénieur
    story.append(Paragraph(s['eng_note_label'], S['h2']))
    story.append(Paragraph(ana.note_ingenieur, S['bleu']))
    story.append(Spacer(1, 3*mm))

    # Points forts / alertes
    if ana.points_forts or ana.alertes:
        col1, col2 = [], []
        if ana.points_forts:
            col1.append(Paragraph(s['strengths_label'], S['h2']))
            for f in ana.points_forts:
                col1.append(Paragraph(f'• {f}', S['body']))
                col1.append(Spacer(1,1*mm))
        if ana.alertes:
            col2.append(Paragraph(s['attention_label'], S['h2']))
            for a in ana.alertes:
                col2.append(Paragraph(f'• {a}', S['note']))
                col2.append(Spacer(1,1*mm))
        tfa = Table([[col1, col2]], colWidths=[CW*0.50, CW*0.50])
        tfa.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]))
        story.append(tfa)
        story.append(Spacer(1, 3*mm))

    # Recommandations
    if ana.recommandations:
        story.append(Paragraph(s['rec_label'], S['h2']))
        rec_data = [[p('N°','th'), p('RECOMMANDATION','th_l')]]
        for i, r in enumerate(ana.recommandations):
            rec_data.append([p(str(i+1),'td_r'), p(r)])
        tr = Table(rec_data, colWidths=[CW*0.06, CW*0.94], repeatRows=1)
        tr.setStyle(table_style())
        story.append(tr)

    # ── PAGE 9 — BOQ ────────────────────────────────────────
    story.append(PageBreak())
    story += section_title('10', s['boq_section'])
    story.append(Paragraph(
        f'Prix unitaires marché {rs.params.ville} 2026 (fournis-posés). Marge estimée ±15%.',
        S['small']))
    story.append(Spacer(1, 2*mm))

    cw_b = [CW*w for w in [0.05, 0.37, 0.09, 0.07, 0.13, 0.14, 0.15]]
    boq_rows = [[p(h,'th') for h in ['Lot','Désignation','Qté','Unité','P.U. (FCFA)','Montant bas','Montant haut']]]

    lots_data = [
        ('1',  s['earthworks_item'],
         fmt_n(boq.terrassement_m3), 'm³', fmt_n(8500),
         fmt_fcfa(boq.cout_terr_fcfa), fmt_fcfa(int(boq.cout_terr_fcfa*1.10))),
        ('2',  s['found_item'],
         '—', 'forfait', '—',
         fmt_fcfa(boq.cout_fond_fcfa), fmt_fcfa(int(boq.cout_fond_fcfa*1.20))),
        ('3a', f'Béton {rs.classe_beton} BPE — structure ({fmt_n(boq.beton_structure_m3,0)} m³)',
         fmt_n(boq.beton_structure_m3,0), 'm³', '185 000',
         fmt_fcfa(boq.cout_beton_fcfa), fmt_fcfa(int(boq.cout_beton_fcfa*1.10))),
        ('3b', f'Acier {rs.classe_acier} fourni-posé ({fmt_n(boq.acier_kg,0)} kg)',
         fmt_n(boq.acier_kg,0), 'kg', '810',
         fmt_fcfa(boq.cout_acier_fcfa), fmt_fcfa(int(boq.cout_acier_fcfa*1.10))),
        ('3c', f'Coffrage toutes faces ({fmt_n(boq.coffrage_m2,0)} m²)',
         fmt_n(boq.coffrage_m2,0), 'm²', '18 000',
         fmt_fcfa(boq.cout_coffrage_fcfa), fmt_fcfa(int(boq.cout_coffrage_fcfa*1.10))),
        ('4',  s['masonry_item'],
         fmt_n(boq.maconnerie_m2,0), 'm²', '24 000',
         fmt_fcfa(boq.cout_maco_fcfa), fmt_fcfa(int(boq.cout_maco_fcfa*1.15))),
        ('5',  f'Étanchéité toiture-terrasse ({fmt_n(boq.etancheite_m2,0)} m²)',
         fmt_n(boq.etancheite_m2,0), 'm²', '18 500',
         fmt_fcfa(boq.cout_etanch_fcfa), fmt_fcfa(int(boq.cout_etanch_fcfa*1.10))),
        ('6',  s['misc_item'],
         '—', 'forfait', '—',
         fmt_fcfa(boq.cout_divers_fcfa), fmt_fcfa(int(boq.cout_divers_fcfa*1.10))),
    ]
    for lot in lots_data:
        boq_rows.append([p(lot[0]), p(lot[1]), p(lot[2],'td_r'), p(lot[3]),
                          p(lot[4],'td_r'), p(lot[5],'td_r'), p(lot[6],'td_r')])
    boq_rows.append([
        p('','td_b'), p(s['total_struct'],'td_b'), p('','td_r'), p(''), p('','td_r'),
        p(fmt_fcfa(boq.total_bas_fcfa),'td_g_r'), p(fmt_fcfa(boq.total_haut_fcfa),'td_g_r'),
    ])
    tboq = Table(boq_rows, colWidths=cw_b, repeatRows=1)
    ts_boq = table_style()
    total_row_style(ts_boq)
    tboq.setStyle(ts_boq)
    story.append(tboq)

    # Ratios
    story.append(Spacer(1, 3*mm))
    rat_data = [
        [p(h,'th') for h in [s['indicator'],s['low_val'],s['high_val'],s['notes']]],
        [p(s['total_built'],'td_b'), p(fmt_n(boq.surface_batie_m2,'','m²')), p('—'),
         p(f'Emprise {int(d.surface_emprise_m2)} m² × {d.nb_niveaux} niveaux', 'small')],
        [p(s['cost_m2_built'],'td_b'), p(f'{boq.ratio_fcfa_m2_bati:,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(f'{int(boq.ratio_fcfa_m2_bati*1.15):,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(s['struct_only'], 'small')],
        [p(s['cost_m2_hab'],'td_b'), p(f'{boq.ratio_fcfa_m2_habitable:,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(f'{int(boq.ratio_fcfa_m2_habitable*1.15):,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(s['hab_note'], 'small')],
        [p(s['total_cost_struct'],'td_b'),
         p(fmt_fcfa(boq.total_bas_fcfa),'td_g_r'), p(fmt_fcfa(boq.total_haut_fcfa),'td_g_r'),
         p(s['estimate_note_short'], 'small')],
    ]
    tr2 = Table(rat_data, colWidths=[CW*0.32, CW*0.20, CW*0.20, CW*0.28], repeatRows=1)
    ts_r = table_style()
    total_row_style(ts_r)
    tr2.setStyle(ts_r)
    story.append(tr2)

    return story

"""
gen_mep_en.py — English MEP Technical Note + EDGE Report + Executive Report
Uses tijan_theme.py for identical design to FR version.
Signatures:
  generer_note_mep(rm, params_dict) → bytes
  generer_edge(rm, params_dict) → bytes
  generer_rapport_executif(rs, rm, params_dict) → bytes
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, Spacer, PageBreak, TableStyle as TS
from tijan_theme import *


# ════════════════════════════════════════════
# 1. MEP TECHNICAL NOTE
# ════════════════════════════════════════════
def generer_note_mep(rm, params: dict) -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rm.params.nom, 'MEP Technical Note', lang='en')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    story = _build_mep(rm)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()

def _build_mep(rm):
    story = []
    d = rm.params
    e = rm.electrique; pl = rm.plomberie; cvc = rm.cvc
    cf = rm.courants_faibles; si = rm.securite_incendie
    asc = rm.ascenseurs; auto = rm.automatisation

    story.append(Spacer(1, 3*mm))
    story.append(p(d.nom, 'titre'))
    story.append(p(f'MEP Technical Note — {d.ville}', 'sous_titre'))
    story.append(p('Indicative sizing ±15% — Must be verified by a licensed MEP engineer.', 'disc'))
    story.append(Spacer(1, 3*mm))

    # Project info
    story += section_title('1', 'PROJECT OVERVIEW')
    cw4 = [CW*0.28, CW*0.22, CW*0.28, CW*0.22]
    info = [
        [p('PARAMETER','th'), p('VALUE','th'), p('PARAMETER','th'), p('VALUE','th')],
        [p('Project','td_b'), p(d.nom), p('Location','td_b'), p(d.ville)],
        [p('Use','td_b'), p(d.usage.value.capitalize()), p('Levels','td_b'), p(str(d.nb_niveaux))],
        [p('Built area','td_b'), p(fmt_n(rm.surf_batie_m2,'','m²')), p('Units','td_b'), p(str(rm.nb_logements))],
        [p('Occupants','td_b'), p(str(rm.nb_personnes)), p('','td_b'), p('')],
    ]
    ti = Table(info, colWidths=cw4, repeatRows=1); ti.setStyle(table_style())
    story.append(ti)

    # ── ELECTRICAL ──
    story += section_title('2', 'ELECTRICAL INSTALLATION (NF C 15-100)')
    story.append(p(e.note_dimensionnement, 'body_j'))
    elec = [
        [p('PARAMETER','th'), p('VALUE','th'), p('DETAIL','th')],
        [p('Total power','td_b'), p(f'{e.puissance_totale_kva:.0f} kVA'), p(f'Lighting {e.puissance_eclairage_kw:.0f} + Sockets {e.puissance_prises_kw:.0f} kW')],
        [p('HVAC power','td_b'), p(f'{e.puissance_cvc_kw:.0f} kW'), p('')],
        [p('Lifts power','td_b'), p(f'{e.puissance_ascenseurs_kw:.0f} kW'), p('')],
        [p('Transformer','td_b'), p(f'{e.transfo_kva} kVA'), p('')],
        [p('Backup generator','td_b'), p(f'{e.groupe_electrogene_kva} kVA'), p('')],
        [p('Annual consumption','td_b'), p(f'{e.conso_annuelle_kwh:,.0f} kWh'), p(f'≈ {fmt_fcfa(e.facture_annuelle_fcfa)}/year')],
    ]
    te = Table(elec, colWidths=[CW*0.25, CW*0.25, CW*0.50], repeatRows=1); te.setStyle(table_style())
    story.append(te)
    if e.marques_recommandees:
        story.append(p(f'Recommended brands: {", ".join(e.marques_recommandees)}', 'note'))

    # ── PLUMBING ──
    story.append(PageBreak())
    story += section_title('3', 'PLUMBING (DTU 60.11 + EN 12056)')
    story.append(p(pl.note_dimensionnement, 'body_j'))
    plb = [
        [p('PARAMETER','th'), p('VALUE','th'), p('DETAIL','th')],
        [p('Daily demand','td_b'), p(f'{pl.besoin_total_m3_j:.1f} m³/day'), p(f'{pl.nb_personnes} occupants')],
        [p('Storage tank','td_b'), p(f'{pl.volume_citerne_m3:.0f} m³'), p('24h reserve')],
        [p('Booster pump','td_b'), p(f'{pl.debit_surpresseur_m3h:.1f} m³/h'), p('')],
        [p('Solar water heaters','td_b'), p(str(pl.nb_chauffe_eau_solaire)), p('Energy savings')],
        [p('Dual-flush WC','td_b'), p(str(pl.nb_wc_double_chasse)), p('Water savings 3/6L')],
        [p('Eco faucets','td_b'), p(str(pl.nb_robinets_eco)), p('6 L/min aerator')],
        [p('Annual water','td_b'), p(f'{pl.conso_eau_annuelle_m3:,.0f} m³'), p(f'≈ {fmt_fcfa(pl.facture_eau_fcfa)}/year')],
    ]
    tp = Table(plb, colWidths=[CW*0.25, CW*0.25, CW*0.50], repeatRows=1); tp.setStyle(table_style())
    story.append(tp)

    # ── HVAC ──
    story += section_title('4', 'HVAC — AIR CONDITIONING & VENTILATION')
    story.append(p(cvc.note_dimensionnement, 'body_j'))
    hvac = [
        [p('PARAMETER','th'), p('VALUE','th'), p('DETAIL','th')],
        [p('Cooling capacity','td_b'), p(f'{cvc.puissance_frigorifique_kw:.0f} kW'), p('')],
        [p('Living room splits','td_b'), p(str(cvc.nb_splits_sejour)), p('')],
        [p('Bedroom splits','td_b'), p(str(cvc.nb_splits_chambre)), p('')],
        [p('Cassette units','td_b'), p(str(cvc.nb_cassettes)), p('Common areas')],
        [p('Extract fans (VMC)','td_b'), p(str(cvc.nb_vmc)), p(cvc.type_vmc)],
        [p('Annual consumption','td_b'), p(f'{cvc.conso_cvc_kwh_an:,.0f} kWh'), p('')],
    ]
    tc = Table(hvac, colWidths=[CW*0.25, CW*0.25, CW*0.50], repeatRows=1); tc.setStyle(table_style())
    story.append(tc)

    # ── FIRE SAFETY ──
    story.append(PageBreak())
    story += section_title('5', 'FIRE SAFETY')
    story.append(p(si.note_dimensionnement, 'body_j'))
    fire = [
        [p('PARAMETER','th'), p('VALUE','th'), p('REMARK','th')],
        [p('ERP category','td_b'), p(si.categorie_erp), p('')],
        [p('Smoke detectors','td_b'), p(str(si.nb_detecteurs_fumee)), p('')],
        [p('Manual call points','td_b'), p(str(si.nb_declencheurs_manuels)), p('')],
        [p('Extinguishers (CO2/Powder)','td_b'), p(f'{si.nb_extincteurs_co2} / {si.nb_extincteurs_poudre}'), p('')],
        [p('Fire hose cabinets','td_b'), p(f'{si.longueur_ria_ml:.0f} ml'), p('')],
        [p('Sprinklers','td_b'), p(str(si.nb_tetes_sprinkler)), p('Required' if si.sprinklers_requis else 'Not required')],
        [p('Smoke extraction','td_b'), p('Required' if si.desenfumage_requis else 'Not required'), p('')],
    ]
    tsi = Table(fire, colWidths=[CW*0.30, CW*0.25, CW*0.45], repeatRows=1); tsi.setStyle(table_style())
    story.append(tsi)

    # ── LIFTS ──
    story += section_title('6', 'LIFTS & VERTICAL TRANSPORT')
    story.append(p(asc.note_dimensionnement, 'body_j'))
    lifts = [
        [p('PARAMETER','th'), p('VALUE','th')],
        [p('Passenger lifts','td_b'), p(str(asc.nb_ascenseurs))],
        [p('Capacity','td_b'), p(f'{asc.capacite_kg} kg')],
        [p('Speed','td_b'), p(f'{asc.vitesse_ms} m/s')],
        [p('Goods lifts','td_b'), p(str(asc.nb_monte_charges))],
        [p('Total power','td_b'), p(f'{asc.puissance_totale_kw:.0f} kW')],
    ]
    ta = Table(lifts, colWidths=[CW*0.50, CW*0.50], repeatRows=1); ta.setStyle(table_style())
    story.append(ta)
    if asc.note_impact_prix:
        story.append(p(f'ℹ {asc.note_impact_prix}', 'note'))

    # ── LOW CURRENT ──
    story += section_title('7', 'LOW-CURRENT SYSTEMS')
    story.append(p(cf.note_dimensionnement, 'body_j'))
    low = [
        [p('PARAMETER','th'), p('VALUE','th')],
        [p('RJ45 sockets','td_b'), p(str(cf.nb_prises_rj45))],
        [p('CCTV (indoor/outdoor)','td_b'), p(f'{cf.nb_cameras_int} / {cf.nb_cameras_ext}')],
        [p('Access control doors','td_b'), p(str(cf.nb_portes_controle_acces))],
        [p('Intercoms','td_b'), p(str(cf.nb_interphones))],
        [p('Server racks','td_b'), p(str(cf.baies_serveur))],
    ]
    tcf = Table(low, colWidths=[CW*0.50, CW*0.50], repeatRows=1); tcf.setStyle(table_style())
    story.append(tcf)

    # ── AUTOMATION ──
    story += section_title('8', 'BUILDING AUTOMATION (BMS)')
    story.append(p(auto.note_dimensionnement, 'body_j'))
    bms = [
        [p('PARAMETER','th'), p('VALUE','th')],
        [p('Automation level','td_b'), p(auto.niveau.capitalize())],
        [p('Protocol','td_b'), p(auto.protocole)],
        [p('Control points','td_b'), p(str(auto.nb_points_controle))],
        [p('BMS required','td_b'), p('Yes' if auto.bms_requis else 'No')],
    ]
    tau = Table(bms, colWidths=[CW*0.50, CW*0.50], repeatRows=1); tau.setStyle(table_style())
    story.append(tau)

    return story


# ════════════════════════════════════════════
# 2. EDGE REPORT
# ════════════════════════════════════════════
def generer_edge(rm, params: dict) -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rm.params.nom, 'EDGE Certification Report', lang='en')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    story = _build_edge(rm)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()

def _build_edge(rm):
    story = []

    if not hasattr(rm, 'edge') or rm.edge is None:
        return [Paragraph("EDGE data not available", S['titre'])]

    e = rm.edge

    story.append(Spacer(1, 3*mm))
    story.append(p(rm.params.nom, 'titre'))
    story.append(p('EDGE Certification Report — IFC / World Bank', 'sous_titre'))
    story.append(Spacer(1, 3*mm))

    story += section_title('1', 'PERFORMANCE SCORES')
    cert = '✓ CERTIFIABLE' if e.certifiable else '✗ NOT YET CERTIFIABLE'
    scores = [
        [p('PILLAR','th'), p('BASELINE','th'), p('PROJECT','th'), p('SAVINGS','th'), p('TARGET','th')],
        [p('Energy'), p(f'{e.base_energie_kwh_m2_an:.0f} kWh/m²/yr'), p(f'{e.projet_energie_kwh_m2_an:.0f}'), p(f'{e.economie_energie_pct:.1f}%'), p('≥ 20%')],
        [p('Water'), p(f'{e.base_eau_L_pers_j:.0f} L/pers/day'), p(f'{e.projet_eau_L_pers_j:.0f}'), p(f'{e.economie_eau_pct:.1f}%'), p('≥ 20%')],
        [p('Materials'), p(f'{e.base_ei_kwh_m2:.0f} kWh/m²'), p(f'{e.projet_ei_kwh_m2:.0f}'), p(f'{e.economie_materiaux_pct:.1f}%'), p('≥ 20%')],
    ]
    ts = Table(scores, colWidths=[CW*0.15, CW*0.22, CW*0.18, CW*0.15, CW*0.12], repeatRows=1); ts.setStyle(table_style())
    story.append(ts)
    story.append(p(f'{e.niveau_certification} — {cert}', 'td_g' if e.certifiable else 'td_o'))
    story.append(Spacer(1, 3*mm))

    for title_num, title_txt, measures in [
        ('2', 'ENERGY MEASURES', e.mesures_energie),
        ('3', 'WATER MEASURES', e.mesures_eau),
        ('4', 'MATERIALS MEASURES', e.mesures_materiaux),
    ]:
        story += section_title(title_num, title_txt)
        for m in measures:
            if isinstance(m, dict):
                prix = f' — {fmt_fcfa(m["impact_prix"])}' if m.get('impact_prix') else ''
                story.append(p(f'• {m.get("mesure","")} — +{m.get("gain_pct",0):.1f}% — {m.get("statut","")}{prix}', 'body'))

    if e.plan_action:
        story += section_title('5', 'ACTION PLAN — PATH TO CERTIFICATION')
        for a in e.plan_action:
            if isinstance(a, dict):
                story.append(p(f'→ [{a.get("pilier","").upper()}] {a.get("action","")} — +{a.get("gain_pct",0):.1f}% — {fmt_fcfa(a.get("cout_fcfa",0))}', 'body'))

    story += section_title('6', 'COST AND ROI')
    story.append(p(f'Compliance cost: {fmt_fcfa(e.cout_mise_conformite_fcfa)} | Payback: {e.roi_ans:.1f} years | Method: {e.methode_calcul}', 'body'))
    story.append(p(e.note_generale, 'bleu'))

    return story


# ════════════════════════════════════════════
# 3. EXECUTIVE REPORT
# ════════════════════════════════════════════
def generer_rapport_executif(rs, rm, params: dict) -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rs.params.nom, 'Executive Summary Report', lang='en')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    story = _build_exec(rs, rm)
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()

def _build_exec(rs, rm):
    story = []
    boq = rs.boq; bmep = rm.boq; e = rm.edge; ana = rs.analyse

    story.append(Spacer(1, 3*mm))
    story.append(p(rs.params.nom, 'titre'))
    story.append(p('Executive Summary — Owner / Investor Brief', 'sous_titre'))
    story.append(Spacer(1, 3*mm))

    story += section_title('1', 'STRUCTURAL OVERVIEW')
    story.append(p(f'Concrete: {rs.classe_beton} — Steel: {rs.classe_acier}', 'body'))
    story.append(p(f'Total concrete: {boq.beton_total_m3:.0f} m³ — Total steel: {fmt_n(boq.acier_kg,0)} kg', 'body'))
    story.append(p(f'Structural cost: {fmt_fcfa(boq.total_bas_fcfa)} – {fmt_fcfa(boq.total_haut_fcfa)}', 'body'))

    story += section_title('2', 'MEP OVERVIEW')
    story.append(p(f'MEP Basic: {fmt_fcfa(bmep.total_basic_fcfa)} | High-End: {fmt_fcfa(bmep.total_hend_fcfa)} | Luxury: {fmt_fcfa(bmep.total_luxury_fcfa)}', 'body'))
    story.append(p(f'Recommendation: {bmep.recommandation}', 'body'))

    story += section_title('3', 'TOTAL PROJECT COST')
    total_bas = boq.total_bas_fcfa + bmep.total_basic_fcfa
    total_haut = boq.total_haut_fcfa + bmep.total_hend_fcfa
    cost = [
        [p('ITEM','th'), p('LOW ESTIMATE','th'), p('HIGH ESTIMATE','th')],
        [p('Structure','td_b'), p(fmt_fcfa(boq.total_bas_fcfa),'td_r'), p(fmt_fcfa(boq.total_haut_fcfa),'td_r')],
        [p('MEP (Basic / High-End)','td_b'), p(fmt_fcfa(bmep.total_basic_fcfa),'td_r'), p(fmt_fcfa(bmep.total_hend_fcfa),'td_r')],
        [p('TOTAL','td_b'), p(fmt_fcfa(total_bas),'td_g_r'), p(fmt_fcfa(total_haut),'td_g_r')],
        [p('Cost / m² built','td_b'), p(f'{total_bas//max(int(rm.surf_batie_m2),1):,} FCFA/m²'.replace(',', ' '),'td_r'),
         p(f'{total_haut//max(int(rm.surf_batie_m2),1):,} FCFA/m²'.replace(',', ' '),'td_r')],
    ]
    tc = Table(cost, colWidths=[CW*0.40, CW*0.30, CW*0.30], repeatRows=1)
    tsc = table_style(); total_row_style(tsc); tc.setStyle(tsc)
    story.append(tc)

    story += section_title('4', 'EDGE GREEN CERTIFICATION')
    story.append(p(f'Energy: {e.economie_energie_pct:.0f}% | Water: {e.economie_eau_pct:.0f}% | Materials: {e.economie_materiaux_pct:.0f}%', 'body'))
    story.append(p(f'{e.niveau_certification} — {"Certifiable" if e.certifiable else "Action plan required"} — Compliance cost: {fmt_fcfa(e.cout_mise_conformite_fcfa)}', 'body'))

    if ana.recommandations:
        story += section_title('5', 'KEY RECOMMENDATIONS')
        for r in ana.recommandations:
            story.append(p(f'→ {r}', 'body'))

    if ana.alertes:
        story += section_title('6', 'ALERTS')
        for a in ana.alertes:
            story.append(p(f'⚠ {a}', 'note'))

    return story

"""
gen_mep_en.py — English MEP Technical Note + EDGE Report + Executive Report
Native EN generator. Mirrors gen_mep.py (FR).
Signatures:
  generer_note_mep(rm, params_dict) → bytes
  generer_edge(rm, params_dict) → bytes
  generer_rapport_executif(rs, rm, params_dict) → bytes
Input: rm = ResultatsMEP from engine_mep_v2, params_dict = ParamsProjet.dict()
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.platypus.flowables import HRFlowable

TIJAN_BLACK=HexColor("#111111"); TIJAN_GREY=HexColor("#555555"); TIJAN_GREEN=HexColor("#43A956")
TIJAN_LIGHT=HexColor("#FAFAFA"); TIJAN_WHITE=HexColor("#FFFFFF"); TIJAN_BORDER=HexColor("#E0E0E0")
PAGE_W,PAGE_H=A4; M=20*mm

def _S():
    s=getSampleStyleSheet()
    for n,c in {
        'TT':dict(fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=TIJAN_BLACK,alignment=TA_CENTER,spaceAfter=6*mm),
        'H1':dict(fontName='Helvetica-Bold',fontSize=13,leading=16,textColor=TIJAN_BLACK,spaceBefore=8*mm,spaceAfter=3*mm),
        'H2':dict(fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=TIJAN_GREY,spaceBefore=4*mm,spaceAfter=2*mm),
        'BD':dict(fontName='Helvetica',fontSize=9.5,leading=13,textColor=TIJAN_BLACK,alignment=TA_JUSTIFY,spaceAfter=2*mm),
        'SM':dict(fontName='Helvetica',fontSize=8,leading=10,textColor=TIJAN_GREY,alignment=TA_CENTER),
        'TH':dict(fontName='Helvetica-Bold',fontSize=8.5,leading=11,textColor=TIJAN_WHITE,alignment=TA_CENTER),
        'TC':dict(fontName='Helvetica',fontSize=8.5,leading=11,textColor=TIJAN_BLACK,alignment=TA_CENTER),
        'TL':dict(fontName='Helvetica',fontSize=8.5,leading=11,textColor=TIJAN_BLACK,alignment=TA_LEFT),
        'TR':dict(fontName='Helvetica',fontSize=8.5,leading=11,textColor=TIJAN_BLACK,alignment=TA_RIGHT),
    }.items():
        s.add(ParagraphStyle(name=n,**c))
    return s

def _hf(title_en):
    def _cb(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(TIJAN_GREEN); canvas.setLineWidth(1.5)
        canvas.line(M, PAGE_H-15*mm, PAGE_W-M, PAGE_H-15*mm)
        canvas.setFont("Helvetica-Bold",8); canvas.setFillColor(TIJAN_BLACK)
        canvas.drawString(M, PAGE_H-13*mm, "TIJAN AI")
        canvas.setFont("Helvetica",8); canvas.setFillColor(TIJAN_GREY)
        canvas.drawRightString(PAGE_W-M, PAGE_H-13*mm, title_en)
        canvas.setStrokeColor(TIJAN_BORDER); canvas.setLineWidth(0.5)
        canvas.line(M, 12*mm, PAGE_W-M, 12*mm)
        canvas.setFont("Helvetica",7); canvas.setFillColor(TIJAN_GREY)
        canvas.drawString(M, 8*mm, "Tijan AI — BIM & MEP Engineering Automation")
        canvas.drawRightString(PAGE_W-M, 8*mm, f"Page {doc.page}")
        canvas.restoreState()
    return _cb

def _info(data, S, c1=60*mm, c2=100*mm):
    rows=[[Paragraph(f"<b>{r[0]}</b>",S['BD']),Paragraph(str(r[1]),S['BD'])] for r in data]
    t=Table(rows,colWidths=[c1,c2])
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER),('BACKGROUND',(0,0),(0,-1),TIJAN_LIGHT),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)]))
    return t

def _disclaimer(S):
    return [Spacer(1,10*mm), HRFlowable(width="100%",thickness=0.5,color=TIJAN_BORDER,spaceAfter=3*mm),
            Paragraph("<b>Disclaimer:</b> This document has been generated automatically. "
                      "It must be reviewed by a qualified MEP engineer before implementation. "
                      "Tijan AI accepts no liability for use without professional verification.", S['SM'])]

def _cover(story, S, title, subtitle, p, rm):
    story += [Spacer(1,25*mm), Paragraph(title, S['TT'])]
    if subtitle: story.append(Paragraph(subtitle, S['SM']))
    story += [Spacer(1,3*mm), HRFlowable(width="60%",thickness=2,color=TIJAN_GREEN,spaceAfter=8*mm)]
    story.append(_info([
        ["Project", p.get('nom','Project')],
        ["Location", f"{p.get('ville','Dakar')}, {p.get('pays','Senegal')}"],
        ["Building use", p.get('usage','residential').capitalize()],
        ["Levels", str(p.get('nb_niveaux',4))],
        ["Built area", f"{rm.surf_batie_m2:,.0f} m²"],
        ["Units", str(rm.nb_logements)],
        ["Occupants", str(rm.nb_personnes)],
    ], S))
    story.append(PageBreak())


# ════════════════════════════════════════════
# 1. MEP TECHNICAL NOTE
# ════════════════════════════════════════════
def generer_note_mep(rm, params_dict: dict) -> bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=22*mm,bottomMargin=18*mm,leftMargin=M,rightMargin=M)
    S=_S(); story=[]; p=params_dict or {}
    cb=_hf("MEP Technical Note")

    _cover(story, S, "MEP TECHNICAL NOTE", "Electrical · Plumbing · HVAC · Fire Safety · Lifts", p, rm)

    # ELECTRICAL
    story.append(Paragraph("1. ELECTRICAL INSTALLATION", S['H1']))
    story.append(Paragraph("1.1 Regulatory Framework", S['H2']))
    story.append(Paragraph("Design per NF C 15-100 (low-voltage installations) and NF C 14-100 (utility connection). "
                           "TN-S earthing system. 30 mA RCDs on all final circuits.", S['BD']))
    e = rm.electrique
    story.append(Paragraph("1.2 Power Assessment", S['H2']))
    story.append(Paragraph(
        f"<b>Total installed power:</b> {e.puissance_totale_kW:.1f} kW<br/>"
        f"<b>Simultaneity factor:</b> {e.coef_simultaneite:.2f}<br/>"
        f"<b>Design power:</b> {e.puissance_dimensionnement_kW:.1f} kW<br/>"
        f"<b>Main breaker:</b> {e.disjoncteur_general}<br/>"
        f"<b>Transformer:</b> {e.transfo_kVA:.0f} kVA", S['BD']))
    story.append(Paragraph("1.3 Earthing & Surge Protection", S['H2']))
    story.append(Paragraph(
        "Earth electrode: copper-clad rod, R ≤ 10 Ω. Main equipotential bonding per NF C 15-100 §411. "
        "SPD Type 2 at main distribution board. Emergency lighting in common areas.", S['BD']))
    story.append(PageBreak())

    # PLUMBING
    story.append(Paragraph("2. PLUMBING INSTALLATION", S['H1']))
    story.append(Paragraph("Design per DTU 60.11 (sizing) and EN 12056 (drainage).", S['BD']))
    pl = rm.plomberie
    story.append(Paragraph("2.1 Cold Water Supply", S['H2']))
    story.append(Paragraph(
        f"<b>Total flow rate:</b> {pl.debit_total_Ls:.2f} L/s<br/>"
        f"<b>Supply pressure:</b> {pl.pression_reseau_bar:.1f} bar<br/>"
        f"<b>Pipe material:</b> PPR (hot) / PVC-C (cold)", S['BD']))
    story.append(Paragraph("2.2 Hot Water & Drainage", S['H2']))
    story.append(Paragraph(
        f"Hot water: {pl.type_production_ecs}<br/>"
        f"Design temp: 60°C storage / 50°C distribution / anti-Legionella 70°C weekly<br/>"
        f"Drainage: gravity per EN 12056-2 — separated wastewater and rainwater", S['BD']))
    story.append(PageBreak())

    # HVAC
    story.append(Paragraph("3. HVAC — HEATING, VENTILATION & AIR CONDITIONING", S['H1']))
    cvc = rm.cvc
    story.append(Paragraph(
        f"<b>Total cooling load:</b> {cvc.puissance_froid_kW:.1f} kW<br/>"
        f"<b>System:</b> {cvc.type_systeme}<br/>"
        f"<b>Refrigerant:</b> {cvc.refrigerant}<br/>"
        f"<b>Design conditions:</b> indoor 24°C / outdoor {cvc.t_ext_design_C:.0f}°C", S['BD']))
    story.append(Paragraph("3.1 Ventilation", S['H2']))
    story.append(Paragraph(
        "Natural ventilation + mechanical extract in wet rooms. "
        "Rates: kitchen 75 m³/h, bathroom 30 m³/h, WC 15 m³/h.", S['BD']))
    story.append(PageBreak())

    # FIRE SAFETY
    story.append(Paragraph("4. FIRE SAFETY", S['H1']))
    si = rm.securite_incendie
    story.append(Paragraph(
        f"<b>Building classification:</b> {si.classification_batiment}<br/>"
        f"<b>Fire detection:</b> {si.type_detection}<br/>"
        f"<b>Extinguishers:</b> {si.nb_extincteurs} units<br/>"
        f"<b>Fire hose cabinets:</b> {si.nb_ria} RIA", S['BD']))

    # LIFTS
    story.append(Paragraph("5. LIFTS", S['H1']))
    asc = rm.ascenseurs
    story.append(Paragraph(
        f"<b>Number of lifts:</b> {asc.nb_ascenseurs}<br/>"
        f"<b>Capacity:</b> {asc.capacite_personnes} persons ({asc.charge_kg} kg)<br/>"
        f"<b>Type:</b> {asc.type_ascenseur}<br/>"
        f"<b>Speed:</b> {asc.vitesse_ms:.1f} m/s", S['BD']))

    # LOW CURRENT
    story.append(Paragraph("6. LOW-CURRENT SYSTEMS", S['H1']))
    cf = rm.courants_faibles
    story.append(Paragraph(
        f"<b>Intercom:</b> {cf.type_interphone}<br/>"
        f"<b>CCTV cameras:</b> {cf.nb_cameras}<br/>"
        f"<b>Network:</b> {cf.type_reseau}", S['BD']))

    # REFERENCES
    story += [Spacer(1,8*mm), Paragraph("REFERENCES", S['H2']), Paragraph(
        "NF C 15-100 — Low-voltage electrical installations<br/>"
        "DTU 60.11 — Sanitary installation sizing<br/>"
        "EN 12056 — Gravity drainage<br/>"
        "EN 12831 — Heating load calculation<br/>"
        "ASHRAE 55 — Thermal comfort", S['BD'])]
    story += _disclaimer(S)

    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    buf.seek(0); return buf.read()


# ════════════════════════════════════════════
# 2. EDGE REPORT
# ════════════════════════════════════════════
def generer_edge(rm, params_dict: dict) -> bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=22*mm,bottomMargin=18*mm,leftMargin=M,rightMargin=M)
    S=_S(); story=[]; p=params_dict or {}
    cb=_hf("EDGE Certification Report")

    _cover(story, S, "EDGE CERTIFICATION REPORT", "IFC / World Bank — Green Building Standard", p, rm)

    e = rm.edge
    story.append(Paragraph("1. EDGE OVERVIEW", S['H1']))
    story.append(Paragraph(
        "EDGE (Excellence in Design for Greater Efficiencies) is the IFC/World Bank green building "
        "certification system. Minimum requirement: 20% savings in energy, water, and embodied energy "
        "vs. local baseline.", S['BD']))

    story.append(Paragraph("2. PERFORMANCE SCORES", S['H1']))
    cert = "✅ CERTIFIABLE" if e.certifiable else "❌ NOT YET CERTIFIABLE"
    story.append(_info([
        ["Energy savings", f"{e.economie_energie_pct:.1f}% (target ≥ 20%)"],
        ["Water savings", f"{e.economie_eau_pct:.1f}% (target ≥ 20%)"],
        ["Materials savings", f"{e.economie_materiaux_pct:.1f}% (target ≥ 20%)"],
        ["Certification level", e.niveau_certification],
        ["Status", cert],
    ], S))

    story.append(Paragraph("3. ENERGY MEASURES", S['H1']))
    for m in e.mesures_energie: story.append(Paragraph(f"• {m}", S['BD']))
    story.append(Paragraph("4. WATER MEASURES", S['H1']))
    for m in e.mesures_eau: story.append(Paragraph(f"• {m}", S['BD']))
    story.append(Paragraph("5. MATERIALS MEASURES", S['H1']))
    for m in e.mesures_materiaux: story.append(Paragraph(f"• {m}", S['BD']))

    if e.plan_action:
        story.append(Paragraph("6. ACTION PLAN", S['H1']))
        for a in e.plan_action: story.append(Paragraph(f"→ {a}", S['BD']))

    story.append(Paragraph("7. COST AND ROI", S['H1']))
    story.append(Paragraph(
        f"<b>Compliance cost:</b> {e.cout_mise_conformite_fcfa:,.0f} FCFA<br/>"
        f"<b>Payback period:</b> {e.roi_ans:.1f} years<br/>"
        f"<b>Calculation method:</b> {e.methode_calcul}", S['BD']))

    story += _disclaimer(S)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    buf.seek(0); return buf.read()


# ════════════════════════════════════════════
# 3. EXECUTIVE REPORT
# ════════════════════════════════════════════
def generer_rapport_executif(rs, rm, params_dict: dict) -> bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=22*mm,bottomMargin=18*mm,leftMargin=M,rightMargin=M)
    S=_S(); story=[]; p=params_dict or {}
    cb=_hf("Executive Summary Report")

    _cover(story, S, "EXECUTIVE SUMMARY REPORT", "Owner / Investor Technical Brief", p, rm)

    story.append(Paragraph("1. STRUCTURAL OVERVIEW", S['H1']))
    boq = rs.boq
    story.append(Paragraph(
        f"<b>Concrete class:</b> {rs.classe_beton} — <b>Steel:</b> {rs.classe_acier}<br/>"
        f"<b>Total concrete:</b> {boq.beton_total_m3:.0f} m³ — <b>Total steel:</b> {boq.acier_total_kg:,.0f} kg<br/>"
        f"<b>Estimated structural cost:</b> {boq.cout_total_fcfa:,.0f} FCFA", S['BD']))

    story.append(Paragraph("2. MEP OVERVIEW", S['H1']))
    bmep = rm.boq
    story.append(Paragraph(
        f"<b>MEP cost (Basic):</b> {bmep.total_basic_fcfa:,.0f} FCFA<br/>"
        f"<b>MEP cost (High-End):</b> {bmep.total_hend_fcfa:,.0f} FCFA<br/>"
        f"<b>Recommendation:</b> {bmep.recommandation}", S['BD']))

    story.append(Paragraph("3. TOTAL PROJECT COST ESTIMATE", S['H1']))
    total_basic = boq.cout_total_fcfa + bmep.total_basic_fcfa
    total_hend = boq.cout_total_fcfa + bmep.total_hend_fcfa
    story.append(_info([
        ["Structure", f"{boq.cout_total_fcfa:,.0f} FCFA"],
        ["MEP (Basic)", f"{bmep.total_basic_fcfa:,.0f} FCFA"],
        ["MEP (High-End)", f"{bmep.total_hend_fcfa:,.0f} FCFA"],
        ["TOTAL (Basic)", f"{total_basic:,.0f} FCFA"],
        ["TOTAL (High-End)", f"{total_hend:,.0f} FCFA"],
        ["Cost / m² (Basic)", f"{total_basic/max(rm.surf_batie_m2,1):,.0f} FCFA/m²"],
    ], S))

    story.append(Paragraph("4. EDGE GREEN CERTIFICATION", S['H1']))
    e = rm.edge
    story.append(Paragraph(
        f"Energy: {e.economie_energie_pct:.0f}% | Water: {e.economie_eau_pct:.0f}% | "
        f"Materials: {e.economie_materiaux_pct:.0f}%<br/>"
        f"<b>Status:</b> {e.niveau_certification} — "
        f"{'Certifiable' if e.certifiable else 'Action plan required'}", S['BD']))

    if hasattr(rs, 'analyse') and rs.analyse:
        a = rs.analyse
        if hasattr(a, 'recommandations') and a.recommandations:
            story.append(Paragraph("5. KEY RECOMMENDATIONS", S['H1']))
            for r in a.recommandations: story.append(Paragraph(f"• {r}", S['BD']))

    story += _disclaimer(S)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    buf.seek(0); return buf.read()

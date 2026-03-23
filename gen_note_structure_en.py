"""
gen_note_structure_en.py — English Structural Calculation Note (9 pages)
Native EN generator. Mirrors gen_note_structure.py (FR).
Signature: generer(rs, params_dict) → bytes
Input: rs = ResultatsStructure from engine_structure_v2, params_dict = ParamsProjet.dict()
"""

import io
import dataclasses
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.platypus.flowables import HRFlowable

TIJAN_BLACK  = HexColor("#111111")
TIJAN_GREY   = HexColor("#555555")
TIJAN_GREEN  = HexColor("#43A956")
TIJAN_LIGHT  = HexColor("#FAFAFA")
TIJAN_WHITE  = HexColor("#FFFFFF")
TIJAN_BORDER = HexColor("#E0E0E0")
PAGE_W, PAGE_H = A4
M = 20 * mm

def _S():
    s = getSampleStyleSheet()
    for n, c in {
        'TT': dict(fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=TIJAN_BLACK, alignment=TA_CENTER, spaceAfter=6*mm),
        'H1': dict(fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=TIJAN_BLACK, spaceBefore=8*mm, spaceAfter=3*mm),
        'H2': dict(fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=TIJAN_GREY, spaceBefore=4*mm, spaceAfter=2*mm),
        'BD': dict(fontName='Helvetica', fontSize=9.5, leading=13, textColor=TIJAN_BLACK, alignment=TA_JUSTIFY, spaceAfter=2*mm),
        'SM': dict(fontName='Helvetica', fontSize=8, leading=10, textColor=TIJAN_GREY, alignment=TA_CENTER),
        'TH': dict(fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=TIJAN_WHITE, alignment=TA_CENTER),
        'TC': dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_CENTER),
        'TL': dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_LEFT),
    }.items():
        s.add(ParagraphStyle(name=n, **c))
    return s

def _hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TIJAN_GREEN); canvas.setLineWidth(1.5)
    canvas.line(M, PAGE_H-15*mm, PAGE_W-M, PAGE_H-15*mm)
    canvas.setFont("Helvetica-Bold", 8); canvas.setFillColor(TIJAN_BLACK)
    canvas.drawString(M, PAGE_H-13*mm, "TIJAN AI")
    canvas.setFont("Helvetica", 8); canvas.setFillColor(TIJAN_GREY)
    canvas.drawRightString(PAGE_W-M, PAGE_H-13*mm, "Structural Calculation Note")
    canvas.setStrokeColor(TIJAN_BORDER); canvas.setLineWidth(0.5)
    canvas.line(M, 12*mm, PAGE_W-M, 12*mm)
    canvas.setFont("Helvetica", 7); canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(M, 8*mm, "Tijan AI — BIM & Structural Engineering Automation")
    canvas.drawRightString(PAGE_W-M, 8*mm, f"Page {doc.page}")
    canvas.restoreState()

def _tbl(headers, rows, cw, S):
    data = [[Paragraph(h, S['TH']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S['TC'] if i > 0 else S['TL']) for i, c in enumerate(row)])
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),TIJAN_GREEN), ('TEXTCOLOR',(0,0),(-1,0),white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[TIJAN_WHITE,TIJAN_LIGHT]),
        ('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6), ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    return t

def _info_table(data, S, c1=55*mm, c2=105*mm):
    rows = [[Paragraph(f"<b>{r[0]}</b>", S['BD']), Paragraph(str(r[1]), S['BD'])] for r in data]
    t = Table(rows, colWidths=[c1, c2])
    t.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER), ('BACKGROUND',(0,0),(0,-1),TIJAN_LIGHT),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5), ('LEFTPADDING',(0,0),(-1,-1),8),
    ]))
    return t


def generer(rs, params_dict: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22*mm, bottomMargin=18*mm, leftMargin=M, rightMargin=M)
    S = _S(); story = []; p = params_dict or {}

    nom = p.get('nom','Project'); ville = p.get('ville','Dakar'); pays = p.get('pays','Senegal')
    niv = p.get('nb_niveaux',4); surf = p.get('surface_emprise_m2',500)
    usage = p.get('usage','residential'); pmax = p.get('portee_max_m',5.5); pmin = p.get('portee_min_m',4.0)

    # ── P1 COVER ──
    story += [Spacer(1,30*mm), Paragraph("STRUCTURAL CALCULATION NOTE", S['TT']),
              HRFlowable(width="60%", thickness=2, color=TIJAN_GREEN, spaceAfter=8*mm)]
    story.append(_info_table([
        ["Project", nom], ["Location", f"{ville}, {pays}"], ["Building use", usage.capitalize()],
        ["Number of levels", str(niv)], ["Footprint area", f"{surf:,.0f} m²"],
        ["Max / Min span", f"{pmax} m / {pmin} m"], ["Concrete class", rs.classe_beton],
        ["Reinforcement steel", rs.classe_acier], ["Seismic zone", str(rs.zone_sismique)],
        ["Applicable codes", "Eurocode 2 (EC2), Eurocode 8 (EC8)"],
    ], S))
    story += [Spacer(1,12*mm), Paragraph(
        "This document has been automatically generated by the Tijan AI structural engine "
        "in compliance with Eurocodes EC2 and EC8.", S['SM']), PageBreak()]

    # ── P2 DESIGN ASSUMPTIONS ──
    story.append(Paragraph("1. DESIGN ASSUMPTIONS", S['H1']))
    story.append(Paragraph("1.1 Materials", S['H2']))
    story.append(Paragraph(
        f"<b>Concrete:</b> {rs.classe_beton} — Suppliers: CIMAF / SOCOCIM<br/>"
        f"<b>Steel:</b> {rs.classe_acier} — Supplier: Fabrimetal Sénégal (Sébikotane)", S['BD']))
    story.append(Paragraph("1.2 Loads (Eurocode 1)", S['H2']))
    story.append(Paragraph(
        f"<b>Dead load:</b> G = {rs.charge_G_kNm2:.2f} kN/m²<br/>"
        f"<b>Live load ({usage}):</b> Q = {rs.charge_Q_kNm2:.2f} kN/m²", S['BD']))
    story.append(Paragraph("1.3 Load Combinations (EC0)", S['H2']))
    story.append(Paragraph(
        "<b>ULS:</b> 1.35G + 1.5Q &nbsp; | &nbsp; <b>SLS char.:</b> G + Q &nbsp; | &nbsp; "
        "<b>SLS quasi-perm.:</b> G + ψ<sub>2</sub>Q", S['BD']))
    story.append(Paragraph("1.4 Exposure and Durability", S['H2']))
    expo = "XS1 (coastal)" if rs.distance_mer_km < 5 else "XC1 (internal)"
    story.append(Paragraph(f"Exposure class: {expo} — Distance to sea: {rs.distance_mer_km:.1f} km. "
                           f"Design service life: 50 years.", S['BD']))
    story.append(Paragraph("1.5 Geotechnical Data", S['H2']))
    story.append(Paragraph(
        f"Allowable bearing pressure: {rs.pression_sol_MPa:.3f} MPa ({rs.pression_sol_MPa*1000:.0f} kPa)<br/>"
        f"Foundation type: {rs.fondation.type_fondation}", S['BD']))
    sism = rs.sismique
    story.append(Paragraph("1.6 Seismic Parameters (EC8)", S['H2']))
    story.append(Paragraph(
        f"Zone: {rs.zone_sismique} — a<sub>g</sub> = {sism.ag:.2f}g, S = {sism.S:.2f}, "
        f"q = {sism.q:.1f} ({sism.classe_ductilite})<br/>"
        f"Importance: {sism.classe_importance} — γ<sub>I</sub> = {sism.gamma_I:.1f}", S['BD']))
    story.append(PageBreak())

    # ── P3 SLAB ──
    story.append(Paragraph("2. SLAB DESIGN", S['H1']))
    d = rs.dalle
    story.append(_info_table([
        ["Slab type", d.type_dalle], ["Thickness (cm)", f"{d.epaisseur_cm:.0f}"],
        ["Span moment M+ (kN·m/ml)", f"{d.moment_travee_kNm_ml:.1f}"],
        ["Support moment M- (kN·m/ml)", f"{d.moment_appui_kNm_ml:.1f}"],
        ["Bottom reinforcement", d.acier_travee], ["Top reinforcement", d.acier_appui],
        ["Deflection check", d.verification_fleche],
    ], S, c1=70*mm, c2=90*mm))
    story.append(Paragraph(
        "Design per EC2 §5.3 (one-way/two-way). Moments via simplified coefficient method. "
        "Deflection checked L/250 and L/500. Min. reinforcement per EC2 §9.2.1.1.", S['BD']))
    story.append(PageBreak())

    # ── P4 BEAMS ──
    story.append(Paragraph("3. BEAM DESIGN", S['H1']))
    for label, poutre in [("3.1 Main Beam", rs.poutre_principale),
                           ("3.2 Secondary Beam", rs.poutre_secondaire)]:
        if poutre is None: continue
        story.append(Paragraph(label, S['H2']))
        story.append(_info_table([
            ["Section b × h (cm)", f"{poutre.largeur_cm:.0f} × {poutre.hauteur_cm:.0f}"],
            ["Span (m)", f"{poutre.portee_m:.2f}"],
            ["Span moment M+ (kN·m)", f"{poutre.moment_travee_kNm:.1f}"],
            ["Support moment M- (kN·m)", f"{poutre.moment_appui_kNm:.1f}"],
            ["Shear force V (kN)", f"{poutre.effort_tranchant_kN:.1f}"],
            ["Bottom reinforcement", poutre.acier_travee],
            ["Top reinforcement", poutre.acier_appui],
            ["Stirrups", poutre.cadres], ["Verification", poutre.verification],
        ], S, c1=65*mm, c2=95*mm))
    story.append(Paragraph("Shear per EC2 §6.2. Seismic critical zone detailing per EC8 §5.4.3.", S['BD']))
    story.append(PageBreak())

    # ── P5 COLUMNS ──
    story.append(Paragraph("4. COLUMN DESIGN", S['H1']))
    cols = [["Level","Section (cm)","NEd (kN)","Reinforcement","ρ (%)","λ","Check"]]
    for po in rs.poteaux:
        cols.append([po.niveau, po.section_cm, f"{po.ned_kN:.0f}", po.armatures,
                     f"{po.taux_armatures_pct:.2f}", f"{po.elancement:.0f}", po.verification])
    if len(cols) > 1:
        story.append(_tbl(cols[0], cols[1:], [18*mm,22*mm,20*mm,28*mm,16*mm,14*mm,20*mm], S))
    story.append(Paragraph("Slenderness per EC2 §5.8.3.1. Second-order via nominal curvature §5.8.8. "
                           "Biaxial bending per §5.8.9.", S['BD']))
    story.append(PageBreak())

    # ── P6 FOUNDATION ──
    story.append(Paragraph("5. FOUNDATION DESIGN", S['H1']))
    f = rs.fondation
    fd = [["Foundation type", f.type_fondation],
          ["Bearing pressure", f"{rs.pression_sol_MPa*1000:.0f} kPa"],
          ["Dimensions", f.dimensions], ["Depth", f.profondeur],
          ["Reinforcement", f.armatures], ["Verification", f.verification]]
    if hasattr(f, 'beton_proprete'): fd.append(["Lean concrete", f.beton_proprete])
    story.append(_info_table(fd, S))
    story.append(Paragraph("Design per EC2 §6.4 (punching) and §9.8. Bearing per EC7 DA2.", S['BD']))
    story.append(PageBreak())

    # ── P7 SEISMIC ──
    story.append(Paragraph("6. SEISMIC VERIFICATION (EC8)", S['H1']))
    story.append(Paragraph(
        f"a<sub>g</sub> = {sism.ag:.2f}g, S = {sism.S:.2f}, q = {sism.q:.1f}<br/>"
        f"Seismic weight: {sism.poids_sismique_kN:.0f} kN — Base shear: V<sub>b</sub> = {sism.effort_base_kN:.0f} kN", S['BD']))
    story.append(Paragraph(
        "<b>Capacity design:</b> ΣM<sub>Rc</sub> ≥ 1.3·ΣM<sub>Rb</sub><br/>"
        "<b>Interstorey drift:</b> d<sub>r</sub>·ν ≤ 0.005·h", S['BD']))
    if hasattr(sism, 'verifications') and sism.verifications:
        for v in sism.verifications:
            story.append(Paragraph(f"• {v}", S['BD']))
    story.append(PageBreak())

    # ── P8 BOQ SUMMARY ──
    story.append(Paragraph("7. BILL OF QUANTITIES — SUMMARY", S['H1']))
    boq = rs.boq
    story.append(Paragraph(
        f"<b>Total concrete:</b> {boq.beton_total_m3:.1f} m³<br/>"
        f"<b>Total steel:</b> {boq.acier_total_kg:.0f} kg<br/>"
        f"<b>Total formwork:</b> {boq.coffrage_total_m2:.0f} m²<br/>"
        f"<b>Estimated cost:</b> {boq.cout_total_fcfa:,.0f} FCFA excl. tax", S['BD']))
    story.append(Paragraph("Detailed BOQ (7 lots) available via /generate-boq endpoint.", S['BD']))
    story.append(PageBreak())

    # ── P9 CONCLUSION ──
    story.append(Paragraph("8. CONCLUSION AND RECOMMENDATIONS", S['H1']))
    if hasattr(rs, 'analyse'):
        a = rs.analyse
        if hasattr(a, 'resume') and a.resume: story.append(Paragraph(a.resume, S['BD']))
        if hasattr(a, 'recommandations') and a.recommandations:
            story.append(Paragraph("8.1 Recommendations", S['H2']))
            for r in a.recommandations: story.append(Paragraph(f"• {r}", S['BD']))
        if hasattr(a, 'alertes') and a.alertes:
            story.append(Paragraph("8.2 Alerts", S['H2']))
            for al in a.alertes: story.append(Paragraph(f"⚠ {al}", S['BD']))

    story += [Spacer(1,8*mm), Paragraph("REFERENCES", S['H2']), Paragraph(
        "EN 1990 — Basis of structural design<br/>EN 1991 — Actions on structures<br/>"
        "EN 1992-1-1 — Design of concrete structures<br/>EN 1997-1 — Geotechnical design<br/>"
        "EN 1998-1 — Seismic design", S['BD'])]
    story += [Spacer(1,10*mm), HRFlowable(width="100%", thickness=0.5, color=TIJAN_BORDER, spaceAfter=3*mm),
              Paragraph("<b>Disclaimer:</b> This document has been generated automatically. "
                        "It must be reviewed by a qualified structural engineer before construction. "
                        "Tijan AI accepts no liability for use without professional verification.", S['SM'])]

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()

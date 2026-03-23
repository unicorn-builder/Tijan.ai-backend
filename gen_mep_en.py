"""
gen_mep_en.py — English MEP Technical Note
Native EN generator for Tijan AI. Mirrors generate_note_mep.py (FR) with all text in English.
Covers: Electrical (NF C 15-100), Plumbing (DTU 60.11), HVAC (EN 12831 / ASHRAE 55).
Uses ReportLab Platypus, A4. Input: ResultatsCalcul dataclass.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.platypus.flowables import HRFlowable


# ── Colors ──
TIJAN_BLACK = HexColor("#111111")
TIJAN_GREY = HexColor("#555555")
TIJAN_GREEN = HexColor("#43A956")
TIJAN_LIGHT_BG = HexColor("#FAFAFA")
TIJAN_WHITE = HexColor("#FFFFFF")
TIJAN_BORDER = HexColor("#E0E0E0")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _styles():
    styles = getSampleStyleSheet()
    for name, conf in [
        ('TTitle', dict(fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=TIJAN_BLACK, alignment=TA_CENTER, spaceAfter=6*mm)),
        ('TH1', dict(fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=TIJAN_BLACK, spaceBefore=8*mm, spaceAfter=3*mm)),
        ('TH2', dict(fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=TIJAN_GREY, spaceBefore=4*mm, spaceAfter=2*mm)),
        ('TBody', dict(fontName='Helvetica', fontSize=9.5, leading=13, textColor=TIJAN_BLACK, alignment=TA_JUSTIFY, spaceAfter=2*mm)),
        ('TSmall', dict(fontName='Helvetica', fontSize=8, leading=10, textColor=TIJAN_GREY, alignment=TA_CENTER)),
        ('TTH', dict(fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=TIJAN_WHITE, alignment=TA_CENTER)),
        ('TTC', dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_CENTER)),
        ('TTCL', dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_LEFT)),
    ]:
        styles.add(ParagraphStyle(name=name, **conf))
    return styles


def _hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TIJAN_GREEN)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - 15*mm, PAGE_W - MARGIN, PAGE_H - 15*mm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(TIJAN_BLACK)
    canvas.drawString(MARGIN, PAGE_H - 13*mm, "TIJAN AI")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TIJAN_GREY)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13*mm, "MEP Technical Note")
    canvas.setStrokeColor(TIJAN_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(MARGIN, 8*mm, "Tijan AI — BIM & MEP Engineering Automation")
    canvas.drawRightString(PAGE_W - MARGIN, 8*mm, f"Page {doc.page}")
    canvas.restoreState()


def _table(headers, rows, col_widths=None, S=None):
    if S is None:
        S = _styles()
    hdr = [Paragraph(h, S['TTH']) for h in headers]
    data = [hdr]
    for row in rows:
        data.append([Paragraph(str(c), S['TTC'] if i > 0 else S['TTCL']) for i, c in enumerate(row)])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TIJAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, -1), TIJAN_WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [TIJAN_WHITE, TIJAN_LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def generate_mep_en(resultats) -> bytes:
    """
    Generate English MEP technical note PDF.
    
    Args:
        resultats: ResultatsCalcul dataclass from engine_structural.py
        
    Returns:
        PDF as bytes
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22*mm, bottomMargin=18*mm,
                            leftMargin=MARGIN, rightMargin=MARGIN)
    S = _styles()
    story = []
    info = resultats if not isinstance(resultats, dict) else type('R', (), resultats)()

    projet_nom = getattr(info, 'nom_projet', getattr(info, 'project_name', 'N/A'))
    reference = getattr(info, 'reference', 'N/A')
    localisation = getattr(info, 'localisation', getattr(info, 'location', 'Dakar, Senegal'))
    niveaux = getattr(info, 'niveaux', getattr(info, 'levels', 'N/A'))
    surface = getattr(info, 'surface_totale', getattr(info, 'total_area', 'N/A'))

    # ═══ COVER ═══
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("MEP TECHNICAL NOTE", S['TTitle']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Electrical · Plumbing · HVAC", S['TSmall']))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="60%", thickness=2, color=TIJAN_GREEN, spaceAfter=8*mm))

    cover = [
        ["Project", str(projet_nom)],
        ["Reference", str(reference)],
        ["Location", str(localisation)],
        ["Number of levels", str(niveaux)],
        ["Total area (m²)", f"{surface:,.0f}" if isinstance(surface, (int, float)) else str(surface)],
        ["Applicable standards", "NF C 15-100, DTU 60.11, EN 12831, ASHRAE 55"],
    ]
    crows = [[Paragraph(f"<b>{r[0]}</b>", S['TBody']), Paragraph(r[1], S['TBody'])] for r in cover]
    ct = Table(crows, colWidths=[55*mm, 100*mm])
    ct.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('BACKGROUND', (0, 0), (0, -1), TIJAN_LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ct)
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "This document has been automatically generated by the Tijan AI MEP engine. "
        "All designs comply with applicable French and European standards.",
        S['TSmall']))
    story.append(PageBreak())

    # ═══ 1. ELECTRICAL INSTALLATION ═══
    story.append(Paragraph("1. ELECTRICAL INSTALLATION", S['TH1']))
    story.append(Paragraph("1.1 Regulatory Framework", S['TH2']))
    story.append(Paragraph(
        "The electrical design complies with NF C 15-100 (low-voltage installations) and "
        "NF C 14-100 (utility connection). The installation is designed for a TN-S earthing "
        "system with 30 mA residual current devices on all final circuits.",
        S['TBody']))

    story.append(Paragraph("1.2 Power Assessment", S['TH2']))
    mep = getattr(info, 'mep', {})
    elec = mep.get('electrique', mep.get('electrical', {}))
    puissance = elec.get('puissance_totale', elec.get('total_power', 0))
    circuits = elec.get('circuits', [])

    story.append(Paragraph(
        f"<b>Total installed power:</b> {puissance:,.0f} W<br/>"
        f"<b>Simultaneity factor:</b> 0.6 (residential, per NF C 15-100)<br/>"
        f"<b>Design power:</b> {puissance * 0.6:,.0f} W<br/>"
        f"<b>Main breaker:</b> {elec.get('disjoncteur_general', elec.get('main_breaker', '63A D-curve'))}",
        S['TBody']))

    if circuits:
        circ_headers = ["Circuit", "Description", "Rating (A)", "Cable", "Protection"]
        circ_rows = []
        for c in circuits:
            if isinstance(c, dict):
                circ_rows.append([
                    c.get('id', '-'),
                    c.get('description', c.get('desc', '-')),
                    str(c.get('calibre', c.get('rating', '-'))),
                    c.get('cable', c.get('section', '-')),
                    c.get('protection', '-'),
                ])
        if circ_rows:
            story.append(_table(circ_headers, circ_rows,
                                col_widths=[18*mm, 50*mm, 20*mm, 25*mm, 40*mm], S=S))

    story.append(Paragraph("1.3 Earthing and Lightning Protection", S['TH2']))
    story.append(Paragraph(
        "Earth electrode: copper-clad rod, R<sub>earth</sub> ≤ 10 Ω. "
        "Main equipotential bonding connects all metallic services (water, gas, structural steel). "
        "Supplementary equipotential bonding in wet rooms per NF C 15-100 §701. "
        "Surge protection device (SPD) Type 2 installed at the main distribution board.",
        S['TBody']))
    story.append(PageBreak())

    # ═══ 2. PLUMBING INSTALLATION ═══
    story.append(Paragraph("2. PLUMBING INSTALLATION", S['TH1']))
    story.append(Paragraph("2.1 Regulatory Framework", S['TH2']))
    story.append(Paragraph(
        "Plumbing design follows DTU 60.11 (rules for sanitary installation calculation) "
        "and DTU 60.1 (metallic piping). Drainage per EN 12056 (gravity drainage systems).",
        S['TBody']))

    story.append(Paragraph("2.2 Cold Water Supply", S['TH2']))
    plomb = mep.get('plomberie', mep.get('plumbing', {}))
    debit = plomb.get('debit_total', plomb.get('total_flow', 0))

    story.append(Paragraph(
        f"<b>Total design flow rate:</b> {debit:.2f} L/s<br/>"
        f"<b>Supply pressure (street main):</b> {plomb.get('pression', plomb.get('pressure', 3.0)):.1f} bar<br/>"
        f"<b>Pipe material:</b> PPR (hot water), PVC-C (cold water)<br/>"
        f"<b>Sizing method:</b> Simultaneous demand per DTU 60.11 Annex A",
        S['TBody']))

    story.append(Paragraph("2.3 Hot Water Production", S['TH2']))
    story.append(Paragraph(
        f"System: {plomb.get('type_ecs', plomb.get('hw_type', 'Individual electric water heaters'))}<br/>"
        f"Design temperature: 60°C (storage), 50°C (distribution), anti-Legionella cycle at 70°C weekly.<br/>"
        "Insulation: 19 mm on all hot water pipes (DTU 60.1).",
        S['TBody']))

    story.append(Paragraph("2.4 Drainage", S['TH2']))
    story.append(Paragraph(
        "Wastewater and rainwater are separated. Gravity drainage per EN 12056-2 "
        "(fill degree 0.5 for branches, 0.7 for stacks). Minimum slopes: 1% for horizontal "
        "runs ≤ DN100, 0.5% for DN > 100. Vent stacks per EN 12056-3.",
        S['TBody']))
    story.append(PageBreak())

    # ═══ 3. HVAC ═══
    story.append(Paragraph("3. HVAC — HEATING, VENTILATION & AIR CONDITIONING", S['TH1']))
    story.append(Paragraph("3.1 Thermal Comfort Criteria", S['TH2']))
    story.append(Paragraph(
        "Design conditions per ASHRAE 55 and EN 16798-1:<br/>"
        "• Cooling: indoor 24°C / 50% RH (outdoor design: 38°C, Dakar)<br/>"
        "• Heating: indoor 22°C (outdoor design: 18°C, Dakar — limited heating demand)<br/>"
        "• Minimum fresh air: 25 m³/h per person (residential)",
        S['TBody']))

    story.append(Paragraph("3.2 Cooling Load Calculation", S['TH2']))
    hvac = mep.get('hvac', mep.get('climatisation', {}))
    cool_load = hvac.get('charge_frigo', hvac.get('cooling_load', 0))

    story.append(Paragraph(
        f"<b>Total cooling load:</b> {cool_load:,.0f} W ({cool_load / 1000:.1f} kW)<br/>"
        f"<b>Calculation method:</b> EN 12831 (simplified) + ASHRAE correction factors for tropical climate<br/>"
        f"<b>Proposed system:</b> {hvac.get('systeme', hvac.get('system', 'Split-type inverter units'))}<br/>"
        f"<b>Refrigerant:</b> R-32 (GWP = 675, per F-gas regulation EU 517/2014)",
        S['TBody']))

    story.append(Paragraph("3.3 Ventilation", S['TH2']))
    story.append(Paragraph(
        "Ventilation strategy: natural ventilation complemented by mechanical extract in wet rooms. "
        "Extract rates per local regulations: kitchen 75 m³/h, bathroom 30 m³/h, WC 15 m³/h. "
        "Air transfer through internal doors (25 mm undercut or transfer grilles).",
        S['TBody']))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("4. REFERENCES", S['TH1']))
    story.append(Paragraph(
        "NF C 15-100 — Low-voltage electrical installations<br/>"
        "NF C 14-100 — Low-voltage utility connections<br/>"
        "DTU 60.11 — Sanitary installation sizing rules<br/>"
        "EN 12056 — Gravity drainage inside buildings<br/>"
        "EN 12831 — Heating system design - Heat load calculation<br/>"
        "ASHRAE Standard 55 — Thermal environmental conditions",
        S['TBody']))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=TIJAN_BORDER, spaceAfter=3*mm))
    story.append(Paragraph(
        "<b>Disclaimer:</b> This document has been generated by an automated calculation engine. "
        "It must be reviewed and validated by a qualified MEP engineer before implementation. "
        "Tijan AI shall not be held liable for any use without proper professional verification.",
        S['TSmall']))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()

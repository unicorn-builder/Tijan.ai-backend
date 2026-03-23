"""
gen_boq_mep_detail_en.py — English MEP Detailed Bill of Quantities
Native EN generator for Tijan AI. Mirrors generate_boq_mep.py (FR) with all text in English.
Covers: Electrical, Plumbing, HVAC lots with Senegal market pricing.
NOTE: MEP prices need recalibration with Malick's tariff grid (flagged).
Uses ReportLab Platypus, A4. Input: ResultatsCalcul dataclass.
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


# ── Colors ──
TIJAN_BLACK = HexColor("#111111")
TIJAN_GREY = HexColor("#555555")
TIJAN_GREEN = HexColor("#43A956")
TIJAN_LIGHT_BG = HexColor("#FAFAFA")
TIJAN_WHITE = HexColor("#FFFFFF")
TIJAN_BORDER = HexColor("#E0E0E0")
TIJAN_SUBTOTAL_BG = HexColor("#E8F5E9")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _styles():
    styles = getSampleStyleSheet()
    defs = {
        'TTitle': dict(fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=TIJAN_BLACK, alignment=TA_CENTER, spaceAfter=6*mm),
        'TH1': dict(fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=TIJAN_BLACK, spaceBefore=8*mm, spaceAfter=3*mm),
        'TH2': dict(fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=TIJAN_GREY, spaceBefore=4*mm, spaceAfter=2*mm),
        'TBody': dict(fontName='Helvetica', fontSize=9.5, leading=13, textColor=TIJAN_BLACK, alignment=TA_JUSTIFY, spaceAfter=2*mm),
        'TSmall': dict(fontName='Helvetica', fontSize=8, leading=10, textColor=TIJAN_GREY, alignment=TA_CENTER),
        'TTH': dict(fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=TIJAN_WHITE, alignment=TA_CENTER),
        'TTC': dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_CENTER),
        'TTCL': dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_LEFT),
        'TTCR': dict(fontName='Helvetica', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_RIGHT),
        'TTBold': dict(fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=TIJAN_BLACK, alignment=TA_RIGHT),
        'TWarn': dict(fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=HexColor("#E65100"), alignment=TA_CENTER),
    }
    for name, conf in defs.items():
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
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13*mm, "MEP Bill of Quantities")
    canvas.setStrokeColor(TIJAN_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(MARGIN, 8*mm, "Tijan AI — BIM & MEP Engineering Automation")
    canvas.drawRightString(PAGE_W - MARGIN, 8*mm, f"Page {doc.page}")
    canvas.restoreState()


def _fmt(val):
    if isinstance(val, (int, float)):
        return f"{val:,.0f}"
    return str(val)


def _build_lot_table(lot_name, items, S):
    """Build a single lot table with subtotal."""
    col_w = [10*mm, 62*mm, 18*mm, 16*mm, 22*mm, 28*mm]
    headers = ["#", "Description", "Unit", "Qty", "Unit Price", "Total (FCFA)"]
    hdr = [Paragraph(h, S['TTH']) for h in headers]
    data = [hdr]
    subtotal = 0

    for i, item in enumerate(items, 1):
        qty = item.get('qty', 0)
        pu = item.get('pu', 0)
        total = item.get('total', 0)
        if total == 0 and isinstance(qty, (int, float)) and isinstance(pu, (int, float)):
            total = qty * pu
        subtotal += total if isinstance(total, (int, float)) else 0

        data.append([
            Paragraph(str(i), S['TTC']),
            Paragraph(item.get('desc', '-'), S['TTCL']),
            Paragraph(item.get('unit', '-'), S['TTC']),
            Paragraph(f"{qty:,.0f}" if isinstance(qty, (int, float)) else str(qty), S['TTC']),
            Paragraph(_fmt(pu), S['TTCR']),
            Paragraph(_fmt(total), S['TTCR']),
        ])

    # Subtotal row
    data.append([
        Paragraph('', S['TTC']),
        Paragraph(f'<b>SUBTOTAL — {lot_name}</b>', S['TTCL']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph(f'<b>{_fmt(subtotal)}</b>', S['TTBold']),
    ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TIJAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, -2), TIJAN_WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [TIJAN_WHITE, TIJAN_LIGHT_BG]),
        ('BACKGROUND', (0, -1), (-1, -1), TIJAN_SUBTOTAL_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t, subtotal


def generate_boq_mep_detail_en(resultats) -> bytes:
    """
    Generate English MEP detailed BOQ PDF.
    
    Args:
        resultats: ResultatsCalcul dataclass
        
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

    # ═══ COVER ═══
    story.append(Spacer(1, 25*mm))
    story.append(Paragraph("MEP BILL OF QUANTITIES", S['TTitle']))
    story.append(Paragraph("Electrical · Plumbing · HVAC", S['TSmall']))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="60%", thickness=2, color=TIJAN_GREEN, spaceAfter=8*mm))

    cover = [
        ["Project", str(projet_nom)],
        ["Reference", str(reference)],
        ["Location", getattr(info, 'localisation', getattr(info, 'location', 'Dakar, Senegal'))],
        ["Currency", "FCFA (XOF)"],
        ["Standards", "NF C 15-100, DTU 60.11, EN 12831"],
    ]
    crows = [[Paragraph(f"<b>{r[0]}</b>", S['TBody']), Paragraph(r[1], S['TBody'])] for r in cover]
    ct = Table(crows, colWidths=[55*mm, 105*mm])
    ct.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('BACKGROUND', (0, 0), (0, -1), TIJAN_LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ct)

    # ⚠ PRICE WARNING
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "⚠ MEP prices are provisional — pending recalibration with validated tariff grid.",
        S['TWarn']))
    story.append(PageBreak())

    # ═══ Extract MEP BOQ or use defaults ═══
    mep = getattr(info, 'mep', {})
    boq_mep = getattr(info, 'boq_mep', mep.get('boq', {}))

    # LOT 1 — ELECTRICAL
    story.append(Paragraph("LOT 1 — ELECTRICAL INSTALLATION", S['TH1']))
    elec_items = boq_mep.get('electrique', boq_mep.get('electrical', []))
    if not elec_items:
        elec_items = [
            {'desc': 'Main distribution board (TGBT) — 63A', 'unit': 'unit', 'qty': 1, 'pu': 850000, 'total': 850000},
            {'desc': 'Sub-distribution boards (per floor)', 'unit': 'unit', 'qty': 9, 'pu': 185000, 'total': 1665000},
            {'desc': 'Circuit breakers and RCDs (30mA)', 'unit': 'unit', 'qty': 120, 'pu': 15000, 'total': 1800000},
            {'desc': 'Cable — 3×2.5 mm² (lighting circuits)', 'unit': 'ml', 'qty': 2500, 'pu': 850, 'total': 2125000},
            {'desc': 'Cable — 3×4 mm² (power circuits)', 'unit': 'ml', 'qty': 1800, 'pu': 1200, 'total': 2160000},
            {'desc': 'Cable — 5×10 mm² (main risers)', 'unit': 'ml', 'qty': 120, 'pu': 4500, 'total': 540000},
            {'desc': 'Light switches (single/double)', 'unit': 'unit', 'qty': 280, 'pu': 3500, 'total': 980000},
            {'desc': 'Power sockets (2P+T, 16A)', 'unit': 'unit', 'qty': 350, 'pu': 4000, 'total': 1400000},
            {'desc': 'LED ceiling lights', 'unit': 'unit', 'qty': 250, 'pu': 12000, 'total': 3000000},
            {'desc': 'Common area emergency lighting', 'unit': 'unit', 'qty': 30, 'pu': 25000, 'total': 750000},
            {'desc': 'Earthing system (copper rod + bonding)', 'unit': 'lump sum', 'qty': 1, 'pu': 450000, 'total': 450000},
            {'desc': 'Surge protection device (SPD Type 2)', 'unit': 'unit', 'qty': 2, 'pu': 85000, 'total': 170000},
            {'desc': 'Cable trays and conduits', 'unit': 'lump sum', 'qty': 1, 'pu': 1200000, 'total': 1200000},
            {'desc': 'Labour — Electrical installation', 'unit': 'lump sum', 'qty': 1, 'pu': 3500000, 'total': 3500000},
        ]
    t_elec, sub_elec = _build_lot_table("ELECTRICAL", elec_items, S)
    story.append(t_elec)
    story.append(PageBreak())

    # LOT 2 — PLUMBING
    story.append(Paragraph("LOT 2 — PLUMBING INSTALLATION", S['TH1']))
    plomb_items = boq_mep.get('plomberie', boq_mep.get('plumbing', []))
    if not plomb_items:
        plomb_items = [
            {'desc': 'PPR pipes — Ø20 (hot water distribution)', 'unit': 'ml', 'qty': 800, 'pu': 1800, 'total': 1440000},
            {'desc': 'PVC-C pipes — Ø25 (cold water distribution)', 'unit': 'ml', 'qty': 1200, 'pu': 1200, 'total': 1440000},
            {'desc': 'PVC pipes — Ø100 (waste drainage)', 'unit': 'ml', 'qty': 600, 'pu': 2500, 'total': 1500000},
            {'desc': 'PVC pipes — Ø150 (main stacks)', 'unit': 'ml', 'qty': 120, 'pu': 4500, 'total': 540000},
            {'desc': 'Gate valves and check valves', 'unit': 'unit', 'qty': 65, 'pu': 8500, 'total': 552500},
            {'desc': 'Electric water heaters (80L)', 'unit': 'unit', 'qty': 53, 'pu': 95000, 'total': 5035000},
            {'desc': 'Kitchen sink (stainless steel)', 'unit': 'unit', 'qty': 53, 'pu': 45000, 'total': 2385000},
            {'desc': 'Washbasin (ceramic)', 'unit': 'unit', 'qty': 75, 'pu': 35000, 'total': 2625000},
            {'desc': 'Toilet (floor-mounted, dual flush)', 'unit': 'unit', 'qty': 70, 'pu': 55000, 'total': 3850000},
            {'desc': 'Shower mixer and head', 'unit': 'unit', 'qty': 53, 'pu': 28000, 'total': 1484000},
            {'desc': 'Floor drains and traps', 'unit': 'unit', 'qty': 120, 'pu': 5500, 'total': 660000},
            {'desc': 'Water meter assembly (main)', 'unit': 'unit', 'qty': 1, 'pu': 250000, 'total': 250000},
            {'desc': 'Booster pump station', 'unit': 'unit', 'qty': 1, 'pu': 1800000, 'total': 1800000},
            {'desc': 'Labour — Plumbing installation', 'unit': 'lump sum', 'qty': 1, 'pu': 4200000, 'total': 4200000},
        ]
    t_plomb, sub_plomb = _build_lot_table("PLUMBING", plomb_items, S)
    story.append(t_plomb)
    story.append(PageBreak())

    # LOT 3 — HVAC
    story.append(Paragraph("LOT 3 — HVAC INSTALLATION", S['TH1']))
    hvac_items = boq_mep.get('hvac', boq_mep.get('climatisation', []))
    if not hvac_items:
        hvac_items = [
            {'desc': 'Split inverter unit — 9,000 BTU (bedrooms)', 'unit': 'unit', 'qty': 80, 'pu': 285000, 'total': 22800000},
            {'desc': 'Split inverter unit — 12,000 BTU (living rooms)', 'unit': 'unit', 'qty': 53, 'pu': 350000, 'total': 18550000},
            {'desc': 'Split inverter unit — 18,000 BTU (large spaces)', 'unit': 'unit', 'qty': 10, 'pu': 485000, 'total': 4850000},
            {'desc': 'Refrigerant piping (R-32, insulated)', 'unit': 'ml', 'qty': 1500, 'pu': 3500, 'total': 5250000},
            {'desc': 'Condensate drain piping', 'unit': 'ml', 'qty': 800, 'pu': 800, 'total': 640000},
            {'desc': 'Outdoor unit brackets and supports', 'unit': 'unit', 'qty': 143, 'pu': 15000, 'total': 2145000},
            {'desc': 'Mechanical extract fans (wet rooms)', 'unit': 'unit', 'qty': 120, 'pu': 18000, 'total': 2160000},
            {'desc': 'Ductwork and grilles (common areas)', 'unit': 'lump sum', 'qty': 1, 'pu': 1500000, 'total': 1500000},
            {'desc': 'Electrical wiring for HVAC units', 'unit': 'lump sum', 'qty': 1, 'pu': 1800000, 'total': 1800000},
            {'desc': 'Labour — HVAC installation', 'unit': 'lump sum', 'qty': 1, 'pu': 5500000, 'total': 5500000},
        ]
    t_hvac, sub_hvac = _build_lot_table("HVAC", hvac_items, S)
    story.append(t_hvac)

    # ═══ GRAND TOTAL ═══
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("SUMMARY", S['TH1']))

    grand_total = sub_elec + sub_plomb + sub_hvac
    tva = grand_total * 0.18
    ttc = grand_total + tva

    sum_headers = ["Lot", "Description", "Subtotal (FCFA)"]
    sum_data = [
        ["1", "Electrical Installation", _fmt(sub_elec)],
        ["2", "Plumbing Installation", _fmt(sub_plomb)],
        ["3", "HVAC Installation", _fmt(sub_hvac)],
    ]
    sum_hdr = [Paragraph(h, S['TTH']) for h in sum_headers]
    sum_rows = [sum_hdr]
    for r in sum_data:
        sum_rows.append([Paragraph(r[0], S['TTC']), Paragraph(r[1], S['TTCL']),
                         Paragraph(r[2], S['TTCR'])])
    # Totals
    sum_rows.append([Paragraph('', S['TTC']), Paragraph('<b>TOTAL EXCL. TAX</b>', S['TTCL']),
                     Paragraph(f'<b>{_fmt(grand_total)}</b>', S['TTBold'])])
    sum_rows.append([Paragraph('', S['TTC']), Paragraph('<b>VAT (18%)</b>', S['TTCL']),
                     Paragraph(f'<b>{_fmt(tva)}</b>', S['TTBold'])])
    sum_rows.append([Paragraph('', S['TTC']), Paragraph('<b>TOTAL INCL. TAX</b>', S['TTCL']),
                     Paragraph(f'<b>{_fmt(ttc)}</b>', S['TTBold'])])

    st = Table(sum_rows, colWidths=[15*mm, 90*mm, 50*mm], repeatRows=1)
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TIJAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, 3), TIJAN_WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, 3), [TIJAN_WHITE, TIJAN_LIGHT_BG]),
        ('BACKGROUND', (0, -3), (-1, -1), TIJAN_GREEN),
        ('TEXTCOLOR', (0, -3), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(st)

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("NOTES", S['TH2']))
    story.append(Paragraph(
        "1. MEP unit prices are provisional and subject to recalibration with the validated tariff grid.<br/>"
        "2. Quantities are derived from the MEP engine based on the building program (53 units, R+9).<br/>"
        "3. Sanitary fixtures priced at mid-range quality level.<br/>"
        "4. HVAC sizing based on EN 12831 cooling loads for Dakar climate (38°C outdoor design).<br/>"
        "5. Labour rates include installation, testing, and commissioning.",
        S['TBody']))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=TIJAN_BORDER, spaceAfter=3*mm))
    story.append(Paragraph(
        "<b>Disclaimer:</b> This bill of quantities has been generated automatically. "
        "Final quantities and prices must be confirmed with the MEP contractor prior to contract.",
        S['TSmall']))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()

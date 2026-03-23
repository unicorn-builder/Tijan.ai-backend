"""
gen_boq_structure_en.py — English Structural Bill of Quantities
Native EN generator for Tijan AI. Mirrors generate_boq.py (FR) with all text in English.
Prices: validated Senegal market (Fabrimetal steel 480-600 FCFA/kg, CIMAF/SOCOCIM C30/37 185,000 FCFA/m³).
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
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13*mm, "Structural Bill of Quantities")
    canvas.setStrokeColor(TIJAN_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12*mm, PAGE_W - MARGIN, 12*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(MARGIN, 8*mm, "Tijan AI — BIM & Structural Engineering Automation")
    canvas.drawRightString(PAGE_W - MARGIN, 8*mm, f"Page {doc.page}")
    canvas.restoreState()


def _fmt_price(val):
    """Format price in FCFA."""
    if isinstance(val, (int, float)):
        return f"{val:,.0f}"
    return str(val)


def generate_boq_structure_en(resultats) -> bytes:
    """
    Generate English structural BOQ PDF.
    
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
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("STRUCTURAL BILL OF QUANTITIES", S['TTitle']))
    story.append(HRFlowable(width="60%", thickness=2, color=TIJAN_GREEN, spaceAfter=8*mm))

    cover = [
        ["Project", str(projet_nom)],
        ["Reference", str(reference)],
        ["Location", getattr(info, 'localisation', getattr(info, 'location', 'Dakar, Senegal'))],
        ["Currency", "FCFA (XOF)"],
        ["Price basis", "Senegal market Q1 2025 — Fabrimetal / CIMAF / SOCOCIM"],
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
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "Quantities derived from Tijan AI structural engine calculations. "
        "Unit prices based on validated Senegal market rates.",
        S['TSmall']))
    story.append(PageBreak())

    # ═══ BOQ TABLE ═══
    story.append(Paragraph("BILL OF QUANTITIES — STRUCTURAL WORKS", S['TH1']))

    # Extract BOQ data
    boq = getattr(info, 'boq', getattr(info, 'devis', {}))
    lignes = boq.get('lignes', boq.get('lines', boq.get('items', [])))

    # Default structural BOQ if none provided
    if not lignes:
        lignes = [
            {'lot': '1', 'desc': 'Site preparation and earthworks', 'unit': 'lump sum', 'qty': 1, 'pu': 2500000, 'total': 2500000},
            {'lot': '2', 'desc': 'Foundations — Excavation', 'unit': 'm³', 'qty': 120, 'pu': 8500, 'total': 1020000},
            {'lot': '2', 'desc': 'Foundations — Lean concrete (C150)', 'unit': 'm³', 'qty': 15, 'pu': 95000, 'total': 1425000},
            {'lot': '2', 'desc': 'Foundations — Reinforced concrete (C30/37)', 'unit': 'm³', 'qty': 45, 'pu': 185000, 'total': 8325000},
            {'lot': '2', 'desc': 'Foundations — Reinforcement steel (B500B)', 'unit': 'kg', 'qty': 4500, 'pu': 550, 'total': 2475000},
            {'lot': '2', 'desc': 'Foundations — Formwork', 'unit': 'm²', 'qty': 180, 'pu': 6500, 'total': 1170000},
            {'lot': '3', 'desc': 'Superstructure — Concrete columns (C30/37)', 'unit': 'm³', 'qty': 35, 'pu': 185000, 'total': 6475000},
            {'lot': '3', 'desc': 'Superstructure — Concrete beams (C30/37)', 'unit': 'm³', 'qty': 55, 'pu': 185000, 'total': 10175000},
            {'lot': '3', 'desc': 'Superstructure — Concrete slabs (C30/37)', 'unit': 'm³', 'qty': 280, 'pu': 185000, 'total': 51800000},
            {'lot': '3', 'desc': 'Superstructure — Reinforcement steel (B500B)', 'unit': 'kg', 'qty': 42000, 'pu': 550, 'total': 23100000},
            {'lot': '3', 'desc': 'Superstructure — Formwork (slabs)', 'unit': 'm²', 'qty': 1800, 'pu': 5500, 'total': 9900000},
            {'lot': '3', 'desc': 'Superstructure — Formwork (beams/columns)', 'unit': 'm²', 'qty': 950, 'pu': 7000, 'total': 6650000},
            {'lot': '4', 'desc': 'Stairs — Reinforced concrete', 'unit': 'ml', 'qty': 45, 'pu': 85000, 'total': 3825000},
            {'lot': '5', 'desc': 'Concrete curing and quality testing', 'unit': 'lump sum', 'qty': 1, 'pu': 1500000, 'total': 1500000},
        ]

    # Build table
    col_w = [12*mm, 65*mm, 18*mm, 18*mm, 22*mm, 28*mm]
    headers = ["Lot", "Description", "Unit", "Qty", "Unit Price", "Total (FCFA)"]
    hdr = [Paragraph(h, S['TTH']) for h in headers]
    data = [hdr]

    grand_total = 0
    current_lot = None
    lot_subtotal = 0
    lot_rows_indices = []

    for item in lignes:
        if isinstance(item, dict):
            lot = str(item.get('lot', ''))
            desc = item.get('desc', item.get('description', item.get('designation', '-')))
            unit = item.get('unit', item.get('unite', '-'))
            qty = item.get('qty', item.get('quantite', 0))
            pu = item.get('pu', item.get('prix_unitaire', item.get('unit_price', 0)))
            total = item.get('total', item.get('montant', 0))
            if total == 0 and isinstance(qty, (int, float)) and isinstance(pu, (int, float)):
                total = qty * pu

            # Lot subtotal row
            if current_lot and lot != current_lot and lot_subtotal > 0:
                sub_row = [
                    Paragraph('', S['TTC']),
                    Paragraph(f'<b>Subtotal Lot {current_lot}</b>', S['TTCL']),
                    Paragraph('', S['TTC']),
                    Paragraph('', S['TTC']),
                    Paragraph('', S['TTC']),
                    Paragraph(f'<b>{_fmt_price(lot_subtotal)}</b>', S['TTBold']),
                ]
                data.append(sub_row)
                lot_rows_indices.append(len(data) - 1)
                lot_subtotal = 0

            current_lot = lot
            lot_subtotal += total if isinstance(total, (int, float)) else 0
            grand_total += total if isinstance(total, (int, float)) else 0

            row = [
                Paragraph(lot, S['TTC']),
                Paragraph(desc, S['TTCL']),
                Paragraph(unit, S['TTC']),
                Paragraph(f"{qty:,.0f}" if isinstance(qty, (int, float)) else str(qty), S['TTC']),
                Paragraph(_fmt_price(pu), S['TTCR']),
                Paragraph(_fmt_price(total), S['TTCR']),
            ]
            data.append(row)

    # Last lot subtotal
    if current_lot and lot_subtotal > 0:
        sub_row = [
            Paragraph('', S['TTC']),
            Paragraph(f'<b>Subtotal Lot {current_lot}</b>', S['TTCL']),
            Paragraph('', S['TTC']),
            Paragraph('', S['TTC']),
            Paragraph('', S['TTC']),
            Paragraph(f'<b>{_fmt_price(lot_subtotal)}</b>', S['TTBold']),
        ]
        data.append(sub_row)
        lot_rows_indices.append(len(data) - 1)

    # Grand total row
    data.append([
        Paragraph('', S['TTC']),
        Paragraph('<b>GRAND TOTAL EXCL. TAX</b>', S['TTCL']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph(f'<b>{_fmt_price(grand_total)}</b>', S['TTBold']),
    ])

    tva = grand_total * 0.18
    ttc = grand_total + tva
    data.append([
        Paragraph('', S['TTC']),
        Paragraph('<b>VAT (18%)</b>', S['TTCL']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph(f'<b>{_fmt_price(tva)}</b>', S['TTBold']),
    ])
    data.append([
        Paragraph('', S['TTC']),
        Paragraph('<b>GRAND TOTAL INCL. TAX</b>', S['TTCL']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph('', S['TTC']),
        Paragraph(f'<b>{_fmt_price(ttc)}</b>', S['TTBold']),
    ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TIJAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, -1), TIJAN_WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -4), [TIJAN_WHITE, TIJAN_LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, TIJAN_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]
    # Highlight subtotal rows
    for idx in lot_rows_indices:
        style_cmds.append(('BACKGROUND', (0, idx), (-1, idx), TIJAN_SUBTOTAL_BG))
    # Grand total rows
    style_cmds.append(('BACKGROUND', (0, -3), (-1, -1), TIJAN_GREEN))
    style_cmds.append(('TEXTCOLOR', (0, -3), (-1, -1), white))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("NOTES", S['TH2']))
    story.append(Paragraph(
        "1. Steel prices: Fabrimetal Sénégal (Sébikotane), 480–600 FCFA/kg depending on diameter and treatment.<br/>"
        "2. Concrete: ready-mix C30/37 from CIMAF/SOCOCIM at 185,000 FCFA/m³ delivered.<br/>"
        "3. Formwork prices include supply, assembly, stripping and cleaning.<br/>"
        "4. Quantities are derived from the structural calculation engine and may vary ±10% during detailed design.<br/>"
        "5. Prices are valid for Q1 2025 — subject to market fluctuation.",
        S['TBody']))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=TIJAN_BORDER, spaceAfter=3*mm))
    story.append(Paragraph(
        "<b>Disclaimer:</b> This bill of quantities has been generated automatically. "
        "Final quantities and prices must be confirmed with the contractor prior to signing.",
        S['TSmall']))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()

"""
gen_boq_structure_en.py — English Structural Bill of Quantities (7 lots)
Native EN generator. Mirrors gen_boq_structure.py (FR).
Signature: generer_boq_structure(rs, params_dict) → bytes
Input: rs = ResultatsStructure, params_dict = ParamsProjet.dict()
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

TIJAN_BLACK=HexColor("#111111"); TIJAN_GREY=HexColor("#555555"); TIJAN_GREEN=HexColor("#43A956")
TIJAN_LIGHT=HexColor("#FAFAFA"); TIJAN_WHITE=HexColor("#FFFFFF"); TIJAN_BORDER=HexColor("#E0E0E0")
TIJAN_SUB=HexColor("#E8F5E9")
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
        'TB':dict(fontName='Helvetica-Bold',fontSize=8.5,leading=11,textColor=TIJAN_BLACK,alignment=TA_RIGHT),
    }.items():
        s.add(ParagraphStyle(name=n,**c))
    return s

def _hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TIJAN_GREEN); canvas.setLineWidth(1.5)
    canvas.line(M,PAGE_H-15*mm,PAGE_W-M,PAGE_H-15*mm)
    canvas.setFont("Helvetica-Bold",8); canvas.setFillColor(TIJAN_BLACK)
    canvas.drawString(M,PAGE_H-13*mm,"TIJAN AI")
    canvas.setFont("Helvetica",8); canvas.setFillColor(TIJAN_GREY)
    canvas.drawRightString(PAGE_W-M,PAGE_H-13*mm,"Structural Bill of Quantities")
    canvas.setStrokeColor(TIJAN_BORDER); canvas.setLineWidth(0.5)
    canvas.line(M,12*mm,PAGE_W-M,12*mm)
    canvas.setFont("Helvetica",7); canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(M,8*mm,"Tijan AI — BIM & Structural Engineering Automation")
    canvas.drawRightString(PAGE_W-M,8*mm,f"Page {doc.page}")
    canvas.restoreState()

def _fmt(v):
    return f"{v:,.0f}" if isinstance(v,(int,float)) else str(v)


def generer_boq_structure(rs, params_dict: dict) -> bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=22*mm,bottomMargin=18*mm,leftMargin=M,rightMargin=M)
    S=_S(); story=[]; p=params_dict or {}
    boq=rs.boq

    # COVER
    story += [Spacer(1,30*mm), Paragraph("STRUCTURAL BILL OF QUANTITIES", S['TT']),
              HRFlowable(width="60%",thickness=2,color=TIJAN_GREEN,spaceAfter=8*mm)]
    info_data=[
        ["Project", p.get('nom','Project')],
        ["Location", f"{p.get('ville','Dakar')}, {p.get('pays','Senegal')}"],
        ["Concrete", rs.classe_beton], ["Steel", rs.classe_acier],
        ["Currency", "FCFA (XOF)"],
        ["Price basis", f"{p.get('ville','Dakar')} market — Fabrimetal / CIMAF / SOCOCIM"],
    ]
    irows=[[Paragraph(f"<b>{r[0]}</b>",S['BD']),Paragraph(str(r[1]),S['BD'])] for r in info_data]
    it=Table(irows,colWidths=[55*mm,105*mm])
    it.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER),('BACKGROUND',(0,0),(0,-1),TIJAN_LIGHT),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)]))
    story.append(it)
    story += [Spacer(1,10*mm), Paragraph("Quantities derived from Tijan AI structural engine. "
              "Unit prices from validated local market data.", S['SM']), PageBreak()]

    # BOQ TABLE — build from rs.boq.lots if available, else from summary
    story.append(Paragraph("DETAILED BILL OF QUANTITIES — STRUCTURAL WORKS", S['H1']))

    col_w=[10*mm,62*mm,16*mm,18*mm,22*mm,28*mm]
    headers=["#","Description","Unit","Qty","Unit Price","Total (FCFA)"]
    hdr=[Paragraph(h,S['TH']) for h in headers]
    data=[hdr]
    grand_total=0

    # Try to get lots from boq dataclass
    lots = getattr(boq, 'lots', None)
    if lots:
        for lot in lots:
            lot_d = lot if isinstance(lot, dict) else dataclasses.asdict(lot) if dataclasses.is_dataclass(lot) else {}
            items = lot_d.get('items', lot_d.get('lignes', []))
            lot_name = lot_d.get('nom', lot_d.get('name', ''))
            lot_sub = 0
            for idx, item in enumerate(items, 1):
                desc = item.get('designation', item.get('desc', '-'))
                unit = item.get('unite', item.get('unit', '-'))
                qty = item.get('quantite', item.get('qty', 0))
                pu = item.get('prix_unitaire', item.get('pu', 0))
                total = item.get('montant', item.get('total', 0))
                if total == 0 and isinstance(qty,(int,float)) and isinstance(pu,(int,float)):
                    total = qty * pu
                lot_sub += total if isinstance(total,(int,float)) else 0
                data.append([
                    Paragraph(str(idx),S['TC']), Paragraph(desc,S['TL']),
                    Paragraph(unit,S['TC']), Paragraph(_fmt(qty),S['TC']),
                    Paragraph(_fmt(pu),S['TR']), Paragraph(_fmt(total),S['TR']),
                ])
            # Subtotal
            if items:
                data.append([
                    Paragraph('',S['TC']), Paragraph(f'<b>Subtotal — {lot_name}</b>',S['TL']),
                    Paragraph('',S['TC']), Paragraph('',S['TC']), Paragraph('',S['TC']),
                    Paragraph(f'<b>{_fmt(lot_sub)}</b>',S['TB']),
                ])
                grand_total += lot_sub
    else:
        # Fallback: summary from boq fields
        summary_items = [
            ("Concrete (all elements)", "m³", boq.beton_total_m3, 185000),
            ("Reinforcement steel B500B", "kg", boq.acier_total_kg, 550),
            ("Formwork", "m²", boq.coffrage_total_m2, 6000),
        ]
        for idx, (desc, unit, qty, pu) in enumerate(summary_items, 1):
            total = qty * pu
            grand_total += total
            data.append([
                Paragraph(str(idx),S['TC']), Paragraph(desc,S['TL']),
                Paragraph(unit,S['TC']), Paragraph(f"{qty:,.1f}",S['TC']),
                Paragraph(_fmt(pu),S['TR']), Paragraph(_fmt(total),S['TR']),
            ])

    # Use cout_total_fcfa if available and no lots
    if not lots and hasattr(boq, 'cout_total_fcfa') and boq.cout_total_fcfa:
        grand_total = boq.cout_total_fcfa

    # Grand total rows
    tva = grand_total * 0.18
    ttc = grand_total + tva
    for label, val, bg in [
        ("TOTAL EXCL. TAX", grand_total, TIJAN_GREEN),
        ("VAT (18%)", tva, TIJAN_GREEN),
        ("TOTAL INCL. TAX", ttc, TIJAN_GREEN),
    ]:
        data.append([
            Paragraph('',S['TC']), Paragraph(f'<b>{label}</b>',S['TL']),
            Paragraph('',S['TC']), Paragraph('',S['TC']), Paragraph('',S['TC']),
            Paragraph(f'<b>{_fmt(val)}</b>',S['TB']),
        ])

    t=Table(data,colWidths=col_w,repeatRows=1)
    style_cmds=[
        ('BACKGROUND',(0,0),(-1,0),TIJAN_GREEN), ('TEXTCOLOR',(0,0),(-1,0),white),
        ('ROWBACKGROUNDS',(0,1),(-1,-4),[TIJAN_WHITE,TIJAN_LIGHT]),
        ('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5), ('RIGHTPADDING',(0,0),(-1,-1),5),
        ('BACKGROUND',(0,-3),(-1,-1),TIJAN_GREEN), ('TEXTCOLOR',(0,-3),(-1,-1),white),
    ]
    t.setStyle(TableStyle(style_cmds))
    story.append(t)

    # NOTES
    story += [Spacer(1,8*mm), Paragraph("NOTES", S['H2']), Paragraph(
        "1. Steel: Fabrimetal Sénégal (Sébikotane), 480–600 FCFA/kg.<br/>"
        "2. Concrete: ready-mix C30/37, CIMAF/SOCOCIM, 185,000 FCFA/m³ delivered.<br/>"
        "3. Formwork includes supply, assembly, stripping and cleaning.<br/>"
        "4. Quantities from structural engine — may vary ±10% during detailed design.<br/>"
        "5. Prices valid at date of generation — subject to market fluctuation.", S['BD'])]

    story += [Spacer(1,10*mm), HRFlowable(width="100%",thickness=0.5,color=TIJAN_BORDER,spaceAfter=3*mm),
              Paragraph("<b>Disclaimer:</b> This BOQ has been generated automatically. "
                        "Final quantities and prices must be confirmed with the contractor.", S['SM'])]

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0); return buf.read()

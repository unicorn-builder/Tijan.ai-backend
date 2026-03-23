"""
gen_boq_mep_detail_en.py — English MEP Detailed Bill of Quantities (7 lots × 3 tiers)
Native EN generator. Mirrors gen_boq_mep_detail.py (FR).
Signature: generer_boq_mep_detail(rm, params_dict) → bytes
Input: rm = ResultatsMEP from engine_mep_v2, params_dict = ParamsProjet.dict()
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
        'H1':dict(fontName='Helvetica-Bold',fontSize=13,leading=16,textColor=TIJAN_BLACK,spaceBefore=6*mm,spaceAfter=3*mm),
        'H2':dict(fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=TIJAN_GREY,spaceBefore=4*mm,spaceAfter=2*mm),
        'BD':dict(fontName='Helvetica',fontSize=9.5,leading=13,textColor=TIJAN_BLACK,alignment=TA_JUSTIFY,spaceAfter=2*mm),
        'SM':dict(fontName='Helvetica',fontSize=8,leading=10,textColor=TIJAN_GREY,alignment=TA_CENTER),
        'TH':dict(fontName='Helvetica-Bold',fontSize=7.5,leading=10,textColor=TIJAN_WHITE,alignment=TA_CENTER),
        'TC':dict(fontName='Helvetica',fontSize=7.5,leading=10,textColor=TIJAN_BLACK,alignment=TA_CENTER),
        'TL':dict(fontName='Helvetica',fontSize=7.5,leading=10,textColor=TIJAN_BLACK,alignment=TA_LEFT),
        'TR':dict(fontName='Helvetica',fontSize=7.5,leading=10,textColor=TIJAN_BLACK,alignment=TA_RIGHT),
        'TB':dict(fontName='Helvetica-Bold',fontSize=7.5,leading=10,textColor=TIJAN_BLACK,alignment=TA_RIGHT),
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
    canvas.drawRightString(PAGE_W-M,PAGE_H-13*mm,"MEP Bill of Quantities")
    canvas.setStrokeColor(TIJAN_BORDER); canvas.setLineWidth(0.5)
    canvas.line(M,12*mm,PAGE_W-M,12*mm)
    canvas.setFont("Helvetica",7); canvas.setFillColor(TIJAN_GREY)
    canvas.drawString(M,8*mm,"Tijan AI — BIM & MEP Engineering Automation")
    canvas.drawRightString(PAGE_W-M,8*mm,f"Page {doc.page}")
    canvas.restoreState()

def _fmt(v):
    return f"{v:,.0f}" if isinstance(v,(int,float)) else str(v)

# Lot name translations
LOT_NAMES_EN = {
    "Électricité": "Electrical",
    "Plomberie": "Plumbing",
    "CVC / Climatisation": "HVAC",
    "Courants faibles": "Low Current",
    "Sécurité incendie": "Fire Safety",
    "Ascenseurs": "Lifts",
    "Automatisation": "Building Automation",
    # Fallbacks
    "Electricité": "Electrical",
    "Climatisation": "HVAC",
    "CVC": "HVAC",
}

def _translate_lot(name):
    return LOT_NAMES_EN.get(name, name)


def generer_boq_mep_detail(rm, params_dict: dict) -> bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=22*mm,bottomMargin=18*mm,leftMargin=M,rightMargin=M)
    S=_S(); story=[]; p=params_dict or {}
    bmep=rm.boq

    # COVER
    story += [Spacer(1,25*mm), Paragraph("MEP BILL OF QUANTITIES", S['TT']),
              Paragraph("Electrical · Plumbing · HVAC · Fire · Lifts · Automation", S['SM']),
              Spacer(1,3*mm), HRFlowable(width="60%",thickness=2,color=TIJAN_GREEN,spaceAfter=8*mm)]

    info_data=[
        ["Project", p.get('nom','Project')],
        ["Location", f"{p.get('ville','Dakar')}, {p.get('pays','Senegal')}"],
        ["Built area", f"{rm.surf_batie_m2:,.0f} m²"],
        ["Units", str(rm.nb_logements)],
        ["Currency", "FCFA (XOF)"],
        ["Tiers", "Basic / High-End / Luxury"],
    ]
    irows=[[Paragraph(f"<b>{r[0]}</b>",S['BD']),Paragraph(str(r[1]),S['BD'])] for r in info_data]
    it=Table(irows,colWidths=[55*mm,105*mm])
    it.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER),('BACKGROUND',(0,0),(0,-1),TIJAN_LIGHT),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),8)]))
    story.append(it)
    story += [Spacer(1,8*mm), Paragraph(
        "Three pricing tiers allow the owner to choose finish level per lot.", S['SM']), PageBreak()]

    # LOT SUMMARY TABLE
    story.append(Paragraph("SUMMARY BY LOT", S['H1']))
    sum_headers=["Lot","Description","Basic (FCFA)","High-End (FCFA)","Luxury (FCFA)","Note"]
    sum_hdr=[Paragraph(h,S['TH']) for h in sum_headers]
    sum_data=[sum_hdr]

    lots = bmep.lots if hasattr(bmep,'lots') else []
    for l in lots:
        ld = l if isinstance(l,dict) else dataclasses.asdict(l) if dataclasses.is_dataclass(l) else {}
        lot_num = ld.get('lot','')
        designation = _translate_lot(ld.get('designation',''))
        basic = ld.get('pu_basic_fcfa', ld.get('basic_fcfa',0))
        hend = ld.get('pu_hend_fcfa', ld.get('hend_fcfa',0))
        luxury = ld.get('pu_luxury_fcfa', ld.get('luxury_fcfa',0))
        note = ld.get('note_impact', ld.get('note',''))
        sum_data.append([
            Paragraph(str(lot_num),S['TC']), Paragraph(designation,S['TL']),
            Paragraph(_fmt(basic),S['TR']), Paragraph(_fmt(hend),S['TR']),
            Paragraph(_fmt(luxury),S['TR']), Paragraph(str(note)[:60],S['TL']),
        ])

    # Totals
    for label, basic_v, hend_v, luxury_v in [
        ("TOTAL EXCL. TAX", bmep.total_basic_fcfa, bmep.total_hend_fcfa, bmep.total_luxury_fcfa),
    ]:
        sum_data.append([
            Paragraph('',S['TC']), Paragraph(f'<b>{label}</b>',S['TL']),
            Paragraph(f'<b>{_fmt(basic_v)}</b>',S['TB']),
            Paragraph(f'<b>{_fmt(hend_v)}</b>',S['TB']),
            Paragraph(f'<b>{_fmt(luxury_v)}</b>',S['TB']),
            Paragraph('',S['TL']),
        ])
    # VAT + TTC
    tva_b=bmep.total_basic_fcfa*0.18; tva_h=bmep.total_hend_fcfa*0.18; tva_l=bmep.total_luxury_fcfa*0.18
    sum_data.append([
        Paragraph('',S['TC']), Paragraph('<b>VAT (18%)</b>',S['TL']),
        Paragraph(f'<b>{_fmt(tva_b)}</b>',S['TB']), Paragraph(f'<b>{_fmt(tva_h)}</b>',S['TB']),
        Paragraph(f'<b>{_fmt(tva_l)}</b>',S['TB']), Paragraph('',S['TL']),
    ])
    sum_data.append([
        Paragraph('',S['TC']), Paragraph('<b>TOTAL INCL. TAX</b>',S['TL']),
        Paragraph(f'<b>{_fmt(bmep.total_basic_fcfa+tva_b)}</b>',S['TB']),
        Paragraph(f'<b>{_fmt(bmep.total_hend_fcfa+tva_h)}</b>',S['TB']),
        Paragraph(f'<b>{_fmt(bmep.total_luxury_fcfa+tva_l)}</b>',S['TB']),
        Paragraph('',S['TL']),
    ])

    col_w=[12*mm,42*mm,28*mm,28*mm,28*mm,25*mm]
    st=Table(sum_data,colWidths=col_w,repeatRows=1)
    st.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),TIJAN_GREEN), ('TEXTCOLOR',(0,0),(-1,0),white),
        ('ROWBACKGROUNDS',(0,1),(-1,-4),[TIJAN_WHITE,TIJAN_LIGHT]),
        ('BACKGROUND',(0,-3),(-1,-1),TIJAN_GREEN), ('TEXTCOLOR',(0,-3),(-1,-1),white),
        ('GRID',(0,0),(-1,-1),0.5,TIJAN_BORDER), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5), ('RIGHTPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(st)

    # COST RATIOS
    story.append(Spacer(1,6*mm))
    story.append(Paragraph("COST RATIOS", S['H2']))
    story.append(Paragraph(
        f"<b>Basic:</b> {bmep.ratio_basic_m2:,.0f} FCFA/m² | "
        f"<b>High-End:</b> {bmep.ratio_hend_m2:,.0f} FCFA/m²<br/>"
        f"<b>Recommendation:</b> {bmep.recommandation}", S['BD']))
    if bmep.note_choix:
        story.append(Paragraph(f"<i>{bmep.note_choix}</i>", S['BD']))

    # NOTES
    story += [Spacer(1,8*mm), Paragraph("NOTES", S['H2']), Paragraph(
        "1. Three tiers: Basic (standard), High-End (quality), Luxury (premium).<br/>"
        "2. Prices from validated local market data (Senegal, Côte d'Ivoire, Morocco).<br/>"
        "3. Labour, testing, and commissioning included per lot.<br/>"
        "4. Owner selects tier per lot — mix-and-match is supported.<br/>"
        "5. Prices valid at date of generation — subject to market fluctuation.", S['BD'])]

    story += [Spacer(1,10*mm), HRFlowable(width="100%",thickness=0.5,color=TIJAN_BORDER,spaceAfter=3*mm),
              Paragraph("<b>Disclaimer:</b> This BOQ has been generated automatically. "
                        "Final prices must be confirmed with the MEP contractor.", S['SM'])]

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0); return buf.read()

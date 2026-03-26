"""
generate_fiches_structure_en.py — Structural Materials Technical Sheets
Tijan AI — concrete, steel, formwork, Dakar suppliers
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_LOGO = next((c for c in [_os.path.join(_HERE,'tijan_logo_crop.png'),'/opt/render/project/src/tijan_logo_crop.png'] if _os.path.exists(c)), None)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
import io

NOIR = colors.HexColor("#111111")
GRIS = colors.HexColor("#888888")
GRIS_CLAIR = colors.HexColor("#E5E5E5")
FOND = colors.HexColor("#FAFAFA")
BLANC = colors.white
VERT = colors.HexColor("#43A956")
VERT_PALE = colors.HexColor("#F0FAF1")

def get_styles():
    return {
        'brand':   ParagraphStyle('brand', fontSize=8, textColor=VERT, fontName='Helvetica-Bold', spaceAfter=2),
        'title':   ParagraphStyle('title', fontSize=16, textColor=NOIR, fontName='Helvetica-Bold', spaceAfter=4),
        'subtitle':ParagraphStyle('sub', fontSize=9, textColor=GRIS, spaceAfter=8),
        'h2':      ParagraphStyle('h2', fontSize=11, textColor=VERT, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5),
        'h3':      ParagraphStyle('h3', fontSize=9, textColor=NOIR, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3),
        'normal':  ParagraphStyle('n', fontSize=9, textColor=NOIR, spaceAfter=3),
        'small':   ParagraphStyle('s', fontSize=7.5, textColor=GRIS, spaceAfter=2),
        'disc':    ParagraphStyle('d', fontSize=7, textColor=GRIS, spaceAfter=2),
    }

def hf(canvas, doc, nom, date_str):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(VERT); canvas.setFont('Helvetica-Bold', 8)
    canvas.drawString(15*mm, h-12*mm, "TIJAN AI")
    canvas.setFillColor(GRIS); canvas.setFont('Helvetica', 7.5)
    canvas.drawString(15*mm, h-17*mm, f"{nom}  —  Structural Materials Technical Sheets")
    canvas.setStrokeColor(GRIS_CLAIR)
    canvas.line(15*mm, h-19*mm, w-15*mm, h-19*mm)
    canvas.line(15*mm, 14*mm, w-15*mm, 14*mm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(15*mm, 10*mm, f"Tijan AI — {date_str} | Technical reference document")
    canvas.drawRightString(w-15*mm, 10*mm, f"Page {doc.page}")
    canvas.restoreState()

def fiche_table(titre, data, col_widths, styles):
    story = []
    story.append(Paragraph(titre, styles['h2']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_CLAIR))
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), VERT),
        ('TEXTCOLOR', (0,0), (-1,0), BLANC),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.3, GRIS_CLAIR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BLANC, FOND]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))
    return story

def generer_fiches_structure(resultats, buf, params_dict=None):
    params = {}
    if params_dict:
        params = vars(params_dict) if hasattr(params_dict, '__dict__') else params_dict

    date_str = datetime.now().strftime("%d/%m/%Y")
    nom = params.get('nom', 'Projet Tijan')
    beton = params.get('classe_beton', 'C30/37')
    fck = int(beton.split('/')[0][1:]) if '/' in beton else 30

    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm, topMargin=25*mm, bottomMargin=20*mm,
        title=f"Structural Technical Sheets — {nom}", author="Tijan AI")

    def _hf(c, d): hf(c, d, nom, date_str)
    styles = get_styles()
    story = []

    # Page de garde
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("TIJAN AI", styles['brand']))
    story.append(Paragraph("FICHES TECHNIQUES — MATERIAUX STRUCTURE", styles['title']))
    story.append(Paragraph(f"Reinforced Concrete | Steel | Formwork — {nom}", styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=VERT))
    story.append(Spacer(1, 8*mm))

    entete = [["Projet", nom], ["Localisation", params.get('ville','Dakar').capitalize() + ", Senegal"],
              ["Concrete selected", beton], ["Steel", "FeE500 / HA500 B500B"],
              ["Norme", "EN 1992-1-1 (Eurocodes) + EN 206"], ["Date", date_str]]
    t = Table(entete, colWidths=[50*mm, 125*mm])
    t.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),9),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('TEXTCOLOR',(0,0),(0,-1),VERT),('GRID',(0,0),(-1,-1),0.3,GRIS_CLAIR),
        ('BACKGROUND',(0,0),(-1,-1),FOND),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)]))
    story.append(t)
    story.append(PageBreak())

    # FICHE 1 — BÉTON
    story += fiche_table("1. REINFORCED CONCRETE — " + beton, [
        ["Parametre", "Valeur", "Reference"],
        ["Characteristic strength fck", f"{fck} MPa", "EN 206"],
        ["Design strength fcd", f"{fck/1.5:.1f} MPa", "fck / yc = 1.5"],
        ["Module d'elasticite Ecm", f"{33000 + (fck-30)*500:.0f} MPa", "EN 1992-1-1 Tab.3.1"],
        ["Classe d'exposition", "XS1 (air marin, distance mer < 5km)", "EN 1992-1-1 §4.2"],
        ["Enrobage nominal cnom", "40 mm", "EN 1992-1-1 Tab.4.4N"],
        ["Affaissement cible", "S3 — 100-150 mm", "EN 206"],
        ["Minimum cement content", "350 kg/m³", "DTU / BCEAO"],
        ["Max W/C ratioimum", "0.50", "EN 206 XS1"],
        ["Max casting temperature", "32°C (adapt in Dakar hot season)", "BFUP"],
        ["Dakar Suppliers", "CIMAF Senegal, SOCOCIM Industries", "Local market 2025"],
        ["Prix indicatif C30/37", "185 000 – 210 000 FCFA/m³", "Marche Dakar 2025"],
    ], [80*mm, 75*mm, 30*mm], styles)

    # FICHE 2 — ACIER
    story += fiche_table("2. ACIER A BETON — FeE500 / B500B", [
        ["Parametre", "Valeur", "Reference"],
        ["Designation", "FeE500 / B500B TMT", "EN 10080"],
        ["Characteristic yield strength fyk", "500 MPa", "EN 10080"],
        ["Design yield strength fyd", "434.8 MPa", "fyk / ys = 1.15"],
        ["Module d'elasticite Es", "200 000 MPa", "EN 1992-1-1"],
        ["Elongation at break minimum", "A5 >= 8%", "EN 10080"],
        ["Masse volumique", "7 850 kg/m³", "—"],
        ["Certification", "ISO 9001 + 14001, SGS", "Fabrimetal Senegal"],
        ["HA8  — 0.395 kg/ml", "480 – 540 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA10 — 0.617 kg/ml", "490 – 550 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA12 — 0.888 kg/ml", "500 – 560 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA16 — 1.578 kg/ml", "510 – 570 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA20 — 2.466 kg/ml", "510 – 580 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA25 — 3.854 kg/ml", "520 – 590 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["HA32 — 6.313 kg/ml", "530 – 600 FCFA/kg", "Fabrimetal / CFAO 2025"],
        ["Dakar Suppliers", "Fabrimetal Senegal (Sebikotane), CFAO Materials, SONACOS", "—"],
        ["Volatilite prix", "±15% selon cours LME — verifier avant marche", "LME Hot-Rolled Steel"],
    ], [70*mm, 70*mm, 45*mm], styles)

    story.append(PageBreak())

    # FICHE 3 — COFFRAGES
    story += fiche_table("3. FORMWORK AND SHORINGS", [
        ["Type", "Description", "Prix indicatif (FCFA/m²)"],
        ["Steel formwork columns", "Steel shuttering possible — 3 min rotations.", "8 000 – 12 000"],
        ["Timber formwork beams", "Soffit + sides, shoring H=3m", "7 000 – 10 000"],
        ["Table coffrante dalles", "Tables coffrantes pour dalles pleines", "5 500 – 8 000"],
        ["Stair formwork", "Custom-cut timber formwork", "12 000 – 18 000"],
        ["Etais metalliques", "Etais reglables H=2.5 a 4.0m", "Location 800 FCFA/j/piece"],
        ["Produit decoffrant", "Huile de decoffrage industrielle", "3 500 FCFA/L"],
        ["Dakar Suppliers", "CFAO Materials, Afrique Materiaux, hardware stores Industrial Zone", "—"],
    ], [60*mm, 80*mm, 45*mm], styles)

    # FICHE 4 — CONTRÔLES ET ESSAIS
    story += fiche_table("4. CONTROLES QUALITE ET ESSAIS", [
        ["Essai", "Frequence", "Laboratoire"],
        ["Concrete cubes 28d (fck)", "1 set / 50 m³ poured", "LNBTP Dakar"],
        ["In-situ concrete coring", "In case of doubt or damage", "LNBTP / Geocotra"],
        ["Steel tensile test", "1 test / batch of 20 tonnes", "LNBTP"],
        ["Steel bend test", "1 test / batch of 20 tonnes", "LNBTP"],
        ["Cover check (pachometer)", "At each level poured", "Engineering / Technical control"],
        ["Essai de compactage sol", "1 / 500 m² remblai", "LNBTP / Geocotra"],
        ["Pile load test", "1 pile / geotechnical zone", "LNBTP / Geocotra"],
        ["Essai de carbonatation", "Apres 28j, zones exposees", "LNBTP"],
        ["Bureau de controle agree", "SOCOTEC Senegal, APAVE Senegal, BUREAU VERITAS SN", "—"],
    ], [65*mm, 75*mm, 45*mm], styles)

    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_CLAIR))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Technical sheets for reference only. Dakar market prices 2024-2025, verify before tendering. "
        "Specifications definitives a valider par l'ingenieur responsable du projet.",
        styles['disc']))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)

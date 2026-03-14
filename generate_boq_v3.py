"""Wrapper BOQ pour moteur v3"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generer_boq(resultats, buf):
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("BOQ — BORDEREAU DES QUANTITÉS ET PRIX", styles['Title']))
    story.append(Paragraph("Tijan AI — Structure béton armé", styles['Normal']))
    story.append(Spacer(1, 20))
    
    b = resultats.boq
    
    story.append(Paragraph("RÉCAPITULATIF GÉNÉRAL", styles['Heading2']))
    data = [
        ["Désignation", "Quantité", "Prix unitaire", "Total FCFA"],
        ["Béton armé", f"{b.beton_total_m3:.1f} m³", "120 000 FCFA/m³", f"{b.beton_total_m3*120000:,.0f}"],
        ["Acier HA", f"{b.acier_total_kg:.0f} kg", "690 FCFA/kg", f"{b.acier_total_kg*690:,.0f}"],
        ["TOTAL BAS", "", "", f"{b.cout_total_bas:,}"],
        ["TOTAL HAUT (+20%)", "", "", f"{b.cout_total_haut:,}"],
    ]
    t = Table(data, colWidths=[180, 90, 120, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#43A956')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,-2), (-1,-1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0,-2), (-1,-1), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(f"Ratio structure : {b.ratio_fcfa_m2:,} FCFA/m²", styles['Normal']))
    story.append(Spacer(1, 10))
    
    if b.detail_lots:
        story.append(Paragraph("DÉTAIL PAR LOT", styles['Heading2']))
        for k, v in b.detail_lots.items():
            story.append(Paragraph(f"• {k} : {v:,.0f}" if isinstance(v, (int, float)) else f"• {k} : {v}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("⚠ Prix estimatifs marché Dakar 2024-2025. Acier ±15% volatilité. Vérifier avant usage contractuel.", styles['Normal']))
    
    doc.build(story)

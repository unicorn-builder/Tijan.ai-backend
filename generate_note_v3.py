"""Wrapper note de calcul pour moteur v3"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generer_note(resultats, buf):
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("NOTE DE CALCUL STRUCTUREL", styles['Title']))
    story.append(Paragraph("Tijan AI — Eurocodes EC2/EC8", styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("POTEAUX PAR NIVEAU", styles['Heading2']))
    data = [["Niveau", "Section (mm)", "Armatures", "NEd (kN)", "Vérif."]]
    for p in resultats.poteaux_par_niveau:
        data.append([
            p.label,
            f"{p.section_mm}×{p.section_mm}",
            f"{p.nb_barres}HA{p.diametre_mm}",
            f"{p.NEd_kN:.0f}",
            "✓" if p.verif_ok else "✗"
        ])
    t = Table(data, colWidths=[80, 100, 100, 80, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#43A956')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("POUTRE TYPE", styles['Heading2']))
    p = resultats.poutre_type
    story.append(Paragraph(f"Section : {p.b_mm}×{p.h_mm} mm", styles['Normal']))
    story.append(Paragraph(f"Armatures inférieures : {p.As_inf_cm2} cm²", styles['Normal']))
    story.append(Paragraph(f"Armatures supérieures : {p.As_sup_cm2} cm²", styles['Normal']))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("FONDATION", styles['Heading2']))
    f = resultats.fondation
    story.append(Paragraph(f"Type : {f.type_fond}", styles['Normal']))
    if f.nb_pieux > 0:
        story.append(Paragraph(f"Pieux : {f.nb_pieux}×ø{f.diam_pieu_mm}mm L={f.longueur_pieu_m}m", styles['Normal']))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("BOQ RÉSUMÉ", styles['Heading2']))
    b = resultats.boq
    data2 = [
        ["Béton total", f"{b.beton_total_m3:.1f} m³"],
        ["Acier total", f"{b.acier_total_kg:.0f} kg"],
        ["Coût bas", f"{b.cout_total_bas:,} FCFA"],
        ["Coût haut", f"{b.cout_total_haut:,} FCFA"],
        ["Ratio", f"{b.ratio_fcfa_m2:,} FCFA/m²"],
    ]
    t2 = Table(data2, colWidths=[200, 200])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f5f5')),
    ]))
    story.append(t2)
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("Prix estimatifs — marché Dakar 2024-2025. Vérifier avant usage contractuel.", styles['Normal']))
    
    doc.build(story)

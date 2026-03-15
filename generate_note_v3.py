"""generate_note_v3.py — Note de calcul PDF simple"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from datetime import datetime

VERT = colors.HexColor('#43A956')
NOIR = colors.HexColor('#111111')
GRIS = colors.HexColor('#555555')
BLANC = colors.white

def generer_note(resultats, buf, params_dict=None):
    generer_note_avec_donnees(resultats, params_dict or {}, buf)

def generer_note_avec_donnees(resultats, donnees_v3, buf):
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    
    nom = getattr(donnees_v3, 'nom', None) or (donnees_v3.get('nom', 'Projet Tijan') if isinstance(donnees_v3, dict) else 'Projet Tijan')
    ville = getattr(donnees_v3, 'ville', None) or (donnees_v3.get('ville', 'Dakar') if isinstance(donnees_v3, dict) else 'Dakar')
    nb_niveaux = getattr(donnees_v3, 'nb_niveaux', None) or (donnees_v3.get('nb_niveaux', 5) if isinstance(donnees_v3, dict) else 5)
    beton = getattr(donnees_v3, 'classe_beton', None) or (donnees_v3.get('classe_beton', 'C30/37') if isinstance(donnees_v3, dict) else 'C30/37')
    surface = getattr(donnees_v3, 'surface_emprise_m2', None) or (donnees_v3.get('surface_emprise_m2', 500) if isinstance(donnees_v3, dict) else 500)
    pression = getattr(donnees_v3, 'pression_sol_MPa', None) or (donnees_v3.get('pression_sol_MPa', 0.15) if isinstance(donnees_v3, dict) else 0.15)

    title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=NOIR, spaceAfter=4)
    sub_style = ParagraphStyle('S', parent=styles['Normal'], fontSize=10, textColor=GRIS, spaceAfter=12)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11, textColor=VERT, spaceBefore=12, spaceAfter=6)
    normal = ParagraphStyle('N', parent=styles['Normal'], fontSize=9, textColor=NOIR)

    story = []
    story.append(Paragraph("TIJAN AI", ParagraphStyle('brand', parent=styles['Normal'], fontSize=9, textColor=VERT)))
    story.append(Paragraph("NOTE DE CALCUL STRUCTURELLE", title_style))
    story.append(Paragraph("Eurocodes EN 1990 / EN 1991 / EN 1992 / EN 1997", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=VERT))
    story.append(Spacer(1, 8*mm))

    info = [
        ["PROJET", nom],
        ["LOCALISATION", ville],
        ["TYPE", f"R+{nb_niveaux-1}"],
        ["SURFACE EMPRISE", f"{surface} m²"],
        ["BÉTON", beton],
        ["PRESSION SOL", f"{pression} MPa"],
        ["DATE", datetime.now().strftime("%d %B %Y")],
        ["INGÉNIEUR", "À compléter par l'ingénieur responsable"],
    ]
    t = Table(info, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), VERT),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#E5E5E5')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 8*mm))

    poteaux = getattr(resultats, 'poteaux_par_niveau', [])
    if poteaux:
        story.append(Paragraph("POTEAUX PAR NIVEAU", h2_style))
        data = [["Niveau", "Section (mm)", "Armatures", "NEd (kN)", "Vérif."]]
        for p in poteaux:
            data.append([p.label, f"{p.section_mm}×{p.section_mm}",
                         f"{p.nb_barres}HA{p.diametre_mm}", f"{p.NEd_kN:.0f}",
                         "✓" if p.verif_ok else "✗"])
        t2 = Table(data, colWidths=[30*mm, 40*mm, 40*mm, 35*mm, 20*mm])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), VERT),
            ('TEXTCOLOR', (0,0), (-1,0), BLANC),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#E5E5E5')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [BLANC, colors.HexColor('#FAFAFA')]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t2)
        story.append(Spacer(1, 6*mm))

    pt = getattr(resultats, 'poutre_type', None)
    if pt:
        story.append(Paragraph("POUTRE TYPE", h2_style))
        data_pt = [
            ["Section", f"{pt.b_mm}×{pt.h_mm} mm"],
            ["Armatures inférieures", f"{pt.As_inf_cm2} cm²"],
            ["Armatures supérieures", f"{pt.As_sup_cm2} cm²"],
            ["Étriers", f"HA{pt.etrier_diam_mm}/{pt.etrier_esp_mm} mm"],
            ["Portée", f"{pt.portee_m} m"],
        ]
        t3 = Table(data_pt, colWidths=[60*mm, 100*mm])
        t3.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), VERT),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#E5E5E5')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t3)
        story.append(Spacer(1, 6*mm))

    fd = getattr(resultats, 'fondation', None)
    if fd:
        story.append(Paragraph("FONDATION", h2_style))
        data_fd = [["Type", fd.type_fond]]
        if fd.nb_pieux > 0:
            data_fd += [
                ["Nombre de pieux", str(fd.nb_pieux)],
                ["Diamètre", f"{fd.diam_pieu_mm} mm"],
                ["Longueur", f"{fd.longueur_pieu_m} m"],
                ["Armatures", f"{fd.As_cm2} cm²"],
            ]
        t4 = Table(data_fd, colWidths=[60*mm, 100*mm])
        t4.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), VERT),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#E5E5E5')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t4)
        story.append(Spacer(1, 6*mm))

    bq = getattr(resultats, 'boq', None)
    if bq:
        story.append(Paragraph("BOQ RÉSUMÉ", h2_style))
        data_bq = [
            ["Béton total", f"{bq.beton_total_m3:.1f} m³"],
            ["Acier total", f"{bq.acier_total_kg:.0f} kg"],
            ["Coût bas", f"{bq.cout_total_bas:,} FCFA"],
            ["Coût haut", f"{bq.cout_total_haut:,} FCFA"],
            ["Ratio structure", f"{bq.ratio_fcfa_m2:,} FCFA/m²"],
        ]
        t5 = Table(data_bq, colWidths=[60*mm, 100*mm])
        t5.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), VERT),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#E5E5E5')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t5)

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E5E5')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Document d'assistance à l'ingénierie. Doit être vérifié et signé par un ingénieur habilité. "
        "Prix estimatifs marché Dakar — vérifier avant usage contractuel.",
        ParagraphStyle('disc', parent=styles['Normal'], fontSize=7, textColor=GRIS)
    ))

    doc.build(story)

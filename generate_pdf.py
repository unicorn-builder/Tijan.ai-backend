"""
Tijan AI — Générateur de Note de Calcul PDF Signable
Référentiel : Eurocodes EN 1990 / EN 1991 / EN 1992 / EN 1997
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus import Frame, PageTemplate
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
import os

from engine_structural import NoteCalculComplete, ProjetStructurel

# ============================================================
# COULEURS TIJAN AI
# ============================================================
TIJAN_NOIR       = colors.HexColor("#1C1C1C")      # Texte principal
TIJAN_BLEU       = colors.HexColor("#2D6A4F")      # Vert forêt profond (headers)
TIJAN_ACCENT     = colors.HexColor("#40916C")      # Vert écologique (accents)
TIJAN_OR         = colors.HexColor("#52B788")      # Vert clair (highlights)
TIJAN_GRIS_CLAIR = colors.HexColor("#F8FAF9")      # Fond très légèrement vert
TIJAN_GRIS       = colors.HexColor("#6C757D")      # Texte secondaire
TIJAN_VERT       = colors.HexColor("#2D6A4F")      # Vérifications OK
TIJAN_ROUGE      = colors.HexColor("#DC3545")      # Alertes
TIJAN_BLANC      = colors.white                    # Blanc pur
TIJAN_VERT_PALE  = colors.HexColor("#D8F3DC")      # Fond vert très pâle
TIJAN_VERT_BORD  = colors.HexColor("#95D5B2")      # Bordure verte légère

# ============================================================
# EN-TÊTE ET PIED DE PAGE
# ============================================================

def build_header_footer(canvas, doc, projet_nom: str, ingenieur: str):
    canvas.saveState()
    w, h = A4

    # Header — fond blanc avec barre verte fine en haut
    canvas.setFillColor(TIJAN_BLANC)
    canvas.rect(0, h - 22*mm, w, 22*mm, fill=1, stroke=0)

    # Barre verte fine en haut
    canvas.setFillColor(TIJAN_ACCENT)
    canvas.rect(0, h - 1.5*mm, w, 1.5*mm, fill=1, stroke=0)

    # Accent vert vertical gauche
    canvas.setFillColor(TIJAN_OR)
    canvas.rect(0, h - 22*mm, 3*mm, 22*mm, fill=1, stroke=0)

    # Nom Tijan AI
    canvas.setFillColor(TIJAN_BLEU)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(8*mm, h - 11*mm, "TIJAN AI")

    canvas.setFillColor(TIJAN_ACCENT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(8*mm, h - 17*mm, "Engineering Intelligence for Africa")

    # Séparateur vertical
    canvas.setStrokeColor(TIJAN_VERT_BORD)
    canvas.setLineWidth(0.8)
    canvas.line(55*mm, h - 19*mm, 55*mm, h - 6*mm)

    # Infos projet
    canvas.setFillColor(TIJAN_NOIR)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(58*mm, h - 10*mm, projet_nom)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TIJAN_GRIS)
    canvas.drawString(58*mm, h - 16*mm, "Note de calcul structurelle — Eurocodes EN 1990 / EN 1991 / EN 1992 / EN 1997")

    # Ligne séparatrice header
    canvas.setStrokeColor(TIJAN_VERT_BORD)
    canvas.setLineWidth(0.8)
    canvas.line(0, h - 22*mm, w, h - 22*mm)

    # Pied de page — fond blanc
    canvas.setFillColor(TIJAN_BLANC)
    canvas.rect(0, 0, w, 14*mm, fill=1, stroke=0)

    # Ligne verte pied
    canvas.setStrokeColor(TIJAN_VERT_BORD)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, 14*mm, w - 15*mm, 14*mm)

    # Accent vert bas gauche
    canvas.setFillColor(TIJAN_OR)
    canvas.rect(0, 0, 3*mm, 14*mm, fill=1, stroke=0)

    canvas.setFillColor(TIJAN_GRIS)
    canvas.setFont("Helvetica", 6.5)
    canvas.drawString(8*mm, 8.5*mm,
        f"Genere par Tijan AI — {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
        f"Ref : EN 1990, EN 1991-1-1, EN 1992-1-1, EN 1997-1"
    )
    canvas.drawString(8*mm, 4*mm,
        "Document d'assistance a l'ingenierie. Doit etre verifie et signe par un ingenieur habilite."
    )
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(TIJAN_ACCENT)
    canvas.drawRightString(w - 15*mm, 8*mm, f"Page {doc.page}")

    canvas.restoreState()


# ============================================================
# STYLES
# ============================================================

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='TijanTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=TIJAN_BLEU,
        spaceAfter=6,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='TijanSubTitle',
        fontName='Helvetica',
        fontSize=11,
        textColor=TIJAN_GRIS,
        spaceAfter=4,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=TIJAN_BLANC,
        spaceBefore=8,
        spaceAfter=6,
        leftIndent=0,
        backColor=TIJAN_BLEU,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        name='EdgeHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=TIJAN_BLANC,
        spaceBefore=8,
        spaceAfter=6,
        backColor=TIJAN_ACCENT,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=TIJAN_BLEU,
        spaceBefore=6,
        spaceAfter=3,
        leftIndent=0,
    ))
    styles.add(ParagraphStyle(
        name='CalcNote',
        fontName='Courier',
        fontSize=7.5,
        textColor=TIJAN_NOIR,
        spaceAfter=1,
        leftIndent=8,
        leading=11,
    ))
    styles.add(ParagraphStyle(
        name='NormalSmall',
        fontName='Helvetica',
        fontSize=8,
        textColor=TIJAN_NOIR,
        spaceAfter=2,
        leading=11,
    ))
    styles.add(ParagraphStyle(
        name='OKStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=TIJAN_VERT,
    ))
    styles.add(ParagraphStyle(
        name='WarnStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=TIJAN_ROUGE,
    ))
    styles.add(ParagraphStyle(
        name='Disclaimer',
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        textColor=TIJAN_GRIS,
        spaceAfter=2,
        alignment=TA_JUSTIFY,
    ))
    styles.add(ParagraphStyle(
        name='EdgeNote',
        fontName='Helvetica',
        fontSize=8,
        textColor=TIJAN_BLEU,
        spaceAfter=2,
        leftIndent=5,
        leading=12,
    ))

    return styles


# ============================================================
# COMPOSANTS RÉUTILISABLES
# ============================================================

def section_header(title: str, styles) -> list:
    return [
        Spacer(1, 4*mm),
        Table(
            [[Paragraph(f"  {title}", styles['SectionHeader'])]],
            colWidths=[180*mm],
            style=TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), TIJAN_BLEU),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-1), 2, TIJAN_OR),
            ])
        ),
        Spacer(1, 2*mm),
    ]

def edge_section_header(title: str, styles) -> list:
    return [
        Spacer(1, 4*mm),
        Table(
            [[Paragraph(f"  {title}", styles['EdgeHeader'])]],
            colWidths=[180*mm],
            style=TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), TIJAN_ACCENT),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('LINEBELOW', (0,0), (-1,-1), 2, TIJAN_OR),
            ])
        ),
        Spacer(1, 2*mm),
    ]

def result_table(data: list, col_widths: list, styles) -> Table:
    """Tableau de résultats — fond blanc, en-tête vert."""
    row_styles = [
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.3, TIJAN_VERT_BORD),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        # Header
        ('BACKGROUND', (0,0), (-1,0), TIJAN_BLEU),
        ('TEXTCOLOR', (0,0), (-1,0), TIJAN_BLANC),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        # Lignes alternées très légèrement vertes
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [TIJAN_BLANC, TIJAN_GRIS_CLAIR]),
        # Ligne verte sous header
        ('LINEBELOW', (0,0), (-1,0), 1.5, TIJAN_OR),
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(row_styles))
    return t

def edge_table(data: list, col_widths: list) -> Table:
    """Tableau Edge — palette verte."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.3, TIJAN_VERT_BORD),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), TIJAN_ACCENT),
        ('TEXTCOLOR', (0,0), (-1,0), TIJAN_BLANC),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('LINEBELOW', (0,0), (-1,0), 1.5, TIJAN_BLEU),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [TIJAN_BLANC, TIJAN_VERT_PALE]),
    ]))
    return t

def note_calcul_block(notes: list, styles, titre: str = None) -> list:
    """Bloc note de calcul avec fond gris clair."""
    items = []
    if titre:
        items.append(Paragraph(titre, styles['SubSection']))

    calc_data = []
    for note in notes:
        if note.startswith("==="):
            continue  # déjà dans le titre de section
        # Remplacer les caractères spéciaux pour ReportLab
        note_clean = (note
            .replace("✓", "[OK]")
            .replace("⚠", "[!]")
            .replace("→", "->")
            .replace("≤", "<=")
            .replace("≥", ">=")
            .replace("×", "x")
            .replace("²", "2")
            .replace("³", "3")
            .replace("π", "pi")
            .replace("√", "sqrt")
            .replace("⌈", "ceil(")
            .replace("⌉", ")")
            .replace("σ", "sigma")
            .replace("λ", "lambda")
            .replace("ρ", "rho")
            .replace("γ", "gamma")
            .replace("τ", "tau")
            .replace("°", "deg")
        )
        if note_clean.strip():
            calc_data.append([Paragraph(note_clean, styles['CalcNote'])])

    if calc_data:
        t = Table(calc_data, colWidths=[175*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F6F8")),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CED4DA")),
            ('LINEAFTER', (0,0), (0,-1), 2, TIJAN_ACCENT),
        ]))
        items.append(t)
        items.append(Spacer(1, 3*mm))

    return items


# ============================================================
# PAGES DU DOCUMENT
# ============================================================

def page_garde(projet: ProjetStructurel, ingenieur: str, styles) -> list:
    story = []
    story.append(Spacer(1, 20*mm))

    # Bloc projet
    story.append(Paragraph("NOTE DE CALCUL STRUCTURELLE", styles['TijanTitle']))
    story.append(Paragraph("Dimensionnement selon Eurocodes EN 1990 / EN 1991 / EN 1992 / EN 1997", styles['TijanSubTitle']))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=TIJAN_OR))
    story.append(Spacer(1, 6*mm))

    # Infos projet
    info_data = [
        ["PROJET", projet.nom],
        ["LOCALISATION", f"{projet.localisation.ville.value.capitalize()} — Distance mer : {projet.localisation.distance_mer_km} km"],
        ["TYPE", f"Bâtiment {projet.usage.usage_principal.value} — R+{projet.geometrie.nb_niveaux}"],
        ["SURFACE EMPRISE", f"{projet.geometrie.surface_emprise_m2} m²"],
        ["PORTÉE MAX", f"{projet.geometrie.portee_max_m} m"],
        ["HAUTEUR D'ÉTAGE", f"{projet.geometrie.hauteur_etage_m} m"],
        ["PRESSION SOL", f"{projet.sol.pression_admissible_MPa} MPa — {projet.sol.description}"],
        ["DATE", datetime.now().strftime("%d %B %Y")],
        ["INGÉNIEUR", ingenieur],
    ]

    t = Table(info_data, colWidths=[55*mm, 125*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), TIJAN_ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.HexColor("#DEE2E6")),
        ('BACKGROUND', (0,0), (-1,-1), TIJAN_GRIS_CLAIR),
        ('BOX', (0,0), (-1,-1), 1, TIJAN_ACCENT),
    ]))
    story.append(t)
    story.append(Spacer(1, 10*mm))

    # Disclaimer signable
    story.append(HRFlowable(width="100%", thickness=0.5, color=TIJAN_GRIS))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Ce document constitue une note de calcul générée par Tijan AI sur la base des données "
        "fournies et des Eurocodes en vigueur. Il appartient à l'ingénieur responsable de vérifier "
        "l'ensemble des hypothèses, de valider les résultats au regard du contexte spécifique du "
        "projet, et d'apposer sa signature avant toute utilisation dans le cadre d'une procédure "
        "réglementaire ou contractuelle.",
        styles['Disclaimer']
    ))
    story.append(Spacer(1, 12*mm))

    # Zone signature
    sig_data = [
        ["VÉRIFIÉ PAR", "DATE DE VALIDATION", "SIGNATURE & CACHET"],
        ["\n\n\n", "\n\n\n", "\n\n\n"],
    ]
    t_sig = Table(sig_data, colWidths=[60*mm, 60*mm, 60*mm])
    t_sig.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), TIJAN_BLANC),
        ('BACKGROUND', (0,0), (-1,0), TIJAN_BLEU),
        ('GRID', (0,0), (-1,-1), 0.5, TIJAN_GRIS),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_sig)
    story.append(PageBreak())

    return story


def page_resume(resultat: NoteCalculComplete, styles) -> list:
    story = []
    story += section_header("RÉSUMÉ EXÉCUTIF — SYNTHÈSE DES RÉSULTATS", styles)

    r = resultat.resume_executif
    v = r.get("verifications", {})

    # Tableau résumé principal
    resume_data = [
        ["ÉLÉMENT", "RÉSULTAT", "VÉRIFICATION"],
        ["Béton / Exposition", r.get("beton", "—"), "OK"],
        ["Enrobage nominal", r.get("enrobage", "—"), "OK"],
        ["Voiles — épaisseur", r.get("voile_epaisseur", "—"), v.get("flambement_voile", "—")],
        ["Voiles — ferraillage vertical", r.get("voile_ferraillage_vertical", "—"), "OK"],
        ["Dalle — épaisseur", r.get("dalle_epaisseur", "—"), v.get("fleche_dalle", "—")],
        ["Dalle — As inférieur", r.get("dalle_ferraillage_inf", "—"), v.get("poinconnement_dalle", "—")],
        ["Poteaux — section (RDC)", r.get("poteau_section", "—"), v.get("flambement_poteau", "—")],
        ["Poteaux — ferraillage", r.get("poteau_ferraillage", "—"), "OK"],
        ["Poteaux — cadres", r.get("poteau_cadres", "—"), "OK"],
        ["Poutres — section", r.get("poutre_section", "—"), "OK"],
        ["Poutres — As inférieur", r.get("poutre_ferraillage_inf", "—"), v.get("cisaillement_poutre", "—")],
        ["Poutres — étriers", r.get("poutre_etriers", "—"), "OK"],
        ["Fondations — type", r.get("fondations_type", "—"), "OK"],
        ["Charge totale base", r.get("charge_totale_base", "—"), "—"],
    ]

    # Colorer les vérifications
    styled_data = []
    for i, row in enumerate(resume_data):
        if i == 0:
            styled_data.append(row)
        else:
            verif = row[2]
            if "OK" in str(verif):
                verif_p = Paragraph(verif, styles['OKStyle'])
            elif "REVOIR" in str(verif) or "REQUIS" in str(verif):
                verif_p = Paragraph(verif, styles['WarnStyle'])
            else:
                verif_p = Paragraph(str(verif), styles['NormalSmall'])
            styled_data.append([row[0], row[1], verif_p])

    t = result_table(styled_data, [70*mm, 75*mm, 35*mm], styles)
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # Encadré chapeau si présent
    if resultat.dalle.epaisseur_chapeau_m:
        chapeau_data = [
            ["CHAPEAU DE POINÇONNEMENT REQUIS"],
            [f"Épaisseur locale : {int(resultat.dalle.epaisseur_chapeau_m*100)} cm  |  "
             f"Rayon zone épaissie : {round(3*(resultat.dalle.epaisseur_retenue_m - 0.048),2)*100:.0f} cm autour du poteau  |  "
             f"As poinçonnement : {resultat.dalle.ferraillage_chapeau_cm2} cm²"],
        ]
        t_ch = Table(chapeau_data, colWidths=[180*mm])
        t_ch.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FFF3CD")),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FFFBF0")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#856404")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#FFEEBA")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_ch)

    story.append(PageBreak())
    return story


def page_notes_calcul(resultat: NoteCalculComplete, styles) -> list:
    story = []
    story += section_header("NOTES DE CALCUL DÉTAILLÉES — RÉFÉRENTIEL EUROCODES", styles)

    # 1. Matériaux
    story.append(Paragraph("1. CLASSE BÉTON ET MATÉRIAUX", styles['SubSection']))
    beton = resultat.beton
    mat_data = [
        ["Paramètre", "Valeur", "Référence"],
        ["Classe exposition", beton.classe_exposition.value, "EN 1992-1-1 §4.4"],
        ["Justification", beton.justification, "—"],
        ["Résistance caractéristique fck", f"{beton.fc28_MPa} MPa", "EN 206"],
        ["Résistance de calcul fcd", f"{beton.fcd_MPa} MPa", f"fck/yc = {beton.fc28_MPa}/{1.5}"],
        ["Acier FeE500 — fyk", "500 MPa", "EN 10080"],
        ["Résistance de calcul fyd", f"{beton.fyd_MPa:.1f} MPa", f"fyk/ys = 500/1.15"],
        ["Enrobage nominal cnom", f"{beton.enrobage_mm} mm", "EN 1992-1-1 Tab.4.4N"],
    ]
    story.append(result_table(mat_data, [65*mm, 70*mm, 45*mm], styles))
    story.append(Spacer(1, 4*mm))

    # 2. Descente de charges
    story.append(Paragraph("2. DESCENTE DE CHARGES — EN 1991-1-1 + EN 1990", styles['SubSection']))
    dc = resultat.descente_charges
    charges_data = [
        ["Charge", "Valeur (kN/m²)", "Référence"],
        ["G dalle (poids propre béton)", f"{dc.charge_permanente_G_kNm2 - 2.0:.2f}", "EN 1991-1-1"],
        ["G superposé (cloisons + revêt.)", "2.00", "EN 1991-1-1"],
        ["G total", f"{dc.charge_permanente_G_kNm2:.2f}", "—"],
        ["Q exploitation", f"{dc.charge_exploitation_Q_kNm2:.2f}", "EN 1991-1-1 Tab.6.1"],
        ["Combinaison ELU (1.35G+1.5Q)", f"{dc.combinaison_ELU_kNm2:.2f}", "EN 1990 §6.4.3"],
        ["Combinaison ELS (G+Q)", f"{dc.combinaison_ELS_kNm2:.2f}", "EN 1990 §6.5.3"],
        ["Charge totale par niveau", f"{dc.charge_totale_par_niveau_kN:.1f} kN", "—"],
        ["Charge totale à la base", f"{dc.charge_totale_base_kN:.1f} kN", "—"],
    ]
    story.append(result_table(charges_data, [80*mm, 55*mm, 45*mm], styles))
    story.append(Spacer(1, 4*mm))

    # Notes détaillées descente
    story += note_calcul_block(
        [n for n in dc.note_calcul if not n.startswith("===")],
        styles
    )

    # 3. Voiles
    story.append(Paragraph("3. DIMENSIONNEMENT VOILES — EN 1992-1-1 §9.6", styles['SubSection']))
    vo = resultat.voile
    voile_data = [
        ["Paramètre", "Valeur", "Vérification"],
        ["Épaisseur retenue", f"{vo.epaisseur_retenue_m*100:.0f} cm",
         "OK [OK]" if vo.verification_flambement else "[!] A REVOIR"],
        ["Ferraillage vertical", f"{vo.ferraillage_vertical_cm2_m} cm²/ml", "EN 1992-1-1 §9.6.2"],
        ["Ferraillage horizontal", f"{vo.ferraillage_horizontal_cm2_m} cm²/ml", "EN 1992-1-1 §9.6.2"],
        ["Taux d'armature", f"{vo.taux_armature_pct}%", "min 0.2% OK"],
        ["Contrainte compression", f"{vo.contrainte_compression_MPa} MPa", f"<= 0.3fcd = {round(0.3*beton.fcd_MPa,1)} MPa"],
    ]
    story.append(result_table(voile_data, [80*mm, 55*mm, 45*mm], styles))
    story.append(Spacer(1, 3*mm))
    story += note_calcul_block(
        [n for n in vo.note_calcul if not n.startswith("===")], styles
    )

    # 4. Dalle
    story.append(Paragraph("4. DIMENSIONNEMENT DALLE PLEINE — EN 1992-1-1 §5.3 + §6.4", styles['SubSection']))
    da = resultat.dalle
    dalle_data = [
        ["Paramètre", "Valeur", "Vérification"],
        ["Épaisseur dalle courante", f"{da.epaisseur_retenue_m*100:.0f} cm",
         "OK [OK]" if da.verification_fleche else "[!] A REVOIR"],
        ["As inférieur (travée)", f"{da.ferraillage_inferieur_cm2_m} cm²/ml", "—"],
        ["As supérieur (appuis)", f"{da.ferraillage_superieur_cm2_m} cm²/ml", "—"],
        ["Poinçonnement", "Chapeau requis" if da.epaisseur_chapeau_m else "OK sans armatures",
         "OK [OK]" if da.verification_poinconnement else "[!] A REVOIR"],
    ]
    if da.epaisseur_chapeau_m:
        dalle_data.append(["Épaisseur chapeau local", f"{da.epaisseur_chapeau_m*100:.0f} cm", "Zone 3d autour poteau"])
        dalle_data.append(["As poinçonnement", f"{da.ferraillage_chapeau_cm2} cm²", "EN 1992-1-1 §6.4.5"])
    story.append(result_table(dalle_data, [80*mm, 55*mm, 45*mm], styles))
    story.append(Spacer(1, 3*mm))
    story += note_calcul_block(
        [n for n in da.note_calcul if not n.startswith("===")], styles
    )

    story.append(PageBreak())

    # 5. Poteaux
    story += section_header("NOTES DE CALCUL — POTEAUX, POUTRES ET FONDATIONS", styles)
    story.append(Paragraph("5. DIMENSIONNEMENT POTEAUX — EN 1992-1-1 §5.8 + §9.5", styles['SubSection']))
    po = resultat.poteau
    poteau_data = [
        ["Paramètre", "Valeur (RDC)", "Vérification"],
        ["Section (poteau le plus chargé)", f"{int(po.section_b_m*100)}x{int(po.section_h_m*100)} cm",
         "OK [OK]" if po.verification_flambement else "[!] FLAMB."],
        ["Longueur de flambement l0", f"{po.longueur_flambement_m} m", "0.7 x H etage"],
        ["Ferraillage longitudinal", f"{po.nb_barres}HA{po.diametre_barres_mm} ({po.ferraillage_longitudinal_cm2} cm²)", "—"],
        ["Taux d'armature", f"{po.taux_armature_pct}%", "0.2% <= t <= 3%"],
        ["Cadres transversaux", f"HA{po.ferraillage_transversal_mm} / {po.espacement_cadres_mm} mm", "EN 1992-1-1 §9.5.3"],
        ["Contrainte compression", f"{po.contrainte_compression_MPa} MPa", "—"],
    ]
    story.append(result_table(poteau_data, [80*mm, 60*mm, 40*mm], styles))
    story.append(Spacer(1, 3*mm))
    story += note_calcul_block(
        [n for n in po.note_calcul if not n.startswith("===") and n.strip()], styles
    )

    # 6. Poutres
    story.append(Paragraph("6. DIMENSIONNEMENT POUTRES — EN 1992-1-1 §6.1 + §6.2", styles['SubSection']))
    pu = resultat.poutre
    poutre_data = [
        ["Paramètre", "Valeur", "Vérification"],
        ["Section b x h", f"{int(pu.largeur_b_m*100)}x{int(pu.hauteur_h_m*100)} cm", "—"],
        ["Hauteur utile d", f"{pu.hauteur_utile_d_m} m", "—"],
        ["Moment travée", f"{pu.moment_travee_kNm} kN.m", "—"],
        ["Moment appui", f"{pu.moment_appui_kNm} kN.m", "—"],
        ["Effort tranchant V_Ed", f"{pu.effort_tranchant_kN} kN", "—"],
        ["As inférieur (travée)", f"{pu.nb_barres_inf}HA{pu.diametre_barres_mm} ({pu.ferraillage_inferieur_cm2} cm²)", "—"],
        ["As supérieur (appuis)", f"{pu.nb_barres_sup}HA{pu.diametre_barres_mm} ({pu.ferraillage_superieur_cm2} cm²)", "—"],
        ["Étriers cisaillement", f"HA{pu.ferraillage_transversal_mm} / {pu.espacement_cadres_mm} mm",
         "OK [OK]" if pu.verification_cisaillement else "[!] A REVOIR"],
    ]
    story.append(result_table(poutre_data, [80*mm, 60*mm, 40*mm], styles))
    story.append(Spacer(1, 3*mm))
    story += note_calcul_block(
        [n for n in pu.note_calcul if not n.startswith("===")], styles
    )

    # 7. Fondations
    story.append(Paragraph("7. DIMENSIONNEMENT FONDATIONS — EN 1997-1", styles['SubSection']))
    fo = resultat.fondations
    fondations_data = [["Paramètre", "Valeur", "Note"]]
    fondations_data.append(["Type de fondation", fo.type_fondation, "—"])
    fondations_data.append(["Justification", fo.justification, "EN 1997-1"])

    if fo.type_fondation == "Semelles isolées":
        fondations_data += [
            ["Dimensions semelle", f"{fo.largeur_semelle_m}x{fo.longueur_semelle_m} m", "—"],
            ["Épaisseur semelle", f"{fo.epaisseur_semelle_m} m", "—"],
        ]
    elif fo.type_fondation == "Radier général":
        fondations_data += [
            ["Épaisseur radier", f"{fo.epaisseur_radier_m} m", "—"],
            ["As radier", f"{fo.ferraillage_radier_cm2_m} cm²/ml", "Bi-directionnel inf+sup"],
        ]
    elif fo.type_fondation == "Pieux forés":
        fondations_data += [
            ["Diamètre pieux", f"{fo.diametre_pieux_m} m", "—"],
            ["Longueur pieux", f"{fo.longueur_pieux_m} m", "—"],
            ["Nb pieux par poteau", f"{fo.nb_pieux_par_poteau}", "—"],
        ]

    story.append(result_table(fondations_data, [80*mm, 60*mm, 40*mm], styles))
    story.append(Spacer(1, 3*mm))
    story += note_calcul_block(
        [n for n in fo.note_calcul if not n.startswith("===")], styles
    )

    story.append(PageBreak())
    return story


def page_references(styles) -> list:
    story = []
    story += section_header("RÉFÉRENCES NORMATIVES ET HYPOTHÈSES DE CALCUL", styles)

    refs_data = [
        ["Norme", "Titre", "Application"],
        ["EN 1990:2002", "Bases de calcul des structures", "Combinaisons ELU/ELS"],
        ["EN 1991-1-1:2002", "Actions sur les structures — Charges permanentes et d'exploitation", "Descente de charges"],
        ["EN 1991-1-4:2005", "Actions sur les structures — Actions du vent", "Charges latérales"],
        ["EN 1992-1-1:2004", "Calcul des structures en béton — Règles générales", "Dimensionnement BA"],
        ["EN 1997-1:2004", "Calcul géotechnique — Règles générales", "Dimensionnement fondations"],
        ["EN 206:2013", "Béton — Spécification, performances, production et conformité", "Classe béton/exposition"],
    ]
    story.append(result_table(refs_data, [40*mm, 90*mm, 50*mm], styles))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("HYPOTHÈSES DE CALCUL", styles['SubSection']))
    hyp_data = [
        ["Hypothèse", "Valeur retenue"],
        ["Poids volumique béton armé", "25.0 kN/m³ (EN 1991-1-1)"],
        ["Charges superposées (cloisons + revêt.)", "2.0 kN/m² (forfaitaire)"],
        ["Charge exploitation résidentiel", "1.5 kN/m² (EN 1991-1-1 Tab.6.1 Cat.A)"],
        ["Charge exploitation bureaux", "2.5 kN/m² (EN 1991-1-1 Tab.6.1 Cat.B)"],
        ["Coefficient partiel béton yc", "1.50 (EN 1992-1-1 §2.4.2.4)"],
        ["Coefficient partiel acier ys", "1.15 (EN 1992-1-1 §2.4.2.4)"],
        ["Acier longitudinal", "FeE500 — fyk = 500 MPa (EN 10080)"],
        ["Longueur de flambement poteaux", "l0 = 0.7 x H_étage (pied encastré, tête rotule)"],
        ["Élancement limite poteaux", "lambda <= 30 (EN 1992-1-1 §5.8.3.1)"],
        ["Taux armature max poteaux (sécurité)", "3% (vs 4% normative)"],
        ["Méthode calcul cisaillement", "EN 1992-1-1 §6.2.3 — bielles inclinées theta=45deg"],
        ["Poinçonnement — périmètre contrôle", "u1 à 2d de la face du poteau (EN 1992-1-1 §6.4.2)"],
    ]
    story.append(result_table(hyp_data, [100*mm, 80*mm], styles))
    story.append(Spacer(1, 6*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=TIJAN_GRIS))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Les calculs présentés dans cette note constituent une assistance à la conception structurelle. "
        "Ils sont basés sur les Eurocodes et les données fournies par le maître d'ouvrage. "
        "L'ingénieur responsable doit vérifier la cohérence des hypothèses avec les conditions réelles "
        "du site, valider les résultats par rapport aux normes locales applicables, et apposer sa "
        "signature et son cachet professionnel avant toute utilisation officielle de ce document.",
        styles['Disclaimer']
    ))

    return story


# ============================================================
# PAGE EDGE — CONFORMITÉ CERTIFICATION
# ============================================================

def calculer_score_edge(projet: ProjetStructurel, resultat: NoteCalculComplete) -> dict:
    """
    Calcul du score Edge basé sur les paramètres structurels et MEP estimés.
    Edge cible : 20% minimum de réduction sur énergie, eau et matériaux.
    Référentiel : IFC Edge Standard v3.
    """
    geo = projet.geometrie
    beton = resultat.beton
    dalle = resultat.dalle

    score = {}

    # === ÉNERGIE (cible : -20% vs baseline) ===
    # Paramètres influencés par les choix structurels
    points_energie = []

    # Orientation et masse thermique (dalle épaisse = inertie thermique)
    inertie = "Élevée" if dalle.epaisseur_retenue_m >= 0.20 else "Moyenne"
    gain_inertie = 4 if dalle.epaisseur_retenue_m >= 0.20 else 2
    points_energie.append({
        "critere": "Masse thermique (inertie dalle)",
        "valeur": f"e={int(dalle.epaisseur_retenue_m*100)}cm — {inertie}",
        "gain_pct": gain_inertie,
        "statut": "OK"
    })

    # Isolation thermique estimée (voiles béton — recommandation)
    points_energie.append({
        "critere": "Isolation thermique voiles (recommandation)",
        "valeur": "Isolant extérieur 6cm minimum recommande",
        "gain_pct": 8,
        "statut": "A SPECIFIER"
    })

    # Vitrage performant (estimé)
    points_energie.append({
        "critere": "Vitrage performant (estimation)",
        "valeur": "Double vitrage Low-E recommande",
        "gain_pct": 5,
        "statut": "A SPECIFIER"
    })

    # Ventilation naturelle (Dakar — vents dominants favorables)
    if projet.localisation.ville.value == "dakar":
        points_energie.append({
            "critere": "Ventilation naturelle (Dakar — vents favorables)",
            "valeur": "Orientation et ouvertures a optimiser",
            "gain_pct": 5,
            "statut": "A OPTIMISER"
        })

    total_energie = sum(p["gain_pct"] for p in points_energie)
    score["energie"] = {
        "points": points_energie,
        "total_pct": total_energie,
        "cible_pct": 20,
        "conforme": total_energie >= 20,
        "ecart": total_energie - 20
    }

    # === EAU (cible : -20% vs baseline) ===
    points_eau = []

    # Récupération eaux pluviales (toiture disponible)
    surface_toiture = geo.surface_emprise_m2
    points_eau.append({
        "critere": "Recuperation eaux pluviales",
        "valeur": f"Surface toiture disponible : {surface_toiture} m2",
        "gain_pct": 8,
        "statut": "A SPECIFIER"
    })

    points_eau.append({
        "critere": "Robinetterie economique (debit reduit)",
        "valeur": "Robinets 6L/min vs 12L/min standard",
        "gain_pct": 7,
        "statut": "A SPECIFIER"
    })

    points_eau.append({
        "critere": "Chasse d'eau double debit",
        "valeur": "3/6L vs 9L standard",
        "gain_pct": 6,
        "statut": "A SPECIFIER"
    })

    total_eau = sum(p["gain_pct"] for p in points_eau)
    score["eau"] = {
        "points": points_eau,
        "total_pct": total_eau,
        "cible_pct": 20,
        "conforme": total_eau >= 20,
        "ecart": total_eau - 20
    }

    # === MATÉRIAUX (cible : -20% vs baseline) ===
    points_materiaux = []

    # Béton optimisé (sections variables poteaux = moins de béton)
    points_materiaux.append({
        "critere": "Optimisation sections poteaux (variables/niveau)",
        "valeur": "Sections reduites aux niveaux superieurs",
        "gain_pct": 5,
        "statut": "OK"
    })

    # Classe béton minimale (éviter surdimensionnement)
    gain_beton = 4 if beton.fc28_MPa <= 30 else 2
    points_materiaux.append({
        "critere": f"Classe beton optimisee (C{int(beton.fc28_MPa)})",
        "valeur": f"C{int(beton.fc28_MPa)} — Minimum requis exposition {beton.classe_exposition.value}",
        "gain_pct": gain_beton,
        "statut": "OK"
    })

    # Acier recyclé
    points_materiaux.append({
        "critere": "Acier a haute teneur en recyclee (recommandation)",
        "valeur": "Acier FeE500 issu de filieres recyclees >= 70%",
        "gain_pct": 6,
        "statut": "A SPECIFIER"
    })

    # Béton avec cendres volantes ou laitier
    points_materiaux.append({
        "critere": "Substitution ciment (cendres volantes/laitier)",
        "valeur": "30% substitution recommandee — reduire empreinte carbone",
        "gain_pct": 7,
        "statut": "A SPECIFIER"
    })

    total_mat = sum(p["gain_pct"] for p in points_materiaux)
    score["materiaux"] = {
        "points": points_materiaux,
        "total_pct": total_mat,
        "cible_pct": 20,
        "conforme": total_mat >= 20,
        "ecart": total_mat - 20
    }

    # Score global
    nb_conformes = sum(1 for k in ["energie", "eau", "materiaux"] if score[k]["conforme"])
    score["global"] = {
        "nb_criteres_conformes": nb_conformes,
        "certifiable": nb_conformes == 3,
        "statut": "CERTIFIABLE" if nb_conformes == 3 else f"{nb_conformes}/3 criteres conformes"
    }

    return score


def page_edge(projet: ProjetStructurel, resultat: NoteCalculComplete, styles) -> list:
    story = []
    story += edge_section_header(
        "ANALYSE DE CONFORMITE EDGE — IFC EDGE STANDARD v3", styles
    )

    # Intro Edge
    intro_data = [
        [Paragraph(
            "La certification EDGE (Excellence in Design for Greater Efficiencies) exige une reduction "
            "minimale de 20% de la consommation d'energie, d'eau et des emissions liees aux materiaux "
            "incorpores, par rapport a un batiment de reference. Cette analyse est basee sur les choix "
            "structurels retenus dans la presente note de calcul et sur les recommandations techniques "
            "pour atteindre la certification.",
            styles['EdgeNote']
        )]
    ]
    t_intro = Table(intro_data, colWidths=[180*mm])
    t_intro.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), TIJAN_VERT_PALE),
        ('BOX', (0,0), (-1,-1), 1, TIJAN_VERT_BORD),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBEFORE', (0,0), (0,-1), 3, TIJAN_ACCENT),
    ]))
    story.append(t_intro)
    story.append(Spacer(1, 5*mm))

    # Calcul score
    score = calculer_score_edge(projet, resultat)

    # Tableau synthèse globale
    story.append(Paragraph("SYNTHESE DES SCORES EDGE", styles['SubSection']))

    def statut_edge(conforme, total, cible):
        if conforme:
            return f"[OK] {total}% >= {cible}%"
        else:
            return f"[!] {total}% < {cible}% (ecart : {total-cible}%)"

    synthese_data = [
        ["Pilier Edge", "Score Atteint", "Cible", "Statut"],
        [
            "Energie",
            f"{score['energie']['total_pct']}%",
            "20%",
            statut_edge(score['energie']['conforme'],
                       score['energie']['total_pct'], 20)
        ],
        [
            "Eau",
            f"{score['eau']['total_pct']}%",
            "20%",
            statut_edge(score['eau']['conforme'],
                       score['eau']['total_pct'], 20)
        ],
        [
            "Materiaux",
            f"{score['materiaux']['total_pct']}%",
            "20%",
            statut_edge(score['materiaux']['conforme'],
                       score['materiaux']['total_pct'], 20)
        ],
        [
            "RESULTAT GLOBAL",
            f"{score['global']['nb_criteres_conformes']}/3 criteres",
            "3/3",
            score['global']['statut']
        ],
    ]
    story.append(edge_table(synthese_data, [50*mm, 35*mm, 25*mm, 70*mm]))
    story.append(Spacer(1, 5*mm))

    # Détail par pilier
    for pilier_key, pilier_label, emoji in [
        ("energie", "PILIER 1 — ENERGIE", "Energie"),
        ("eau", "PILIER 2 — EAU", "Eau"),
        ("materiaux", "PILIER 3 — MATERIAUX ET EMISSIONS", "Materiaux"),
    ]:
        pilier = score[pilier_key]
        story.append(Paragraph(
            f"{pilier_label} — Objectif : -{pilier['cible_pct']}% | "
            f"Score : {pilier['total_pct']}% | "
            f"{'CONFORME [OK]' if pilier['conforme'] else 'NON CONFORME [!]'}",
            styles['SubSection']
        ))

        detail_data = [["Critere", "Specification", "Gain (%)", "Statut"]]
        for p in pilier["points"]:
            detail_data.append([
                p["critere"],
                p["valeur"],
                f"+{p['gain_pct']}%",
                p["statut"]
            ])
        # Ligne total
        detail_data.append([
            "TOTAL",
            "",
            f"+{pilier['total_pct']}%",
            "OK" if pilier["conforme"] else f"Deficit {abs(pilier['ecart'])}%"
        ])

        story.append(edge_table(detail_data, [60*mm, 72*mm, 18*mm, 30*mm]))
        story.append(Spacer(1, 4*mm))

    # Recommandations finales
    story.append(Paragraph("RECOMMANDATIONS POUR CERTIFICATION EDGE", styles['SubSection']))
    reco_data = [
        ["Priorite", "Action", "Impact"],
        ["1 — Obligatoire",
         "Mandater un auditeur Edge agree IFC pour verification officielle",
         "Prerequis certification"],
        ["2 — Conception",
         "Integrer simulation thermique dynamique (logiciel Edge App IFC)",
         "Validation score energie"],
        ["3 — Materiaux",
         "Sourcer acier FeE500 recycle >= 70% et beton avec 30% laitier/cendres",
         "+11% score materiaux"],
        ["4 — Eau",
         "Specifier robinetterie 6L/min, chasse double debit, cuve recuperation pluviale",
         "+21% score eau"],
        ["5 — Enveloppe",
         "Isolation exterieure voiles 6cm + double vitrage Low-E (U <= 1.8 W/m2K)",
         "+13% score energie"],
        ["6 — Documentation",
         "Constituer le dossier Edge : fiches FDES materiaux, bilans energie/eau",
         "Dossier certification"],
    ]
    story.append(edge_table(reco_data, [38*mm, 102*mm, 40*mm]))
    story.append(Spacer(1, 4*mm))

    # Disclaimer Edge
    disclaimer_data = [
        [Paragraph(
            "AVERTISSEMENT : Cette analyse Edge est une pre-evaluation indicative basee sur les "
            "parametres structurels du projet. Elle ne constitue pas une certification officielle. "
            "La certification Edge requiert l'utilisation de l'outil officiel Edge App (IFC), "
            "un audit par un verificateur agree, et la validation de l'ensemble des criteres "
            "selon le referentiel Edge v3 applicable au pays du projet.",
            styles['Disclaimer']
        )]
    ]
    t_disc = Table(disclaimer_data, colWidths=[180*mm])
    t_disc.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, TIJAN_VERT_BORD),
        ('BACKGROUND', (0,0), (-1,-1), TIJAN_GRIS_CLAIR),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_disc)
    story.append(PageBreak())

    return story


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def generer_pdf(
    resultat: NoteCalculComplete,
    projet: ProjetStructurel,
    output_path: str,
    ingenieur: str = "A completer par l'ingenieur responsable"
):
    """Génère le PDF complet de la note de calcul."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=28*mm,
        bottomMargin=20*mm,
        title=f"Note de calcul — {projet.nom}",
        author="Tijan AI",
        subject="Note de calcul structurelle — Eurocodes + Edge",
    )

    styles = get_styles()

    def header_footer(canvas, doc):
        build_header_footer(canvas, doc, projet.nom, ingenieur)

    story = []
    story += page_garde(projet, ingenieur, styles)
    story += page_resume(resultat, styles)
    story += page_notes_calcul(resultat, styles)
    story += page_edge(projet, resultat, styles)
    story += page_references(styles)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF genere : {output_path}")
    return output_path

"""
generate_fiches_all.py — Fiches techniques completes pour TOUS les postes du DPGF
Tijan AI — 36 fiches : Structure (9) + MEP (21) + Finitions (6)
Chaque fiche = 1 page avec specs, prix materiau/pose, mise en oeuvre, fournisseurs
"""
from tijan_theme import *
from prix_marche import get_prix_structure, get_prix_mep, get_prix
from tijan_theme import devise_label
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io

# ══════════════════════════════════════════════════════════════
# STYLES LOCAUX
# ══════════════════════════════════════════════════════════════
_S = {
    'fiche_code': ParagraphStyle(
        'fiche_code', fontName='Helvetica-Bold', fontSize=11,
        textColor=VERT_DARK, spaceBefore=0, spaceAfter=1, leading=13),
    'fiche_title': ParagraphStyle(
        'fiche_title', fontName='Helvetica-Bold', fontSize=10,
        textColor=NOIR, spaceBefore=0, spaceAfter=1, leading=12),
    'fiche_norm': ParagraphStyle(
        'fiche_norm', fontName='Helvetica-Oblique', fontSize=7,
        textColor=GRIS3, spaceBefore=0, spaceAfter=3, leading=9),
    'sec_h': ParagraphStyle(
        'sec_h', fontName='Helvetica-Bold', fontSize=8,
        textColor=VERT, spaceBefore=4, spaceAfter=2, leading=10),
    'meo': ParagraphStyle(
        'meo', fontName='Helvetica', fontSize=7, textColor=NOIR,
        leading=9, spaceAfter=1, leftIndent=6),
    'meo_b': ParagraphStyle(
        'meo_b', fontName='Helvetica-Bold', fontSize=7, textColor=NOIR,
        leading=9, spaceAfter=1, leftIndent=6),
    'footer_note': ParagraphStyle(
        'footer_note', fontName='Helvetica-Oblique', fontSize=6,
        textColor=GRIS3, leading=8, spaceAfter=0),
}

# ══════════════════════════════════════════════════════════════
# HELPER: build one fiche page
# ══════════════════════════════════════════════════════════════

def _prix_split(total, ratio_mat):
    """Split total price into material and labour."""
    mat = int(total * ratio_mat)
    pose = total - mat
    return mat, pose


def _specs_table(specs_pairs):
    """
    Build 4-column specs table from list of (label, value) pairs.
    Uses full content width split into left/right halves with proper spacing.
    """
    mid = (len(specs_pairs) + 1) // 2
    left = specs_pairs[:mid]
    right = specs_pairs[mid:]
    rows = []
    for i in range(max(len(left), len(right))):
        lp = left[i] if i < len(left) else ('', '')
        rp = right[i] if i < len(right) else ('', '')
        rows.append([
            Paragraph(str(lp[0]), S['td_b']),
            Paragraph(str(lp[1]), S['td']),
            Paragraph(str(rp[0]), S['td_b']),
            Paragraph(str(rp[1]), S['td']),
        ])
    # Full-width table: label (30%) + value (20%) | label (30%) + value (20%)
    t = Table(rows, colWidths=[CW * 0.28, CW * 0.22, CW * 0.28, CW * 0.22])
    style_cmds = [
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.3, GRIS2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        # Light green header-like background for label columns
        ('BACKGROUND', (0, 0), (0, -1), VERT_LIGHT),
        ('BACKGROUND', (2, 0), (2, -1), VERT_LIGHT),
    ]
    # zebra on value columns
    for i in range(0, len(rows), 2):
        style_cmds.append(('BACKGROUND', (1, i), (1, i), GRIS1))
        style_cmds.append(('BACKGROUND', (3, i), (3, i), GRIS1))
    t.setStyle(TableStyle(style_cmds))
    return t


def _prix_table(ville, mat_prix, mat_unit, pose_prix, pose_unit, ratio_label_fr, ratio_label_en, lang):
    """Build 3-row pricing table."""
    dl = devise_label()
    lbl_mat = "Materiau / Equipement" if lang == 'fr' else "Material / Equipment"
    lbl_pose = "Pose / Installation" if lang == 'fr' else "Installation / Labour"
    lbl_total = "Total fourni-pose" if lang == 'fr' else "Total supplied-installed"
    total = mat_prix + pose_prix
    header = f"PRIX MARCHE ({ville})" if lang == 'fr' else f"MARKET PRICE ({ville})"
    rows = [
        [Paragraph(header, S['td_b']), '', '', ''],
        [Paragraph(lbl_mat, S['td']),
         Paragraph(fmt_fcfa(mat_prix), S['td_r']),
         Paragraph(f"/ {mat_unit}", S['td']),
         Paragraph(ratio_label_fr if lang == 'fr' else ratio_label_en, S['td'])],
        [Paragraph(lbl_pose, S['td']),
         Paragraph(fmt_fcfa(pose_prix), S['td_r']),
         Paragraph(f"/ {mat_unit}", S['td']), Paragraph('', S['td'])],
        [Paragraph(lbl_total, S['td_b']),
         Paragraph(fmt_fcfa(total), S['td_b_r']),
         Paragraph(f"/ {mat_unit}", S['td_b']), Paragraph('', S['td'])],
    ]
    t = Table(rows, colWidths=[CW * 0.35, CW * 0.25, CW * 0.15, CW * 0.25])
    t.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), VERT),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLANC),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.3, GRIS2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, -1), (-1, -1), VERT_LIGHT),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, VERT),
    ]))
    return t


def _meo_block(items, lang):
    """Build mise en oeuvre bullet list."""
    title = "MISE EN OEUVRE" if lang == 'fr' else "IMPLEMENTATION"
    elems = [Paragraph(title, _S['sec_h'])]
    for item in items:
        elems.append(Paragraph(f"• {item}", _S['meo']))
    return elems


def _footer_block(fournisseurs, normes, lang):
    """Build supplier and norms footer."""
    lbl_f = "Fournisseurs" if lang == 'fr' else "Suppliers"
    lbl_n = "Normes" if lang == 'fr' else "Standards"
    return [
        Spacer(1, 2 * mm),
        HRFlowable(width=CW, thickness=0.3, color=GRIS2, spaceAfter=1),
        Paragraph(f"<b>{lbl_f} :</b> {fournisseurs}", _S['footer_note']),
        Paragraph(f"<b>{lbl_n} :</b> {normes}", _S['footer_note']),
    ]


def _build_fiche(code, titre, norme_ref, specs, ville, mat_prix, mat_unit,
                 pose_prix, ratio_label_fr, ratio_label_en, meo_items,
                 fournisseurs, normes, lang):
    """Assemble a full fiche page as a KeepTogether."""
    elems = []
    elems.append(Paragraph(code, _S['fiche_code']))
    elems.append(Paragraph(titre, _S['fiche_title']))
    elems.append(Paragraph(f"{'Norme de reference' if lang == 'fr' else 'Reference standard'}: {norme_ref}", _S['fiche_norm']))
    elems.append(Spacer(1, 1 * mm))
    elems.append(_specs_table(specs))
    elems.append(Spacer(1, 2 * mm))
    elems.append(_prix_table(ville, mat_prix, mat_unit, pose_prix, mat_unit,
                             ratio_label_fr, ratio_label_en, lang))
    elems.append(Spacer(1, 2 * mm))
    elems.extend(_meo_block(meo_items, lang))
    elems.extend(_footer_block(fournisseurs, normes, lang))
    return [KeepTogether(elems), PageBreak()]


def _build_fiche_no_prix(code, titre, norme_ref, specs, meo_items,
                         fournisseurs, normes, lang):
    """Assemble a fiche page WITHOUT pricing section."""
    elems = []
    elems.append(Paragraph(code, _S['fiche_code']))
    elems.append(Paragraph(titre, _S['fiche_title']))
    elems.append(Paragraph(f"{'Norme de reference' if lang == 'fr' else 'Reference standard'}: {norme_ref}", _S['fiche_norm']))
    elems.append(Spacer(1, 1 * mm))
    elems.append(_specs_table(specs))
    elems.append(Spacer(1, 3 * mm))
    elems.extend(_meo_block(meo_items, lang))
    elems.extend(_footer_block(fournisseurs, normes, lang))
    return [KeepTogether(elems), PageBreak()]


# ══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════

def generer_fiches_techniques(rs_structure, rs_mep, params: dict, lang: str = "fr") -> bytes:
    """
    Generate comprehensive technical data sheets for ALL BOQ items.

    rs_structure: ResultatsStructure (can be None)
    rs_mep: ResultatsMEP (can be None)
    params: project params dict with keys: nom, ville, nb_niveaux, surface_emprise_m2, usage, etc.
    """
    set_pdf_lang(lang)
    buf = io.BytesIO()
    ville = params.get('ville', 'Dakar')
    nom = params.get('nom', 'Projet Tijan')
    nb_niveaux = params.get('nb_niveaux', 5)
    surface = params.get('surface_emprise_m2', 300)
    usage = params.get('usage', 'residentiel')
    date_str = datetime.now().strftime('%d/%m/%Y')

    # Resolve prices
    ps = get_prix_structure(ville)
    pm = get_prix_mep(ville)
    pp = get_prix(ville)
    ville_cap = ville.capitalize()

    # Resolve concrete/steel from engine or params
    classe_beton = 'C30/37'
    classe_acier = 'HA500'
    fck = 30.0
    fyk = 500.0
    if rs_structure:
        classe_beton = getattr(rs_structure, 'classe_beton', classe_beton)
        classe_acier = getattr(rs_structure, 'classe_acier', classe_acier)
        fck = getattr(rs_structure, 'fck_MPa', fck)
        fyk = getattr(rs_structure, 'fyk_MPa', fyk)
    elif params.get('classe_beton'):
        classe_beton = params['classe_beton']
        try:
            fck = float(classe_beton.split('/')[0].replace('C', ''))
        except Exception:
            fck = 30.0

    fcd = fck / 1.5
    ecm = 22000 * (fck / 10) ** 0.3  # EN 1992-1-1 Tab 3.1
    fyd = fyk / 1.15

    # Pick beton price based on class
    beton_map = {
        'C25/30': ps.beton_c2530_m3,
        'C30/37': ps.beton_c3037_m3,
        'C35/45': ps.beton_c3545_m3,
        'C40/50': ps.beton_c4050_m3,
    }
    prix_beton = beton_map.get(classe_beton, ps.beton_c3037_m3)

    # Header/footer
    doc_title = "Fiches Techniques Completes" if lang == 'fr' else "Complete Technical Data Sheets"
    hf = HeaderFooter(nom, doc_title, lang=lang)

    doc = SimpleDocTemplate(
        buf, pagesize=PAGE,
        rightMargin=MR, leftMargin=ML,
        topMargin=24 * mm, bottomMargin=18 * mm,
        title=f"{doc_title} — {nom}", author="Tijan AI",
    )

    story = []

    # ── COVER PAGE ──────────────────────────────────────────
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph("TIJAN AI", S['h1']))
    story.append(Spacer(1, 2 * mm))
    cover_title = "FICHES TECHNIQUES COMPLETES" if lang == 'fr' else "COMPLETE TECHNICAL DATA SHEETS"
    cover_sub = "Structure + MEP + Finitions — 36 fiches" if lang == 'fr' else "Structure + MEP + Finishes — 36 sheets"
    story.append(Paragraph(cover_title, S['titre']))
    story.append(Paragraph(cover_sub, S['sous_titre']))
    story.append(HRFlowable(width=CW, thickness=2, color=VERT, spaceAfter=6))
    story.append(Spacer(1, 6 * mm))

    info_rows = [
        [p("Projet" if lang == 'fr' else "Project", 'td_b'), p(nom, 'td')],
        [p("Localisation" if lang == 'fr' else "Location", 'td_b'), p(f"{ville_cap}", 'td')],
        [p("Niveaux" if lang == 'fr' else "Levels", 'td_b'), p(f"R+{nb_niveaux}", 'td')],
        [p("Surface emprise" if lang == 'fr' else "Footprint", 'td_b'), p(f"{surface} m2", 'td')],
        [p("Beton" if lang == 'fr' else "Concrete", 'td_b'), p(classe_beton, 'td')],
        [p("Acier" if lang == 'fr' else "Steel", 'td_b'), p(classe_acier, 'td')],
        [p("Date", 'td_b'), p(date_str, 'td')],
    ]
    t = Table(info_rows, colWidths=[CW * 0.3, CW * 0.7])
    t.setStyle(table_style(zebra=True))
    story.append(t)

    # Table of contents
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("SOMMAIRE" if lang == 'fr' else "TABLE OF CONTENTS", S['h1']))
    story.append(HRFlowable(width=CW, thickness=0.5, color=GRIS2, spaceAfter=4))

    toc_items_fr = [
        "STRUCTURE",
        "  STR-01 Beton arme", "  STR-02 Acier a beton", "  STR-03 Coffrage et etaiement",
        "  STR-04 Terrassement", "  STR-05 Fondations profondes (pieux)",
        "  STR-06 Maconnerie", "  STR-07 Enduits et platres",
        "  STR-08 Etancheite", "  STR-09 Controles qualite",
        "MEP - ELECTRICITE",
        "  MEP-E01 Transformateur HTA/BT", "  MEP-E02 Groupe electrogene",
        "  MEP-E03 TGBT", "  MEP-E04 Cablage electrique",
        "  MEP-E05 Luminaires LED", "  MEP-E06 Appareillage",
        "MEP - PLOMBERIE",
        "  MEP-P01 Tuyauterie PVC", "  MEP-P02 Equipements sanitaires",
        "  MEP-P03 Cuves et pompes", "  MEP-P04 Chauffe-eau solaire",
        "MEP - CVC",
        "  MEP-C01 Splits/climatiseurs", "  MEP-C02 VMC",
        "  MEP-C03 Gaines de ventilation",
        "MEP - COURANTS FAIBLES",
        "  MEP-CF01 Cablage RJ45/fibre", "  MEP-CF02 Videosurveillance",
        "  MEP-CF03 Controle d'acces",
        "MEP - SECURITE INCENDIE",
        "  MEP-SI01 Detection incendie", "  MEP-SI02 RIA / Sprinklers",
        "  MEP-SI03 Extincteurs",
        "MEP - DIVERS",
        "  MEP-ASC01 Ascenseurs", "  MEP-GTB01 Systeme GTB/BMS",
        "FINITIONS",
        "  FIN-01 Carrelage", "  FIN-02 Menuiserie interieure",
        "  FIN-03 Menuiserie exterieure", "  FIN-04 Faux-plafonds",
        "  FIN-05 Peinture", "  FIN-06 Cuisine",
    ]
    toc_items_en = [
        "STRUCTURE",
        "  STR-01 Reinforced concrete", "  STR-02 Reinforcing steel", "  STR-03 Formwork",
        "  STR-04 Earthworks", "  STR-05 Deep foundations (piles)",
        "  STR-06 Masonry", "  STR-07 Renders and plasters",
        "  STR-08 Waterproofing", "  STR-09 Quality control",
        "MEP - ELECTRICAL",
        "  MEP-E01 HV/LV Transformer", "  MEP-E02 Generator set",
        "  MEP-E03 MSSB", "  MEP-E04 Electrical cabling",
        "  MEP-E05 LED Luminaires", "  MEP-E06 Wiring accessories",
        "MEP - PLUMBING",
        "  MEP-P01 PVC piping", "  MEP-P02 Sanitary equipment",
        "  MEP-P03 Tanks and pumps", "  MEP-P04 Solar water heater",
        "MEP - HVAC",
        "  MEP-C01 Split AC units", "  MEP-C02 Ventilation (CMV)",
        "  MEP-C03 Ventilation ducts",
        "MEP - LOW CURRENT",
        "  MEP-CF01 RJ45/fibre cabling", "  MEP-CF02 Video surveillance",
        "  MEP-CF03 Access control",
        "MEP - FIRE SAFETY",
        "  MEP-SI01 Fire detection", "  MEP-SI02 Hose reels / Sprinklers",
        "  MEP-SI03 Extinguishers",
        "MEP - MISC",
        "  MEP-ASC01 Elevators", "  MEP-GTB01 BMS system",
        "FINISHES",
        "  FIN-01 Tiling", "  FIN-02 Interior joinery",
        "  FIN-03 Exterior joinery", "  FIN-04 Suspended ceilings",
        "  FIN-05 Painting", "  FIN-06 Kitchen",
    ]
    toc = toc_items_fr if lang == 'fr' else toc_items_en
    for item in toc:
        st = 'td_b' if not item.startswith('  ') else 'td'
        story.append(Paragraph(item, S[st]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # SECTION 1: STRUCTURE FICHES
    # ══════════════════════════════════════════════════════════
    story.extend(section_title("A", "STRUCTURE" if lang == 'fr' else "STRUCTURE"))
    story.append(PageBreak())

    # ── STR-01 Beton arme ────────────────────────────────────
    mat_b, pose_b = _prix_split(prix_beton, 0.75)
    enrobage = "40 mm" if fck >= 30 else "35 mm"
    dosage = "400 kg/m3" if fck >= 30 else "350 kg/m3"
    ec_ratio = "0.50" if fck >= 30 else "0.55"
    exposition = "XS1 (air marin)" if lang == 'fr' else "XS1 (marine air)"

    story.extend(_build_fiche(
        code="STR-01",
        titre="Beton arme" if lang == 'fr' else "Reinforced Concrete",
        norme_ref="NF EN 206 / NF EN 1992-1-1 (Eurocode 2)",
        specs=[
            ("Classe", classe_beton),
            ("fck", f"{fck:.0f} MPa"),
            ("fcd", f"{fcd:.1f} MPa"),
            ("Ecm", f"{ecm:.0f} MPa"),
            ("Dosage ciment" if lang == 'fr' else "Cement dosage", dosage),
            ("Rapport E/C max" if lang == 'fr' else "W/C ratio max", ec_ratio),
            ("Affaissement" if lang == 'fr' else "Slump", "S3 (100-150 mm)"),
            ("Adjuvants", "Plastifiant + retardateur"),
            ("Cure", "7 jours min, bache humide" if lang == 'fr' else "7 days min, wet curing"),
            ("Exposition" if lang == 'fr' else "Exposure", exposition),
            ("Enrobage cnom", enrobage),
            ("Temp. max coulage" if lang == 'fr' else "Max pour temp.", "32 C"),
        ],
        ville=ville_cap, mat_prix=mat_b, mat_unit="m3",
        pose_prix=pose_b,
        ratio_label_fr="75% mat. / 25% pose",
        ratio_label_en="75% mat. / 25% labour",
        meo_items=[
            "Verifier coffrages et ferraillage avant coulage" if lang == 'fr' else "Check formwork and rebar before pour",
            "Vibration par aiguille vibrante (diam. 40-60 mm), pas > 50 cm" if lang == 'fr' else "Vibrate with needle vibrator (40-60 mm), max 50 cm spacing",
            "Cure humide obligatoire 7 jours (bache + arrosage)" if lang == 'fr' else "Wet curing mandatory 7 days (sheeting + watering)",
            "Eviter coulage > 32 C; decaler aux heures fraiches (5h-10h)" if lang == 'fr' else "Avoid pouring above 32 C; schedule early morning (5-10 AM)",
            "Eprouvettes: 1 serie de 3 cubes / 50 m3 coules" if lang == 'fr' else "Test cubes: 1 set of 3 per 50 m3 poured",
            "Equipe: 1 chef + 2 macons + 4 manoeuvres + 1 vibreur" if lang == 'fr' else "Crew: 1 foreman + 2 masons + 4 labourers + 1 vibrator",
            "Rendement: 15-25 m3/jour selon element" if lang == 'fr' else "Output: 15-25 m3/day depending on element",
            "Reception: eprouvettes 28j >= fck, pas de nid de cailloux" if lang == 'fr' else "Acceptance: 28d cubes >= fck, no honeycombing",
        ],
        fournisseurs="SOCOCIM Industries, CIMAF Senegal, DANGOTE Cement, Lafarge Holcim",
        normes="NF EN 206, NF EN 1992-1-1, DTU 21, NF EN 12350/12390",
        lang=lang,
    ))

    # ── STR-02 Acier a beton ─────────────────────────────────
    prix_acier = ps.acier_ha500_kg if 'HA500' in classe_acier else ps.acier_ha400_kg
    mat_a, pose_a = _prix_split(prix_acier, 0.60)

    story.extend(_build_fiche(
        code="STR-02",
        titre="Acier a beton" if lang == 'fr' else "Reinforcing Steel",
        norme_ref="NF EN 10080 / NF A 35-080-1",
        specs=[
            ("Designation", f"{classe_acier} B500B"),
            ("fyk", f"{fyk:.0f} MPa"),
            ("fyd", f"{fyd:.1f} MPa"),
            ("Es", "200 000 MPa"),
            ("Allongement Agt" if lang == 'fr' else "Elongation Agt", ">= 5%"),
            ("Allongement A5", ">= 8%"),
            ("Densite" if lang == 'fr' else "Density", "7 850 kg/m3"),
            ("HA8", "0.395 kg/ml"),
            ("HA10", "0.617 kg/ml"),
            ("HA12", "0.888 kg/ml"),
            ("HA16", "1.578 kg/ml"),
            ("HA20", "2.466 kg/ml"),
            ("HA25", "3.854 kg/ml"),
            ("HA32", "6.313 kg/ml"),
        ],
        ville=ville_cap, mat_prix=mat_a, mat_unit="kg",
        pose_prix=pose_a,
        ratio_label_fr="60% mat. / 40% faconnage+pose",
        ratio_label_en="60% mat. / 40% fabrication+install",
        meo_items=[
            "Stockage sur cales, a l'abri des intemperies" if lang == 'fr' else "Store on blocks, sheltered from weather",
            "Faconnage: mandrin >= 4d (HA8-16), >= 7d (HA20-32)" if lang == 'fr' else "Bending: mandrel >= 4d (HA8-16), >= 7d (HA20-32)",
            "Longueur de recouvrement: Lb >= 40d (zone courante)" if lang == 'fr' else "Lap length: Lb >= 40d (standard zone)",
            "Ligatures HA6 tous les 15 cm sur poteaux" if lang == 'fr' else "Ties HA6 every 15 cm on columns",
            "Calage enrobage: cales plastiques certifiees" if lang == 'fr' else "Cover spacers: certified plastic chairs",
            "Equipe: 1 chef ferrailleur + 3 ferrailleurs + 2 aides" if lang == 'fr' else "Crew: 1 rebar foreman + 3 fitters + 2 helpers",
            "Rendement: 300-500 kg/jour/equipe" if lang == 'fr' else "Output: 300-500 kg/day/crew",
            "Reception: essai traction + pliage sur 1 lot / 20 tonnes" if lang == 'fr' else "Acceptance: tensile + bend test per 20-tonne lot",
        ],
        fournisseurs="Fabrimetal Senegal (Sebikotane), CFAO Materials, ArcelorMittal West Africa",
        normes="NF EN 10080, NF A 35-080-1, NF EN 1992-1-1 ch.8",
        lang=lang,
    ))

    # ── STR-03 Coffrage et etaiement ────────────────────────
    mat_c, pose_c = _prix_split(ps.coffrage_bois_m2, 0.30)

    story.extend(_build_fiche(
        code="STR-03",
        titre="Coffrage et etaiement" if lang == 'fr' else "Formwork and Shoring",
        norme_ref="NF EN 13670 / DTU 21",
        specs=[
            ("Coffrage bois" if lang == 'fr' else "Timber formwork", f"{fmt_fcfa(ps.coffrage_bois_m2)}/m2"),
            ("Coffrage metal" if lang == 'fr' else "Steel formwork", f"{fmt_fcfa(ps.coffrage_metal_m2)}/m2"),
            ("Reutilisations bois" if lang == 'fr' else "Timber reuses", "3-5 fois"),
            ("Reutilisations metal" if lang == 'fr' else "Steel reuses", "50-100 fois"),
            ("Hauteur max etaiement" if lang == 'fr' else "Max shoring height", "4.0 m"),
            ("Fleche max" if lang == 'fr' else "Max deflection", "L/500"),
            ("Decoffrage poteaux" if lang == 'fr' else "Strip columns", "24-48h"),
            ("Decoffrage dalles" if lang == 'fr' else "Strip slabs", "21 jours"),
            ("Huile de decoffrage" if lang == 'fr' else "Release agent", "3 500 FCFA/L"),
            ("Etais reglables" if lang == 'fr' else "Adjustable props", "800 FCFA/j/piece"),
        ],
        ville=ville_cap, mat_prix=mat_c, mat_unit="m2",
        pose_prix=pose_c,
        ratio_label_fr="30% mat. / 70% pose",
        ratio_label_en="30% mat. / 70% labour",
        meo_items=[
            "Nettoyer et huiler les panneaux avant chaque usage" if lang == 'fr' else "Clean and oil panels before each use",
            "Verification alignement et verticalite au fil a plomb" if lang == 'fr' else "Check alignment and plumb with plumb line",
            "Etaiement: espacement max 1.20 m sous dalles" if lang == 'fr' else "Props: max 1.20 m spacing under slabs",
            "Decoffrage progressif, jamais brutal (risque fissures)" if lang == 'fr' else "Progressive stripping, never sudden (crack risk)",
            "Attendre resistance >= 70% fck pour decoffrage porteur" if lang == 'fr' else "Wait for >= 70% fck before load-bearing strip",
            "Equipe: 1 chef coffreur + 2 coffreurs + 2 manoeuvres" if lang == 'fr' else "Crew: 1 formwork foreman + 2 carpenters + 2 labourers",
            "Rendement: 15-20 m2/jour/equipe (coffrage traditionnel)" if lang == 'fr' else "Output: 15-20 m2/day/crew (traditional formwork)",
            "Reception: tolerance +/- 5 mm sur dimensions finies" if lang == 'fr' else "Acceptance: +/- 5 mm tolerance on finished dimensions",
        ],
        fournisseurs="CFAO Materials, Afrique Materiaux, quincailleries Zone Industrielle Dakar",
        normes="NF EN 13670, DTU 21, NF EN 1065 (etais)",
        lang=lang,
    ))

    # ── STR-04 Terrassement ──────────────────────────────────
    mat_t, pose_t = _prix_split(ps.terr_mecanique_m3, 0.40)

    story.extend(_build_fiche(
        code="STR-04",
        titre="Terrassement" if lang == 'fr' else "Earthworks",
        norme_ref="DTU 12 / NF P 11-300",
        specs=[
            ("Terrassement mecanique" if lang == 'fr' else "Mechanical excavation", f"{fmt_fcfa(ps.terr_mecanique_m3)}/m3"),
            ("Terrassement manuel" if lang == 'fr' else "Manual excavation", f"{fmt_fcfa(ps.terr_manuel_m3)}/m3"),
            ("Remblai compacte" if lang == 'fr' else "Compacted backfill", f"{fmt_fcfa(ps.remblai_m3)}/m3"),
            ("Profondeur fouille" if lang == 'fr' else "Excavation depth", "0.80 - 2.50 m"),
            ("Compactage cible" if lang == 'fr' else "Target compaction", ">= 95% OPM"),
            ("Materiel pelle" if lang == 'fr' else "Excavator", "CAT 320 / Komatsu PC200"),
            ("Camions" if lang == 'fr' else "Trucks", "Benne 10-15 m3"),
            ("Blindage" if lang == 'fr' else "Shoring", "> 1.30 m profondeur"),
        ],
        ville=ville_cap, mat_prix=mat_t, mat_unit="m3",
        pose_prix=pose_t,
        ratio_label_fr="40% engin / 60% MO+transport",
        ratio_label_en="40% equipment / 60% labour+transport",
        meo_items=[
            "Implantation topographique avant demarrage" if lang == 'fr' else "Topographic survey before start",
            "Verifier nappe phreatique (rabattement si necessaire)" if lang == 'fr' else "Check water table (dewatering if needed)",
            "Blindage obligatoire au-dela de 1.30 m de profondeur" if lang == 'fr' else "Shoring mandatory beyond 1.30 m depth",
            "Compactage par couches de 30 cm max" if lang == 'fr' else "Compact in layers of 30 cm max",
            "Essai a la plaque tous les 500 m2" if lang == 'fr' else "Plate bearing test every 500 m2",
            "Eviter terrassement en saison des pluies (juin-octobre)" if lang == 'fr' else "Avoid earthworks in rainy season (June-October)",
            "Equipe: 1 conducteur + 1 topographe + 4 manoeuvres" if lang == 'fr' else "Crew: 1 operator + 1 surveyor + 4 labourers",
            "Rendement: 80-150 m3/jour (mecanique)" if lang == 'fr' else "Output: 80-150 m3/day (mechanical)",
        ],
        fournisseurs="CSE Senegal, Eiffage Senegal, Jean Lefevre, entreprises locales",
        normes="DTU 12, NF P 11-300, NF P 94-078 (CBR)",
        lang=lang,
    ))

    # ── STR-05 Fondations profondes (pieux) ─────────────────
    prix_pieu = ps.pieu_fore_d800_ml
    mat_p, pose_p = _prix_split(prix_pieu, 0.55)

    story.extend(_build_fiche(
        code="STR-05",
        titre="Fondations profondes (pieux)" if lang == 'fr' else "Deep Foundations (Piles)",
        norme_ref="NF EN 1997-1 (Eurocode 7) / NF EN 1536",
        specs=[
            ("Pieu d600 mm", f"{fmt_fcfa(ps.pieu_fore_d600_ml)}/ml"),
            ("Pieu d800 mm", f"{fmt_fcfa(ps.pieu_fore_d800_ml)}/ml"),
            ("Pieu d1000 mm", f"{fmt_fcfa(ps.pieu_fore_d1000_ml)}/ml"),
            ("Type", "Fore a la tariere" if lang == 'fr' else "CFA bored"),
            ("Longueur courante" if lang == 'fr' else "Typical length", "10 - 25 m"),
            ("Beton", classe_beton),
            ("Armature cage" if lang == 'fr' else "Rebar cage", "6-8 HA16-20 + cerces HA8/20cm"),
            ("Essai integrite" if lang == 'fr' else "Integrity test", "Sonique (CSL) 100%"),
            ("Essai chargement" if lang == 'fr' else "Load test", "1 / zone geotechnique"),
            ("Recepage" if lang == 'fr' else "Cut-off", "50-80 cm au-dessus semelle"),
        ],
        ville=ville_cap, mat_prix=mat_p, mat_unit="ml",
        pose_prix=pose_p,
        ratio_label_fr="55% mat. / 45% forage+pose",
        ratio_label_en="55% mat. / 45% drilling+install",
        meo_items=[
            "Etude geotechnique G2 AVP obligatoire avant forage" if lang == 'fr' else "G2 geotechnical study mandatory before drilling",
            "Verifier verticalite foreuse (tolerance 1/100)" if lang == 'fr' else "Check drill verticality (tolerance 1/100)",
            "Betonnage au tube plongeur, remontee continue" if lang == 'fr' else "Concrete via tremie pipe, continuous pull-up",
            "Cage d'armature: centreurs tous les 3 m" if lang == 'fr' else "Rebar cage: spacers every 3 m",
            "Essai sonique systematique avant recepage" if lang == 'fr' else "Systematic sonic test before cut-off",
            "Recepage au marteau hydraulique, pas au BRH sur beton frais" if lang == 'fr' else "Cut-off with hydraulic hammer, not breaker on fresh concrete",
            "Equipe: 1 foreuse + 1 grutier + 1 chef pieux + 4 ouvriers" if lang == 'fr' else "Crew: 1 drill rig + 1 crane op + 1 pile foreman + 4 workers",
            "Rendement: 2-4 pieux/jour selon longueur et terrain" if lang == 'fr' else "Output: 2-4 piles/day depending on length and ground",
        ],
        fournisseurs="Bachy Senegal, Franki Fondation, Soletanche Bachy, Geocotra",
        normes="NF EN 1997-1, NF EN 1536, NF P 94-262, NF EN 12699",
        lang=lang,
    ))

    # ── STR-06 Maconnerie ────────────────────────────────────
    mat_m, pose_m = _prix_split(ps.agglo_creux_20_m2, 0.55)

    story.extend(_build_fiche(
        code="STR-06",
        titre="Maconnerie" if lang == 'fr' else "Masonry",
        norme_ref="DTU 20.1 / NF EN 1996-1-1 (Eurocode 6)",
        specs=[
            ("Agglo creux 10 cm" if lang == 'fr' else "Hollow block 10 cm", f"{fmt_fcfa(ps.agglo_creux_10_m2)}/m2"),
            ("Agglo creux 15 cm", f"{fmt_fcfa(ps.agglo_creux_15_m2)}/m2"),
            ("Agglo creux 20 cm", f"{fmt_fcfa(ps.agglo_creux_20_m2)}/m2"),
            ("Agglo plein 25 cm" if lang == 'fr' else "Solid block 25 cm", f"{fmt_fcfa(ps.agglo_plein_25_m2)}/m2"),
            ("Brique pleine" if lang == 'fr' else "Solid brick", f"{fmt_fcfa(ps.brique_pleine_m2)}/m2"),
            ("BA13 simple" if lang == 'fr' else "Plasterboard single", f"{fmt_fcfa(ps.ba13_simple_m2)}/m2"),
            ("BA13 double" if lang == 'fr' else "Plasterboard double", f"{fmt_fcfa(ps.ba13_double_m2)}/m2"),
            ("Mortier dosage" if lang == 'fr' else "Mortar dosage", "350-400 kg/m3 ciment"),
            ("Chainages" if lang == 'fr' else "Ring beams", "Tous les 3.00 m de hauteur"),
            ("13 agglos/m2", "Joints 1-2 cm"),
        ],
        ville=ville_cap, mat_prix=mat_m, mat_unit="m2",
        pose_prix=pose_m,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% labour",
        meo_items=[
            "Mouiller les agglos la veille (absorption mortier)" if lang == 'fr' else "Wet blocks the day before (mortar absorption)",
            "Montee max 1.50 m/jour pour laisser secher le mortier" if lang == 'fr' else "Max 1.50 m/day to let mortar dry",
            "Chainages horizontaux tous les 3 m de hauteur" if lang == 'fr' else "Horizontal ring beams every 3 m height",
            "Chainages verticaux aux angles et encadrements" if lang == 'fr' else "Vertical tie beams at corners and openings",
            "Aplomb au fil a plomb, regle de 2 m" if lang == 'fr' else "Check plumb with plumb line, 2 m straightedge",
            "Joints remplis: pas de joints secs" if lang == 'fr' else "Filled joints: no dry joints",
            "Equipe: 1 macon + 1 aide + 1 manoeuvre" if lang == 'fr' else "Crew: 1 mason + 1 helper + 1 labourer",
            "Rendement: 3-5 m2/heure/macon" if lang == 'fr' else "Output: 3-5 m2/hour/mason",
        ],
        fournisseurs="SOCOCIM, CIMAF, DANGOTE Cement, agglotieres locales",
        normes="DTU 20.1, NF EN 1996-1-1, NF EN 771-3 (agglos)",
        lang=lang,
    ))

    # ── STR-07 Enduits et platres ────────────────────────────
    # Estimated enduit price: ~8,000 FCFA/m2 (not in prix_marche directly)
    prix_enduit = int(ps.agglo_creux_10_m2 * 0.65)  # approximate
    mat_e, pose_e = _prix_split(prix_enduit, 0.40)

    story.extend(_build_fiche(
        code="STR-07",
        titre="Enduits et platres" if lang == 'fr' else "Renders and Plasters",
        norme_ref="DTU 26.1 / NF EN 998-1",
        specs=[
            ("Enduit ciment ext." if lang == 'fr' else "Ext. cement render", "15-20 mm"),
            ("Enduit ciment int." if lang == 'fr' else "Int. cement render", "10-15 mm"),
            ("Enduit platre" if lang == 'fr' else "Plaster render", "10 mm"),
            ("Dosage gobetis" if lang == 'fr' else "Spatter dash dosage", "500-600 kg/m3"),
            ("Dosage corps enduit" if lang == 'fr' else "Body coat dosage", "350-400 kg/m3"),
            ("Dosage finition" if lang == 'fr' else "Finish coat dosage", "250-300 kg/m3"),
            ("3 couches" if lang == 'fr' else "3 coats", "Gobetis + corps + finition"),
            ("Epaisseur totale" if lang == 'fr' else "Total thickness", "15-25 mm"),
        ],
        ville=ville_cap, mat_prix=mat_e, mat_unit="m2",
        pose_prix=pose_e,
        ratio_label_fr="40% mat. / 60% pose",
        ratio_label_en="40% mat. / 60% labour",
        meo_items=[
            "Humidifier le support la veille (sauf platre)" if lang == 'fr' else "Moisten substrate day before (except plaster)",
            "Gobetis rugueux: jeter a la truelle, ne pas lisser" if lang == 'fr' else "Spatter dash: throw with trowel, do not smooth",
            "Attendre 48h entre couches" if lang == 'fr' else "Wait 48h between coats",
            "Temperature ambiante 5-35 C, pas de vent fort" if lang == 'fr' else "Ambient temp 5-35 C, no strong wind",
            "Arroser pendant 3 jours apres application (cure)" if lang == 'fr' else "Water for 3 days after application (curing)",
            "Equipe: 1 enduiseur + 1 aide" if lang == 'fr' else "Crew: 1 plasterer + 1 helper",
            "Rendement: 8-12 m2/jour/enduiseur" if lang == 'fr' else "Output: 8-12 m2/day/plasterer",
            "Reception: planeite 5 mm sous regle de 2 m" if lang == 'fr' else "Acceptance: flatness 5 mm under 2 m straightedge",
        ],
        fournisseurs="SOCOCIM, CIMAF, Placoplatre (platre), Weber (enduits prets)",
        normes="DTU 26.1, NF EN 998-1, NF EN 13914",
        lang=lang,
    ))

    # ── STR-08 Etancheite ────────────────────────────────────
    mat_et, pose_et = _prix_split(ps.etanch_sbs_m2, 0.55)

    story.extend(_build_fiche(
        code="STR-08",
        titre="Etancheite" if lang == 'fr' else "Waterproofing",
        norme_ref="DTU 43 / NF EN 13707 (SBS) / NF EN 13956 (PVC)",
        specs=[
            ("SBS bicouche" if lang == 'fr' else "SBS 2-layer", f"{fmt_fcfa(ps.etanch_sbs_m2)}/m2"),
            ("PVC membrane", f"{fmt_fcfa(ps.etanch_pvc_m2)}/m2"),
            ("Liquide (SDB)" if lang == 'fr' else "Liquid (bathroom)", f"{fmt_fcfa(ps.etanch_liquide_m2)}/m2"),
            ("Methode SBS" if lang == 'fr' else "SBS method", "Soudee au chalumeau"),
            ("Protection SBS", "Autoprotegee minerale"),
            ("Pente min toiture" if lang == 'fr' else "Min roof slope", "1-3%"),
            ("Releve min" if lang == 'fr' else "Min upstand", "15 cm"),
            ("Garantie" if lang == 'fr' else "Warranty", "10 ans (decennale)"),
        ],
        ville=ville_cap, mat_prix=mat_et, mat_unit="m2",
        pose_prix=pose_et,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% labour",
        meo_items=[
            "Support sec, propre, avec forme de pente (1-3%)" if lang == 'fr' else "Dry, clean substrate with slope screed (1-3%)",
            "Primaire d'accrochage (EIF) avant soudage SBS" if lang == 'fr' else "Primer coat (EIF) before SBS welding",
            "Soudage SBS au chalumeau: recouvrements 10 cm" if lang == 'fr' else "SBS torch welding: 10 cm overlaps",
            "Test d'etancheite par mise en eau 48h" if lang == 'fr' else "Waterproofing test by 48h ponding",
            "Proteger immediatement apres pose (UV, circulation)" if lang == 'fr' else "Protect immediately after installation (UV, traffic)",
            "Pas d'application sous la pluie ou sur support humide" if lang == 'fr' else "No application in rain or on wet substrate",
            "Equipe: 1 etancheur qualifie + 1 aide" if lang == 'fr' else "Crew: 1 qualified waterproofer + 1 helper",
            "Rendement: 30-50 m2/jour (SBS bicouche)" if lang == 'fr' else "Output: 30-50 m2/day (SBS 2-layer)",
        ],
        fournisseurs="Soprema, Siplast, IKO, fournisseurs locaux Dakar",
        normes="DTU 43.1/43.5, NF EN 13707, NF EN 13956, NF EN 14909",
        lang=lang,
    ))

    # ── STR-09 Controles qualite ─────────────────────────────
    # Use average test cost ~150,000 FCFA
    prix_ctrl = 150_000
    mat_ct, pose_ct = _prix_split(prix_ctrl, 0.70)

    story.extend(_build_fiche(
        code="STR-09",
        titre="Controles qualite" if lang == 'fr' else "Quality Control",
        norme_ref="NF EN 12350/12390 / NF P 94-078 / NF EN 12504",
        specs=[
            ("Eprouvettes beton 28j" if lang == 'fr' else "Concrete cubes 28d", "1 serie / 50 m3"),
            ("Carottage in situ" if lang == 'fr' else "In-situ coring", "En cas de doute" if lang == 'fr' else "When in doubt"),
            ("Traction acier" if lang == 'fr' else "Steel tensile", "1 essai / 20 t"),
            ("Pliage acier" if lang == 'fr' else "Steel bend", "1 essai / 20 t"),
            ("Pachometre (enrobage)" if lang == 'fr' else "Cover meter", "Chaque niveau" if lang == 'fr' else "Each level"),
            ("Compactage sol" if lang == 'fr' else "Soil compaction", "1 / 500 m2"),
            ("Integrite pieux" if lang == 'fr' else "Pile integrity", "Sonique 100%"),
            ("Chargement pieu" if lang == 'fr' else "Pile load test", "1 / zone geo"),
            ("Carbonatation", "Apres 28j, zones exposees" if lang == 'fr' else "After 28d, exposed areas"),
            ("Labo agree" if lang == 'fr' else "Approved lab", "LNBTP, Geocotra"),
        ],
        ville=ville_cap, mat_prix=mat_ct, mat_unit="essai",
        pose_prix=pose_ct,
        ratio_label_fr="70% labo / 30% prelevement",
        ratio_label_en="70% lab / 30% sampling",
        meo_items=[
            "Programmer les essais en amont du planning coulage" if lang == 'fr' else "Schedule tests ahead of pour programme",
            "Eprouvettes conservees en conditions normalisees (20 C, eau)" if lang == 'fr' else "Test cubes stored in standard conditions (20 C, water)",
            "PV d'essai archiver avec le dossier chantier" if lang == 'fr' else "Test reports filed with site documentation",
            "Non-conformite: contre-essais + expertise structurelle" if lang == 'fr' else "Non-conformity: re-testing + structural assessment",
            "Bureau de controle: visite bi-mensuelle minimum" if lang == 'fr' else "Control office: bi-monthly visit minimum",
            "Responsable qualite present a chaque coulage" if lang == 'fr' else "QA manager present at every pour",
        ],
        fournisseurs="LNBTP Dakar, Geocotra, SOCOTEC Senegal, APAVE Senegal, Bureau Veritas SN",
        normes="NF EN 12350, NF EN 12390, NF P 94-078, NF EN 12504, NF EN 1997-1",
        lang=lang,
    ))

    # ══════════════════════════════════════════════════════════
    # SECTION 2: MEP FICHES
    # ══════════════════════════════════════════════════════════
    story.extend(section_title("B", "MEP" if lang == 'fr' else "MEP"))
    story.append(PageBreak())

    # ── MEP-E01 Transformateur HTA/BT ───────────────────────
    # Select transformer based on building size
    if nb_niveaux <= 4:
        transfo_prix = pm.transfo_160kva
        transfo_label = "160 kVA"
    elif nb_niveaux <= 8:
        transfo_prix = pm.transfo_250kva
        transfo_label = "250 kVA"
    else:
        transfo_prix = pm.transfo_400kva
        transfo_label = "400 kVA"
    mat_tr, pose_tr = _prix_split(transfo_prix, 0.80)

    story.extend(_build_fiche(
        code="MEP-E01",
        titre="Transformateur HTA/BT" if lang == 'fr' else "HV/LV Transformer",
        norme_ref="NF EN 60076 / IEC 60076",
        specs=[
            ("Puissance" if lang == 'fr' else "Power", transfo_label),
            ("Tension primaire" if lang == 'fr' else "Primary voltage", "30 kV / 20 kV"),
            ("Tension secondaire" if lang == 'fr' else "Secondary voltage", "400/230 V"),
            ("Couplage", "Dyn 11"),
            ("Isolation", "Huile minerale" if lang == 'fr' else "Mineral oil"),
            ("Refroidissement", "ONAN"),
            ("Pertes a vide" if lang == 'fr' else "No-load losses", "< 1% Pn"),
            ("Pertes en charge" if lang == 'fr' else "Load losses", "< 4% Pn"),
            ("Dimensions (L x l x H)", "1200 x 800 x 1500 mm"),
            ("Poids", "800-1200 kg"),
        ],
        ville=ville_cap, mat_prix=mat_tr, mat_unit="u",
        pose_prix=pose_tr,
        ratio_label_fr="80% equip. / 20% pose",
        ratio_label_en="80% equip. / 20% install",
        meo_items=[
            "Local transformateur ventile conforme NF C 13-200" if lang == 'fr' else "Ventilated transformer room per NF C 13-200",
            "Dalle beton avec bac de retention huile" if lang == 'fr' else "Concrete slab with oil retention tank",
            "Raccordement HTA par entreprise agreee SENELEC" if lang == 'fr' else "HV connection by SENELEC-approved contractor",
            "Mise a la terre < 10 ohms (boucle de fond de fouille)" if lang == 'fr' else "Earthing < 10 ohms (foundation loop)",
            "Essai dielectrique avant mise en service" if lang == 'fr' else "Dielectric test before commissioning",
            "Equipe: 1 ingenieur + 2 electriciens HTA + grue" if lang == 'fr' else "Crew: 1 engineer + 2 HV electricians + crane",
            "Duree installation: 3-5 jours" if lang == 'fr' else "Install duration: 3-5 days",
        ],
        fournisseurs="Schneider Electric, ABB, Siemens, CAHORS, SONETEL Dakar",
        normes="NF EN 60076, NF C 13-100, NF C 13-200, IEC 60076",
        lang=lang,
    ))

    # ── MEP-E02 Groupe electrogene ──────────────────────────
    if nb_niveaux <= 4:
        ge_prix = pm.groupe_electrogene_100kva
        ge_label = "100 kVA"
    elif nb_niveaux <= 8:
        ge_prix = pm.groupe_electrogene_200kva
        ge_label = "200 kVA"
    else:
        ge_prix = pm.groupe_electrogene_400kva
        ge_label = "400 kVA"
    mat_ge, pose_ge = _prix_split(ge_prix, 0.80)

    story.extend(_build_fiche(
        code="MEP-E02",
        titre="Groupe electrogene" if lang == 'fr' else "Generator Set",
        norme_ref="NF EN ISO 8528 / NF C 15-100",
        specs=[
            ("Puissance" if lang == 'fr' else "Power", ge_label),
            ("Moteur" if lang == 'fr' else "Engine", "Diesel 4 temps turbo"),
            ("Alternateur", "Triphasé 400V / 50Hz" if lang == 'fr' else "Three-phase 400V / 50Hz"),
            ("Demarrage" if lang == 'fr' else "Start-up", "Automatique (ATS)"),
            ("Transfert", "< 10 secondes"),
            ("Cuve" if lang == 'fr' else "Fuel tank", "500 L interne"),
            ("Autonomie", "8-12 h a 75% charge"),
            ("Niveau sonore" if lang == 'fr' else "Noise level", "75 dB(A) a 7 m (capoté)"),
            ("Consommation", "18-30 L/h selon charge"),
            ("Dimensions", "2500 x 1100 x 1600 mm"),
        ],
        ville=ville_cap, mat_prix=mat_ge, mat_unit="u",
        pose_prix=pose_ge,
        ratio_label_fr="80% equip. / 20% pose",
        ratio_label_en="80% equip. / 20% install",
        meo_items=[
            "Local GE ventile avec extraction forcee" if lang == 'fr' else "Ventilated genset room with forced extraction",
            "Plot anti-vibratile sous le groupe" if lang == 'fr' else "Anti-vibration mounts under the genset",
            "Silencieux d'echappement + sortie en toiture" if lang == 'fr' else "Exhaust silencer + roof outlet",
            "Bac de retention carburant conforme" if lang == 'fr' else "Compliant fuel retention tank",
            "Test de permutation ATS hebdomadaire" if lang == 'fr' else "Weekly ATS switchover test",
            "Entretien preventif toutes les 250 h" if lang == 'fr' else "Preventive maintenance every 250 h",
            "Equipe: 1 ingenieur + 2 electriciens + manutention lourde" if lang == 'fr' else "Crew: 1 engineer + 2 electricians + heavy handling",
            "Duree installation: 3-5 jours" if lang == 'fr' else "Install duration: 3-5 days",
        ],
        fournisseurs="SDMO/Kohler, Caterpillar, Cummins, FG Wilson, SONETEL",
        normes="NF EN ISO 8528, NF C 15-100, NF S 31-010 (bruit)",
        lang=lang,
    ))

    # ── MEP-E03 TGBT ─────────────────────────────────────────
    mat_tg, pose_tg = _prix_split(pm.tableau_general_bt, 0.70)

    story.extend(_build_fiche(
        code="MEP-E03",
        titre="TGBT (Tableau General Basse Tension)" if lang == 'fr' else "MSSB (Main Sub-Station Board)",
        norme_ref="NF C 15-100 / NF EN 61439",
        specs=[
            ("Courant nominal In" if lang == 'fr' else "Rated current In", "400-1600 A"),
            ("Icc presume" if lang == 'fr' else "Prospective Icc", "25-50 kA"),
            ("Nombre de departs" if lang == 'fr' else "Number of outgoers", "12-32 modules"),
            ("Inverseur de source" if lang == 'fr' else "Transfer switch", "ATS motorise"),
            ("Indice de protection" if lang == 'fr' else "Protection rating", "IP 31 (local technique)"),
            ("Forme de separation" if lang == 'fr' else "Form of separation", "Forme 2b ou 3b"),
            ("Protection differentielle" if lang == 'fr' else "RCD protection", "30 mA (prises), 300 mA (puissance)"),
            ("Comptage", "TC/TT depart general" if lang == 'fr' else "CT/VT main incomer"),
        ],
        ville=ville_cap, mat_prix=mat_tg, mat_unit="u",
        pose_prix=pose_tg,
        ratio_label_fr="70% equip. / 30% pose",
        ratio_label_en="70% equip. / 30% install",
        meo_items=[
            "Installation dans local electrique ventile, acces restreint" if lang == 'fr' else "Install in ventilated electrical room, restricted access",
            "Fixation murale ou sur chassis autoportant" if lang == 'fr' else "Wall-mounted or free-standing frame",
            "Raccordement par barres cuivre ou cables souples" if lang == 'fr' else "Connection via copper busbars or flexible cables",
            "Serrage au couple des connexions (verification)" if lang == 'fr' else "Torque-check all connections",
            "Test de declenchement de tous les disjoncteurs" if lang == 'fr' else "Trip test all circuit breakers",
            "Mesure d'isolement 500 V avant mise sous tension" if lang == 'fr' else "Insulation test at 500 V before energizing",
            "Equipe: 1 ingenieur + 2 tableautiers + 1 aide" if lang == 'fr' else "Crew: 1 engineer + 2 panel builders + 1 helper",
            "Duree: 5-10 jours (fabrication + installation)" if lang == 'fr' else "Duration: 5-10 days (fabrication + installation)",
        ],
        fournisseurs="Schneider Electric, Legrand, Hager, ABB, SONETEL Dakar",
        normes="NF C 15-100, NF EN 61439-1/2, NF C 14-100",
        lang=lang,
    ))

    # ── MEP-E04 Cablage electrique ──────────────────────────
    mat_ca, pose_ca = _prix_split(pm.canalisation_cuivre_ml, 0.55)

    story.extend(_build_fiche(
        code="MEP-E04",
        titre="Cablage electrique" if lang == 'fr' else "Electrical Cabling",
        norme_ref="NF C 15-100 / NF C 32-321 (U1000R2V)",
        specs=[
            ("1.5 mm2", "Eclairage / prises commandees"),
            ("2.5 mm2", "Prises de courant 16A"),
            ("6 mm2", "Plaques de cuisson / chauffe-eau"),
            ("10-16 mm2", "Climatiseurs / sous-tableaux"),
            ("25-35 mm2", "Colonnes montantes"),
            ("70-240 mm2", "Distribution principale"),
            ("Type cable" if lang == 'fr' else "Cable type", "U1000R2V (rigide), H07RN-F (souple)"),
            ("Cheminement" if lang == 'fr' else "Routing", "Goulottes, chemins de cables, encastre"),
            ("Code couleur" if lang == 'fr' else "Color code", "Ph: R/N/Br, N: Bleu, PE: V/J"),
            ("Chute de tension max" if lang == 'fr' else "Max voltage drop", "3% eclairage, 5% force"),
        ],
        ville=ville_cap, mat_prix=mat_ca, mat_unit="ml",
        pose_prix=pose_ca,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Tirage cables apres pose chemins de cables / goulottes" if lang == 'fr' else "Pull cables after tray/trunking installation",
            "Pas de cables sous chape sans fourreau" if lang == 'fr' else "No cables in screed without conduit",
            "Respecter rayons de courbure: >= 8 x diametre cable" if lang == 'fr' else "Respect bend radii: >= 8 x cable diameter",
            "Reperage des circuits a chaque extremite" if lang == 'fr' else "Label circuits at each end",
            "Tests d'isolement et de continuite avant mise sous tension" if lang == 'fr' else "Insulation and continuity tests before energizing",
            "Separation courants forts / courants faibles (30 cm min)" if lang == 'fr' else "Separate power/data cables (30 cm min)",
            "Equipe: 1 electricien + 1 aide par 50-80 ml/jour" if lang == 'fr' else "Crew: 1 electrician + 1 helper per 50-80 ml/day",
            "Reception: mesure chute de tension + test differentiel" if lang == 'fr' else "Acceptance: voltage drop measurement + RCD test",
        ],
        fournisseurs="Nexans, Prysmian, Top Cable, General Cable, SONETEL",
        normes="NF C 15-100, NF C 32-321, NF EN 60228, IEC 60502",
        lang=lang,
    ))

    # ── MEP-E05 Luminaires LED ──────────────────────────────
    mat_lu, pose_lu = _prix_split(pm.luminaire_led_standard, 0.75)

    story.extend(_build_fiche(
        code="MEP-E05",
        titre="Luminaires LED" if lang == 'fr' else "LED Luminaires",
        norme_ref="NF EN 60598 / NF EN 12464-1",
        specs=[
            ("Standard" if lang == 'fr' else "Standard", f"{fmt_fcfa(pm.luminaire_led_standard)}/u"),
            ("Premium", f"{fmt_fcfa(pm.luminaire_led_premium)}/u"),
            ("Detecteur presence" if lang == 'fr' else "Occupancy sensor", f"{fmt_fcfa(pm.eclairage_detecteur_presence)}/u"),
            ("Puissance" if lang == 'fr' else "Power", "12-36 W"),
            ("Flux lumineux" if lang == 'fr' else "Luminous flux", "1000-4000 lm"),
            ("IRC", ">= 80 (bureaux >= 90)"),
            ("Temperature couleur" if lang == 'fr' else "Color temp.", "4000K (bureaux), 3000K (residentiel)"),
            ("Duree de vie" if lang == 'fr' else "Lifespan", "50 000 h (L80B10)"),
            ("Type" if lang == 'fr' else "Type", "Encastre, saillie, spot, reglette"),
            ("Eclairage min bureau" if lang == 'fr' else "Min office lighting", "500 lux (NF EN 12464-1)"),
        ],
        ville=ville_cap, mat_prix=mat_lu, mat_unit="u",
        pose_prix=pose_lu,
        ratio_label_fr="75% equip. / 25% pose",
        ratio_label_en="75% equip. / 25% install",
        meo_items=[
            "Implantation selon calcul d'eclairage (Dialux/Relux)" if lang == 'fr' else "Layout per lighting calculation (Dialux/Relux)",
            "Alimentation en attente avant pose faux-plafond" if lang == 'fr' else "Power feeds ready before ceiling installation",
            "Fixation adaptee au type de plafond (clips, ressorts)" if lang == 'fr' else "Fixing suitable for ceiling type (clips, springs)",
            "Detecteur de presence: zones de circulation communes" if lang == 'fr' else "Occupancy sensors: common circulation areas",
            "Pas de luminaire au-dessus des baignoires (zone 1)" if lang == 'fr' else "No luminaire above bathtubs (zone 1)",
            "Equipe: 1 electricien / 15-20 luminaires/jour" if lang == 'fr' else "Crew: 1 electrician / 15-20 luminaires/day",
        ],
        fournisseurs="Philips/Signify, OSRAM/Ledvance, Legrand, Schneider, Sylvania",
        normes="NF EN 60598, NF EN 12464-1, NF C 15-100, NF EN 62471 (securite photo.)",
        lang=lang,
    ))

    # ── MEP-E06 Appareillage ────────────────────────────────
    # Approximate price for outlets/switches
    prix_appareillage = pm.compteur_monophase * 0.15  # ~22,500
    mat_ap, pose_ap = _prix_split(int(prix_appareillage), 0.65)

    story.extend(_build_fiche(
        code="MEP-E06",
        titre="Appareillage (prises / interrupteurs)" if lang == 'fr' else "Wiring Accessories (outlets / switches)",
        norme_ref="NF C 15-100 / NF EN 60669 / NF EN 60884",
        specs=[
            ("Prise 2P+T 16A" if lang == 'fr' else "Socket 2P+E 16A", "Standard, encastree"),
            ("Prise 2P+T etanche" if lang == 'fr' else "Socket 2P+E waterproof", "IP 44 (SDB, exterieur)"),
            ("Interrupteur SA" if lang == 'fr' else "Switch 1-way", "10A, encastre"),
            ("Interrupteur VA" if lang == 'fr' else "Switch 2-way", "10A, encastre"),
            ("Bouton-poussoir" if lang == 'fr' else "Push button", "Pour minuterie/telerupteur"),
            ("Gamme" if lang == 'fr' else "Range", "Legrand Mosaic / Schneider Odace"),
            ("IP" if lang == 'fr' else "IP rating", "IP 20 courant, IP 44 humid/ext."),
            ("Hauteur prises" if lang == 'fr' else "Outlet height", "30 cm (courant), 110 cm (cuisine)"),
            ("Nbre min/piece" if lang == 'fr' else "Min per room", "5 prises (NF C 15-100 §10.1)"),
        ],
        ville=ville_cap, mat_prix=mat_ap, mat_unit="u",
        pose_prix=pose_ap,
        ratio_label_fr="65% equip. / 35% pose",
        ratio_label_en="65% equip. / 35% install",
        meo_items=[
            "Pose apres enduits, avant peinture" if lang == 'fr' else "Install after renders, before painting",
            "Encastrement dans boites d'encastrement d67 mm" if lang == 'fr' else "Flush mounting in d67 mm back boxes",
            "Raccordement par bornes automatiques (Wago)" if lang == 'fr' else "Connect via push-in terminals (Wago)",
            "Respecter distances SDB: zone 0/1/2/3 (NF C 15-100)" if lang == 'fr' else "Respect bathroom zones: 0/1/2/3 (NF C 15-100)",
            "Test de continuite PE et isolement avant mise en service" if lang == 'fr' else "PE continuity and insulation test before commissioning",
            "Equipe: 1 electricien / 20-30 points/jour" if lang == 'fr' else "Crew: 1 electrician / 20-30 points/day",
        ],
        fournisseurs="Legrand, Schneider Electric, Hager, ABB, Bticino",
        normes="NF C 15-100, NF EN 60669, NF EN 60884, IEC 60884",
        lang=lang,
    ))

    # ── MEP-P01 Tuyauterie PVC ──────────────────────────────
    mat_pvc, pose_pvc = _prix_split(pm.tuyau_pvc_dn100_ml, 0.55)

    story.extend(_build_fiche(
        code="MEP-P01",
        titre="Tuyauterie PVC" if lang == 'fr' else "PVC Piping",
        norme_ref="NF EN 1401 / NF EN 1329 / DTU 60.33",
        specs=[
            ("DN 50", f"{fmt_fcfa(pm.tuyau_pvc_dn50_ml)}/ml"),
            ("DN 100", f"{fmt_fcfa(pm.tuyau_pvc_dn100_ml)}/ml"),
            ("DN 150", f"{fmt_fcfa(pm.tuyau_pvc_dn150_ml)}/ml"),
            ("Colonne montante" if lang == 'fr' else "Riser", f"{fmt_fcfa(pm.colonne_montante_ml)}/ml"),
            ("Pression nominale" if lang == 'fr' else "Nominal pressure", "PN 6 (evacuation), PN 10 (pression)"),
            ("Type raccords" if lang == 'fr' else "Fitting type", "Collage (EU) / Joint a levre (EP)"),
            ("Pente EU" if lang == 'fr' else "Waste slope", "1-3 cm/m"),
            ("Pente EP" if lang == 'fr' else "Rainwater slope", "0.5-1 cm/m"),
            ("Ventilation primaire" if lang == 'fr' else "Primary vent", "DN 100 en toiture"),
            ("Fixation" if lang == 'fr' else "Support", "Colliers tous les 1.50 m"),
        ],
        ville=ville_cap, mat_prix=mat_pvc, mat_unit="ml",
        pose_prix=pose_pvc,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Couper proprement avec scie a metaux + ebavurer" if lang == 'fr' else "Clean cut with hacksaw + deburr",
            "Degraissage + colle PVC (sechage 5 min avant assemblage)" if lang == 'fr' else "Degrease + PVC cement (5 min drying before assembly)",
            "Pente constante, pas de contre-pente (verifier au niveau)" if lang == 'fr' else "Constant slope, no sags (check with level)",
            "Fourreau au passage des dalles + joint coupe-feu" if lang == 'fr' else "Sleeve at slab penetrations + fire seal",
            "Test d'etancheite a l'eau (EU: bouchon + remplissage)" if lang == 'fr' else "Water tightness test (waste: plug + fill)",
            "Equipe: 1 plombier + 1 aide / 30-50 ml/jour" if lang == 'fr' else "Crew: 1 plumber + 1 helper / 30-50 ml/day",
        ],
        fournisseurs="Aliaxis (Nicoll), Wavin, Plastique du Senegal, First Plast",
        normes="NF EN 1401, NF EN 1329, DTU 60.33, DTU 60.11",
        lang=lang,
    ))

    # ── MEP-P02 Equipements sanitaires ──────────────────────
    mat_wc, pose_wc = _prix_split(pm.wc_double_chasse, 0.70)

    story.extend(_build_fiche(
        code="MEP-P02",
        titre="Equipements sanitaires" if lang == 'fr' else "Sanitary Equipment",
        norme_ref="NF EN 997 (WC) / NF EN 14688 (lavabos) / DTU 60.1",
        specs=[
            ("WC standard", f"{fmt_fcfa(pm.wc_standard)}/u"),
            ("WC double chasse 3/6L" if lang == 'fr' else "Dual flush WC 3/6L", f"{fmt_fcfa(pm.wc_double_chasse)}/u"),
            ("Robinet standard" if lang == 'fr' else "Standard faucet", f"{fmt_fcfa(pm.robinet_standard)}/u"),
            ("Robinet eco 6 L/min" if lang == 'fr' else "Eco faucet 6 L/min", f"{fmt_fcfa(pm.robinet_eco)}/u"),
            ("Materiau WC" if lang == 'fr' else "WC material", "Ceramique vitrifiee"),
            ("Fixation WC" if lang == 'fr' else "WC fixing", "Au sol (standard) / Suspendu"),
            ("Siphon lavabo" if lang == 'fr' else "Basin trap", "d32 mm, demontable"),
            ("Bonde douche" if lang == 'fr' else "Shower drain", "d60-90 mm siphoide"),
            ("Debit robinet" if lang == 'fr' else "Faucet flow", "6-9 L/min (eco)"),
            ("Garantie" if lang == 'fr' else "Warranty", "2-5 ans fabricant"),
        ],
        ville=ville_cap, mat_prix=mat_wc, mat_unit="u",
        pose_prix=pose_wc,
        ratio_label_fr="70% equip. / 30% pose",
        ratio_label_en="70% equip. / 30% install",
        meo_items=[
            "Pose apres carrelage sol + murs (sauf WC suspendu: bati support avant)" if lang == 'fr' else "Install after floor + wall tiling (except wall-hung: frame before)",
            "Etancheite silicone sanitaire autour des appareils" if lang == 'fr' else "Sanitary silicone seal around fixtures",
            "Raccordement eau: flexible inox 60 cm (pas de cuivre rigide)" if lang == 'fr' else "Water connection: SS flex hose 60 cm (no rigid copper)",
            "Test d'ecoulement et verification siphon" if lang == 'fr' else "Flow test and trap verification",
            "Equipe: 1 plombier / 3-5 appareils/jour" if lang == 'fr' else "Crew: 1 plumber / 3-5 fixtures/day",
        ],
        fournisseurs="Grohe, Roca, Jacob Delafon, Porcher, importateurs locaux",
        normes="NF EN 997, NF EN 14688, NF EN 200, DTU 60.1",
        lang=lang,
    ))

    # ── MEP-P03 Cuves et pompes ─────────────────────────────
    mat_cv, pose_cv = _prix_split(pm.cuve_eau_10000l, 0.75)

    story.extend(_build_fiche(
        code="MEP-P03",
        titre="Cuves et pompes" if lang == 'fr' else "Tanks and Pumps",
        norme_ref="NF EN 13341 (cuves) / NF EN ISO 9906 (pompes)",
        specs=[
            ("Cuve 5 000 L", f"{fmt_fcfa(pm.cuve_eau_5000l)}"),
            ("Cuve 10 000 L", f"{fmt_fcfa(pm.cuve_eau_10000l)}"),
            ("Pompe 1 kW", f"{fmt_fcfa(pm.pompe_surpresseur_1kw)}"),
            ("Pompe 3 kW", f"{fmt_fcfa(pm.pompe_surpresseur_3kw)}"),
            ("Materiau cuve" if lang == 'fr' else "Tank material", "Polyethylene HD alimentaire"),
            ("Pression pompe" if lang == 'fr' else "Pump pressure", "2-6 bar"),
            ("Debit pompe" if lang == 'fr' else "Pump flow", "3-15 m3/h"),
            ("Ballon tampon" if lang == 'fr' else "Pressure vessel", "100-500 L"),
            ("Protection anti-coup de belier" if lang == 'fr' else "Anti-hammer protection", "Obligatoire"),
            ("Reserve incendie" if lang == 'fr' else "Fire reserve", "Volume selon IT 246"),
        ],
        ville=ville_cap, mat_prix=mat_cv, mat_unit="u",
        pose_prix=pose_cv,
        ratio_label_fr="75% equip. / 25% pose",
        ratio_label_en="75% equip. / 25% install",
        meo_items=[
            "Cuve sur dalle beton dosee a 350 kg/m3 min" if lang == 'fr' else "Tank on concrete slab min 350 kg/m3",
            "Canalisation d'alimentation et trop-plein vers reseau EP" if lang == 'fr' else "Feed pipe and overflow to rainwater network",
            "Pompe sur plots anti-vibratiles + manchons souples" if lang == 'fr' else "Pump on anti-vibration mounts + flexible connectors",
            "Pressostat de commande + manometre" if lang == 'fr' else "Pressure switch + pressure gauge",
            "Cuve potable: attestation de conformite alimentaire" if lang == 'fr' else "Potable tank: food-grade compliance certificate",
            "Desinfection avant mise en service (chlore 50 ppm, 24h)" if lang == 'fr' else "Disinfection before commissioning (chlorine 50 ppm, 24h)",
            "Equipe: 1 plombier + 1 electricien + manutention" if lang == 'fr' else "Crew: 1 plumber + 1 electrician + handling",
            "Duree: 2-3 jours" if lang == 'fr' else "Duration: 2-3 days",
        ],
        fournisseurs="Grundfos, KSB, Wilo, Simop, cuves PE locales",
        normes="NF EN 13341, NF EN ISO 9906, ACS (contact alimentaire)",
        lang=lang,
    ))

    # ── MEP-P04 Chauffe-eau solaire ─────────────────────────
    mat_ces, pose_ces = _prix_split(pm.chauffe_eau_solaire_200l, 0.70)

    story.extend(_build_fiche(
        code="MEP-P04",
        titre="Chauffe-eau solaire (CESI)" if lang == 'fr' else "Solar Water Heater (SWH)",
        norme_ref="NF EN 12976 (CESI) / NF EN 12975 (capteurs)",
        specs=[
            ("Volume ballon" if lang == 'fr' else "Tank volume", "200 L (standard logement)"),
            ("Capteurs" if lang == 'fr' else "Collectors", "2 x 2 m2 plans vitres"),
            ("Rendement optique" if lang == 'fr' else "Optical efficiency", ">= 75%"),
            ("Taux couverture solaire" if lang == 'fr' else "Solar fraction", "70-90% (Dakar)"),
            ("Appoint" if lang == 'fr' else "Backup", "Electrique 2 kW"),
            ("Type" if lang == 'fr' else "Type", "Thermosiphon (economique)"),
            ("Orientation" if lang == 'fr' else "Orientation", "Sud, inclinaison 14-15 (lat. Dakar)"),
            ("Temp. eau sortie" if lang == 'fr' else "Outlet temp.", "55-65 C"),
            ("Antigel" if lang == 'fr' else "Antifreeze", "Non necessaire a Dakar"),
            ("Chauffe-eau elec. 100L" if lang == 'fr' else "Elec. heater 100L", f"{fmt_fcfa(pm.chauffe_eau_electrique_100l)}"),
        ],
        ville=ville_cap, mat_prix=mat_ces, mat_unit="u",
        pose_prix=pose_ces,
        ratio_label_fr="70% equip. / 30% pose",
        ratio_label_en="70% equip. / 30% install",
        meo_items=[
            "Toiture plate: support incline a 14-15 degres plein sud" if lang == 'fr' else "Flat roof: tilted frame at 14-15 degrees facing south",
            "Fixation anti-vent (boulons + lest beton si necessaire)" if lang == 'fr' else "Wind-resistant fixing (bolts + concrete ballast if needed)",
            "Raccordement cuivre isolé (calorifuge epaisseur >= 19 mm)" if lang == 'fr' else "Insulated copper connection (cladding >= 19 mm)",
            "Mitigeur thermostatique en sortie (anti-brulure 50 C)" if lang == 'fr' else "Thermostatic mixing valve at outlet (anti-scald 50 C)",
            "Essai de pression 6 bar pendant 30 min" if lang == 'fr' else "Pressure test 6 bar for 30 min",
            "Equipe: 1 plombier + 1 aide / 1 CESI par jour" if lang == 'fr' else "Crew: 1 plumber + 1 helper / 1 SWH per day",
        ],
        fournisseurs="Bosch, Atlantic, Viessmann, Heliopac, fournisseurs solaires locaux",
        normes="NF EN 12976, NF EN 12975, Solar Keymark, EDGE v3",
        lang=lang,
    ))

    # ── MEP-C01 Splits / climatiseurs ───────────────────────
    mat_sp, pose_sp = _prix_split(pm.split_2cv, 0.75)

    story.extend(_build_fiche(
        code="MEP-C01",
        titre="Splits / climatiseurs" if lang == 'fr' else "Split AC Units",
        norme_ref="NF EN 14511 / NF EN 16583",
        specs=[
            ("Split 1 CV (9000 BTU)", f"{fmt_fcfa(pm.split_1cv)}/u"),
            ("Split 2 CV (18000 BTU)", f"{fmt_fcfa(pm.split_2cv)}/u"),
            ("Cassette 4 CV", f"{fmt_fcfa(pm.split_cassette_4cv)}/u"),
            ("COP froid" if lang == 'fr' else "Cooling COP", ">= 3.5 (classe A)"),
            ("EER", ">= 3.0"),
            ("Refrigerant" if lang == 'fr' else "Refrigerant", "R32 (faible GWP)"),
            ("Niveau sonore int." if lang == 'fr' else "Indoor noise", "22-40 dB(A)"),
            ("Niveau sonore ext." if lang == 'fr' else "Outdoor noise", "48-56 dB(A)"),
            ("Filtration", "Filtre lavable + anti-bacterien"),
            ("Telecommande" if lang == 'fr' else "Remote", "IR + WiFi (option)"),
        ],
        ville=ville_cap, mat_prix=mat_sp, mat_unit="u",
        pose_prix=pose_sp,
        ratio_label_fr="75% equip. / 25% pose",
        ratio_label_en="75% equip. / 25% install",
        meo_items=[
            "Unite interieure a >= 2.20 m du sol, loin des sources de chaleur" if lang == 'fr' else "Indoor unit >= 2.20 m from floor, away from heat sources",
            "Unite exterieure: ventilation libre, pas de recirculation" if lang == 'fr' else "Outdoor unit: free ventilation, no recirculation",
            "Liaison frigorifique cuivre 1/4 + 3/8 pouces, calorifuge" if lang == 'fr' else "Copper refrigerant line 1/4 + 3/8 inch, insulated",
            "Evacuation condensats en PVC d16-20 mm avec pente" if lang == 'fr' else "Condensate drain PVC d16-20 mm with slope",
            "Tirage au vide 30 min avant ouverture vannes" if lang == 'fr' else "Vacuum 30 min before opening valves",
            "Alimentation electrique dediee avec disjoncteur 16-20A" if lang == 'fr' else "Dedicated power supply with 16-20A breaker",
            "Equipe: 1 frigoriste / 2-3 splits/jour" if lang == 'fr' else "Crew: 1 HVAC tech / 2-3 splits/day",
            "Reception: mesure temperatures soufflage / delta T >= 8 C" if lang == 'fr' else "Acceptance: measure supply temp / delta T >= 8 C",
        ],
        fournisseurs="Daikin, Mitsubishi, LG, Samsung, Carrier, Midea",
        normes="NF EN 14511, NF EN 16583, F-Gas Reg., EDGE v3 (R32)",
        lang=lang,
    ))

    # ── MEP-C02 VMC ──────────────────────────────────────────
    mat_vmc, pose_vmc = _prix_split(pm.vmc_simple_flux, 0.65)

    story.extend(_build_fiche(
        code="MEP-C02",
        titre="VMC (Ventilation Mecanique Controlee)" if lang == 'fr' else "CMV (Controlled Mechanical Ventilation)",
        norme_ref="DTU 68.3 / Arrete du 24 mars 1982",
        specs=[
            ("VMC simple flux", f"{fmt_fcfa(pm.vmc_simple_flux)}/logement"),
            ("VMC double flux", f"{fmt_fcfa(pm.vmc_double_flux)}/logement"),
            ("Debit cuisine" if lang == 'fr' else "Kitchen flow", "45-135 m3/h (hygro B)"),
            ("Debit SDB" if lang == 'fr' else "Bathroom flow", "15-30 m3/h"),
            ("Debit WC" if lang == 'fr' else "Toilet flow", "15 m3/h"),
            ("Rendement DF" if lang == 'fr' else "HR efficiency", ">= 85% (double flux)"),
            ("Capteurs hygro" if lang == 'fr' else "Hygro sensors", "Bouches hygroreglables"),
            ("Raccordement GTB" if lang == 'fr' else "BMS connection", "Contact sec / Modbus"),
            ("Niveau sonore" if lang == 'fr' else "Noise level", "< 30 dB(A) en cuisine"),
        ],
        ville=ville_cap, mat_prix=mat_vmc, mat_unit="logement",
        pose_prix=pose_vmc,
        ratio_label_fr="65% equip. / 35% pose",
        ratio_label_en="65% equip. / 35% install",
        meo_items=[
            "Caisson VMC en combles / local technique ventile" if lang == 'fr' else "VMC unit in attic / ventilated plant room",
            "Gaines rigides ou semi-rigides (pas de gaines souples > 2 m)" if lang == 'fr' else "Rigid or semi-rigid ducts (no flex ducts > 2 m)",
            "Bouches d'extraction en cuisine, SDB, WC" if lang == 'fr' else "Extract grilles in kitchen, bathroom, toilet",
            "Entrees d'air dans les pieces de vie (coffres de volet)" if lang == 'fr' else "Air inlets in living rooms (roller shutter boxes)",
            "Rejet air vicie en toiture (pas en facade)" if lang == 'fr' else "Exhaust stale air on roof (not facade)",
            "Equipe: 1 plombier/CVC + 1 aide / 1 logement par jour" if lang == 'fr' else "Crew: 1 HVAC tech + 1 helper / 1 dwelling per day",
        ],
        fournisseurs="Aldes, Atlantic, Unelvent, S&P (Soler & Palau)",
        normes="DTU 68.3, Arrete 24/03/1982, NF EN 13141, EDGE v3",
        lang=lang,
    ))

    # ── MEP-C03 Gaines de ventilation ───────────────────────
    prix_gaine = int(pm.vmc_simple_flux * 0.25)  # approximate per ml
    mat_ga, pose_ga = _prix_split(prix_gaine, 0.60)

    story.extend(_build_fiche(
        code="MEP-C03",
        titre="Gaines de ventilation" if lang == 'fr' else "Ventilation Ducts",
        norme_ref="DTU 68.3 / NF EN 12237 / NF EN 1507",
        specs=[
            ("Type circulaire" if lang == 'fr' else "Circular type", "Spirale acier galvanise"),
            ("Type rectangulaire" if lang == 'fr' else "Rectangular type", "Tole galva 0.6-1.0 mm"),
            ("Diametres courants" if lang == 'fr' else "Common diameters", "125, 160, 200, 250, 315 mm"),
            ("Vitesse max" if lang == 'fr' else "Max velocity", "5 m/s (gaines), 3 m/s (bouches)"),
            ("Etancheite" if lang == 'fr' else "Airtightness", "Classe B min (NF EN 15727)"),
            ("Isolation" if lang == 'fr' else "Insulation", "Laine min. 25 mm (si climatisee)"),
            ("Clapets coupe-feu" if lang == 'fr' else "Fire dampers", "A chaque passage de paroi CF"),
            ("Materiau" if lang == 'fr' else "Material", "Acier galva Z275 / Alu (cuisine)"),
        ],
        ville=ville_cap, mat_prix=mat_ga, mat_unit="ml",
        pose_prix=pose_ga,
        ratio_label_fr="60% mat. / 40% pose",
        ratio_label_en="60% mat. / 40% install",
        meo_items=[
            "Assemblage par raccords a joints caoutchouc ou mastic" if lang == 'fr' else "Assembly with rubber gasket fittings or mastic",
            "Supports et suspentes tous les 2 m" if lang == 'fr' else "Supports and hangers every 2 m",
            "Isolation apres test d'etancheite des gaines" if lang == 'fr' else "Insulate after duct airtightness test",
            "Clapets coupe-feu motorises avec fusible thermique" if lang == 'fr' else "Motorized fire dampers with thermal fuse",
            "Nettoyage interieur avant mise en service" if lang == 'fr' else "Interior cleaning before commissioning",
            "Equipe: 1 tuyauteur CVC + 1 aide / 20-30 ml/jour" if lang == 'fr' else "Crew: 1 HVAC pipefitter + 1 helper / 20-30 ml/day",
        ],
        fournisseurs="Atlantic, Aldes, Lindab, Dospel, fabricants locaux",
        normes="DTU 68.3, NF EN 12237, NF EN 1507, NF EN 15727",
        lang=lang,
    ))

    # ── MEP-CF01 Cablage RJ45 / fibre ──────────────────────
    mat_rj, pose_rj = _prix_split(pm.cablage_rj45_ml, 0.55)

    story.extend(_build_fiche(
        code="MEP-CF01",
        titre="Cablage RJ45 / fibre optique" if lang == 'fr' else "RJ45 / Fibre Optic Cabling",
        norme_ref="NF EN 50173 / ISO/IEC 11801",
        specs=[
            ("Cable RJ45 Cat.6", f"{fmt_fcfa(pm.cablage_rj45_ml)}/ml"),
            ("Prise RJ45" if lang == 'fr' else "RJ45 outlet", f"{fmt_fcfa(pm.prise_rj45)}/u"),
            ("Baie serveur 12U" if lang == 'fr' else "Server rack 12U", f"{fmt_fcfa(pm.baie_serveur_12u)}"),
            ("Categorie cable" if lang == 'fr' else "Cable category", "Cat.6 (250 MHz) / Cat.6a (500 MHz)"),
            ("Longueur max" if lang == 'fr' else "Max length", "90 m (permanent link)"),
            ("Fibre optique" if lang == 'fr' else "Fibre optic", "OS2 monomode (colonne montante)"),
            ("Connecteur fibre" if lang == 'fr' else "Fibre connector", "LC/APC duplex"),
            ("Blindage" if lang == 'fr' else "Shielding", "FTP ou U/FTP"),
            ("Switch PoE" if lang == 'fr' else "PoE switch", "24/48 ports gere"),
        ],
        ville=ville_cap, mat_prix=mat_rj, mat_unit="ml",
        pose_prix=pose_rj,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Chemins de cables separes des courants forts (30 cm min)" if lang == 'fr' else "Cable trays separate from power (30 cm min)",
            "Tirage cables sans tension excessive (max 110 N)" if lang == 'fr' else "Pull cables without excess tension (max 110 N)",
            "Raccordement en baie: panneau de brassage + jarretiere" if lang == 'fr' else "Rack termination: patch panel + patch cord",
            "Test Fluke (certification canal) sur 100% des liens" if lang == 'fr' else "Fluke test (channel certification) on 100% of links",
            "Etiquetage systematique des 2 extremites" if lang == 'fr' else "Systematic labelling at both ends",
            "Equipe: 1 technicien reseau + 1 aide / 15-25 prises/jour" if lang == 'fr' else "Crew: 1 network tech + 1 helper / 15-25 outlets/day",
        ],
        fournisseurs="Legrand/BTicino, Schneider, CommScope, Nexans, R&M",
        normes="NF EN 50173, ISO/IEC 11801, NF EN 50174, TIA 568",
        lang=lang,
    ))

    # ── MEP-CF02 Videosurveillance ──────────────────────────
    mat_cam, pose_cam = _prix_split(pm.camera_ip_exterieure, 0.70)

    story.extend(_build_fiche(
        code="MEP-CF02",
        titre="Videosurveillance" if lang == 'fr' else "Video Surveillance (CCTV)",
        norme_ref="NF EN 62676 / RGPD",
        specs=[
            ("Camera IP int." if lang == 'fr' else "Indoor IP cam", f"{fmt_fcfa(pm.camera_ip_interieure)}/u"),
            ("Camera IP ext." if lang == 'fr' else "Outdoor IP cam", f"{fmt_fcfa(pm.camera_ip_exterieure)}/u"),
            ("Resolution" if lang == 'fr' else "Resolution", "2-5 MP (1080p-4K)"),
            ("IR nuit" if lang == 'fr' else "Night IR", "30-50 m portee"),
            ("Stockage NVR" if lang == 'fr' else "NVR storage", "4-8 To (30 jours)"),
            ("Alimentation" if lang == 'fr' else "Power", "PoE (IEEE 802.3af/at)"),
            ("IP" if lang == 'fr' else "IP rating", "IP 66 (exterieur), IP 42 (interieur)"),
            ("Compression" if lang == 'fr' else "Compression", "H.265+ (Smart Codec)"),
            ("Angle de vue" if lang == 'fr' else "Field of view", "2.8 mm (110 deg) / 4 mm (90 deg)"),
        ],
        ville=ville_cap, mat_prix=mat_cam, mat_unit="u",
        pose_prix=pose_cam,
        ratio_label_fr="70% equip. / 30% pose",
        ratio_label_en="70% equip. / 30% install",
        meo_items=[
            "Cablage RJ45 Cat.6 dedie (alimentation PoE incluse)" if lang == 'fr' else "Dedicated Cat.6 RJ45 cabling (PoE power included)",
            "Fixation sur mats / consoles inox en exterieur" if lang == 'fr' else "Mounting on poles / SS brackets outdoors",
            "NVR dans local securise avec climatisation" if lang == 'fr' else "NVR in secured air-conditioned room",
            "Onduleur (UPS) sur NVR + switch PoE (autonomie 30 min)" if lang == 'fr' else "UPS on NVR + PoE switch (30 min autonomy)",
            "Parametrage detection de mouvement + zones" if lang == 'fr' else "Motion detection + zone configuration",
            "Declaration CNIL / conformite RGPD" if lang == 'fr' else "CNIL declaration / GDPR compliance",
            "Equipe: 1 technicien securite / 5-8 cameras/jour" if lang == 'fr' else "Crew: 1 security tech / 5-8 cameras/day",
        ],
        fournisseurs="Hikvision, Dahua, Axis, Bosch Security, Hanwha (Samsung)",
        normes="NF EN 62676, RGPD, CNIL recommandations, IEC 62676",
        lang=lang,
    ))

    # ── MEP-CF03 Controle d'acces ───────────────────────────
    mat_ac, pose_ac = _prix_split(pm.systeme_controle_acces, 0.65)

    story.extend(_build_fiche(
        code="MEP-CF03",
        titre="Controle d'acces" if lang == 'fr' else "Access Control",
        norme_ref="NF EN 60839 / NF A2P",
        specs=[
            ("Systeme/porte" if lang == 'fr' else "System/door", f"{fmt_fcfa(pm.systeme_controle_acces)}"),
            ("Interphone video" if lang == 'fr' else "Video intercom", f"{fmt_fcfa(pm.interphone_video)}/logement"),
            ("Type badge" if lang == 'fr' else "Badge type", "MIFARE DESFire EV2 (13.56 MHz)"),
            ("Biometrie" if lang == 'fr' else "Biometrics", "Empreinte / reconnaissance faciale"),
            ("Gache electrique" if lang == 'fr' else "Electric strike", "12/24 VDC, a emission"),
            ("Ventouse" if lang == 'fr' else "Magnetic lock", "300-600 kg force"),
            ("Logiciel" if lang == 'fr' else "Software", "Web-based, multi-site"),
            ("Historique" if lang == 'fr' else "Event log", "> 100 000 evenements"),
            ("Protocole" if lang == 'fr' else "Protocol", "TCP/IP, Wiegand 26/34"),
        ],
        ville=ville_cap, mat_prix=mat_ac, mat_unit="porte",
        pose_prix=pose_ac,
        ratio_label_fr="65% equip. / 35% pose",
        ratio_label_en="65% equip. / 35% install",
        meo_items=[
            "Cablage bus + alimentation 12/24V depuis coffret securise" if lang == 'fr' else "Bus cabling + 12/24V power from secured enclosure",
            "Gache/ventouse: alimentation secourue (batterie 12V)" if lang == 'fr' else "Strike/maglock: backed-up power (12V battery)",
            "Mode degradation: deverrouillage automatique en cas de coupure" if lang == 'fr' else "Fail-safe mode: auto-unlock on power loss",
            "Programmation badges et droits d'acces par l'administrateur" if lang == 'fr' else "Badge and access rights programming by admin",
            "Integration avec systeme incendie (deverrouillage sur alarme)" if lang == 'fr' else "Integration with fire system (unlock on alarm)",
            "Equipe: 1 technicien surete + 1 electricien / 3-5 portes/jour" if lang == 'fr' else "Crew: 1 security tech + 1 electrician / 3-5 doors/day",
        ],
        fournisseurs="Honeywell, HID Global, Suprema, CDVI, Intratone",
        normes="NF EN 60839, NF A2P, RGPD, NF S 61-937 (desenfumage lien)",
        lang=lang,
    ))

    # ── MEP-SI01 Detection incendie ─────────────────────────
    mat_di, pose_di = _prix_split(pm.detecteur_fumee, 0.65)

    story.extend(_build_fiche(
        code="MEP-SI01",
        titre="Detection incendie" if lang == 'fr' else "Fire Detection",
        norme_ref="NF S 61-970 / NF EN 54",
        specs=[
            ("Detecteur fumee optique" if lang == 'fr' else "Optical smoke detector", f"{fmt_fcfa(pm.detecteur_fumee)}/u"),
            ("Declencheur manuel" if lang == 'fr' else "Manual call point", f"{fmt_fcfa(pm.declencheur_manuel)}/u"),
            ("Sirene + flash" if lang == 'fr' else "Sounder + strobe", f"{fmt_fcfa(pm.sirene_flash)}/u"),
            ("Centrale 16 zones", f"{fmt_fcfa(pm.centrale_incendie_16zones)}"),
            ("Centrale 32 zones", f"{fmt_fcfa(pm.centrale_incendie_32zones)}"),
            ("Type detecteur" if lang == 'fr' else "Detector type", "Optique (standard) / thermique (cuisine)"),
            ("Couverture" if lang == 'fr' else "Coverage", "1 / 60 m2 (NF S 61-970)"),
            ("Boucle" if lang == 'fr' else "Loop", "Adressable 2 fils"),
            ("Autonomie batterie" if lang == 'fr' else "Battery autonomy", "72 h (NF S 61-970)"),
        ],
        ville=ville_cap, mat_prix=mat_di, mat_unit="u",
        pose_prix=pose_di,
        ratio_label_fr="65% equip. / 35% pose",
        ratio_label_en="65% equip. / 35% install",
        meo_items=[
            "Implantation selon NF S 61-970: 1 detecteur / 60 m2, max 7.50 m des murs" if lang == 'fr' else "Layout per NF S 61-970: 1 detector/60 m2, max 7.50 m from walls",
            "Declencheurs manuels a chaque sortie de secours + 1 par etage" if lang == 'fr' else "Manual call points at each emergency exit + 1 per level",
            "Boucle adressable: isolation de court-circuit integree" if lang == 'fr' else "Addressable loop: integrated short-circuit isolation",
            "Test fumee 100% des detecteurs a la reception" if lang == 'fr' else "Smoke test 100% of detectors at handover",
            "PV de verification initiale par organisme agree (APAVE, SOCOTEC)" if lang == 'fr' else "Initial verification report by approved body (APAVE, SOCOTEC)",
            "Equipe: 1 technicien SSI + 1 aide / 20-30 detecteurs/jour" if lang == 'fr' else "Crew: 1 fire tech + 1 helper / 20-30 detectors/day",
        ],
        fournisseurs="Siemens, Honeywell (Notifier), Bosch, Finsecur, DEF",
        normes="NF S 61-970, NF EN 54, IT 246, ERP article MS",
        lang=lang,
    ))

    # ── MEP-SI02 Extinction (RIA / sprinklers) ──────────────
    mat_ria, pose_ria = _prix_split(pm.ria_dn25_ml, 0.55)

    story.extend(_build_fiche(
        code="MEP-SI02",
        titre="Extinction (RIA / Sprinklers)" if lang == 'fr' else "Suppression (Hose Reels / Sprinklers)",
        norme_ref="IT 246 / NF EN 671-1 (RIA) / NF EN 12845 (sprinklers)",
        specs=[
            ("RIA DN25", f"{fmt_fcfa(pm.ria_dn25_ml)}/ml"),
            ("Tete sprinkler" if lang == 'fr' else "Sprinkler head", f"{fmt_fcfa(pm.sprinkler_tete)}/u"),
            ("Centrale sprinkler" if lang == 'fr' else "Sprinkler station", f"{fmt_fcfa(pm.sprinkler_centrale)}"),
            ("Pression min RIA" if lang == 'fr' else "Min RIA pressure", "2.5 bar a l'orifice"),
            ("Longueur max tuyau RIA" if lang == 'fr' else "Max RIA hose length", "20 m (IT 246)"),
            ("Coverage sprinkler" if lang == 'fr' else "Sprinkler coverage", "9-21 m2/tete selon risque"),
            ("Temp. declenchement" if lang == 'fr' else "Activation temp.", "68 C (standard) / 93 C (cuisine)"),
            ("Reseau" if lang == 'fr' else "Network", "Acier galva, DN 50-150"),
        ],
        ville=ville_cap, mat_prix=mat_ria, mat_unit="ml",
        pose_prix=pose_ria,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Reseau en acier galvanise (pas de PVC pour incendie)" if lang == 'fr' else "Galvanised steel network (no PVC for fire)",
            "RIA en armoire vitree a chaque etage, 5 m max d'une issue" if lang == 'fr' else "RIA in glazed cabinet each floor, max 5 m from exit",
            "Epreuve hydraulique 15 bar pendant 2 h" if lang == 'fr' else "Hydrostatic test 15 bar for 2 h",
            "Sprinklers: tete orientee correctement (pendant / debout)" if lang == 'fr' else "Sprinklers: heads correctly oriented (pendent/upright)",
            "Poteau d'incendie: debit 60 m3/h pendant 2 h" if lang == 'fr' else "Fire hydrant: flow 60 m3/h for 2 h",
            "Verification semestrielle par organisme agree" if lang == 'fr' else "Semi-annual verification by approved body",
            "Equipe: 1 tuyauteur + 1 soudeur + 1 aide / 15-20 ml/jour" if lang == 'fr' else "Crew: 1 pipefitter + 1 welder + 1 helper / 15-20 ml/day",
        ],
        fournisseurs="Viking, Tyco/Johnson Controls, Marioff, Desautel, Sicli",
        normes="IT 246, NF EN 671-1, NF EN 12845, APSAD R1 (sprinklers)",
        lang=lang,
    ))

    # ── MEP-SI03 Extincteurs ────────────────────────────────
    mat_ex, pose_ex = _prix_split(pm.extincteur_6kg_co2, 0.85)

    story.extend(_build_fiche(
        code="MEP-SI03",
        titre="Extincteurs" if lang == 'fr' else "Fire Extinguishers",
        norme_ref="NF EN 3 / NF S 61-919",
        specs=[
            ("CO2 6 kg", f"{fmt_fcfa(pm.extincteur_6kg_co2)}/u"),
            ("Poudre ABC 9 kg" if lang == 'fr' else "Powder ABC 9 kg", f"{fmt_fcfa(pm.extincteur_9kg_poudre)}/u"),
            ("Classe feu CO2" if lang == 'fr' else "Fire class CO2", "B (liquides) + electrique"),
            ("Classe feu poudre" if lang == 'fr' else "Fire class powder", "A + B + C"),
            ("Portee CO2" if lang == 'fr' else "CO2 range", "2-3 m"),
            ("Portee poudre" if lang == 'fr' else "Powder range", "4-6 m"),
            ("Positionnement" if lang == 'fr' else "Positioning", "1 / 200 m2, max 15 m de distance"),
            ("Hauteur support" if lang == 'fr' else "Support height", "0.90 - 1.20 m (poignee)"),
            ("Verification" if lang == 'fr' else "Inspection", "Annuelle par technicien agree"),
            ("Duree de vie" if lang == 'fr' else "Lifespan", "20 ans (reverifie tous les 5 ans)"),
        ],
        ville=ville_cap, mat_prix=mat_ex, mat_unit="u",
        pose_prix=pose_ex,
        ratio_label_fr="85% equip. / 15% pose",
        ratio_label_en="85% equip. / 15% install",
        meo_items=[
            "1 extincteur a poudre ABC 9 kg par 200 m2 de plancher" if lang == 'fr' else "1 ABC powder 9 kg extinguisher per 200 m2 floor",
            "1 CO2 pres de chaque tableau electrique et local serveur" if lang == 'fr' else "1 CO2 near each electrical panel and server room",
            "Fixation murale avec support metallique + signalisation" if lang == 'fr' else "Wall-mounted with metal bracket + signage",
            "Acces degage, visible, signale par pictogramme NF" if lang == 'fr' else "Clear, visible access, marked with NF pictogram",
            "Plan d'evacuation affiche a chaque etage" if lang == 'fr' else "Evacuation plan displayed on each floor",
            "Equipe: 1 technicien / 20-30 extincteurs/jour" if lang == 'fr' else "Crew: 1 technician / 20-30 extinguishers/day",
        ],
        fournisseurs="Desautel, Sicli, Andrieu, Gloria, importateurs locaux",
        normes="NF EN 3, NF S 61-919, Code du travail R4227-28 a R4227-34",
        lang=lang,
    ))

    # ── MEP-ASC01 Ascenseurs ────────────────────────────────
    if nb_niveaux <= 6:
        asc_prix = pm.ascenseur_630kg_r4_r6
        asc_label = "630 kg / 8 pers. (R+4 a R+6)"
    elif nb_niveaux <= 10:
        asc_prix = pm.ascenseur_630kg_r7_r10
        asc_label = "630 kg / 8 pers. (R+7 a R+10)"
    else:
        asc_prix = pm.ascenseur_1000kg_r11_plus
        asc_label = "1000 kg / 13 pers. (R+11+)"
    mat_as, pose_as = _prix_split(asc_prix, 0.75)

    story.extend(_build_fiche(
        code="MEP-ASC01",
        titre="Ascenseurs" if lang == 'fr' else "Elevators",
        norme_ref="NF EN 81-20/50 / Directive Ascenseurs 2014/33/UE",
        specs=[
            ("Charge" if lang == 'fr' else "Load", asc_label),
            ("Vitesse" if lang == 'fr' else "Speed", "1.0 - 1.6 m/s"),
            ("Type", "Electrique a adherence (MRL)" if lang == 'fr' else "Gearless traction (MRL)"),
            ("Cabine (L x P x H)" if lang == 'fr' else "Car (W x D x H)", "1100 x 1400 x 2200 mm"),
            ("Gaine (L x P)" if lang == 'fr' else "Shaft (W x D)", "1600 x 1800 mm min"),
            ("Portes" if lang == 'fr' else "Doors", "Automatiques telescopiques 800 mm"),
            ("Commande" if lang == 'fr' else "Control", "Collective selective descente"),
            ("Norme PMR" if lang == 'fr' else "Accessibility", "EN 81-70 (handicape)"),
            ("Onduleur secours" if lang == 'fr' else "Emergency UPS", "Descente au niveau 0"),
            ("Entretien" if lang == 'fr' else "Maintenance", "Contrat annuel obligatoire"),
        ],
        ville=ville_cap, mat_prix=mat_as, mat_unit="u",
        pose_prix=pose_as,
        ratio_label_fr="75% equip. / 25% pose",
        ratio_label_en="75% equip. / 25% install",
        meo_items=[
            "Gaine beton: tolerance verticalite +/- 25 mm sur la hauteur" if lang == 'fr' else "Concrete shaft: verticality tolerance +/- 25 mm over height",
            "Cuvette de gaine: 1.40 m min + echelle + prise + eclairage" if lang == 'fr' else "Pit: 1.40 m min + ladder + socket + lighting",
            "Machinerie en gaine (MRL) ou local machines en toiture" if lang == 'fr' else "Machine-room-less (MRL) or rooftop machine room",
            "Alimentation electrique dediee triphasee 400V" if lang == 'fr' else "Dedicated three-phase 400V power supply",
            "Reception: essais de charge (125% Qn), essais de freinage" if lang == 'fr' else "Acceptance: load tests (125% Qn), brake tests",
            "Certification CE + organisme notifie (SOCOTEC, Bureau Veritas)" if lang == 'fr' else "CE certification + notified body (SOCOTEC, Bureau Veritas)",
            "Duree installation: 4-8 semaines selon hauteur" if lang == 'fr' else "Install duration: 4-8 weeks depending on height",
        ],
        fournisseurs="Otis, Schindler, KONE, ThyssenKrupp, Hyundai Elevator",
        normes="NF EN 81-20, NF EN 81-50, NF EN 81-70, Dir. 2014/33/UE",
        lang=lang,
    ))

    # ── MEP-GTB01 Systeme GTB/BMS ───────────────────────────
    mat_bms, pose_bms = _prix_split(pm.bms_systeme, 0.65)

    story.extend(_build_fiche(
        code="MEP-GTB01",
        titre="Systeme GTB / BMS" if lang == 'fr' else "BMS System",
        norme_ref="NF EN ISO 16484 / NF EN 15232",
        specs=[
            ("Forfait batiment" if lang == 'fr' else "Building package", f"{fmt_fcfa(pm.bms_systeme)}"),
            ("Domotique/logement" if lang == 'fr' else "Home automation/dwelling", f"{fmt_fcfa(pm.domotique_logement)}"),
            ("Protocole" if lang == 'fr' else "Protocol", "BACnet IP / Modbus TCP/RS485"),
            ("Points supervises" if lang == 'fr' else "Supervised points", "200-2000 selon batiment"),
            ("Supervision" if lang == 'fr' else "Supervision", "IHM web HTML5, multi-ecran"),
            ("Lots integres" if lang == 'fr' else "Integrated trades", "CVC, eclairage, acces, incendie"),
            ("Comptage energetique" if lang == 'fr' else "Energy metering", "Elec + eau + gaz par lot"),
            ("Alarmes" if lang == 'fr' else "Alarms", "SMS + email + historique 2 ans"),
            ("Classe EN 15232" if lang == 'fr' else "EN 15232 class", "B (systemes avances)"),
        ],
        ville=ville_cap, mat_prix=mat_bms, mat_unit="forfait",
        pose_prix=pose_bms,
        ratio_label_fr="65% equip. / 35% integration",
        ratio_label_en="65% equip. / 35% integration",
        meo_items=[
            "Architecture reseau: automate par sous-station + superviseur central" if lang == 'fr' else "Network architecture: PLC per substation + central supervisor",
            "Cablage bus terrain: cable blinde torsade 2 paires" if lang == 'fr' else "Field bus wiring: shielded twisted pair 2 pairs",
            "Integration progressive: lot par lot (CVC puis eclairage puis SSI)" if lang == 'fr' else "Progressive integration: trade by trade (HVAC then lighting then fire)",
            "Formation exploitant: 3-5 jours sur site" if lang == 'fr' else "Operator training: 3-5 days on site",
            "Maintenance logicielle: contrat annuel recommande" if lang == 'fr' else "Software maintenance: annual contract recommended",
            "Equipe: 1 ingenieur automatisme + 1 technicien / 2-4 semaines" if lang == 'fr' else "Crew: 1 automation engineer + 1 technician / 2-4 weeks",
        ],
        fournisseurs="Schneider Electric (EcoStruxure), Siemens (Desigo), Honeywell (Niagara), Delta Controls",
        normes="NF EN ISO 16484, NF EN 15232, BACnet ISO 16484-5, EDGE v3",
        lang=lang,
    ))

    # ══════════════════════════════════════════════════════════
    # SECTION 3: FINITIONS FICHES
    # ══════════════════════════════════════════════════════════
    story.extend(section_title("C", "FINITIONS" if lang == 'fr' else "FINISHES"))
    story.append(PageBreak())

    # ── FIN-01 Carrelage ────────────────────────────────────
    # Approximate carrelage price: ~18,000 FCFA/m2 (not in prix_marche directly)
    prix_carrelage = 18_000
    mat_car, pose_car = _prix_split(prix_carrelage, 0.55)

    story.extend(_build_fiche(
        code="FIN-01",
        titre="Carrelage" if lang == 'fr' else "Tiling",
        norme_ref="DTU 52.1 / NF EN 14411 / NF EN 12004 (colles)",
        specs=[
            ("Gres cerame" if lang == 'fr' else "Porcelain stoneware", "30x30, 45x45, 60x60 cm"),
            ("Faience murale" if lang == 'fr' else "Wall tiles", "20x25, 25x40, 30x60 cm"),
            ("Classement UPEC" if lang == 'fr' else "UPEC rating", "U3 P3 E2 C1 (residentiel)"),
            ("Resistance glissance" if lang == 'fr' else "Slip resistance", "R10 (int.), R11 (ext./SDB)"),
            ("Absorption eau" if lang == 'fr' else "Water absorption", "< 0.5% (gres cerame)"),
            ("Colle" if lang == 'fr' else "Adhesive", "C2TE (amelioree, double encollage)"),
            ("Joints" if lang == 'fr' else "Grout", "2-5 mm, hydrofuge en SDB"),
            ("Epaisseur" if lang == 'fr' else "Thickness", "8-10 mm (sol), 6-8 mm (mur)"),
        ],
        ville=ville_cap, mat_prix=mat_car, mat_unit="m2",
        pose_prix=pose_car,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% labour",
        meo_items=[
            "Support propre, plan (tolerance 5 mm/2m), sec" if lang == 'fr' else "Clean, flat (5 mm/2m tolerance), dry substrate",
            "Primaire d'accrochage si support poreux" if lang == 'fr' else "Primer if porous substrate",
            "Double encollage obligatoire pour format >= 45x45 cm" if lang == 'fr' else "Double buttering mandatory for tiles >= 45x45 cm",
            "Joints de dilatation perimetriques + tous les 6 m" if lang == 'fr' else "Peripheral expansion joints + every 6 m",
            "Croisillons calibres pour joints reguliers" if lang == 'fr' else "Calibrated spacers for regular joints",
            "Pas de pose en exterieur au-dessus de 40 C" if lang == 'fr' else "No outdoor installation above 40 C",
            "Equipe: 1 carreleur + 1 aide / 10-15 m2/jour (sol)" if lang == 'fr' else "Crew: 1 tiler + 1 helper / 10-15 m2/day (floor)",
            "Reception: planeite 2 mm/2m, sonorite (pas de creux)" if lang == 'fr' else "Acceptance: flatness 2 mm/2m, tap test (no hollow)",
        ],
        fournisseurs="Porcelanosa, Marazzi, RAK Ceramics, importateurs Dakar (Comptoir du Carrelage)",
        normes="DTU 52.1, NF EN 14411, NF EN 12004, classement UPEC",
        lang=lang,
    ))

    # ── FIN-02 Menuiserie interieure ────────────────────────
    prix_porte = 85_000  # estimated
    mat_pi, pose_pi = _prix_split(prix_porte, 0.55)

    story.extend(_build_fiche(
        code="FIN-02",
        titre="Menuiserie interieure" if lang == 'fr' else "Interior Joinery",
        norme_ref="DTU 36.1 / NF EN 14351-2",
        specs=[
            ("Porte isoplane" if lang == 'fr' else "Flush door", "83 x 204 cm, ame alveolee"),
            ("Porte postformee" if lang == 'fr' else "Post-formed door", "83 x 204 cm, stratifie"),
            ("Porte CF (coupe-feu)" if lang == 'fr' else "Fire door", "EI 30 ou EI 60"),
            ("Bloc-porte" if lang == 'fr' else "Door set", "Huisserie bois ou metal"),
            ("Quincaillerie" if lang == 'fr' else "Hardware", "Poignee + serrure + paumelles"),
            ("Finition" if lang == 'fr' else "Finish", "Laque, stratifie, placage bois"),
            ("Epaisseur vantail" if lang == 'fr' else "Leaf thickness", "40 mm (standard), 54 mm (CF)"),
            ("Passage libre" if lang == 'fr' else "Clear opening", "83 cm (standard), 90 cm (PMR)"),
        ],
        ville=ville_cap, mat_prix=mat_pi, mat_unit="u",
        pose_prix=pose_pi,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Pose apres enduits et avant peinture" if lang == 'fr' else "Install after renders, before painting",
            "Huisserie: scellement au mortier ou chevilles mecaniques" if lang == 'fr' else "Frame: mortar fixing or mechanical anchors",
            "Jeu peripherique 3-5 mm pour dilatation" if lang == 'fr' else "3-5 mm peripheral gap for expansion",
            "Reglage des paumelles: aplomb, alignement, fermeture" if lang == 'fr' else "Hinge adjustment: plumb, alignment, closure",
            "Quincaillerie PMR: poignee a 1.05 m, bequille" if lang == 'fr' else "Accessible hardware: handle at 1.05 m, lever type",
            "Equipe: 1 menuisier + 1 aide / 4-6 portes/jour" if lang == 'fr' else "Crew: 1 joiner + 1 helper / 4-6 doors/day",
        ],
        fournisseurs="Menuiseries locales Dakar, CFAO Materials, Sogequip, Huet (import)",
        normes="DTU 36.1, NF EN 14351-2, NF P 23-305 (portes CF)",
        lang=lang,
    ))

    # ── FIN-03 Menuiserie exterieure ────────────────────────
    prix_fenetre = 120_000  # estimated
    mat_fe, pose_fe = _prix_split(prix_fenetre, 0.55)

    story.extend(_build_fiche(
        code="FIN-03",
        titre="Menuiserie exterieure (aluminium)" if lang == 'fr' else "Exterior Joinery (aluminium)",
        norme_ref="DTU 36.5 / NF EN 14351-1",
        specs=[
            ("Profil alu" if lang == 'fr' else "Alu profile", "Rupture de pont thermique (RPT)"),
            ("Vitrage" if lang == 'fr' else "Glazing", "4/16/4 double, Ug <= 1.1 W/m2K"),
            ("Vitrage securite" if lang == 'fr' else "Safety glazing", "44.2 feuillete (RdC, garde-corps)"),
            ("Etancheite air" if lang == 'fr' else "Air tightness", "A*3 (classement AEV)"),
            ("Etancheite eau" if lang == 'fr' else "Water tightness", "E*6A"),
            ("Resistance vent" if lang == 'fr' else "Wind resistance", "V*A3"),
            ("Coulissant" if lang == 'fr' else "Sliding", "2-3 vantaux rail alu"),
            ("Ouvrant a la francaise" if lang == 'fr' else "Casement", "1-2 vantaux + oscillo-battant"),
            ("Volet roulant" if lang == 'fr' else "Roller shutter", "Alu thermo-laque + motorise"),
            ("Coloris" if lang == 'fr' else "Color", "RAL au choix, laquage poudre"),
        ],
        ville=ville_cap, mat_prix=mat_fe, mat_unit="m2",
        pose_prix=pose_fe,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Prises de cotes apres gros oeuvre termine" if lang == 'fr' else "Measurements after structural frame complete",
            "Pose en applique ou en feuillure selon type de mur" if lang == 'fr' else "Surface or rebate mounting depending on wall type",
            "Calfeutrement mousse PU + mastic silicone exterieur" if lang == 'fr' else "PU foam sealing + exterior silicone mastic",
            "Bavette alu en traverse basse (rejet d'eau)" if lang == 'fr' else "Aluminium drip bar at bottom rail (water shed)",
            "Reglage de la quincaillerie: compression joint, gaches" if lang == 'fr' else "Hardware adjustment: gasket compression, keeps",
            "Equipe: 1 poseur alu + 1 aide / 4-6 m2/jour" if lang == 'fr' else "Crew: 1 alu fitter + 1 helper / 4-6 m2/day",
            "Reception: test d'etancheite au jet d'eau" if lang == 'fr' else "Acceptance: water spray tightness test",
        ],
        fournisseurs="Technal, Schuco, Reynaers, ateliers alu locaux Dakar, K-Line",
        normes="DTU 36.5, NF EN 14351-1, classement AEV, DTU 39 (vitrerie)",
        lang=lang,
    ))

    # ── FIN-04 Faux-plafonds ────────────────────────────────
    prix_fp = 22_000  # estimated
    mat_fp, pose_fp = _prix_split(prix_fp, 0.55)

    story.extend(_build_fiche(
        code="FIN-04",
        titre="Faux-plafonds" if lang == 'fr' else "Suspended Ceilings",
        norme_ref="DTU 25.232 (BA13) / NF EN 13964 (ossature)",
        specs=[
            ("BA13 standard" if lang == 'fr' else "Standard plasterboard", "12.5 mm, bord aminci"),
            ("BA13 hydrofuge" if lang == 'fr' else "Moisture-resistant", "H1, pour SDB/cuisine"),
            ("Dalles minerales" if lang == 'fr' else "Mineral tiles", "600x600 mm, ep. 15-19 mm"),
            ("Ossature" if lang == 'fr' else "Grid", "T24 ou T15, porteurs + entretien"),
            ("Plenum" if lang == 'fr' else "Plenum", "15-50 cm selon installations"),
            ("Acoustique NR" if lang == 'fr' else "Acoustic NR", "NRC 0.55-0.70 (dalles minerales)"),
            ("Reaction au feu" if lang == 'fr' else "Fire reaction", "A2-s1,d0 (M0)"),
            ("Trappe visite" if lang == 'fr' else "Access panel", "400x400 mm, articulee"),
        ],
        ville=ville_cap, mat_prix=mat_fp, mat_unit="m2",
        pose_prix=pose_fp,
        ratio_label_fr="55% mat. / 45% pose",
        ratio_label_en="55% mat. / 45% install",
        meo_items=[
            "Suspentes tous les 1.20 m max, fixees dans la dalle" if lang == 'fr' else "Hangers every 1.20 m max, fixed to slab",
            "Verification horizontalite au laser rotatif" if lang == 'fr' else "Check level with rotary laser",
            "Joints BA13: bande + 3 passes d'enduit (lissage)" if lang == 'fr' else "Plasterboard joints: tape + 3 coats of filler (smoothing)",
            "Coordination MEP: percements luminaires, bouches VMC, detecteurs" if lang == 'fr' else "MEP coordination: luminaire cutouts, vent grilles, detectors",
            "Hydrofuge en SDB/cuisine (H1 + peinture etanche)" if lang == 'fr' else "Moisture-resistant in bathrooms/kitchen (H1 + waterproof paint)",
            "Equipe: 1 plaquiste + 1 aide / 15-25 m2/jour" if lang == 'fr' else "Crew: 1 dryliner + 1 helper / 15-25 m2/day",
            "Reception: planeite 3 mm/2m, joints non visibles" if lang == 'fr' else "Acceptance: flatness 3 mm/2m, invisible joints",
        ],
        fournisseurs="Placoplatre (Saint-Gobain), Knauf, Armstrong (dalles), OWA",
        normes="DTU 25.232, NF EN 520 (BA13), NF EN 13964, NF EN 13501-1 (feu)",
        lang=lang,
    ))

    # ── FIN-05 Peinture ─────────────────────────────────────
    prix_peinture = 6_000  # per m2, estimated
    mat_pe, pose_pe = _prix_split(prix_peinture, 0.35)

    story.extend(_build_fiche(
        code="FIN-05",
        titre="Peinture" if lang == 'fr' else "Painting",
        norme_ref="DTU 59.1 / NF EN 13300",
        specs=[
            ("Acrylique mate" if lang == 'fr' else "Matt acrylic", "Interieur, 2 couches"),
            ("Acrylique satinee" if lang == 'fr' else "Satin acrylic", "SDB, cuisine, couloirs"),
            ("Glycero brillante" if lang == 'fr' else "Gloss alkyd", "Huisseries, boiseries"),
            ("Peinture facade" if lang == 'fr' else "Facade paint", "Pliolite / siloxane"),
            ("Impression" if lang == 'fr' else "Primer", "1 couche fixateur / impression"),
            ("Rendement" if lang == 'fr' else "Coverage", "8-12 m2/L selon support"),
            ("Sechage entre couches" if lang == 'fr' else "Recoat time", "2-4 h (acrylique), 12-24 h (glycero)"),
            ("Preparation" if lang == 'fr' else "Preparation", "Egrenage, rebouchage, poncage"),
            ("COV" if lang == 'fr' else "VOC", "< 30 g/L (label A+)"),
        ],
        ville=ville_cap, mat_prix=mat_pe, mat_unit="m2",
        pose_prix=pose_pe,
        ratio_label_fr="35% mat. / 65% pose",
        ratio_label_en="35% mat. / 65% labour",
        meo_items=[
            "Support sec, propre, depousiere; reboucher fissures" if lang == 'fr' else "Dry, clean, dust-free substrate; fill cracks",
            "Impression obligatoire sur supports neufs" if lang == 'fr' else "Primer mandatory on new substrates",
            "2 couches minimum, croisees (vertical puis horizontal)" if lang == 'fr' else "Minimum 2 coats, cross-applied (vertical then horizontal)",
            "Temperature 10-35 C, pas de peinture en plein soleil" if lang == 'fr' else "Temperature 10-35 C, no painting in direct sunlight",
            "Proteger sols et menuiseries (baches + scotch de masquage)" if lang == 'fr' else "Protect floors and joinery (sheets + masking tape)",
            "Equipe: 1 peintre / 25-40 m2/jour (2 couches)" if lang == 'fr' else "Crew: 1 painter / 25-40 m2/day (2 coats)",
            "Reception: aspect uniforme, pas de coulures ni manques" if lang == 'fr' else "Acceptance: uniform finish, no runs or misses",
        ],
        fournisseurs="Seigneurie/PPG, Tollens/Cromology, SIKA, Colorine, peintures locales",
        normes="DTU 59.1, NF EN 13300, NF T 36-005 (classification), label A+",
        lang=lang,
    ))

    # ── FIN-06 Cuisine ──────────────────────────────────────
    prix_cuisine = 350_000  # per kitchen unit, estimated
    mat_cu, pose_cu = _prix_split(prix_cuisine, 0.60)

    story.extend(_build_fiche(
        code="FIN-06",
        titre="Cuisine (meubles et equipements)" if lang == 'fr' else "Kitchen (cabinets and equipment)",
        norme_ref="NF EN 1116 / DTU 60.1 (plomberie)",
        specs=[
            ("Meuble bas" if lang == 'fr' else "Base unit", "Melamine 16-18 mm, L 60-120 cm"),
            ("Meuble haut" if lang == 'fr' else "Wall unit", "H 70 cm, P 35 cm"),
            ("Plan de travail" if lang == 'fr' else "Countertop", "Stratifie HPL ep. 38 mm / granit"),
            ("Evier" if lang == 'fr' else "Sink", "Inox 1 ou 2 bacs, avec egouttoir"),
            ("Robinetterie" if lang == 'fr' else "Faucet", "Mitigeur col de cygne"),
            ("Credence" if lang == 'fr' else "Backsplash", "Faience 10x10 ou 30x60 cm"),
            ("Prise cuisine" if lang == 'fr' else "Kitchen outlet", "4 prises min (NF C 15-100)"),
            ("Ventilation" if lang == 'fr' else "Ventilation", "Hotte aspirante 600-900 mm"),
            ("Eclairage sous meuble" if lang == 'fr' else "Under-cabinet light", "Reglette LED"),
        ],
        ville=ville_cap, mat_prix=mat_cu, mat_unit="cuisine",
        pose_prix=pose_cu,
        ratio_label_fr="60% mat. / 40% pose",
        ratio_label_en="60% mat. / 40% install",
        meo_items=[
            "Pose apres carrelage sol/mur et peinture termines" if lang == 'fr' else "Install after floor/wall tiling and painting complete",
            "Meuble bas: reglage pieds pour horizontalite" if lang == 'fr' else "Base units: adjustable feet for level",
            "Meuble haut: fixation par rail metallique + chevilles 8 mm" if lang == 'fr' else "Wall units: metal rail fixing + 8 mm anchors",
            "Plan de travail: joint silicone etanche contre mur" if lang == 'fr' else "Countertop: silicone seal against wall",
            "Plomberie: raccordement evier + lave-vaisselle (siphon double)" if lang == 'fr' else "Plumbing: sink + dishwasher connection (double trap)",
            "Electricite: circuit dedie 32A pour plaque, 20A pour four" if lang == 'fr' else "Electrical: dedicated 32A for hob, 20A for oven",
            "Equipe: 1 cuisiniste + 1 plombier / 1-2 jours par cuisine" if lang == 'fr' else "Crew: 1 kitchen fitter + 1 plumber / 1-2 days per kitchen",
        ],
        fournisseurs="IKEA (import), menuiseries locales, Schmidt, Cuisinella, ateliers Dakar",
        normes="NF EN 1116, NF C 15-100 (electricite cuisine), DTU 60.1",
        lang=lang,
    ))

    # ── DISCLAIMER PAGE ─────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width=CW, thickness=1, color=VERT, spaceAfter=4))
    disc_text = (
        "Les fiches techniques ci-dessus sont fournies a titre indicatif. "
        "Les prix sont bases sur le marche de {ville} (mise a jour {date}). "
        "Les specifications definitives doivent etre validees par l'ingenieur "
        "responsable du projet. Les prix peuvent varier de +/- 15% selon les "
        "conditions du marche, les quantites commandees et la periode de l'annee."
    ) if lang == 'fr' else (
        "The technical data sheets above are provided for guidance only. "
        "Prices are based on the {ville} market (updated {date}). "
        "Final specifications must be validated by the project engineer. "
        "Prices may vary by +/- 15% depending on market conditions, "
        "order quantities and time of year."
    )
    story.append(Paragraph(
        disc_text.format(ville=ville_cap, date=pp.date_maj),
        S['small'],
    ))

    # Build PDF
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# FINITIONS-ONLY GENERATOR (sans prix)
# ══════════════════════════════════════════════════════════════

def generer_fiches_finitions(rs_structure, params: dict, lang: str = "fr") -> bytes:
    """Generate technical data sheets for FINITIONS items only (no prices)."""
    set_pdf_lang(lang)
    buf = io.BytesIO()
    nom = params.get('nom', 'Projet Tijan')

    doc_title = "Fiches Techniques — Finitions" if lang == 'fr' else "Technical Data Sheets — Finishes"
    hf = HeaderFooter(nom, doc_title, lang=lang)

    doc = SimpleDocTemplate(
        buf, pagesize=PAGE,
        rightMargin=MR, leftMargin=ML,
        topMargin=26 * mm, bottomMargin=18 * mm,
    )

    story = []
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(nom, S['titre']))
    story.append(Paragraph(doc_title, S['sous_titre']))
    story.append(Spacer(1, 2 * mm))

    desc = (
        "Specifications techniques, normes applicables et conseils de mise en oeuvre "
        "pour chaque poste de finition."
    ) if lang == 'fr' else (
        "Technical specifications, applicable standards and implementation guidance "
        "for each finishing item."
    )
    story.append(Paragraph(desc, S['body']))
    story.append(Spacer(1, 4 * mm))

    # ── FIN-01 Carrelage ──
    story.extend(_build_fiche_no_prix(
        code="FIN-01",
        titre="Carrelage" if lang == 'fr' else "Tiling",
        norme_ref="DTU 52.1 / NF EN 14411 / NF EN 12004 (colles)",
        specs=[
            ("Gres cerame" if lang == 'fr' else "Porcelain stoneware", "30x30, 45x45, 60x60 cm"),
            ("Faience murale" if lang == 'fr' else "Wall tiles", "20x25, 25x40, 30x60 cm"),
            ("Classement UPEC" if lang == 'fr' else "UPEC rating", "U3 P3 E2 C1 (residentiel)"),
            ("Resistance glissance" if lang == 'fr' else "Slip resistance", "R10 (int.), R11 (ext./SDB)"),
            ("Absorption eau" if lang == 'fr' else "Water absorption", "< 0.5% (gres cerame)"),
            ("Colle" if lang == 'fr' else "Adhesive", "C2TE (amelioree, double encollage)"),
            ("Joints" if lang == 'fr' else "Grout", "2-5 mm, hydrofuge en SDB"),
            ("Epaisseur" if lang == 'fr' else "Thickness", "8-10 mm (sol), 6-8 mm (mur)"),
        ],
        meo_items=[
            "Support propre, plan (tolerance 5 mm/2m), sec" if lang == 'fr' else "Clean, flat (5 mm/2m tolerance), dry substrate",
            "Primaire d'accrochage si support poreux" if lang == 'fr' else "Primer if porous substrate",
            "Double encollage obligatoire pour format >= 45x45 cm" if lang == 'fr' else "Double buttering mandatory for tiles >= 45x45 cm",
            "Joints de dilatation perimetriques + tous les 6 m" if lang == 'fr' else "Peripheral expansion joints + every 6 m",
            "Equipe: 1 carreleur + 1 aide / 10-15 m2/jour (sol)" if lang == 'fr' else "Crew: 1 tiler + 1 helper / 10-15 m2/day (floor)",
            "Reception: planeite 2 mm/2m, sonorite (pas de creux)" if lang == 'fr' else "Acceptance: flatness 2 mm/2m, tap test (no hollow)",
        ],
        fournisseurs="Porcelanosa, Marazzi, RAK Ceramics, importateurs Dakar (Comptoir du Carrelage)",
        normes="DTU 52.1, NF EN 14411, NF EN 12004, classement UPEC",
        lang=lang,
    ))

    # ── FIN-02 Menuiserie interieure ──
    story.extend(_build_fiche_no_prix(
        code="FIN-02",
        titre="Menuiserie interieure" if lang == 'fr' else "Interior Joinery",
        norme_ref="DTU 36.1 / NF EN 14351-2",
        specs=[
            ("Porte isoplane" if lang == 'fr' else "Flush door", "83 x 204 cm, ame alveolee"),
            ("Porte postformee" if lang == 'fr' else "Post-formed door", "83 x 204 cm, stratifie"),
            ("Porte CF (coupe-feu)" if lang == 'fr' else "Fire door", "EI 30 ou EI 60"),
            ("Bloc-porte" if lang == 'fr' else "Door set", "Huisserie bois ou metal"),
            ("Quincaillerie" if lang == 'fr' else "Hardware", "Poignee + serrure + paumelles"),
            ("Epaisseur vantail" if lang == 'fr' else "Leaf thickness", "40 mm (standard), 54 mm (CF)"),
            ("Passage libre" if lang == 'fr' else "Clear opening", "83 cm (standard), 90 cm (PMR)"),
        ],
        meo_items=[
            "Pose apres enduits et avant peinture" if lang == 'fr' else "Install after renders, before painting",
            "Huisserie: scellement au mortier ou chevilles mecaniques" if lang == 'fr' else "Frame: mortar fixing or mechanical anchors",
            "Jeu peripherique 3-5 mm pour dilatation" if lang == 'fr' else "3-5 mm peripheral gap for expansion",
            "Quincaillerie PMR: poignee a 1.05 m, bequille" if lang == 'fr' else "Accessible hardware: handle at 1.05 m, lever type",
            "Equipe: 1 menuisier + 1 aide / 4-6 portes/jour" if lang == 'fr' else "Crew: 1 joiner + 1 helper / 4-6 doors/day",
        ],
        fournisseurs="Menuiseries locales Dakar, CFAO Materials, Sogequip, Huet (import)",
        normes="DTU 36.1, NF EN 14351-2, NF P 23-305 (portes CF)",
        lang=lang,
    ))

    # ── FIN-03 Menuiserie exterieure ──
    story.extend(_build_fiche_no_prix(
        code="FIN-03",
        titre="Menuiserie exterieure (aluminium)" if lang == 'fr' else "Exterior Joinery (aluminium)",
        norme_ref="DTU 36.5 / NF EN 14351-1",
        specs=[
            ("Profil alu" if lang == 'fr' else "Alu profile", "Rupture de pont thermique (RPT)"),
            ("Vitrage" if lang == 'fr' else "Glazing", "4/16/4 double, Ug <= 1.1 W/m2K"),
            ("Vitrage securite" if lang == 'fr' else "Safety glazing", "44.2 feuillete (RdC, garde-corps)"),
            ("Etancheite air/eau/vent" if lang == 'fr' else "AEV rating", "A*3 / E*6A / V*A3"),
            ("Coulissant" if lang == 'fr' else "Sliding", "2-3 vantaux rail alu"),
            ("Ouvrant a la francaise" if lang == 'fr' else "Casement", "1-2 vantaux + oscillo-battant"),
            ("Volet roulant" if lang == 'fr' else "Roller shutter", "Alu thermo-laque + motorise"),
        ],
        meo_items=[
            "Prises de cotes apres gros oeuvre termine" if lang == 'fr' else "Measurements after structural frame complete",
            "Pose en applique ou en feuillure selon type de mur" if lang == 'fr' else "Surface or rebate mounting depending on wall type",
            "Calfeutrement mousse PU + mastic silicone exterieur" if lang == 'fr' else "PU foam sealing + exterior silicone mastic",
            "Bavette alu en traverse basse (rejet d'eau)" if lang == 'fr' else "Aluminium drip bar at bottom rail (water shed)",
            "Equipe: 1 poseur alu + 1 aide / 4-6 m2/jour" if lang == 'fr' else "Crew: 1 alu fitter + 1 helper / 4-6 m2/day",
            "Reception: test d'etancheite au jet d'eau" if lang == 'fr' else "Acceptance: water spray tightness test",
        ],
        fournisseurs="Technal, Schuco, Reynaers, ateliers alu locaux Dakar, K-Line",
        normes="DTU 36.5, NF EN 14351-1, classement AEV, DTU 39 (vitrerie)",
        lang=lang,
    ))

    # ── FIN-04 Faux-plafonds ──
    story.extend(_build_fiche_no_prix(
        code="FIN-04",
        titre="Faux-plafonds" if lang == 'fr' else "Suspended Ceilings",
        norme_ref="DTU 25.232 (BA13) / NF EN 13964 (ossature)",
        specs=[
            ("BA13 standard" if lang == 'fr' else "Standard plasterboard", "12.5 mm, bord aminci"),
            ("BA13 hydrofuge" if lang == 'fr' else "Moisture-resistant", "H1, pour SDB/cuisine"),
            ("Dalles minerales" if lang == 'fr' else "Mineral tiles", "600x600 mm, ep. 15-19 mm"),
            ("Ossature" if lang == 'fr' else "Grid", "T24 ou T15, porteurs + entretien"),
            ("Plenum" if lang == 'fr' else "Plenum", "15-50 cm selon installations"),
            ("Acoustique NR" if lang == 'fr' else "Acoustic NR", "NRC 0.55-0.70 (dalles minerales)"),
            ("Reaction au feu" if lang == 'fr' else "Fire reaction", "A2-s1,d0 (M0)"),
        ],
        meo_items=[
            "Suspentes tous les 1.20 m max, fixees dans la dalle" if lang == 'fr' else "Hangers every 1.20 m max, fixed to slab",
            "Verification horizontalite au laser rotatif" if lang == 'fr' else "Check level with rotary laser",
            "Joints BA13: bande + 3 passes d'enduit (lissage)" if lang == 'fr' else "Plasterboard joints: tape + 3 coats of filler",
            "Coordination MEP: percements luminaires, bouches VMC, detecteurs" if lang == 'fr' else "MEP coordination: luminaire cutouts, vent grilles, detectors",
            "Equipe: 1 plaquiste + 1 aide / 15-25 m2/jour" if lang == 'fr' else "Crew: 1 dryliner + 1 helper / 15-25 m2/day",
        ],
        fournisseurs="Placoplatre (Saint-Gobain), Knauf, Armstrong (dalles), OWA",
        normes="DTU 25.232, NF EN 520 (BA13), NF EN 13964, NF EN 13501-1 (feu)",
        lang=lang,
    ))

    # ── FIN-05 Peinture ──
    story.extend(_build_fiche_no_prix(
        code="FIN-05",
        titre="Peinture" if lang == 'fr' else "Painting",
        norme_ref="DTU 59.1 / NF EN 13300",
        specs=[
            ("Acrylique mate" if lang == 'fr' else "Matt acrylic", "Interieur, 2 couches"),
            ("Acrylique satinee" if lang == 'fr' else "Satin acrylic", "SDB, cuisine, couloirs"),
            ("Glycero brillante" if lang == 'fr' else "Gloss alkyd", "Huisseries, boiseries"),
            ("Peinture facade" if lang == 'fr' else "Facade paint", "Pliolite / siloxane"),
            ("Impression" if lang == 'fr' else "Primer", "1 couche fixateur / impression"),
            ("Rendement" if lang == 'fr' else "Coverage", "8-12 m2/L selon support"),
            ("COV" if lang == 'fr' else "VOC", "< 30 g/L (label A+)"),
        ],
        meo_items=[
            "Support sec, propre, depousiere; reboucher fissures" if lang == 'fr' else "Dry, clean, dust-free substrate; fill cracks",
            "Impression obligatoire sur supports neufs" if lang == 'fr' else "Primer mandatory on new substrates",
            "2 couches minimum, croisees (vertical puis horizontal)" if lang == 'fr' else "Minimum 2 coats, cross-applied",
            "Temperature 10-35 C, pas de peinture en plein soleil" if lang == 'fr' else "Temperature 10-35 C, no painting in direct sunlight",
            "Equipe: 1 peintre / 25-40 m2/jour (2 couches)" if lang == 'fr' else "Crew: 1 painter / 25-40 m2/day (2 coats)",
            "Reception: aspect uniforme, pas de coulures ni manques" if lang == 'fr' else "Acceptance: uniform finish, no runs or misses",
        ],
        fournisseurs="Seigneurie/PPG, Tollens/Cromology, SIKA, Colorine, peintures locales",
        normes="DTU 59.1, NF EN 13300, NF T 36-005, label A+",
        lang=lang,
    ))

    # ── FIN-06 Cuisine ──
    story.extend(_build_fiche_no_prix(
        code="FIN-06",
        titre="Cuisine (meubles et equipements)" if lang == 'fr' else "Kitchen (cabinets and equipment)",
        norme_ref="NF EN 1116 / DTU 60.1 (plomberie)",
        specs=[
            ("Meuble bas" if lang == 'fr' else "Base unit", "Melamine 16-18 mm, L 60-120 cm"),
            ("Meuble haut" if lang == 'fr' else "Wall unit", "H 70 cm, P 35 cm"),
            ("Plan de travail" if lang == 'fr' else "Countertop", "Stratifie HPL ep. 38 mm / granit"),
            ("Evier" if lang == 'fr' else "Sink", "Inox 1 ou 2 bacs, avec egouttoir"),
            ("Robinetterie" if lang == 'fr' else "Faucet", "Mitigeur col de cygne"),
            ("Prise cuisine" if lang == 'fr' else "Kitchen outlet", "4 prises min (NF C 15-100)"),
            ("Ventilation" if lang == 'fr' else "Ventilation", "Hotte aspirante 600-900 mm"),
        ],
        meo_items=[
            "Pose apres carrelage sol/mur et peinture termines" if lang == 'fr' else "Install after floor/wall tiling and painting complete",
            "Meuble bas: reglage pieds pour horizontalite" if lang == 'fr' else "Base units: adjustable feet for level",
            "Meuble haut: fixation par rail metallique + chevilles 8 mm" if lang == 'fr' else "Wall units: metal rail fixing + 8 mm anchors",
            "Plomberie: raccordement evier + lave-vaisselle (siphon double)" if lang == 'fr' else "Plumbing: sink + dishwasher connection (double trap)",
            "Electricite: circuit dedie 32A pour plaque, 20A pour four" if lang == 'fr' else "Electrical: dedicated 32A for hob, 20A for oven",
            "Equipe: 1 cuisiniste + 1 plombier / 1-2 jours par cuisine" if lang == 'fr' else "Crew: 1 kitchen fitter + 1 plumber / 1-2 days per kitchen",
        ],
        fournisseurs="IKEA (import), menuiseries locales, Schmidt, Cuisinella, ateliers Dakar",
        normes="NF EN 1116, NF C 15-100 (electricite cuisine), DTU 60.1",
        lang=lang,
    ))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    params = {
        'nom': 'Residence Papa Oumar Sakho',
        'ville': 'Dakar',
        'nb_niveaux': 8,
        'surface_emprise_m2': 350,
        'usage': 'residentiel',
        'classe_beton': 'C30/37',
    }
    pdf_bytes = generer_fiches_techniques(None, None, params, lang='fr')
    with open('/tmp/fiches_techniques_all_test.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print(f"PDF generated: {len(pdf_bytes)} bytes -> /tmp/fiches_techniques_all_test.pdf")

"""
gen_boq_structure.py — BOQ Structure détaillé standalone
Tijan AI — données 100% issues du moteur engine_structure_v2
Niveau de détail : consultable pour appel d'offres
Colonnes fourniture / pose séparées pour transparence coûts
"""
import io, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                  Spacer, PageBreak, KeepTogether)
from tijan_theme import *


# ── Ratios fourniture / pose par type de prestation ──────────
SPLIT_RATIOS = {
    'beton':              (0.75, 0.25),
    'acier':              (0.60, 0.40),
    'coffrage_bois':      (0.30, 0.70),
    'coffrage_metal':     (0.40, 0.60),
    'terr_mecanique':     (0.35, 0.65),
    'terr_manuel':        (0.15, 0.85),
    'remblai':            (0.50, 0.50),
    'evacuation':         (0.50, 0.50),
    'sable':              (0.50, 0.50),
    'pieux':              (0.55, 0.45),
    'fondation':          (0.55, 0.45),
    'maconnerie':         (0.50, 0.50),
    'enduits':            (0.35, 0.65),
    'etanch_sbs':         (0.60, 0.40),
    'etanch_pvc':         (0.60, 0.40),
    'etanch_liquide':     (0.55, 0.45),
    'ba13':               (0.45, 0.55),
    'escalier':           (0.65, 0.35),
    'forfait':            (0.50, 0.50),
    'honoraires':         (0.00, 1.00),
}


def _split(montant, ratio_key):
    """Split a total amount into (fourniture, pose) using predefined ratios."""
    r_f, r_p = SPLIT_RATIOS.get(ratio_key, (0.50, 0.50))
    f = int(montant * r_f)
    p_ = montant - f  # ensure fourn + pose = montant exactly
    return f, p_


def generer_boq_structure(rs, params: dict, lang: str = "fr") -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rs.params.nom, 'BOQ Structure — Détaillé')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    doc.build(_build(rs), onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _row(lot, desig, qte, unite, fourn, pose, total, note='', bold=False):
    st = 'td_b' if bold else 'td'
    st_r = 'td_b_r' if bold else 'td_r'
    st_g = 'td_g_r' if bold else 'td_r'
    return [p(lot, st), p(desig, st), p(str(qte) if qte != '' else '—', st_r),
            p(unite, st),
            p(fmt_fcfa(fourn) if fourn else '—', st_r),
            p(fmt_fcfa(pose) if pose else '—', st_r),
            p(fmt_fcfa(total) if total else '—', st_g),
            p(note, 'small')]

def _sous_total(desig, fourn, pose, total):
    return [p(''), p(desig, 'td_b'), p(''), p(''),
            p(fmt_fcfa(fourn), 'td_r'),
            p(fmt_fcfa(pose), 'td_r'),
            p(fmt_fcfa(total), 'td_g_r'), p('')]

def _build(rs):
    story = []
    d = rs.params
    boq = rs.boq
    poteaux = rs.poteaux
    poutre = rs.poutre_principale
    dalle = rs.dalle
    fond = rs.fondation
    cl = rs.cloisons

    # Tenter import prix
    try:
        from prix_marche import get_prix_structure
        px = get_prix_structure(d.ville)
    except:
        class _PX:
            beton_c2530_m3=170000; beton_c3037_m3=185000; beton_c3545_m3=210000
            acier_ha400_kg=750; acier_ha500_kg=810; coffrage_bois_m2=18000
            coffrage_metal_m2=25000; terr_mecanique_m3=8500; terr_manuel_m3=5000
            remblai_m3=6500; pieu_fore_d600_ml=220000; pieu_fore_d800_ml=285000
            pieu_fore_d1000_ml=360000; semelle_filante_ml=85000; radier_m2=95000
            agglo_creux_10_m2=18000; agglo_creux_15_m2=24000; agglo_creux_20_m2=30000
            agglo_plein_25_m2=38000; ba13_simple_m2=28000; ba13_double_m2=42000
            etanch_sbs_m2=18500; etanch_pvc_m2=22000; etanch_liquide_m2=12000
            mo_chef_chantier_j=35000; mo_macon_j=18000; mo_ferrailleur_j=20000
            mo_manœuvre_j=8000
        px = _PX()

    # Sélection prix béton selon classe
    prix_beton = {
        'C25/30': px.beton_c2530_m3, 'C30/37': px.beton_c3037_m3,
        'C35/45': px.beton_c3545_m3, 'C40/50': getattr(px,'beton_c4050_m3', 240000),
    }.get(rs.classe_beton, px.beton_c3037_m3)

    prix_acier = px.acier_ha400_kg if rs.classe_acier == 'HA400' else px.acier_ha500_kg

    nb_pot = (d.nb_travees_x + 1) * (d.nb_travees_y + 1)
    ep_dalle_m = dalle.epaisseur_mm / 1000
    surf_batie = boq.surface_batie_m2

    # ── EN-TÊTE ───────────────────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(d.nom, S['titre']))
    story.append(Paragraph(
        f'Bordereau des Quantités et des Prix — Structure — {d.ville} {rs.params.pays}',
        S['sous_titre']))
    story.append(Paragraph(
        f'R+{d.nb_niveaux-1} — {d.usage.value.capitalize()} — '
        f'Surface bâtie : {fmt_n(surf_batie,0,"m²")} — '
        f'Béton {rs.classe_beton} — Acier {rs.classe_acier}',
        S['body']))
    story.append(Paragraph(
        'Prix unitaires marché local 2026. Colonnes matériaux et installation séparées. Marge ±15%. '
        'Document utilisable pour consultation d\'entreprises.',
        S['note']))
    story.append(Spacer(1, 3*mm))

    # Colonnes BOQ — 8 colonnes avec fourniture / pose
    CW_COLS = [CW*w for w in [0.04, 0.30, 0.06, 0.05, 0.13, 0.13, 0.13, 0.16]]
    dl = devise_label()
    HEADERS = [p(h,'th') for h in [
        'Lot', 'Désignation', 'Qté', 'Unité',
        f'Matériaux ({dl})', f'Installation ({dl})', f'Total ({dl})', 'Observations']]

    def make_table(rows):
        t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
        ts = table_style()
        t.setStyle(ts)
        return t

    # Tracking fourniture / pose totals for recap
    recap_fourn = {}
    recap_pose = {}

    # ══════════════════════════════════════════════════════════
    # LOT 1 — INSTALLATION DE CHANTIER
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 1', 'INSTALLATION ET ORGANISATION DE CHANTIER')

    m_cloture = int(4*math.sqrt(d.surface_emprise_m2)*15000)
    m_base = int(surf_batie*800)
    m_branch = int(surf_batie*500)
    m_secu = int(surf_batie*300)
    m_repli = int(surf_batie*600)
    inst_forfait = m_cloture + m_base + m_branch + m_secu + m_repli

    f_clot, p_clot = _split(m_cloture, 'forfait')
    f_base, p_base = _split(m_base, 'forfait')
    f_bran, p_bran = _split(m_branch, 'forfait')
    f_secu, p_secu = _split(m_secu, 'forfait')
    f_repl, p_repl = _split(m_repli, 'forfait')
    f_inst = f_clot + f_base + f_bran + f_secu + f_repl
    p_inst = inst_forfait - f_inst

    rows_inst = [
        _row('1.1', 'Clôture de chantier (palissade bois ou tôle)', int(4*math.sqrt(d.surface_emprise_m2)), 'ml', f_clot, p_clot, m_cloture),
        _row('1.2', 'Base vie chantier (bureau, vestiaires, sanitaires)', 1, 'forfait', f_base, p_base, m_base, 'Modulaires démontables'),
        _row('1.3', 'Branchements provisoires eau + électricité', 1, 'forfait', f_bran, p_bran, m_branch),
        _row('1.4', 'Signalétique sécurité + EPI chantier', 1, 'forfait', f_secu, p_secu, m_secu),
        _row('1.5', 'Repli et nettoyage fin de chantier', 1, 'forfait', f_repl, p_repl, m_repli),
        _sous_total('SOUS-TOTAL LOT 1', f_inst, p_inst, inst_forfait),
    ]
    story.append(make_table(rows_inst))
    recap_fourn['lot1'] = f_inst
    recap_pose['lot1'] = p_inst

    # ══════════════════════════════════════════════════════════
    # LOT 2 — TERRASSEMENT
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 2', 'TERRASSEMENT GÉNÉRAL')
    V_decap = d.surface_emprise_m2 * 0.30
    V_fouilles = d.surface_emprise_m2 * (fond.profondeur_m + 0.50)
    V_remblai  = V_fouilles * 0.30
    V_evacu    = V_fouilles * 0.70

    m_decap = int(V_decap*px.terr_mecanique_m3)
    m_fouilles = int(V_fouilles*px.terr_mecanique_m3)
    m_fouilles_man = int(V_fouilles*0.10*px.terr_manuel_m3)
    m_remblai = int(V_remblai*px.remblai_m3)
    m_evacu = int(V_evacu*5000)
    m_sable = int(d.surface_emprise_m2*0.10*12000)

    f_decap, p_decap = _split(m_decap, 'terr_mecanique')
    f_fouilles, p_fouilles = _split(m_fouilles, 'terr_mecanique')
    f_fouilles_man, p_fouilles_man = _split(m_fouilles_man, 'terr_manuel')
    f_remblai, p_remblai = _split(m_remblai, 'remblai')
    f_evacu, p_evacu = _split(m_evacu, 'evacuation')
    f_sable, p_sable = _split(m_sable, 'sable')

    c_terr = m_decap + m_fouilles + m_remblai + m_evacu
    f_terr = f_decap + f_fouilles + f_fouilles_man + f_remblai + f_evacu + f_sable
    p_terr = (m_decap + m_fouilles + m_fouilles_man + m_remblai + m_evacu + m_sable) - f_terr
    c_terr_all = m_decap + m_fouilles + m_fouilles_man + m_remblai + m_evacu + m_sable

    rows_terr = [
        _row('2.1', 'Décapage terre végétale e=30cm', int(V_decap), 'm³', f_decap, p_decap, m_decap),
        _row('2.2', 'Fouilles générales mécaniques', int(V_fouilles), 'm³', f_fouilles, p_fouilles, m_fouilles, 'Engins mécaniques'),
        _row('2.3', 'Fouilles manuelles en fond de fouille', int(V_fouilles*0.10), 'm³', f_fouilles_man, p_fouilles_man, m_fouilles_man, 'Finitions manuelles'),
        _row('2.4', 'Remblai compacté (matériaux sélectionnés)', int(V_remblai), 'm³', f_remblai, p_remblai, m_remblai),
        _row('2.5', 'Évacuation terres excédentaires', int(V_evacu), 'm³', f_evacu, p_evacu, m_evacu, 'Transport + décharge agréée'),
        _row('2.6', 'Lit de sable sous dallage e=10cm', int(d.surface_emprise_m2*0.10), 'm³', f_sable, p_sable, m_sable),
        _sous_total('SOUS-TOTAL LOT 2', f_terr, p_terr, c_terr_all),
    ]
    story.append(make_table(rows_terr))
    recap_fourn['lot2'] = f_terr
    recap_pose['lot2'] = p_terr

    # ══════════════════════════════════════════════════════════
    # LOT 3 — FONDATIONS
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 3', 'FONDATIONS')
    story.append(Paragraph(
        f'Type : {fond.type.value} — Sol admissible : {d.pression_sol_MPa} MPa — '
        f'Justification : {fond.justification}', S['note']))
    story.append(Spacer(1, 2*mm))

    rows_fond = []
    c_fond = 0
    f_fond = 0
    p_fond = 0

    if fond.nb_pieux > 0:
        prix_pieu = {600: px.pieu_fore_d600_ml, 800: px.pieu_fore_d800_ml,
                     1000: px.pieu_fore_d1000_ml}.get(fond.diam_pieu_mm, px.pieu_fore_d800_ml)
        V_fond_beton = fond.nb_pieux * math.pi*(fond.diam_pieu_mm/1000/2)**2 * fond.longueur_pieu_m
        kg_fond_acier = fond.nb_pieux * fond.As_cm2/10000 * 7850 * fond.longueur_pieu_m
        c_pieux = int(fond.nb_pieux * fond.longueur_pieu_m * prix_pieu)
        c_longr = int(nb_pot * 6 * 85000)
        m_acier_fond = int(kg_fond_acier*prix_acier)
        m_proprete = int(nb_pot*0.5*0.5*0.10*120000)
        m_tete = int(nb_pot*120000)
        c_fond = c_pieux + c_longr + m_acier_fond + m_proprete + m_tete

        f_pieux, p_pieux = _split(c_pieux, 'pieux')
        f_acier_f, p_acier_f = _split(m_acier_fond, 'acier')
        f_proprete, p_proprete = _split(m_proprete, 'beton')
        f_longr, p_longr = _split(c_longr, 'fondation')
        f_tete, p_tete = _split(m_tete, 'fondation')

        f_fond = f_pieux + f_acier_f + f_proprete + f_longr + f_tete
        p_fond = c_fond - f_fond

        rows_fond = [
            _row('3.1', f'Pieux forés béton armé Ø{fond.diam_pieu_mm}mm — L={fond.longueur_pieu_m}m', int(fond.nb_pieux * fond.longueur_pieu_m), 'ml', f_pieux, p_pieux, c_pieux, f'{fond.nb_pieux} pieux × {fond.longueur_pieu_m}m'),
            _row('3.2', f'Armatures pieux HA500B — cage Ø{fond.diam_pieu_mm}mm', int(kg_fond_acier), 'kg', f_acier_f, p_acier_f, m_acier_fond, f'As={fond.As_cm2}cm² par pieu'),
            _row('3.3', f'Béton de propreté e=10cm sous longrines', int(nb_pot*0.5*0.5*0.10), 'm³', f_proprete, p_proprete, m_proprete),
            _row('3.4', f'Longrines béton armé {rs.classe_beton} — section 30×50cm', int(nb_pot * 6), 'ml', f_longr, p_longr, c_longr, 'Liaisons entre pieux'),
            _row('3.5', 'Tête de pieux + chapiteaux béton armé', nb_pot, 'U', f_tete, p_tete, m_tete, 'Connexion pieux-structure'),
            _sous_total('SOUS-TOTAL LOT 3', f_fond, p_fond, c_fond),
        ]
        story.append(Paragraph(
            f'ℹ Les fondations représentent {c_fond/boq.total_bas_fcfa*100:.0f}% du budget structure — '
            f'poste critique nécessitant une étude géotechnique préalable.',
            S['note']))
    elif fond.beton_semelle_m3 > 0:
        m_proprete2 = int(d.surface_emprise_m2*0.10*120000)
        m_semelle_bet = int(fond.beton_semelle_m3*0.6*prix_beton)
        m_semelle_acier = int(fond.beton_semelle_m3*100*prix_acier)
        m_semelle_coff = int(fond.beton_semelle_m3*2*px.coffrage_bois_m2)
        c_fond = m_proprete2 + m_semelle_bet + m_semelle_acier + m_semelle_coff

        f_prop2, p_prop2 = _split(m_proprete2, 'beton')
        f_sb, p_sb = _split(m_semelle_bet, 'beton')
        f_sa, p_sa = _split(m_semelle_acier, 'acier')
        f_sc, p_sc = _split(m_semelle_coff, 'coffrage_bois')

        f_fond = f_prop2 + f_sb + f_sa + f_sc
        p_fond = c_fond - f_fond

        rows_fond = [
            _row('3.1', 'Béton de propreté e=10cm', int(d.surface_emprise_m2*0.10), 'm³', f_prop2, p_prop2, m_proprete2),
            _row('3.2', f'Semelles béton armé {rs.classe_beton}', int(fond.beton_semelle_m3*0.6), 'm³', f_sb, p_sb, m_semelle_bet),
            _row('3.3', f'Armatures semelles {rs.classe_acier}', int(fond.beton_semelle_m3*100), 'kg', f_sa, p_sa, m_semelle_acier),
            _row('3.4', 'Coffrage semelles perdues', int(fond.beton_semelle_m3*2), 'm²', f_sc, p_sc, m_semelle_coff),
            _sous_total('SOUS-TOTAL LOT 3', f_fond, p_fond, c_fond),
        ]

    story.append(make_table(rows_fond))
    recap_fourn['lot3'] = f_fond
    recap_pose['lot3'] = p_fond

    # ══════════════════════════════════════════════════════════
    # LOT 4 — STRUCTURE BÉTON ARMÉ
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 4', f'STRUCTURE BÉTON ARMÉ — {rs.classe_beton} / {rs.classe_acier}')

    # 4.1 Poteaux niveau par niveau
    story.append(Paragraph('4.1 — Poteaux', S['h2']))
    rows_pot = [HEADERS]
    c_pot_total = 0
    f_pot_total = 0
    p_pot_total = 0
    for i, pt in enumerate(poteaux):
        b = pt.section_mm / 1000
        V_niv = b**2 * d.hauteur_etage_m * nb_pot
        As_niv = pt.nb_barres * math.pi * pt.diametre_mm**2 / 400 * nb_pot * d.hauteur_etage_m * 7850 / 10000
        c_beton_niv = int(V_niv * prix_beton)
        c_acier_niv = int(As_niv * prix_acier)
        c_coff_niv  = int(4 * b * d.hauteur_etage_m * nb_pot * px.coffrage_bois_m2)
        c_pot_niv   = c_beton_niv + c_acier_niv + c_coff_niv

        f_bn, p_bn = _split(c_beton_niv, 'beton')
        f_an, p_an = _split(c_acier_niv, 'acier')
        f_cn, p_cn = _split(c_coff_niv, 'coffrage_bois')
        f_pot_niv = f_bn + f_an + f_cn
        p_pot_niv = c_pot_niv - f_pot_niv

        c_pot_total += c_pot_niv
        f_pot_total += f_pot_niv
        p_pot_total += p_pot_niv
        rows_pot.append([
            p(f'4.1.{i+1}'),
            p(f'Poteaux {pt.niveau} — {pt.section_mm}×{pt.section_mm}mm — {pt.nb_barres}HA{pt.diametre_mm}'),
            p(f'{nb_pot}', 'td_r'), p('U'),
            p(fmt_fcfa(f_pot_niv), 'td_r'),
            p(fmt_fcfa(p_pot_niv), 'td_r'),
            p(fmt_fcfa(c_pot_niv), 'td_r'),
            p(f'NEd={pt.NEd_kN:.0f}kN | ρ={pt.taux_armature_pct:.1f}%', 'small'),
        ])
    rows_pot.append(_sous_total('Sous-total poteaux', f_pot_total, p_pot_total, c_pot_total))

    t_pot = Table(rows_pot, colWidths=CW_COLS, repeatRows=1)
    t_pot.setStyle(table_style())
    story.append(t_pot)

    # 4.2 Poutres
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.2 — Poutres', S['h2']))
    b_p = poutre.b_mm/1000; h_p = poutre.h_mm/1000
    L_px = d.nb_travees_x * d.portee_max_m * (d.nb_travees_y+1) * d.nb_niveaux
    L_py = d.nb_travees_y * d.portee_min_m * (d.nb_travees_x+1) * d.nb_niveaux
    V_pout = (L_px + L_py) * b_p * (h_p - ep_dalle_m)
    kg_pout = V_pout * 100
    c_pout_beton = int(V_pout * prix_beton)
    c_pout_acier = int(kg_pout * prix_acier)
    c_pout_coff  = int((L_px+L_py) * (b_p + 2*(h_p-ep_dalle_m)) * px.coffrage_bois_m2 * 0.6)
    c_pout_total = c_pout_beton + c_pout_acier + c_pout_coff

    m_pout_princ = int(c_pout_beton*L_px/(L_px+L_py))
    m_pout_sec = int(c_pout_beton*L_py/(L_px+L_py))

    f_pp, p_pp = _split(m_pout_princ, 'beton')
    f_ps, p_ps = _split(m_pout_sec, 'beton')
    f_pa, p_pa = _split(c_pout_acier, 'acier')
    f_pc, p_pc = _split(c_pout_coff, 'coffrage_bois')
    f_pout_total = f_pp + f_ps + f_pa + f_pc
    p_pout_total = c_pout_total - f_pout_total

    rows_pout = [
        HEADERS,
        _row('4.2.1', f'Poutres principales {poutre.b_mm}×{poutre.h_mm}mm — portée max {d.portee_max_m}m', int(L_px), 'ml', f_pp, p_pp, m_pout_princ, f'As inf={poutre.As_inf_cm2}cm² / As sup={poutre.As_sup_cm2}cm²'),
        _row('4.2.2', f'Poutres secondaires {poutre.b_mm}×{poutre.h_mm}mm — portée min {d.portee_min_m}m', int(L_py), 'ml', f_ps, p_ps, m_pout_sec),
        _row('4.2.3', f'Armatures poutres {rs.classe_acier} (façonnées + posées)', int(kg_pout), 'kg', f_pa, p_pa, c_pout_acier, f'Étriers HA{poutre.etrier_diam_mm} e={poutre.etrier_esp_mm}mm'),
        _row('4.2.4', 'Coffrage poutres (bois + étais)', int((L_px+L_py)*(b_p+2*(h_p-ep_dalle_m))*0.6), 'm²', f_pc, p_pc, c_pout_coff),
        _sous_total('Sous-total poutres', f_pout_total, p_pout_total, c_pout_total),
    ]
    t_pout = Table(rows_pout, colWidths=CW_COLS, repeatRows=1)
    t_pout.setStyle(table_style())
    story.append(t_pout)

    # 4.3 Dalles
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.3 — Dalles', S['h2']))
    V_dalles = surf_batie * ep_dalle_m * 0.85
    kg_dalles = V_dalles * 80
    c_dalle_beton = int(V_dalles * prix_beton)
    c_dalle_acier = int(kg_dalles * prix_acier)
    c_dalle_coff  = int(surf_batie * 0.85 * px.coffrage_bois_m2)
    m_etai = int(surf_batie*0.85*3500)
    m_reserv = int(surf_batie*500)
    c_dalle_total = c_dalle_beton + c_dalle_acier + c_dalle_coff

    f_db, p_db = _split(c_dalle_beton, 'beton')
    f_da, p_da = _split(c_dalle_acier, 'acier')
    f_dc, p_dc = _split(c_dalle_coff, 'coffrage_bois')
    f_de, p_de = _split(m_etai, 'forfait')
    f_dr, p_dr = _split(m_reserv, 'forfait')
    f_dalle_total = f_db + f_da + f_dc + f_de + f_dr
    p_dalle_total = (c_dalle_total + m_etai + m_reserv) - f_dalle_total

    rows_dalles = [
        HEADERS,
        _row('4.3.1', f'Béton dalles {rs.classe_beton} BPE e={dalle.epaisseur_mm}mm', int(V_dalles), 'm³', f_db, p_db, c_dalle_beton, f'As_x={dalle.As_x_cm2_ml}cm²/ml / As_y={dalle.As_y_cm2_ml}cm²/ml'),
        _row('4.3.2', f'Armatures dalles {rs.classe_acier} — HA10 deux sens', int(kg_dalles), 'kg', f_da, p_da, c_dalle_acier, 'Treillis soudé + renforts'),
        _row('4.3.3', 'Coffrage dalles (banches métalliques)', int(surf_batie*0.85), 'm²', f_dc, p_dc, c_dalle_coff),
        _row('4.3.4', 'Étaiement provisoire (échafaudages)', int(surf_batie*0.85), 'm²', f_de, p_de, m_etai, 'Location + main d\'œuvre'),
        _row('4.3.5', 'Réservations trémies (gaines, escaliers)', 1, 'forfait', f_dr, p_dr, m_reserv, 'Estimation 0.5% SHOB'),
        _sous_total('Sous-total dalles', f_db+f_da+f_dc+f_de+f_dr, p_dalle_total, c_dalle_total + m_etai + m_reserv),
    ]
    t_dalles = Table(rows_dalles, colWidths=CW_COLS, repeatRows=1)
    t_dalles.setStyle(table_style())
    story.append(t_dalles)

    # 4.4 Escaliers
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('4.4 — Escaliers', S['h2']))
    nb_esc = max(1, int(surf_batie/1500))
    c_esc = int(nb_esc * d.nb_niveaux * 450000)
    m_garde = int(nb_esc*d.nb_niveaux*3*45000)
    c_esc_total = c_esc + m_garde

    f_esc, p_esc = _split(c_esc, 'escalier')
    f_garde, p_garde = _split(m_garde, 'forfait')
    f_esc_total = f_esc + f_garde
    p_esc_total = c_esc_total - f_esc_total

    rows_esc = [
        HEADERS,
        _row('4.4.1', f'Escaliers béton armé {rs.classe_beton} — volée + paliers', nb_esc * d.nb_niveaux, 'volée', f_esc, p_esc, c_esc, f'{nb_esc} cage(s) × {d.nb_niveaux} niveaux'),
        _row('4.4.2', 'Garde-corps béton/métal escaliers', nb_esc * d.nb_niveaux * 3, 'ml', f_garde, p_garde, m_garde),
        _sous_total('Sous-total escaliers', f_esc_total, p_esc_total, c_esc_total),
    ]
    t_esc = Table(rows_esc, colWidths=CW_COLS, repeatRows=1)
    t_esc.setStyle(table_style())
    story.append(t_esc)

    # Lot 4 recap tracking (all sub-lots)
    f_lot4 = f_pot_total + f_pout_total + f_dalle_total + f_esc_total
    p_lot4 = p_pot_total + p_pout_total + p_dalle_total + p_esc_total
    c_lot4 = c_pot_total + c_pout_total + c_dalle_total + m_etai + m_reserv + c_esc_total
    recap_fourn['lot4'] = f_lot4
    recap_pose['lot4'] = p_lot4

    # ══════════════════════════════════════════════════════════
    # LOT 5 — MAÇONNERIE ET CLOISONS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT 5', 'MAÇONNERIE, CLOISONS ET ENDUITS')
    cl = rs.cloisons
    opt_rec = next((o for o in cl.options if o.type == cl.option_recommandee), cl.options[0])

    rows_maco = [HEADERS]
    c_maco_total = 0
    f_maco_total = 0

    # Façades extérieures
    surf_facades = 4 * math.sqrt(d.surface_emprise_m2) * d.nb_niveaux * d.hauteur_etage_m * 0.70
    c_fac = int(surf_facades * px.agglo_plein_25_m2)
    f_fac, p_fac = _split(c_fac, 'maconnerie')
    rows_maco.append(_row('5.1', 'Maçonnerie façades extérieures — agglos pleins 25cm',
        int(surf_facades), 'm²', f_fac, p_fac, c_fac, 'Murs périphériques enduits 2 faces'))
    c_maco_total += c_fac
    f_maco_total += f_fac

    # Cloisons séparatives
    c_sep = int(cl.surface_separative_m2 * opt_rec.prix_fcfa_m2)
    f_sep, p_sep = _split(c_sep, 'maconnerie')
    rows_maco.append(_row('5.2', f'Cloisons séparatives — {opt_rec.materiau[:40]}',
        int(cl.surface_separative_m2), 'm²', f_sep, p_sep, c_sep,
        f'Option recommandée — {opt_rec.usage_recommande[:35]}'))
    c_maco_total += c_sep
    f_maco_total += f_sep

    # Cloisons légères intérieures
    prix_leger = px.ba13_simple_m2
    c_leg = int(cl.surface_legere_m2 * prix_leger)
    f_leg, p_leg = _split(c_leg, 'ba13')
    rows_maco.append(_row('5.3', 'Cloisons légères intérieures — BA13 simple rail',
        int(cl.surface_legere_m2), 'm²', f_leg, p_leg, c_leg, 'Cloisons intérieures non séparatives'))
    c_maco_total += c_leg
    f_maco_total += f_leg

    # Gaines techniques
    c_gaines = int(cl.surface_gaines_m2 * px.beton_c3037_m3 * 0.20)
    f_gaines, p_gaines = _split(c_gaines, 'beton')
    rows_maco.append(_row('5.4', 'Gaines techniques — béton armé coulé 20cm',
        int(cl.surface_gaines_m2), 'm²', f_gaines, p_gaines, c_gaines,
        'Gaines ascenseurs + colonnes montantes'))
    c_maco_total += c_gaines
    f_maco_total += f_gaines

    # Enduits
    surf_enduit = (surf_facades + cl.surface_separative_m2) * 2
    c_end = int(surf_enduit * 8500)
    f_end, p_end = _split(c_end, 'enduits')
    rows_maco.append(_row('5.5', 'Enduits ciment + plâtre intérieur/extérieur',
        int(surf_enduit), 'm²', f_end, p_end, c_end, 'Finitions surfaces maçonnées'))
    c_maco_total += c_end
    f_maco_total += f_end

    # Acrotères
    perim = 4 * math.sqrt(d.surface_emprise_m2)
    c_acrot = int(perim * 35000)
    f_acrot, p_acrot = _split(c_acrot, 'beton')
    rows_maco.append(_row('5.6', 'Acrotères béton armé h=60cm en toiture',
        int(perim), 'ml', f_acrot, p_acrot, c_acrot))
    c_maco_total += c_acrot
    f_maco_total += f_acrot

    p_maco_total = c_maco_total - f_maco_total
    rows_maco.append(_sous_total('SOUS-TOTAL LOT 5', f_maco_total, p_maco_total, c_maco_total))

    # Note options cloisons
    story.append(Paragraph(
        'ℹ Plusieurs options de cloisons disponibles selon budget et usage. '
        'Voir note de calcul structure pour détail comparatif.',
        S['note']))
    t_maco = Table(rows_maco, colWidths=CW_COLS, repeatRows=1)
    t_maco.setStyle(table_style())
    story.append(t_maco)
    recap_fourn['lot5'] = f_maco_total
    recap_pose['lot5'] = p_maco_total

    # ══════════════════════════════════════════════════════════
    # LOT 6 — ÉTANCHÉITÉ ET ISOLATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 6', 'ÉTANCHÉITÉ ET ISOLATION')
    surf_etanch = d.surface_emprise_m2
    c_sbs  = int(surf_etanch * px.etanch_sbs_m2)
    c_prot = int(surf_etanch * 5000)
    c_dallettes = int(surf_etanch*0.40*8000)
    c_ss_sol = int(d.surface_emprise_m2 * 0.30 * px.etanch_pvc_m2) if d.avec_sous_sol else 0
    c_salles = int(surf_batie * 0.08 * px.etanch_liquide_m2)
    c_etanch_total = c_sbs + c_prot + c_dallettes + c_ss_sol + c_salles

    f_sbs, p_sbs = _split(c_sbs, 'etanch_sbs')
    f_prot, p_prot = _split(c_prot, 'forfait')
    f_dall, p_dall = _split(c_dallettes, 'forfait')
    f_sal, p_sal = _split(c_salles, 'etanch_liquide')
    f_etanch = f_sbs + f_prot + f_dall + f_sal
    if d.avec_sous_sol:
        f_ss, p_ss = _split(c_ss_sol, 'etanch_pvc')
        f_etanch += f_ss
    p_etanch = c_etanch_total - f_etanch

    rows_etanch = [
        HEADERS,
        _row('6.1', 'Étanchéité toiture-terrasse SBS bicouche (primaire + 2 couches)', int(surf_etanch), 'm²', f_sbs, p_sbs, c_sbs, 'Soudage à la flamme — DTU 43.1'),
        _row('6.2', 'Protection étanchéité — chape de protection e=5cm', int(surf_etanch), 'm²', f_prot, p_prot, c_prot),
        _row('6.3', 'Dallettes béton sur plots (toiture accessible)', int(surf_etanch*0.40), 'm²', f_dall, p_dall, c_dallettes, '40% toiture accessible'),
        _row('6.4', 'Étanchéité salles de bains + locaux humides', int(surf_batie*0.08), 'm²', f_sal, p_sal, c_salles, 'Résine monocomposant'),
    ]
    if d.avec_sous_sol:
        rows_etanch.append(_row('6.5', 'Étanchéité sous-sol (membrane PVC)', int(d.surface_emprise_m2), 'm²', f_ss, p_ss, c_ss_sol, 'Cuvelage intérieur'))
    rows_etanch.append(_sous_total('SOUS-TOTAL LOT 6', f_etanch, p_etanch, c_etanch_total))

    t_etanch = Table(rows_etanch, colWidths=CW_COLS, repeatRows=1)
    t_etanch.setStyle(table_style())
    story.append(t_etanch)
    recap_fourn['lot6'] = f_etanch
    recap_pose['lot6'] = p_etanch

    # ══════════════════════════════════════════════════════════
    # LOT 7 — DIVERS ET IMPRÉVUS
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT 7', 'DIVERS, IMPRÉVUS ET HONORAIRES TECHNIQUES')
    sous_tot_travaux = (inst_forfait + c_terr_all + c_fond + c_pot_total +
                        c_pout_total + c_dalle_total + m_etai + m_reserv +
                        c_esc_total + c_maco_total + c_etanch_total)
    m_joints = int(surf_batie/500*850000)
    m_reserv7 = int(surf_batie*800)
    c_impr  = int(sous_tot_travaux * 0.05)
    c_bet   = int(sous_tot_travaux * 0.04)
    c_ctrl  = int(sous_tot_travaux * 0.015)
    c_div_total = m_joints + m_reserv7 + c_impr + c_bet + c_ctrl

    f_joints, p_joints = _split(m_joints, 'forfait')
    f_res7, p_res7 = _split(m_reserv7, 'forfait')
    f_impr, p_impr = _split(c_impr, 'forfait')
    f_bet, p_bet = _split(c_bet, 'honoraires')
    f_ctrl, p_ctrl = _split(c_ctrl, 'honoraires')
    f_div = f_joints + f_res7 + f_impr + f_bet + f_ctrl
    p_div = c_div_total - f_div

    rows_div = [
        HEADERS,
        _row('7.1', 'Joints de dilatation (tous niveaux)', int(surf_batie/500), 'U', f_joints, p_joints, m_joints, '1 joint / 500m² environ'),
        _row('7.2', 'Réservations et scellements divers', 1, 'forfait', f_res7, p_res7, m_reserv7, 'Gaines électriques, plomberie'),
        _row('7.3', 'Imprévus chantier (5% travaux)', 1, 'forfait', f_impr, p_impr, c_impr, 'Aléas et adaptations'),
        _row('7.4', 'Honoraires BET structure (4% travaux)', 1, 'forfait', f_bet, p_bet, c_bet, 'Plans d\'exécution + suivi'),
        _row('7.5', 'Contrôle technique (1.5% travaux)', 1, 'forfait', f_ctrl, p_ctrl, c_ctrl, 'Organisme agréé obligatoire'),
        _sous_total('SOUS-TOTAL LOT 7', f_div, p_div, c_div_total),
    ]

    t_div = Table(rows_div, colWidths=CW_COLS, repeatRows=1)
    t_div.setStyle(table_style())
    story.append(t_div)
    recap_fourn['lot7'] = f_div
    recap_pose['lot7'] = p_div

    # ══════════════════════════════════════════════════════════
    # RÉCAPITULATIF GÉNÉRAL
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('RÉCAP', 'RÉCAPITULATIF GÉNÉRAL')

    total_ht  = (inst_forfait + c_terr_all + c_fond + c_lot4 +
                 c_maco_total + c_etanch_total + c_div_total)
    total_fourn = sum(recap_fourn.values())
    total_pose = total_ht - total_fourn
    total_bas = int(total_ht * 0.95)
    total_haut = int(total_ht * 1.15)

    lot_data = [
        ('1', 'Installation de chantier', inst_forfait),
        ('2', 'Terrassement', c_terr_all),
        ('3', 'Fondations', c_fond),
        ('4', 'Structure béton armé (poteaux + poutres + dalles + escaliers)', c_lot4),
        ('5', 'Maçonnerie et cloisons', c_maco_total),
        ('6', 'Étanchéité et isolation', c_etanch_total),
        ('7', 'Divers + honoraires techniques', c_div_total),
    ]

    recap_rows = [
        [p('LOT','th'), p('DÉSIGNATION','th_l'),
         p(f'FOURNITURE ({dl})','th'), p(f'POSE ({dl})','th'),
         p(f'TOTAL ({dl})','th'), p('% TOTAL','th')],
    ]
    for num, desig, total_lot in lot_data:
        f_lot = recap_fourn.get(f'lot{num}', 0)
        p_lot = recap_pose.get(f'lot{num}', 0)
        recap_rows.append([
            p(num, 'td_b'), p(desig),
            p(fmt_fcfa(f_lot), 'td_r'),
            p(fmt_fcfa(p_lot), 'td_r'),
            p(fmt_fcfa(total_lot), 'td_r'),
            p(f'{total_lot/total_ht*100:.1f}%', 'td_r'),
        ])

    recap_rows.append([p('','td_b'), p('TOTAL ESTIMATIF HT','td_b'),
                       p(fmt_fcfa(total_fourn),'td_r'), p(fmt_fcfa(total_pose),'td_r'),
                       p(fmt_fcfa(total_ht),'td_g_r'), p('100%','td_b')])
    recap_rows.append([p('','td_b'), p('% Matériaux / Installation','td_b'),
                       p(f'{total_fourn/total_ht*100:.0f}%','td_r'), p(f'{total_pose/total_ht*100:.0f}%','td_r'),
                       p('','td_r'), p('','td_b')])
    recap_rows.append([p('','td_b'), p('FOURCHETTE BASSE (-5%)','td_b'),
                       p('','td_r'), p('','td_r'),
                       p(fmt_fcfa(total_bas),'td_g_r'), p('','td_b')])
    recap_rows.append([p('','td_b'), p('FOURCHETTE HAUTE (+15%)','td_b'),
                       p('','td_r'), p('','td_r'),
                       p(fmt_fcfa(total_haut),'td_g_r'), p('','td_b')])

    tr = Table(recap_rows, colWidths=[CW*0.06, CW*0.38, CW*0.16, CW*0.16, CW*0.16, CW*0.08], repeatRows=1)
    ts_r = table_style(zebra=False)
    ts_r.add('BACKGROUND', (0,-3), (-1,-1), VERT_LIGHT)
    ts_r.add('FONTNAME',   (0,-3), (-1,-1), 'Helvetica-Bold')
    ts_r.add('LINEABOVE',  (0,-3), (-1,-3), 1.5, VERT)
    tr.setStyle(ts_r)
    story.append(tr)

    # Ratios
    story.append(Spacer(1, 3*mm))
    rat_data = [
        [p('INDICATEUR','th'), p('VALEUR','th'), p('RÉFÉRENCE MARCHÉ','th')],
        [p('Surface bâtie totale','td_b'), p(f'{fmt_n(surf_batie,0)} m²'), p(f'Emprise {int(d.surface_emprise_m2)} m² × {d.nb_niveaux} niveaux')],
        [p('Coût total / m² bâti','td_b'), p(f'{int(total_ht/surf_batie):,} FCFA/m²'.replace(',', ' ')), p('Résidentiel Dakar : 80 000–160 000 FCFA/m²')],
        [p('Coût béton armé / m² bâti','td_b'), p(f'{int(c_lot4/surf_batie):,} FCFA/m²'.replace(',', ' ')), p('Ratio béton + acier + coffrage')],
        [p('Fondations / total structure','td_b'), p(f'{c_fond/total_ht*100:.1f}%'), p('Normal : 15–25% (fondations profondes)')],
        [p('Ratio acier','td_b'), p(f'{int(boq.acier_kg/surf_batie)} kg/m²'), p('Référence EDGE : 40 kg/m²')],
        [p('Ratio matériaux / installation','td_b'), p(f'{total_fourn/total_ht*100:.0f}% / {total_pose/total_ht*100:.0f}%'), p('Référence marché : 45–55% / 55–45%')],
    ]
    tr2 = Table(rat_data, colWidths=[CW*0.35, CW*0.25, CW*0.40], repeatRows=1)
    tr2.setStyle(table_style())
    story.append(tr2)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '* Ce BOQ est une estimation d\'avant-projet (±15%). Les quantités sont calculées depuis le '
        'dimensionnement EC2/EC8 et les ratios validés pour le marché local. '
        'Les ratios matériaux/installation sont indicatifs et peuvent varier selon les entreprises. '
        'Un métré définitif sur plans d\'exécution est requis avant appel d\'offres.',
        S['disc']))

    return story

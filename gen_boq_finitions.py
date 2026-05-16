"""
gen_boq_finitions.py — BOQ Finitions Tijan AI
═══════════════════════════════════════════════
3 gammes: Basic, High-End, Luxury
6 postes: carrelage, menuiserie int/ext, faux-plafond, peinture, cuisine
Prix par ville (5 marchés) — cohérent avec prix_marche.py
Format BPU : N° | Désignation | Unité | Quantité | Basic | High-End | Luxury
"""
import io, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer, PageBreak
from tijan_theme import *

FINITIONS_DB = {
    "carrelage": {
        "basic": {
            "description": "Grès cérame local 30x30, pose incluse",
            "marques": "Kédia Céramique (SN), Carrelages CI (CI), Super Cérame (MA), Goodwill (NG)",
            "prix_m2": {"Dakar": 18000, "Abidjan": 16000, "Casablanca": 20000, "Lagos": 22000, "default": 18000}
        },
        "high_end": {
            "description": "Grès cérame importé 60x60, pose incluse",
            "marques": "Porcelanosa, RAK Ceramics, Marazzi, Kajaria",
            "prix_m2": {"Dakar": 45000, "Abidjan": 42000, "Casablanca": 50000, "Lagos": 55000, "default": 45000}
        },
        "luxury": {
            "description": "Marbre ou grands formats 80x80+, pose incluse",
            "marques": "Cosentino, Iris Ceramica, ABK, marbre Carrare/Calacatta",
            "prix_m2": {"Dakar": 95000, "Abidjan": 90000, "Casablanca": 110000, "Lagos": 120000, "default": 95000}
        },
        "ratio_plancher": 1.0
    },
    "menuiserie_interieure": {
        "basic": {
            "description": "Portes bois MDF, huisseries métalliques",
            "marques": "Menuiseries locales, Fabrimetal (SN), SIPAM (CI), Vitfoam (NG)",
            "prix_porte": {"Dakar": 85000, "Abidjan": 80000, "Casablanca": 95000, "Lagos": 100000, "default": 85000}
        },
        "high_end": {
            "description": "Portes bois massif prépeint, huisseries alu",
            "marques": "Lapeyre, Jeld-Wen, Righini, Garofoli",
            "prix_porte": {"Dakar": 180000, "Abidjan": 170000, "Casablanca": 200000, "Lagos": 220000, "default": 180000}
        },
        "luxury": {
            "description": "Portes bois noble teck/iroko, huisseries alu anodisé",
            "marques": "Oikos, Lualdi, Rimadesio, ébénistes sur mesure",
            "prix_porte": {"Dakar": 380000, "Abidjan": 360000, "Casablanca": 420000, "Lagos": 450000, "default": 380000}
        },
        "nb_portes_par_100m2": 4.5
    },
    "menuiserie_exterieure": {
        "basic": {
            "description": "Aluminium laqué standard, simple vitrage",
            "marques": "Technal Afrique, SNVA (SN), Aluminium CI, First Aluminium (NG)",
            "prix_m2": {"Dakar": 95000, "Abidjan": 90000, "Casablanca": 105000, "Lagos": 110000, "default": 95000}
        },
        "high_end": {
            "description": "Aluminium thermolaqué, double vitrage",
            "marques": "Schüco, Reynaers, SAPA/Hydro, Aluk",
            "prix_m2": {"Dakar": 185000, "Abidjan": 175000, "Casablanca": 210000, "Lagos": 220000, "default": 185000}
        },
        "luxury": {
            "description": "Aluminium sur mesure, double vitrage feuilleté, stores intégrés",
            "marques": "Schüco AWS, Wicona, Kawneer, Cortizo — stores Somfy",
            "prix_m2": {"Dakar": 380000, "Abidjan": 360000, "Casablanca": 420000, "Lagos": 450000, "default": 380000}
        },
        "ratio_facade": 0.18
    },
    "faux_plafond": {
        "basic": {
            "description": "Dalles BA13 sur ossature métallique",
            "marques": "Knauf, Placo/Saint-Gobain, Siniat, Gyproc",
            "prix_m2": {"Dakar": 22000, "Abidjan": 20000, "Casablanca": 25000, "Lagos": 28000, "default": 22000}
        },
        "high_end": {
            "description": "Plâtre staff décoratif, corniche, spots encastrés",
            "marques": "Armstrong, Hunter Douglas, Barrisol — spots Philips/Osram",
            "prix_m2": {"Dakar": 48000, "Abidjan": 45000, "Casablanca": 55000, "Lagos": 60000, "default": 48000}
        },
        "luxury": {
            "description": "Bois ou métal sur mesure, éclairage LED intégré",
            "marques": "Hunter Douglas (bois), Lindner, Fantoni — LED iGuzzini/Flos",
            "prix_m2": {"Dakar": 110000, "Abidjan": 105000, "Casablanca": 125000, "Lagos": 135000, "default": 110000}
        },
        "ratio_plancher": 0.75
    },
    "peinture": {
        "basic": {
            "description": "Peinture vinylique mate standard, 2 couches",
            "marques": "Seigneurie, Prestige Peintures (SN), Colpaint (CI), CAP (NG)",
            "prix_m2": {"Dakar": 4500, "Abidjan": 4000, "Casablanca": 5000, "Lagos": 5500, "default": 4500}
        },
        "high_end": {
            "description": "Peinture acrylique premium lessivable, 3 couches",
            "marques": "Tollens, Dulux Valentine, Jotun, Sigma Coatings",
            "prix_m2": {"Dakar": 9000, "Abidjan": 8500, "Casablanca": 10000, "Lagos": 11000, "default": 9000}
        },
        "luxury": {
            "description": "Enduit décoratif, béton ciré ou stucco vénitien",
            "marques": "Oikos, Novacolor, Viero, Beal — micro-ciment Topciment",
            "prix_m2": {"Dakar": 22000, "Abidjan": 20000, "Casablanca": 25000, "Lagos": 28000, "default": 22000}
        },
        "ratio_murs": 2.8,
        "ratio_plafond": 1.0
    },
    "cuisine": {
        "basic": {
            "description": "Meubles mélaminé, plan stratifié, évier inox",
            "marques": "Menuisiers locaux, IKEA (MA), Kitea (MA), Mobalpa entrée de gamme",
            "prix_ml": {"Dakar": 180000, "Abidjan": 170000, "Casablanca": 200000, "Lagos": 220000, "default": 180000}
        },
        "high_end": {
            "description": "Meubles MDF laqué, plan granit, électroménager inclus",
            "marques": "Schmidt, SieMatic, Nobilia — élec. Bosch/Siemens",
            "prix_ml": {"Dakar": 450000, "Abidjan": 420000, "Casablanca": 500000, "Lagos": 550000, "default": 450000}
        },
        "luxury": {
            "description": "Meubles sur mesure bois massif, plan quartz, électroménager premium",
            "marques": "Boffi, Poggenpohl, Poliform — élec. Miele/Sub-Zero/Gaggenau",
            "prix_ml": {"Dakar": 1200000, "Abidjan": 1100000, "Casablanca": 1400000, "Lagos": 1500000, "default": 1200000}
        },
        "ml_par_100m2": 2.5
    }
}


def calculer_finitions(surface_emprise_m2: float, nb_niveaux: int, ville: str) -> dict:
    """Calcule les finitions pour 3 gammes. Retourne dict avec basic/high_end/luxury."""
    v = ville if ville in ["Dakar", "Abidjan", "Casablanca", "Lagos"] else "default"
    surface_totale = surface_emprise_m2 * nb_niveaux
    perimetre = 4 * math.sqrt(surface_emprise_m2)
    surface_facade = perimetre * nb_niveaux * 3.0  # hauteur étage 3m

    results = {}
    for gamme in ["basic", "high_end", "luxury"]:
        db = FINITIONS_DB
        detail = {}

        # Carrelage
        q_carrelage = surface_totale * db["carrelage"]["ratio_plancher"]
        carrelage = q_carrelage * db["carrelage"][gamme]["prix_m2"][v]
        detail["carrelage"] = {"montant": round(carrelage), "quantite": round(q_carrelage), "unite": "m²",
                               "pu": db["carrelage"][gamme]["prix_m2"][v],
                               "description": db["carrelage"][gamme]["description"],
                               "marques": db["carrelage"][gamme]["marques"]}

        # Menuiserie intérieure
        nb_portes = (surface_totale / 100) * db["menuiserie_interieure"]["nb_portes_par_100m2"]
        menu_int = nb_portes * db["menuiserie_interieure"][gamme]["prix_porte"][v]
        detail["menuiserie_interieure"] = {"montant": round(menu_int), "quantite": round(nb_portes), "unite": "U",
                                           "pu": db["menuiserie_interieure"][gamme]["prix_porte"][v],
                                           "description": db["menuiserie_interieure"][gamme]["description"],
                                           "marques": db["menuiserie_interieure"][gamme]["marques"]}

        # Menuiserie extérieure
        surface_vitrages = surface_facade * db["menuiserie_exterieure"]["ratio_facade"]
        menu_ext = surface_vitrages * db["menuiserie_exterieure"][gamme]["prix_m2"][v]
        detail["menuiserie_exterieure"] = {"montant": round(menu_ext), "quantite": round(surface_vitrages), "unite": "m²",
                                           "pu": db["menuiserie_exterieure"][gamme]["prix_m2"][v],
                                           "description": db["menuiserie_exterieure"][gamme]["description"],
                                           "marques": db["menuiserie_exterieure"][gamme]["marques"]}

        # Faux-plafond
        q_fp = surface_totale * db["faux_plafond"]["ratio_plancher"]
        fp = q_fp * db["faux_plafond"][gamme]["prix_m2"][v]
        detail["faux_plafond"] = {"montant": round(fp), "quantite": round(q_fp), "unite": "m²",
                                  "pu": db["faux_plafond"][gamme]["prix_m2"][v],
                                  "description": db["faux_plafond"][gamme]["description"],
                                  "marques": db["faux_plafond"][gamme]["marques"]}

        # Peinture
        surface_peinte = surface_totale * (db["peinture"]["ratio_murs"] + db["peinture"]["ratio_plafond"])
        peinture = surface_peinte * db["peinture"][gamme]["prix_m2"][v]
        detail["peinture"] = {"montant": round(peinture), "quantite": round(surface_peinte), "unite": "m²",
                              "pu": db["peinture"][gamme]["prix_m2"][v],
                              "description": db["peinture"][gamme]["description"],
                              "marques": db["peinture"][gamme]["marques"]}

        # Cuisine
        ml_cuisine = (surface_totale / 100) * db["cuisine"]["ml_par_100m2"]
        cuisine = ml_cuisine * db["cuisine"][gamme]["prix_ml"][v]
        detail["cuisine"] = {"montant": round(cuisine), "quantite": round(ml_cuisine, 1), "unite": "ml",
                             "pu": db["cuisine"][gamme]["prix_ml"][v],
                             "description": db["cuisine"][gamme]["description"],
                             "marques": db["cuisine"][gamme]["marques"]}

        total = sum(d["montant"] for d in detail.values())
        results[gamme] = {"total": round(total), "detail": detail}

    return results


def _row(lot, desig, unite, qte, pu_b, pu_h, pu_l):
    """7-column row: N° | Désignation | Unité | Qté | Basic | High-End | Luxury"""
    return [
        p(lot), p(desig),
        p(unite),
        p(str(qte) if qte != '' else '—', 'td_r'),
        p(fmt_fcfa(pu_b) if pu_b else '—', 'td_r'),
        p(fmt_fcfa(pu_h) if pu_h else '—', 'td_r'),
        p(fmt_fcfa(pu_l) if pu_l else '—', 'td_r'),
    ]

def _sous_total(desig, c_b, c_h, c_l):
    return [p(''), p(desig, 'td_b'), p(''), p(''),
            p(fmt_fcfa(c_b), 'td_g_r'), p(fmt_fcfa(c_h), 'td_g_r'), p(fmt_fcfa(c_l), 'td_g_r')]


def generer_boq_finitions_pdf(output_path: str, resultats_finitions: dict, params: dict) -> str:
    """Génère le PDF BOQ Finitions avec le format BPU harmonisé."""
    buf = io.BytesIO()
    nom = params.get("nom", "Projet")
    ville = params.get("ville", "Dakar")

    hf = HeaderFooter(nom, 'BOQ Finitions — 3 Gammes')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)

    story = []

    # En-tête
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(nom, S['titre']))
    story.append(Paragraph(f'Bordereau Finitions — {ville} — 3 gammes de finition', S['sous_titre']))
    story.append(Paragraph(
        'Prix unitaires marché local 2026 — fournis posés — marge ±15%. '
        'Document utilisable pour consultation d\'entreprises.',
        S['note']))
    story.append(Spacer(1, 3*mm))

    # 7 colonnes BPU
    dl = devise_label()
    CW_COLS = [CW*w for w in [0.05, 0.29, 0.05, 0.05, 0.16, 0.16, 0.16]]
    HEADERS = [p(h,'th') for h in [
        'N°', 'Désignation', 'Unité', 'Qté',
        f'Basic ({dl})', f'High-End ({dl})', f'Luxury ({dl})'
    ]]

    poste_config = [
        ("F.1", "carrelage", "Carrelage"),
        ("F.2", "menuiserie_interieure", "Menuiserie intérieure"),
        ("F.3", "menuiserie_exterieure", "Menuiserie extérieure"),
        ("F.4", "faux_plafond", "Faux-plafond"),
        ("F.5", "peinture", "Peinture"),
        ("F.6", "cuisine", "Cuisine équipée"),
    ]

    basic = resultats_finitions.get("basic", {})
    high_end = resultats_finitions.get("high_end", {})
    luxury = resultats_finitions.get("luxury", {})

    rows = []
    for num, key, label in poste_config:
        d_b = basic.get("detail", {}).get(key, {})
        d_h = high_end.get("detail", {}).get(key, {})
        d_l = luxury.get("detail", {}).get(key, {})

        # Use basic quantities (same for all tiers)
        qte = d_b.get("quantite", 0)
        unite = d_b.get("unite", "")
        desc = d_b.get("description", label)

        # Build description with all tier descriptions
        desc_b = d_b.get("description", "")
        desc_h = d_h.get("description", "")
        desc_l = d_l.get("description", "")
        full_desc = f'{label} — {desc_b}'

        rows.append(_row(num, full_desc, unite, int(qte) if isinstance(qte, (int, float)) and qte == int(qte) else qte,
                         d_b.get("montant", 0), d_h.get("montant", 0), d_l.get("montant", 0)))

    # Totaux
    rows.append(_sous_total('TOTAL FINITIONS',
                            basic.get("total", 0),
                            high_end.get("total", 0),
                            luxury.get("total", 0)))

    t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
    t.setStyle(table_style())
    story.append(t)

    # Ratio /m²
    surf = params.get("surface_emprise_m2", 0) * params.get("nb_niveaux", 1)
    if surf > 0:
        story.append(Spacer(1, 3*mm))
        ratio_b = int(basic.get("total", 0) / surf)
        ratio_h = int(high_end.get("total", 0) / surf)
        ratio_l = int(luxury.get("total", 0) / surf)
        story.append(Paragraph(
            f'Ratio finitions / m² bâti ({fmt_n(surf,0)} m²) : '
            f'Basic {ratio_b:,} FCFA/m² — High-End {ratio_h:,} FCFA/m² — Luxury {ratio_l:,} FCFA/m²'.replace(',', ' '),
            S['note']))

    # Détail marques par poste
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Détail des gammes par poste', S['h2']))
    for num, key, label in poste_config:
        d_b = basic.get("detail", {}).get(key, {})
        d_h = high_end.get("detail", {}).get(key, {})
        d_l = luxury.get("detail", {}).get(key, {})
        story.append(Paragraph(
            f'<b>{num} {label}</b> — '
            f'Basic : {d_b.get("description","")} | '
            f'High-End : {d_h.get("description","")} | '
            f'Luxury : {d_l.get("description","")}',
            S['small']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '* Ce BOQ est une estimation d\'avant-projet (±15%). '
        'Les quantités sont calculées depuis les ratios standards pour le marché local. '
        'Un métré définitif sur plans d\'exécution est requis avant appel d\'offres.',
        S['disc']))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)

    # Write to file
    with open(output_path, 'wb') as f:
        f.write(buf.getvalue())
    return output_path

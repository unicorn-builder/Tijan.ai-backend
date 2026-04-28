"""
gen_boq_finitions.py — BOQ Finitions Tijan AI
═══════════════════════════════════════════════
3 gammes: Basic, High-End, Luxury
6 postes: carrelage, menuiserie int/ext, faux-plafond, peinture, cuisine
Prix par ville (5 marchés) — cohérent avec prix_marche.py
"""
import math

FINITIONS_DB = {
    "carrelage": {
        "basic": {
            "description": "Grès cérame local 30x30, pose incluse",
            "prix_m2": {"Dakar": 18000, "Abidjan": 16000, "Casablanca": 20000, "Lagos": 22000, "default": 18000}
        },
        "high_end": {
            "description": "Grès cérame importé 60x60, pose incluse",
            "prix_m2": {"Dakar": 45000, "Abidjan": 42000, "Casablanca": 50000, "Lagos": 55000, "default": 45000}
        },
        "luxury": {
            "description": "Marbre ou grands formats 80x80+, pose incluse",
            "prix_m2": {"Dakar": 95000, "Abidjan": 90000, "Casablanca": 110000, "Lagos": 120000, "default": 95000}
        },
        "ratio_plancher": 1.0
    },
    "menuiserie_interieure": {
        "basic": {
            "description": "Portes bois MDF, huisseries métalliques",
            "prix_porte": {"Dakar": 85000, "Abidjan": 80000, "Casablanca": 95000, "Lagos": 100000, "default": 85000}
        },
        "high_end": {
            "description": "Portes bois massif prépeint, huisseries alu",
            "prix_porte": {"Dakar": 180000, "Abidjan": 170000, "Casablanca": 200000, "Lagos": 220000, "default": 180000}
        },
        "luxury": {
            "description": "Portes bois noble teck/iroko, huisseries alu anodisé",
            "prix_porte": {"Dakar": 380000, "Abidjan": 360000, "Casablanca": 420000, "Lagos": 450000, "default": 380000}
        },
        "nb_portes_par_100m2": 4.5
    },
    "menuiserie_exterieure": {
        "basic": {
            "description": "Aluminium laqué standard, simple vitrage",
            "prix_m2": {"Dakar": 95000, "Abidjan": 90000, "Casablanca": 105000, "Lagos": 110000, "default": 95000}
        },
        "high_end": {
            "description": "Aluminium thermolaqué, double vitrage",
            "prix_m2": {"Dakar": 185000, "Abidjan": 175000, "Casablanca": 210000, "Lagos": 220000, "default": 185000}
        },
        "luxury": {
            "description": "Aluminium sur mesure, double vitrage feuilleté, stores intégrés",
            "prix_m2": {"Dakar": 380000, "Abidjan": 360000, "Casablanca": 420000, "Lagos": 450000, "default": 380000}
        },
        "ratio_facade": 0.18
    },
    "faux_plafond": {
        "basic": {
            "description": "Dalles BA13 sur ossature métallique",
            "prix_m2": {"Dakar": 22000, "Abidjan": 20000, "Casablanca": 25000, "Lagos": 28000, "default": 22000}
        },
        "high_end": {
            "description": "Plâtre staff décoratif, corniche, spots encastrés",
            "prix_m2": {"Dakar": 48000, "Abidjan": 45000, "Casablanca": 55000, "Lagos": 60000, "default": 48000}
        },
        "luxury": {
            "description": "Bois ou métal sur mesure, éclairage LED intégré",
            "prix_m2": {"Dakar": 110000, "Abidjan": 105000, "Casablanca": 125000, "Lagos": 135000, "default": 110000}
        },
        "ratio_plancher": 0.75
    },
    "peinture": {
        "basic": {
            "description": "Peinture vinylique mate standard, 2 couches",
            "prix_m2": {"Dakar": 4500, "Abidjan": 4000, "Casablanca": 5000, "Lagos": 5500, "default": 4500}
        },
        "high_end": {
            "description": "Peinture acrylique premium lessivable, 3 couches",
            "prix_m2": {"Dakar": 9000, "Abidjan": 8500, "Casablanca": 10000, "Lagos": 11000, "default": 9000}
        },
        "luxury": {
            "description": "Enduit décoratif, béton ciré ou stucco vénitien",
            "prix_m2": {"Dakar": 22000, "Abidjan": 20000, "Casablanca": 25000, "Lagos": 28000, "default": 22000}
        },
        "ratio_murs": 2.8,
        "ratio_plafond": 1.0
    },
    "cuisine": {
        "basic": {
            "description": "Meubles mélaminé, plan stratifié, évier inox",
            "prix_ml": {"Dakar": 180000, "Abidjan": 170000, "Casablanca": 200000, "Lagos": 220000, "default": 180000}
        },
        "high_end": {
            "description": "Meubles MDF laqué, plan granit, électroménager inclus",
            "prix_ml": {"Dakar": 450000, "Abidjan": 420000, "Casablanca": 500000, "Lagos": 550000, "default": 450000}
        },
        "luxury": {
            "description": "Meubles sur mesure bois massif, plan quartz, électroménager premium",
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
        carrelage = surface_totale * db["carrelage"]["ratio_plancher"] * db["carrelage"][gamme]["prix_m2"][v]
        detail["carrelage"] = {"montant": round(carrelage), "description": db["carrelage"][gamme]["description"]}

        # Menuiserie intérieure
        nb_portes = (surface_totale / 100) * db["menuiserie_interieure"]["nb_portes_par_100m2"]
        menu_int = nb_portes * db["menuiserie_interieure"][gamme]["prix_porte"][v]
        detail["menuiserie_interieure"] = {"montant": round(menu_int), "description": db["menuiserie_interieure"][gamme]["description"]}

        # Menuiserie extérieure
        surface_vitrages = surface_facade * db["menuiserie_exterieure"]["ratio_facade"]
        menu_ext = surface_vitrages * db["menuiserie_exterieure"][gamme]["prix_m2"][v]
        detail["menuiserie_exterieure"] = {"montant": round(menu_ext), "description": db["menuiserie_exterieure"][gamme]["description"]}

        # Faux-plafond
        fp = surface_totale * db["faux_plafond"]["ratio_plancher"] * db["faux_plafond"][gamme]["prix_m2"][v]
        detail["faux_plafond"] = {"montant": round(fp), "description": db["faux_plafond"][gamme]["description"]}

        # Peinture
        surface_peinte = surface_totale * (db["peinture"]["ratio_murs"] + db["peinture"]["ratio_plafond"])
        peinture = surface_peinte * db["peinture"][gamme]["prix_m2"][v]
        detail["peinture"] = {"montant": round(peinture), "description": db["peinture"][gamme]["description"]}

        # Cuisine
        ml_cuisine = (surface_totale / 100) * db["cuisine"]["ml_par_100m2"]
        cuisine = ml_cuisine * db["cuisine"][gamme]["prix_ml"][v]
        detail["cuisine"] = {"montant": round(cuisine), "description": db["cuisine"][gamme]["description"]}

        total = sum(d["montant"] for d in detail.values())
        results[gamme] = {"total": round(total), "detail": detail}

    return results


def generer_boq_finitions_pdf(output_path: str, resultats_finitions: dict, params: dict) -> str:
    """Génère le PDF BOQ Finitions avec les 3 gammes côte à côte."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    VERT = colors.HexColor('#43A956')
    NAVY = colors.HexColor('#1B2A4A')

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    nom = params.get("nom", "Projet")
    ville = params.get("ville", "Dakar")

    story.append(Paragraph(f"<b>BOQ FINITIONS — {nom}</b>", styles["Title"]))
    story.append(Paragraph(f"{ville} — 3 gammes de finition", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    gamme_labels = {"basic": "BASIC", "high_end": "HIGH-END", "luxury": "LUXURY"}
    poste_labels = {
        "carrelage": "Carrelage",
        "menuiserie_interieure": "Menuiserie intérieure",
        "menuiserie_exterieure": "Menuiserie extérieure",
        "faux_plafond": "Faux-plafond",
        "peinture": "Peinture",
        "cuisine": "Cuisine équipée"
    }

    for gamme, label in gamme_labels.items():
        data = resultats_finitions.get(gamme, {})
        story.append(Paragraph(f"<b>Gamme {label}</b>", styles["Heading2"]))
        rows = [["Poste", "Description", "Montant (FCFA)"]]
        for poste, pl in poste_labels.items():
            d = data.get("detail", {}).get(poste, {})
            montant_str = f"{d.get('montant', 0):,.0f}".replace(",", " ")
            rows.append([pl, d.get("description", ""), montant_str])
        total_str = f"{data.get('total', 0):,.0f}".replace(",", " ")
        rows.append(["TOTAL", "", total_str])

        t = Table(rows, colWidths=[4*cm, 9*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), VERT),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F7F8FA')]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    return output_path

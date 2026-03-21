"""
pdf_translate.py — Traduction post-génération des textes PDF
Ne modifie PAS les moteurs. Traduit uniquement les labels/textes dans les PDFs.
"""

FR_TO_EN = {
    # Structure
    "Note de calcul structure": "Structural Analysis Report",
    "Descente de charges": "Load Path Analysis",
    "Poteaux": "Columns",
    "Niveau": "Level",
    "Section": "Section",
    "Armatures longitudinales": "Longitudinal Reinforcement",
    "Cadres": "Stirrups",
    "Béton": "Concrete",
    "Fondations": "Foundations",
    "Recommandations": "Recommendations",
    "Conforme": "Compliant",
    "Non conforme": "Non-compliant",
    "Dimensionnement": "Design",
    "résidentiel": "residential",
    "bureau": "office",
    "commercial": "commercial",
    "hôtel": "hotel",
    "Sélection automatique": "Automatic selection",
    "distance mer": "distance to sea",
    "usage": "use",
    
    # BOQ
    "BOQ Structure": "Structural BOQ",
    "BOQ MEP": "MEP BOQ",
    "Désignation": "Description",
    "Unité": "Unit",
    "Quantité": "Quantity",
    "Prix unitaire": "Unit Price",
    "Montant": "Amount",
    "TOTAL": "TOTAL",
    "Béton armé": "Reinforced Concrete",
    "Acier": "Steel",
    "Coffrage": "Formwork",
    "Fondations profondes": "Deep Foundations",
    "Terrassement": "Earthwork",
    "Maçonnerie": "Masonry",
    "Estimation": "Estimate",
    
    # MEP
    "Note de calcul MEP": "MEP Analysis Report",
    "Électricité": "Electrical",
    "Plomberie": "Plumbing",
    "Sécurité incendie": "Fire Safety",
    "Ascenseurs": "Elevators",
    "Courants faibles": "Low Current Systems",
    "Automatisation": "Automation",
    "Puissance totale": "Total Power",
    "Transformateur": "Transformer",
    "Groupe électrogène": "Generator",
    "Nb compteurs": "No. meters",
    "Conso annuelle": "Annual Consumption",
    "Facture annuelle": "Annual Bill",
    "Nb logements": "No. units",
    "Besoin eau/jour": "Daily Water Need",
    "Volume citerne": "Tank Volume",
    "Surpresseur": "Booster Pump",
    "Facture eau/an": "Annual Water Bill",
    "Puissance frigo": "Cooling Capacity",
    "Catégorie ERP": "Building Category",
    "Détecteurs fumée": "Smoke Detectors",
    "Extincteurs": "Extinguishers",
    "Requis": "Required",
    "Non requis": "Not required",
    "Indicateur": "Indicator",
    "Valeur": "Value",
    "Paramètre": "Parameter",
    
    # EDGE
    "Pré-évaluation EDGE": "EDGE Pre-assessment",
    "Conformité EDGE": "EDGE Compliance",
    "Économie énergie": "Energy Savings",
    "Économie eau": "Water Savings",
    "Économie matériaux": "Materials Savings",
    "Certifiable": "Certifiable",
    "Non certifiable": "Not Certifiable",
    "Mesures énergie": "Energy Measures",
    "Mesures eau": "Water Measures",
    "Mesures matériaux": "Materials Measures",
    "Plan d'action": "Action Plan",
    "Coût de mise en conformité": "Compliance Cost",
    
    # Rapport exécutif
    "Rapport de synthèse exécutif": "Executive Summary Report",
    "Budget global estimé": "Estimated Global Budget",
    "Note de synthèse ingénieur": "Engineer's Summary",
    "Points forts": "Strengths",
    "Points d'attention": "Points of Attention",
    "Fiche projet": "Project Overview",
    "Performance environnementale": "Environmental Performance",
    "Points clés et recommandations": "Key Points and Recommendations",
    
    # Fiches techniques
    "Fiches techniques structure": "Structural Datasheets",
    "Fiches techniques MEP": "MEP Datasheets",
    "Fiche béton armé": "Reinforced Concrete Datasheet",
    "Fiche fondations": "Foundations Datasheet",
    "Fiche électricité": "Electrical Datasheet",
    "Fiche plomberie": "Plumbing Datasheet",
    
    # Communs
    "Ce document": "This document",
    "maître d'ouvrage": "project owner",
    "bureau d'études": "engineering firm",
    "avant travaux": "before construction",
    "niveaux": "levels",
    "logements": "units",
    "Surface bâtie": "Built Area",
    "Surface habitable": "Living Area",
    "Localisation": "Location",
    "Projet": "Project",
    "Hauteur": "Height",
    "Usage": "Use",
    "Certification EDGE": "EDGE Certification",
}

def translate_pdf_text(text: str) -> str:
    """Traduit un texte français en anglais en utilisant le dictionnaire."""
    result = text
    # Trier par longueur décroissante pour éviter les remplacements partiels
    for fr, en in sorted(FR_TO_EN.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(fr, en)
    return result

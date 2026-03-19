"""
translate_pdf.py — Post-processor de traduction FR→EN
Remplace tous les textes FR dans les PDFs générés par leur équivalent EN.
Fonctionne en interceptant les appels ReportLab Paragraph/TextRun.
"""

# Dictionnaire exhaustif FR→EN — tout ce qui peut apparaître dans les PDFs
FR_TO_EN = {
    # Headers & titres
    "Note de calcul structure": "Structural Calculation Note",
    "Bordereau des Quantités et des Prix — Structure": "Bill of Quantities — Structure",
    "Note de calcul MEP": "MEP Calculation Note",
    "BOQ MEP — Détaillé": "MEP BOQ — Detailed",
    "Pré-évaluation EDGE": "EDGE Pre-assessment",
    "Rapport de synthèse exécutif": "Executive Summary Report",
    "BOQ Structure — Détaillé": "Structure BOQ — Detailed",

    # Sous-titres
    "Calculs indicatifs ±15% — À vérifier par un ingénieur structure habilité.":
        "Indicative calculations ±15% — To be verified by a licensed structural engineer.",
    "Prix unitaires marché local 2026 (fournis-posés). Marge ±15%.":
        "Local market unit prices 2026 (supply & install). Margin ±15%.",
    "Prix unitaires marché local 2026 — fournis posés — marge ±15%.":
        "Local market unit prices 2026 — supply & install — margin ±15%.",
    "Document utilisable pour consultation d'entreprises.":
        "Document suitable for contractor consultation.",

    # Fiche projet
    "DONNÉES DU PROJET": "PROJECT DATA",
    "HYPOTHÈSES ET NORMES DE CALCUL": "ASSUMPTIONS AND DESIGN STANDARDS",
    "DESCENTE DE CHARGES — POTEAUX (EC2/EC8)": "LOAD DESCENT — COLUMNS (EC2/EC8)",
    "DIMENSIONNEMENT POUTRES (EC2)": "BEAM DESIGN (EC2)",
    "DIMENSIONNEMENT DALLE (EC2)": "SLAB DESIGN (EC2)",
    "CLOISONS ET MAÇONNERIE": "PARTITIONS AND MASONRY",
    "ÉTUDE DES FONDATIONS (EC7 + DTU 13.2)": "FOUNDATION STUDY (EC7)",
    "ANALYSE SISMIQUE (EC8 — NF EN 1998-1)": "SEISMIC ANALYSIS (EC8 — EN 1998-1)",
    "ANALYSE ET RECOMMANDATIONS": "ANALYSIS AND RECOMMENDATIONS",
    "BORDEREAU DES QUANTITÉS ET DES PRIX — STRUCTURE": "BILL OF QUANTITIES — STRUCTURE",

    # Labels fiche projet
    "Projet": "Project",
    "Localisation": "Location",
    "Usage": "Use",
    "Niveaux": "Levels",
    "Surface bâtie": "Built area",
    "Surface habitable": "Habitable area",
    "Portées": "Spans",
    "Travées": "Bays",
    "Béton": "Concrete",
    "Acier": "Steel",
    "Sol admissible": "Admissible soil bearing",
    "Distance mer": "Distance to sea",
    "Charges G / Q": "Loads G / Q",
    "Zone sismique": "Seismic zone",
    "niveaux": "levels",

    # Hypothèses
    "Béton armé": "Reinforced concrete",
    "Séismique": "Seismic",
    "Charges perm. G": "Permanent loads G",
    "Charges var. Q": "Variable loads Q",
    "Combinaison ELU": "ULS combination",
    "Fondations": "Foundations",
    "Durabilité": "Durability",

    # Colonnes tableaux
    "PARAMÈTRE": "PARAMETER",
    "VALEUR": "VALUE",
    "DOMAINE": "DOMAIN",
    "NORME": "STANDARD",
    "REMARQUE": "REMARK",
    "RÉFÉRENCE": "REFERENCE",
    "JUSTIFICATION": "JUSTIFICATION",
    "RECOMMANDATION": "RECOMMENDATION",
    "Désignation": "Description",
    "Qté": "Qty",
    "Unité": "Unit",
    "Marque / Réf.": "Brand / Ref.",

    # Statuts
    "Conforme": "Compliant",
    "À vérifier": "To verify",
    "✓ Conforme": "✓ Compliant",
    "⚠ À vérifier": "⚠ To verify",

    # Poteaux
    "Nb bar.": "No. bars",
    "Ø cad.": "Ø stir.",
    "Esp. cad.": "Stir. sp.",
    "ρ = taux armature (EC2 : 0.1% ≤ ρ ≤ 4%) | NEd/NRd < 1 requis":
        "ρ = steel ratio (EC2: 0.1% ≤ ρ ≤ 4%) | NEd/NRd < 1 required",

    # Poutres
    "Poutre principale": "Main beam",
    "Poutre secondaire": "Secondary beam",
    "As inf (cm²)": "As bot (cm²)",
    "As sup (cm²)": "As top (cm²)",
    "Étrierss": "Stirrups",
    "Étriers": "Stirrups",
    "Esp. étr.": "Stir. sp.",
    "portée": "span",
    "Vérif. flèche": "Deflection check",
    "Effort tranchant": "Shear force",

    # Dalle
    "Épaisseur": "Thickness",
    "As x (cm²/ml)": "As x (cm²/m)",
    "As y (cm²/ml)": "As y (cm²/m)",
    "Armatures sens porteur principal": "Main span reinforcement",
    "Armatures sens secondaire": "Secondary span reinforcement",
    "Flèche admissible": "Admissible deflection",
    "Vérification": "Verification",

    # Cloisons
    "CLOISONS ET MAÇONNERIE": "PARTITIONS AND MASONRY",
    "Surface totale cloisons estimée": "Total estimated partition area",
    "séparatives": "separating",
    "légères": "lightweight",
    "gaines": "ducts",
    "Option recommandée": "Recommended option",
    "charge retenue": "retained load",
    "Ép. (cm)": "Th. (cm)",
    "Charge (kN/m²)": "Load (kN/m²)",
    "P.U. (FCFA/m²)": "Unit price",
    "Recommandé": "Recommended",
    "★ Recommandé": "★ Recommended",
    "Avantages principaux": "Key benefits",
    "ℹ Si plusieurs options ont des impacts prix significatifs, les soumettre au maître d'ouvrage avant validation.":
        "ℹ If several options have significant cost impacts, present them to the project owner for validation.",

    # Fondations
    "Justification": "Justification",
    "Diamètre pieu": "Pile diameter",
    "Foré à la tarière creuse": "Bored pile",
    "Longueur pieu": "Pile length",
    "Jusqu'à horizon porteur": "To bearing stratum",
    "Armatures": "Reinforcement",
    "Cage HA500B pleine longueur": "HA500B full length cage",
    "Nb pieux total": "Total no. piles",
    "Estimé — à confirmer par BET géotechnique": "Estimate — to be confirmed by geotechnical engineer",
    "Largeur semelle": "Footing width",
    "Section carrée": "Square section",
    "Profondeur": "Depth",
    "Hors gel + horizon porteur": "Below frost line + bearing stratum",
    "Adapté aux conditions de sol et à la hauteur": "Suited to soil conditions and building height",
    "Fondations profondes = poste le plus coûteux après gros œuvre.":
        "Deep foundations = most costly item after superstructure.",

    # Sismique
    "Accélération ag": "Acceleration ag",
    "Annexe nationale": "National annex",
    "Facteur sol S": "Soil factor S",
    "Sol type C — EC8 Tableau 3.2": "Soil type C — EC8 Table 3.2",
    "Coefficient q": "Behaviour factor q",
    "Période T₁": "Period T₁",
    "Force de base Fb": "Base shear Fb",
    "Conformité DCL": "DCL compliance",
    "⚠ Analyse complémentaire": "⚠ Additional analysis required",
    "EC8 §4.3.3.2 — méthode approchée": "EC8 §4.3.3.2 — approximate method",

    # Analyse
    "Note de synthèse :": "Engineer's summary note:",
    "Engineer's summary note:": "Engineer's summary note:",
    "✅ Points forts": "✅ Key strengths",
    "⚠ Points d'attention": "⚠ Points of attention",
    "Recommandations :": "Recommendations:",

    # BOQ Structure lots
    "INSTALLATION ET ORGANISATION DE CHANTIER": "SITE INSTALLATION AND ORGANISATION",
    "TERRASSEMENT GÉNÉRAL": "EARTHWORKS",
    "STRUCTURE BÉTON ARMÉ": "REINFORCED CONCRETE STRUCTURE",
    "MAÇONNERIE, CLOISONS ET ENDUITS": "MASONRY, PARTITIONS AND RENDER",
    "ÉTANCHÉITÉ ET ISOLATION": "WATERPROOFING AND INSULATION",
    "DIVERS, IMPRÉVUS ET HONORAIRES TECHNIQUES": "MISCELLANEOUS, CONTINGENCIES AND FEES",
    "RÉCAPITULATIF GÉNÉRAL": "GENERAL SUMMARY",
    "SOUS-TOTAL": "SUB-TOTAL",
    "TOTAL ESTIMATIF HT": "TOTAL EXCL. TAX",
    "FOURCHETTE BASSE (-5%)": "LOW RANGE (-5%)",
    "FOURCHETTE HAUTE (+15%)": "HIGH RANGE (+15%)",
    "Terrassement — décapage + fouilles méca.": "Earthworks — stripping + mechanical excavation",
    "Fondations — pieux/semelles/radier béton armé": "Foundations — bored piles / footings / raft",
    "Maçonnerie — agglos 15cm enduits 2 faces": "Masonry — 15cm hollow blocks both faces rendered",
    "Divers — joints, acrotères, réservations": "Miscellaneous — joints, parapets, sleeves",
    "TOTAL STRUCTURE": "TOTAL STRUCTURE",
    "Clôture de chantier (palissade bois ou tôle)": "Site hoarding (timber or steel sheet)",
    "Modulaires démontables": "Demountable modular units",
    "Branchements provisoires eau + électricité": "Temporary water & electrical connections",
    "Signalétique sécurité + EPI chantier": "Safety signage + PPE",
    "Décapage terre végétale e=30cm": "Topsoil stripping e=30cm",
    "Fouilles générales mécaniques": "General mechanical excavation",
    "Engins mécaniques": "Mechanical plant",
    "Remblai compacté (matériaux sélectionnés)": "Compacted backfill (selected materials)",
    "Évacuation terres excédentaires": "Excess soil removal",
    "Transport + décharge agréée": "Transport + licensed disposal",

    # BOQ ratios
    "INDICATEUR": "INDICATOR",
    "VALEUR BASSE": "LOW VALUE",
    "VALEUR HAUTE": "HIGH VALUE",
    "Surface bâtie totale": "Total built area",
    "Coût / m² bâti": "Cost / m² built",
    "Coût / m² habitable": "Cost / m² habitable",
    "COÛT TOTAL STRUCTURE": "TOTAL STRUCTURE COST",
    "Structure seule — hors MEP, finitions, VRD": "Structure only — excl. MEP, finishes, utilities",
    "Surface habitable ≈ 78% surface bâtie": "Habitable area ≈ 78% of built area",
    "Estimation ±15%": "Estimate ±15%",
    "grille": "grid",

    # BOQ MEP lots
    "ÉLECTRICITÉ COURANTS FORTS (NF C 15-100)": "ELECTRICAL — POWER (NF C 15-100)",
    "PLOMBERIE SANITAIRE (DTU 60.11)": "PLUMBING (DTU 60.11)",
    "CLIMATISATION, VENTILATION ET CHAUFFAGE (EN 12831)": "HVAC — AIR CONDITIONING AND VENTILATION (EN 12831)",
    "COURANTS FAIBLES — RÉSEAU, VIDÉO, ACCÈS, INTERPHONIE": "LOW CURRENT — NETWORK, CCTV, ACCESS CONTROL, INTERCOM",
    "SÉCURITÉ INCENDIE (IT 246 — France/Sénégal)": "FIRE SAFETY (IT 246)",
    "ASCENSEURS ET MONTE-CHARGES (EN 81-20/50)": "LIFTS AND GOODS LIFTS (EN 81-20/50)",
    "AUTOMATISATION GTB": "BMS AUTOMATION",
    "RÉCAPITULATIF GÉNÉRAL BOQ MEP": "GENERAL SUMMARY MEP BOQ",

    # MEP labels
    "Puissance éclairage": "Lighting power",
    "Groupe électrogène": "Generator",
    "Nb compteurs": "No. meters",
    "Conso annuelle": "Annual consumption",
    "Facture annuelle": "Annual bill",
    "Marques recommandées": "Recommended brands",
    "Nb logements": "No. units",
    "Besoin eau/jour": "Daily water need",
    "Volume citerne": "Tank volume",
    "Débit surpresseur": "Pump flow rate",
    "Facture eau/an": "Annual water bill",
    "Puissance frigo": "Cooling capacity",
    "Type VMC": "Ventilation type",
    "Splits séjour": "Living room splits",
    "Splits chambre": "Bedroom splits",
    "Cassettes": "Cassette units",
    "Conso CVC/an": "Annual HVAC consumption",
    "Caméras intérieur": "Indoor cameras",
    "Caméras extérieur": "Outdoor cameras",
    "Contrôle accès": "Access control",
    "Interphones vidéo": "Video intercom",
    "Audio/vidéo collectif": "Collective A/V system",
    "Baies serveur": "Server racks",
    "Catégorie ERP": "Building category",
    "Détecteurs fumée": "Smoke detectors",
    "Déclencheurs manuel": "Manual call points",
    "Extincteurs CO2": "CO2 extinguishers",
    "Sprinklers": "Sprinklers",
    "Désenfumage": "Smoke extraction",
    "Obligatoire": "Mandatory",
    "Non requis": "Not required",
    "Obligatoires": "Mandatory",

    # EDGE
    "SYNTHÈSE DES SCORES EDGE": "EDGE SCORES SUMMARY",
    "PILIER": "PILLAR",
    "SCORE PROJET": "PROJECT SCORE",
    "SEUIL CIBLE": "TARGET",
    "STATUT": "STATUS",
    "CERTIFIABLE": "CERTIFIABLE",
    "NON CERTIFIABLE": "NOT CERTIFIABLE",
    "Énergie": "Energy",
    "Eau": "Water",
    "Matériaux": "Materials",
    "PLAN D'ACTION — OPTIMISATION VERS CERTIFICATION": "ACTION PLAN — OPTIMISATION TOWARDS CERTIFICATION",
    "PILIER 1 — ÉNERGIE": "PILLAR 1 — ENERGY",
    "PILIER 2 — EAU": "PILLAR 2 — WATER",
    "PILIER 3 — MATÉRIAUX": "PILLAR 3 — MATERIALS",
    "MESURE": "MEASURE",
    "GAIN (%)": "SAVING (%)",
    "IMPACT PRIX": "COST IMPACT",
    "ACTION": "ACTION",
    "COÛT": "COST",
    "ROI": "ROI",

    # Rapport exécutif
    "FICHE PROJET": "PROJECT SHEET",
    "ESTIMATION BUDGÉTAIRE GLOBALE": "GLOBAL BUDGET ESTIMATE",
    "PERFORMANCE ENVIRONNEMENTALE (EDGE IFC)": "ENVIRONMENTAL PERFORMANCE (EDGE IFC)",
    "POINTS CLÉS ET RECOMMANDATIONS": "KEY POINTS AND RECOMMENDATIONS",
    "CORPS D'ÉTAT": "TRADE",
    "TOTAL GROS ŒUVRE": "TOTAL STRUCTURAL WORKS",
    "Finitions (estimation)": "Finishes (estimate)",
    "COÛT TOTAL ESTIMÉ": "TOTAL ESTIMATED COST",
    "hors MEP, finitions, VRD": "excl. MEP, finishes, utilities",

    # BOQ MEP items détaillés
    "TGBT — tableau général basse tension": "MDB — main distribution board",
    "insonorisé": "soundproofed",
    "Câbles NYM / H07RN": "NYM / H07RN cables",
    "Mise à la terre + parafoudres": "Earthing + surge protection",
    "Citerne polyéthylène": "Polyethylene tank",
    "Acier galvanisé / PPR": "Galvanised steel / PPR",
    "Colonne montante": "Rising main",
    "Réseau EU/EV": "Soil & waste network",
    "Chauffe-eau électrique": "Electric water heater",
    "Réseau de gaines ventilation": "Ductwork network",
    "Grilles + bouches de ventilation": "Grilles + ventilation outlets",
    "Régulation et thermostat par zone": "Zone control & thermostat",
    "Câblage réseau Cat6A": "Cat6A network cabling",
    "NVR enregistreur vidéo + stockage": "NVR video recorder + storage",
    "Système audio/vidéo collectif": "Collective A/V system",
    "Centrale incendie adressable": "Addressable fire control panel",
    "Centrale sprinkler + réseau alimentation": "Sprinkler central + supply network",
    "Désenfumage — volets motorisés + gaines": "Smoke extraction — motorised dampers + ducts",
    "Trémie béton armé + fosse ascenseur": "RC pit + lift shaft",
    "Tableau électrique dédié ascenseurs": "Dedicated lift electrical panel",
    "monte-charge": "goods lift",
    "Gestion éclairage": "Lighting control",
    "Gestion CVC centralisée": "Centralised HVAC control",
    "Comptage énergie + tableaux de bord": "Energy metering + dashboards",
    "Domotique par logement": "Home automation per unit",

    # Footer
    "Document d'assistance à l'ingénierie — Version bêta ±15%. Doit être vérifié par un ingénieur habilité. Ne remplace pas l'intervention légalement obligatoire d'un bureau d'études.":
        "Engineering assistance document — Beta version ±15%. Must be verified by a licensed engineer. Does not replace the legally required involvement of a certified engineering firm.",

    # Misc
    "Auto-sélectionné": "Auto-selected",
    "Sélection automatique": "Auto-selection",
    "logements / unités": "units",
    "personnes": "persons",
    "forfait": "lump sum",
    "Estimation ±15% — BOQ détaillé disponible en téléchargement.":
        "Estimate ±15% — detailed BOQ available for download.",
    "Détail complet disponible dans le PDF": "Full breakdown available in the PDF",
    "Recommandation": "Recommendation",
    "Gamme Basic à High-End recommandée pour usage résidentiel standard":
        "Basic to High-End range recommended for standard residential use",
    "Gamme High-End recommandée": "High-End range recommended",
    "Gamme High-End à Luxury recommandée": "High-End to Luxury range recommended",
    "Écart Basic → Luxury": "Gap Basic → Luxury",
    "de surcoût": "additional cost",
    "Ce rapport est destiné au maître d'ouvrage. Téléchargez le PDF complet ci-dessous.":
        "This report is for the project owner. Download the full PDF below.",
    "Bientôt": "Coming soon",
}


def translate(text: str, lang: str = 'fr') -> str:
    """Traduit un texte FR→EN si lang=='en'."""
    if lang != 'en' or not text:
        return text
    result = text
    for fr, en in FR_TO_EN.items():
        if fr in result:
            result = result.replace(fr, en)
    return result

"""
pdf_strings.py — Strings bilingues pour les générateurs PDF Tijan AI
Usage : from pdf_strings import get_strings
        s = get_strings('en')
        s['note_title']  → 'Structural Calculation Note'
"""

STRINGS = {
    'fr': {
        # Titres documents
        'note_structure_title':     'Note de calcul structure',
        'boq_structure_title':      'Bordereau des Quantités et des Prix — Structure',
        'note_mep_title':           'Note de calcul MEP',
        'boq_mep_title':            'BOQ MEP — Détaillé',
        'edge_title':               'Pré-évaluation EDGE',
        'executif_title':           'Rapport de synthèse exécutif',

        # Sous-titres
        'subtitle_structure':       'Calculs indicatifs ±15% — À vérifier par un ingénieur structure habilité.',
        'subtitle_boq':             'Prix unitaires marché local 2026 (fournis-posés). Marge ±15%.',
        'subtitle_mep':             'Document utilisable pour consultation d\'entreprises.',
        'subtitle_edge':            'IFC EDGE Standard v3',
        'subtitle_executif':        'Ce document est destiné au maître d\'ouvrage.',

        # Sections structure
        'project_data':             'DONNÉES DU PROJET',
        'hypotheses':               'HYPOTHÈSES ET NORMES DE CALCUL',
        'columns':                  'DESCENTE DE CHARGES — POTEAUX (EC2/EC8)',
        'beams':                    'DIMENSIONNEMENT POUTRES (EC2)',
        'slab':                     'DIMENSIONNEMENT DALLE (EC2)',
        'partitions':               'CLOISONS ET MAÇONNERIE',
        'foundations':              'ÉTUDE DES FONDATIONS (EC7 + DTU 13.2)',
        'seismic':                  'ANALYSE SISMIQUE (EC8 — NF EN 1998-1)',
        'analysis':                 'ANALYSE ET RECOMMANDATIONS',
        'boq_section':              'BORDEREAU DES QUANTITÉS ET DES PRIX — STRUCTURE',

        # Colonnes tableaux
        'parameter':    'PARAMÈTRE',
        'value':        'VALEUR',
        'justif':       'JUSTIFICATION',
        'lot':          'Lot',
        'designation':  'Désignation',
        'qty':          'Qté',
        'unit':         'Unité',
        'pu':           'P.U. (FCFA)',
        'amount':       'Montant (FCFA)',
        'amount_low':   'Montant bas',
        'amount_high':  'Montant haut',
        'notes':        'Observations',
        'level':        'Niveau',
        'section':      'Section',
        'rebars':       'Armatures',
        'rate':         'Taux arm.',
        'verif':        'Vérif.',

        # Statuts
        'ok':           '✓ OK',
        'nok':          '✗ NOK',
        'compliant':    '✓ Conforme',
        'to_verify':    '⚠ À vérifier',
        'soon':         'Bientôt',

        # MEP sections
        'elec_section': 'BILAN ÉLECTRICITÉ (NF C 15-100)',
        'plumb_section':'BILAN PLOMBERIE (DTU 60.11 — ONAS)',
        'cvc_section':  'BILAN CVC (EN 12831 — ASHRAE 55)',
        'cf_section':   'COURANTS FAIBLES',
        'fire_section': 'SÉCURITÉ INCENDIE (IT 246)',
        'elev_section': 'ASCENSEURS (EN 81-20/50)',
        'auto_section': 'AUTOMATISATION GTB',

        # EDGE
        'edge_scores':  'SYNTHÈSE DES SCORES EDGE',
        'pillar':       'PILIER',
        'score':        'SCORE PROJET',
        'target':       'SEUIL CIBLE',
        'status':       'STATUT',
        'certifiable':  'CERTIFIABLE',
        'not_cert':     'NON CERTIFIABLE',
        'energy':       'Énergie',
        'water':        'Eau',
        'materials':    'Matériaux',
        'action_plan':  'PLAN D\'ACTION — OPTIMISATION VERS CERTIFICATION',
        'pillar1':      'PILIER 1 — ÉNERGIE',
        'pillar2':      'PILIER 2 — EAU',
        'pillar3':      'PILIER 3 — MATÉRIAUX',
        'measure':      'MESURE',
        'gain':         'GAIN (%)',
        'impact':       'IMPACT PRIX',
        'action':       'ACTION',
        'cost':         'COÛT',
        'roi':          'ROI',

        # Rapport exécutif
        'project_sheet':    'FICHE PROJET',
        'global_budget':    'ESTIMATION BUDGÉTAIRE GLOBALE',
        'edge_perf':        'PERFORMANCE ENVIRONNEMENTALE (EDGE IFC)',
        'key_points':       'POINTS CLÉS ET RECOMMANDATIONS',
        'body_of_work':     'CORPS D\'ÉTAT',
        'total':            'TOTAL',
        'total_go':         'TOTAL GROS ŒUVRE',
        'finishes':         'Finitions (estimation)',
        'total_estimate':   'COÛT TOTAL ESTIMÉ',

        # BOQ labels
        'installation':     'INSTALLATION ET ORGANISATION DE CHANTIER',
        'earthworks':       'TERRASSEMENT GÉNÉRAL',
        'foundation_lot':   'FONDATIONS',
        'structure_lot':    'STRUCTURE BÉTON ARMÉ',
        'masonry_lot':      'MAÇONNERIE, CLOISONS ET ENDUITS',
        'waterproof_lot':   'ÉTANCHÉITÉ ET ISOLATION',
        'misc_lot':         'DIVERS, IMPRÉVUS ET HONORAIRES TECHNIQUES',
        'recap':            'RÉCAPITULATIF GÉNÉRAL',
        'sub_total':        'SOUS-TOTAL',
        'grand_total':      'TOTAL ESTIMATIF HT',
        'low_range':        'FOURCHETTE BASSE (-5%)',
        'high_range':       'FOURCHETTE HAUTE (+15%)',

        # BOQ MEP lots
        'lot_elec':     'ÉLECTRICITÉ COURANTS FORTS (NF C 15-100)',
        'lot_plumb':    'PLOMBERIE SANITAIRE (DTU 60.11)',
        'lot_cvc':      'CLIMATISATION, VENTILATION ET CHAUFFAGE (EN 12831)',
        'lot_cf':       'COURANTS FAIBLES — RÉSEAU, VIDÉO, ACCÈS, INTERPHONIE',
        'lot_fire':     'SÉCURITÉ INCENDIE (IT 246 — France/Sénégal)',
        'lot_elev':     'ASCENSEURS ET MONTE-CHARGES (EN 81-20/50)',
        'lot_auto':     'AUTOMATISATION GTB',

        # Footer disclaimer
        'disclaimer':   (
            'Document d\'assistance à l\'ingénierie — Version bêta ±15%. '
            'Doit être vérifié par un ingénieur habilité. '
            'Ne remplace pas l\'intervention légalement obligatoire d\'un bureau d\'études.'
        ),

        # Misc
        'surface_note': '* Surface bâtie estimée (emprise × niveaux) — à confirmer avec plans définitifs.',
        'built_area':   'Surface bâtie',
        'hab_area':     'Surface habitable',
        'footprint':    'Emprise',
        'levels':       'niveaux',
        'prices_note':  'Prix unitaires marché local 2026 (fournis-posés). Marge ±15%.',
        'indicator':    'INDICATEUR',
        'market_ref':   'RÉFÉRENCE MARCHÉ',
        'brand':        'Marque / Réf.',
        'brands':       'Marques recommandées',
        'basic_col':    'Basic (FCFA)',
        'hend_col':     'High-End',
        'luxury_col':   'Luxury',
        'pct_total':    '% TOTAL',
        'cost_m2':      'COÛT / m² BÂTI',
    },

    'en': {
        # Document titles
        'note_structure_title':     'Structural Calculation Note',
        'boq_structure_title':      'Bill of Quantities — Structure',
        'note_mep_title':           'MEP Calculation Note',
        'boq_mep_title':            'MEP BOQ — Detailed',
        'edge_title':               'EDGE Pre-assessment',
        'executif_title':           'Executive Summary Report',

        # Subtitles
        'subtitle_structure':       'Indicative calculations ±15% — To be verified by a licensed structural engineer.',
        'subtitle_boq':             'Local market unit prices 2026 (supply and install). Margin ±15%.',
        'subtitle_mep':             'Document suitable for contractor consultation.',
        'subtitle_edge':            'IFC EDGE Standard v3',
        'subtitle_executif':        'This document is intended for the project owner.',

        # Structure sections
        'project_data':             'PROJECT DATA',
        'hypotheses':               'ASSUMPTIONS AND DESIGN STANDARDS',
        'columns':                  'LOAD DESCENT — COLUMNS (EC2/EC8)',
        'beams':                    'BEAM DESIGN (EC2)',
        'slab':                     'SLAB DESIGN (EC2)',
        'partitions':               'PARTITIONS AND MASONRY',
        'foundations':              'FOUNDATION STUDY (EC7)',
        'seismic':                  'SEISMIC ANALYSIS (EC8 — EN 1998-1)',
        'analysis':                 'ANALYSIS AND RECOMMENDATIONS',
        'boq_section':              'BILL OF QUANTITIES — STRUCTURE',

        # Table headers
        'parameter':    'PARAMETER',
        'value':        'VALUE',
        'justif':       'JUSTIFICATION',
        'lot':          'Lot',
        'designation':  'Description',
        'qty':          'Qty',
        'unit':         'Unit',
        'pu':           'Unit price',
        'amount':       'Amount',
        'amount_low':   'Low amount',
        'amount_high':  'High amount',
        'notes':        'Notes',
        'level':        'Level',
        'section':      'Section',
        'rebars':       'Reinforcement',
        'rate':         'Steel ratio',
        'verif':        'Check',

        # Status labels
        'ok':           '✓ OK',
        'nok':          '✗ NOK',
        'compliant':    '✓ Compliant',
        'to_verify':    '⚠ To verify',
        'soon':         'Coming soon',

        # MEP sections
        'elec_section': 'ELECTRICAL BALANCE (NF C 15-100)',
        'plumb_section':'PLUMBING BALANCE (DTU 60.11)',
        'cvc_section':  'HVAC BALANCE (EN 12831 — ASHRAE 55)',
        'cf_section':   'LOW CURRENT SYSTEMS',
        'fire_section': 'FIRE SAFETY (IT 246)',
        'elev_section': 'LIFTS (EN 81-20/50)',
        'auto_section': 'BMS AUTOMATION',

        # EDGE
        'edge_scores':  'EDGE SCORES SUMMARY',
        'pillar':       'PILLAR',
        'score':        'PROJECT SCORE',
        'target':       'TARGET',
        'status':       'STATUS',
        'certifiable':  'CERTIFIABLE',
        'not_cert':     'NOT CERTIFIABLE',
        'energy':       'Energy',
        'water':        'Water',
        'materials':    'Materials',
        'action_plan':  'ACTION PLAN — OPTIMISATION TOWARDS CERTIFICATION',
        'pillar1':      'PILLAR 1 — ENERGY',
        'pillar2':      'PILLAR 2 — WATER',
        'pillar3':      'PILLAR 3 — MATERIALS',
        'measure':      'MEASURE',
        'gain':         'SAVING (%)',
        'impact':       'COST IMPACT',
        'action':       'ACTION',
        'cost':         'COST',
        'roi':          'ROI',

        # Executive report
        'project_sheet':    'PROJECT SHEET',
        'global_budget':    'GLOBAL BUDGET ESTIMATE',
        'edge_perf':        'ENVIRONMENTAL PERFORMANCE (EDGE IFC)',
        'key_points':       'KEY POINTS AND RECOMMENDATIONS',
        'body_of_work':     'TRADE',
        'total':            'TOTAL',
        'total_go':         'TOTAL STRUCTURAL WORKS',
        'finishes':         'Finishes (estimate)',
        'total_estimate':   'TOTAL ESTIMATED COST',

        # BOQ labels
        'installation':     'SITE INSTALLATION AND ORGANISATION',
        'earthworks':       'EARTHWORKS',
        'foundation_lot':   'FOUNDATIONS',
        'structure_lot':    'REINFORCED CONCRETE STRUCTURE',
        'masonry_lot':      'MASONRY, PARTITIONS AND RENDER',
        'waterproof_lot':   'WATERPROOFING AND INSULATION',
        'misc_lot':         'MISCELLANEOUS, CONTINGENCIES AND FEES',
        'recap':            'GENERAL SUMMARY',
        'sub_total':        'SUB-TOTAL',
        'grand_total':      'TOTAL EXCL. TAX',
        'low_range':        'LOW RANGE (-5%)',
        'high_range':       'HIGH RANGE (+15%)',

        # BOQ MEP lots
        'lot_elec':     'ELECTRICAL — POWER (NF C 15-100)',
        'lot_plumb':    'PLUMBING (DTU 60.11)',
        'lot_cvc':      'HVAC — AIR CONDITIONING AND VENTILATION (EN 12831)',
        'lot_cf':       'LOW CURRENT — NETWORK, CCTV, ACCESS CONTROL, INTERCOM',
        'lot_fire':     'FIRE SAFETY (IT 246)',
        'lot_elev':     'LIFTS AND GOODS LIFTS (EN 81-20/50)',
        'lot_auto':     'BMS AUTOMATION',

        # Footer disclaimer
        'disclaimer':   (
            'Engineering assistance document — Beta version ±15%. '
            'Must be verified by a licensed engineer. '
            'Does not replace the legally required involvement of a certified engineering firm.'
        ),

        # Misc
        'surface_note': '* Built area estimated (footprint × levels) — to be confirmed with final plans.',
        'built_area':   'Built area',
        'hab_area':     'Habitable area',
        'footprint':    'Footprint',
        'levels':       'levels',
        'prices_note':  'Local market unit prices 2026 (supply and install). Margin ±15%.',
        'indicator':    'INDICATOR',
        'market_ref':   'MARKET REFERENCE',
        'brand':        'Brand / Ref.',
        'brands':       'Recommended brands',
        'basic_col':    'Basic',
        'hend_col':     'High-End',
        'luxury_col':   'Luxury',
        'pct_total':    '% TOTAL',
        'cost_m2':      'COST / m² BUILT',
    }
}

def get_strings(lang: str = 'fr') -> dict:
    return STRINGS.get(lang, STRINGS['fr'])

"""
chat_engine.py — Moteur de conversation Tijan AI
Reçoit le contexte projet + historique + message utilisateur
Retourne une réponse Claude contextualisée
"""
import os
import anthropic

SYSTEM_PROMPT = """Tu es Tijan AI, un ingénieur expert en construction et BTP pour les marchés africains.
Tu as calculé et généré le dossier technique du projet décrit dans le contexte ci-dessous.
Tu réponds en français par défaut, en anglais si l'utilisateur écrit en anglais.

Tes domaines d'expertise :
- Structure béton armé (Eurocodes EC2/EC8)
- MEP : électricité, plomberie, CVC, sécurité incendie, ascenseurs
- Certification EDGE IFC (énergie, eau, matériaux)
- Prix marché Dakar, Abidjan, Casablanca, Lagos, Accra
- Réglementation construction Sénégal, Côte d'Ivoire, Maroc

Règles de réponse :
- Sois concis et direct — max 5-6 phrases sauf si une explication détaillée est demandée
- Utilise les données réelles du projet (fournies dans le contexte) dans tes réponses
- Ne dis jamais "je suis une IA" — tu es Tijan AI, un ingénieur virtuel
- Si la question dépasse ton domaine, oriente vers un professionnel qualifié
- Toujours rappeler que les calculs sont indicatifs et doivent être validés par un BET agréé
- Réponds dans la langue de l'utilisateur (français par défaut, anglais si il écrit en anglais)

MODIFICATION DES ÉTUDES :
Quand l'utilisateur demande de MODIFIER un paramètre du projet (portée, niveaux, surface, béton, acier, usage, ville, etc.), tu DOIS :
1. Commencer ta réponse par une ligne JSON entre balises: <MODIF>{"param":"valeur",...}</MODIF>
2. Puis expliquer l'impact du changement en texte normal

Les paramètres modifiables et leurs clés JSON :
- portee_max_m : portée principale (ex: "augmente la portée à 7m" → {"portee_max_m": 7.0})
- portee_min_m : portée secondaire
- nb_niveaux : nombre de niveaux (ex: "passe à R+6" → {"nb_niveaux": 7})
- surface_emprise_m2 : surface au sol
- nb_travees_x / nb_travees_y : nombre de travées
- classe_beton : classe béton (ex: "utilise du C35/45" → {"classe_beton": "C35/45"})
- classe_acier : classe acier
- usage : usage (residentiel/bureau/hotel/mixte/commercial/industriel)
- ville : ville du projet
- hauteur_etage_m : hauteur d'étage

Exemples de consignes utilisateur et réponses attendues :
- "Augmente la portée à 7m" → <MODIF>{"portee_max_m": 7.0}</MODIF>
En augmentant la portée...
- "Passe en R+6" → <MODIF>{"nb_niveaux": 7}</MODIF>
Passer de R+X à R+6...
- "Et si on prenait du C25/30 ?" → <MODIF>{"classe_beton": "C25/30"}</MODIF>
Le C25/30...
- "Change pour un usage bureau" → <MODIF>{"usage": "bureau"}</MODIF>
Pour un usage bureau...

Si l'utilisateur pose une simple QUESTION (sans demander de changement), NE PAS inclure <MODIF>.

FORMAT :
- Réponds directement, sans préambule
- Pour les comparaisons : utilise des listes courtes
- Pour les impacts prix : donne toujours un chiffre en FCFA ou dans la devise locale
"""

def formater_contexte(params: dict, resultats_structure: dict, resultats_mep: dict = None) -> str:
    """Formate les données projet en contexte lisible pour Claude."""
    ctx = f"""
PROJET : {params.get('nom', 'N/A')}
Ville : {params.get('ville', 'Dakar')} | Usage : {params.get('usage', 'résidentiel')} | Niveaux : R+{params.get('nb_niveaux', 0)-1}
Surface emprise : {params.get('surface_emprise_m2', 0)} m² | Surface bâtie estimée : {params.get('surface_emprise_m2', 0) * params.get('nb_niveaux', 1)} m²
Portées : {params.get('portee_min_m', 0)}–{params.get('portee_max_m', 0)} m | Travées : {params.get('nb_travees_x', 0)}×{params.get('nb_travees_y', 0)}

STRUCTURE :
Béton : {resultats_structure.get('classe_beton', 'N/A')} | Acier : {resultats_structure.get('classe_acier', 'N/A')}
Sol admissible : {resultats_structure.get('pression_sol_MPa', 0)} MPa | Distance mer : {resultats_structure.get('distance_mer_km', 0)} km
Fondations : {resultats_structure.get('fondation', {}).get('type', 'N/A')}
"""
    boq = resultats_structure.get('boq', {})
    if boq:
        ctx += f"""
BOQ STRUCTURE :
Béton total : {boq.get('beton_total_m3', 0):.0f} m³ | Acier total : {boq.get('acier_kg', 0):.0f} kg
Coût structure bas : {boq.get('total_bas_fcfa', 0)/1e6:.1f} M FCFA
Coût structure haut : {boq.get('total_haut_fcfa', 0)/1e6:.1f} M FCFA
Ratio : {boq.get('ratio_fcfa_m2_bati', 0):,.0f} FCFA/m²
"""
    if resultats_mep:
        edge = resultats_mep.get('edge', {})
        boqm = resultats_mep.get('boq_mep', {})
        ctx += f"""
MEP :
Puissance électrique : {resultats_mep.get('electrique', {}).get('puissance_totale_kva', 0):.0f} kVA
Besoin eau : {resultats_mep.get('plomberie', {}).get('besoin_total_m3_j', 0):.1f} m³/j
Ascenseurs : {resultats_mep.get('ascenseurs', {}).get('nb_ascenseurs', 0)} × {resultats_mep.get('ascenseurs', {}).get('capacite_kg', 0)} kg
BOQ MEP Basic : {boqm.get('basic_fcfa', 0)/1e6:.0f} M FCFA | High-End : {boqm.get('hend_fcfa', 0)/1e6:.0f} M FCFA

EDGE :
Énergie : {edge.get('economie_energie_pct', 0)}% | Eau : {edge.get('economie_eau_pct', 0)}% | Matériaux : {edge.get('economie_materiaux_pct', 0)}%
Certifiable EDGE : {'Oui' if edge.get('certifiable') else 'Non'} | {edge.get('niveau_certification', '')}
"""
    analyse = resultats_structure.get('analyse', {})
    if analyse.get('note_ingenieur'):
        ctx += f"\nSYNTHÈSE INGÉNIEUR : {analyse.get('note_ingenieur', '')}"
    if analyse.get('alertes'):
        ctx += f"\nALERTES : {' | '.join(analyse.get('alertes', []))}"

    return ctx.strip()


def chat(
    message: str,
    historique: list,
    params: dict,
    resultats_structure: dict,
    resultats_mep: dict = None
) -> str:
    """
    Envoie un message à Claude avec le contexte projet.
    
    historique : liste de dicts {role: 'user'|'assistant', content: str}
    Retourne la réponse texte.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    contexte = formater_contexte(params, resultats_structure, resultats_mep)
    system = f"{SYSTEM_PROMPT}\n\n=== CONTEXTE DU PROJET ===\n{contexte}"

    messages = []
    for msg in historique[-10:]:  # Max 10 messages d'historique
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=messages,
    )

    return response.content[0].text

"""
parse_sol.py — Extraction paramètres géotechniques depuis PDF étude de sol
Utilise pymupdf + Claude API
"""
import os
import re
import json
import logging
import pathlib

logger = logging.getLogger("tijan")

CLAUDE_MODEL = "claude-sonnet-4-20250514"

DEFAULTS_SOL = {
    "type_sol": "latéritique",
    "pression_admissible_MPa": 0.15,
    "profondeur_nappe_m": 10.0,
    "profondeur_ancrage_m": 1.5,
    "module_young_MPa": 20.0,
    "taux_humidite_pct": 15.0,
    "classe_agressivite": "faible",
    "recommandation_fondation": "Pieux forés béton armé",
    "observations": "",
}

PROMPT_SOL = """Tu es un ingénieur géotechnicien expert. Analyse ce rapport d'étude de sol et extrais les paramètres géotechniques clés.
Réponds UNIQUEMENT avec un JSON valide sans markdown :
{
  "type_sol": "description courte du type de sol dominant",
  "pression_admissible_MPa": float (contrainte admissible en MPa),
  "profondeur_nappe_m": float (profondeur nappe phréatique en mètres, null si non mentionnée),
  "profondeur_ancrage_m": float (profondeur minimale d'ancrage des fondations en mètres),
  "module_young_MPa": float (module de Young ou déformation en MPa, null si absent),
  "taux_humidite_pct": float (teneur en eau en %, null si absent),
  "classe_agressivite": "faible" ou "modérée" ou "forte" (agressivité chimique pour béton),
  "recommandation_fondation": "type de fondation recommandé par le rapport",
  "observations": "observations importantes en 1-2 phrases max"
}
Si une valeur est absente du rapport mets null. Réponds UNIQUEMENT avec le JSON."""


def _get_client():
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY manquante")
    return anthropic.Anthropic(api_key=key)


def _apply_defaults(p: dict) -> dict:
    for k, v in DEFAULTS_SOL.items():
        if k not in p or p[k] is None:
            p[k] = v
    return p


def _clean_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


def extraire_params_sol(fichier_path: str) -> dict:
    """
    Extrait les paramètres géotechniques depuis un PDF d'étude de sol.
    Retourne dict avec ok:bool + paramètres sol.
    """
    ext = pathlib.Path(fichier_path).suffix.lower()
    if ext != ".pdf":
        return {"ok": False, "message": f"Format '{ext}' non supporté pour étude de sol. PDF uniquement."}

    try:
        import fitz
    except ImportError:
        return {"ok": False, "message": "pymupdf non installé"}

    try:
        doc = fitz.open(fichier_path)
        texte = "".join(page.get_text() for page in doc).strip()
        doc.close()
    except Exception as e:
        return {"ok": False, "message": f"PDF illisible : {e}"}

    if len(texte) < 50:
        return {"ok": False, "message": "PDF vide ou non vectoriel"}

    try:
        client = _get_client()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"{PROMPT_SOL}\n\nRAPPORT GÉOTECHNIQUE :\n{texte[:8000]}"
            }]
        )
        params = _clean_json(msg.content[0].text)
        params = _apply_defaults(params)
        params["ok"] = True
        params["source"] = "etude_sol_claude"
        logger.info(f"Étude sol parsée : {params['type_sol']} / {params['pression_admissible_MPa']} MPa")
        return params
    except json.JSONDecodeError as e:
        return {"ok": False, "message": f"Réponse Claude non parsable : {e}"}
    except Exception as e:
        return {"ok": False, "message": f"Erreur : {e}"}

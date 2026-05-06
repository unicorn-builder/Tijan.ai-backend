#!/usr/bin/env python3
"""
test_bim_api.py — Test de l'endpoint /generate-dossier-bim sur Render

Envoie un payload ParamsProjet au backend déployé et récupère le PDF.

Usage:
    cd ~/tijan-repo
    python tests/test_bim_api.py                     # Backend Render
    python tests/test_bim_api.py http://localhost:10000  # Backend local

Output:
    tests/output/dossier_bim_api_test.pdf
"""
import os
import sys
import time
import json

try:
    import httpx
except ImportError:
    print("❌ httpx requis: pip install httpx")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

DEFAULT_URL = "https://build-ai-backend.onrender.com"
ENDPOINT = "/generate-dossier-bim"

# Payload Sakho R+8 — format ParamsProjet
PAYLOAD_SAKHO = {
    "nom": "Résidence Papa Oumar Sakho",
    "ville": "Dakar",
    "pays": "Senegal",
    "usage": "residentiel",
    "nb_niveaux": 9,           # RDC + R+1 à R+8
    "nb_travees_x": 4,        # 4 travées en X
    "nb_travees_y": 5,        # 5 travées en Y
    "portee_max_m": 7.0,      # 28m / 4
    "portee_min_m": 10.0,     # 50m / 5
    "hauteur_etage_m": 3.0,
    "classe_beton": "C30/37",
    "classe_acier": "HA500",
    "zone_sismique": 2,
    "pression_sol_MPa": 0.15,
    "distance_mer_km": 5.0,
    "charges_permanentes_kN_m2": 6.5,
    "charges_exploitation_kN_m2": 2.5,
    "type_fondation": "radier",
    "epaisseur_dalle_m": 0.22,
}

# Payload plus simple pour test rapide
PAYLOAD_SIMPLE = {
    "nom": "Test BIM Simple",
    "ville": "Dakar",
    "pays": "Senegal",
    "usage": "residentiel",
    "nb_niveaux": 3,
    "nb_travees_x": 2,
    "nb_travees_y": 2,
    "portee_max_m": 5.5,
    "portee_min_m": 4.0,
    "hauteur_etage_m": 3.0,
    "classe_beton": "C25/30",
    "classe_acier": "HA500",
    "zone_sismique": 2,
}


def test_endpoint(base_url: str, payload: dict, label: str):
    """Call the /generate-dossier-bim endpoint and save the PDF."""
    url = f"{base_url}{ENDPOINT}"
    print(f"\n{'=' * 60}")
    print(f"TEST: {label}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)[:200]}...")
    print(f"{'=' * 60}")

    t0 = time.time()
    try:
        print("⏳ Envoi de la requête (peut prendre 30-60s)...")
        resp = httpx.post(
            url,
            json=payload,
            timeout=120.0,
            headers={"Content-Type": "application/json"},
        )
    except httpx.TimeoutException:
        print(f"❌ Timeout après 120s — le backend met trop de temps")
        return False
    except httpx.ConnectError as e:
        print(f"❌ Connexion impossible: {e}")
        print(f"   Vérifiez que le backend tourne sur {base_url}")
        return False

    elapsed = time.time() - t0

    print(f"\n▶ Réponse en {elapsed:.1f}s")
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('content-type', '?')}")

    # Check custom headers
    boq = resp.headers.get("X-Tijan-BOQ-Summary", "")
    trades = resp.headers.get("X-Tijan-Trades", "")
    if trades:
        print(f"  Trades: {trades}")
    if boq:
        print(f"  BOQ: {boq[:100]}...")

    if resp.status_code != 200:
        print(f"\n❌ ERREUR {resp.status_code}")
        try:
            detail = resp.json()
            print(f"  Détail: {json.dumps(detail, ensure_ascii=False)}")
        except Exception:
            print(f"  Body: {resp.text[:500]}")
        return False

    # Save PDF
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)

    fname = f"dossier_bim_{label.lower().replace(' ', '_')}.pdf"
    out_path = os.path.join(out_dir, fname)

    with open(out_path, "wb") as f:
        f.write(resp.content)

    size_kb = len(resp.content) / 1024
    print(f"\n✓ PDF sauvegardé: {out_path}")
    print(f"  Taille: {size_kb:.0f} KB")

    # Basic validation
    if not resp.content[:4] == b"%PDF":
        print("⚠️  Le fichier ne commence pas par %PDF — vérifiez le contenu")
        return False

    print(f"\n✓ TEST RÉUSSI — {label}")
    return True


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    print("╔══════════════════════════════════════════════╗")
    print("║  TIJAN AI — Test API BIM Phase 4             ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"\nBackend: {base_url}")

    # Test 1: Simple (rapide)
    ok1 = test_endpoint(base_url, PAYLOAD_SIMPLE, "Simple R+3")

    # Test 2: Sakho complet (plus long)
    ok2 = test_endpoint(base_url, PAYLOAD_SAKHO, "Sakho R+8")

    # Summary
    print(f"\n{'=' * 60}")
    print("RÉSUMÉ:")
    print(f"  Test Simple R+3: {'✓ OK' if ok1 else '❌ ÉCHEC'}")
    print(f"  Test Sakho R+8:  {'✓ OK' if ok2 else '❌ ÉCHEC'}")
    print(f"{'=' * 60}")

    if ok1 and ok2:
        print("\n🎉 Tous les tests API passent !")
    else:
        print("\n⚠️  Certains tests ont échoué")
        sys.exit(1)


if __name__ == "__main__":
    main()

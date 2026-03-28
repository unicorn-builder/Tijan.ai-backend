"""
Tijan AI — aps_parser_v2.py
Pipeline DWG parsing via Autodesk Platform Services (APS).
Validated workflow: Auth → S3 Upload → Model Derivative → Property Extraction.

Uses Developer Hub app "Tijan AI Backend" (NOT @personal).
All endpoints validated on Free tier, March 28, 2026.
"""

import os
import time
import json
import base64
import logging
import tempfile
from typing import Optional, Dict, List, Any
from collections import Counter

import requests

logger = logging.getLogger("aps_parser")

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

APS_CLIENT_ID = os.getenv("APS_CLIENT_ID", "")
APS_CLIENT_SECRET = os.getenv("APS_CLIENT_SECRET", "")
APS_BUCKET = os.getenv("APS_BUCKET", "tijan-ai-prod")

APS_AUTH_URL = "https://developer.api.autodesk.com/authentication/v2/token"
APS_OSS_URL = "https://developer.api.autodesk.com/oss/v2/buckets"
APS_MD_URL = "https://developer.api.autodesk.com/modelderivative/v2/designdata"

# ════════════════════════════════════════════════════════════
# AUTH — token cache
# ════════════════════════════════════════════════════════════

_token_cache: Dict[str, Any] = {"token": None, "expires_at": 0}


def get_token() -> str:
    """Get or refresh APS access token."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 120:
        return _token_cache["token"]

    if not APS_CLIENT_ID or not APS_CLIENT_SECRET:
        raise EnvironmentError(
            "APS_CLIENT_ID et APS_CLIENT_SECRET requis. "
            "Configurez-les dans les variables d'environnement Render."
        )

    r = requests.post(APS_AUTH_URL, data={
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "data:read data:write data:create bucket:create bucket:read viewables:read",
    }, timeout=15)
    r.raise_for_status()
    data = r.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"]
    logger.info("APS token refreshed, expires in %ds", data["expires_in"])
    return _token_cache["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ════════════════════════════════════════════════════════════
# BUCKET — ensure exists
# ════════════════════════════════════════════════════════════

def ensure_bucket(token: str) -> None:
    """Create bucket if it doesn't exist. 409 = already exists = OK."""
    r = requests.post(
        APS_OSS_URL,
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"bucketKey": APS_BUCKET, "policyKey": "transient"},
        timeout=15,
    )
    if r.status_code not in (200, 409):
        logger.error("Bucket creation failed: %s %s", r.status_code, r.text[:200])
        r.raise_for_status()
    logger.info("Bucket '%s' ready", APS_BUCKET)


# ════════════════════════════════════════════════════════════
# UPLOAD — Direct-to-S3 (signed URL workflow)
# ════════════════════════════════════════════════════════════

def upload_file(filepath: str, object_key: str, token: str) -> str:
    """
    Upload file to APS OSS via signed S3 URL.
    Returns the base64-encoded URN for Model Derivative.
    """
    with open(filepath, "rb") as f:
        content = f.read()

    file_size = len(content)
    logger.info("Uploading %s (%.1f MB)...", object_key, file_size / 1024 / 1024)

    # Step 1: Get signed URL
    url = f"{APS_OSS_URL}/{APS_BUCKET}/objects/{object_key}/signeds3upload"
    r = requests.get(url, headers=auth_headers(token), timeout=15)
    r.raise_for_status()
    signed_data = r.json()
    upload_url = signed_data["urls"][0]
    upload_key = signed_data["uploadKey"]

    # Step 2: PUT to S3
    r = requests.put(upload_url, data=content, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"S3 upload failed: {r.status_code} {r.text[:200]}")
    etag = r.headers.get("ETag", "").strip('"')
    logger.info("S3 upload OK, ETag=%s", etag)

    # Step 3: Finalize
    r = requests.post(
        url,
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"uploadKey": upload_key, "size": file_size, "eTags": [etag]},
        timeout=30,
    )
    r.raise_for_status()
    object_id = r.json().get("objectId", f"urn:adsk.objects:os.object:{APS_BUCKET}/{object_key}")
    logger.info("Finalize OK: %s", object_id)

    # Encode URN for Model Derivative
    urn = base64.urlsafe_b64encode(object_id.encode()).decode().rstrip("=")
    return urn


# ════════════════════════════════════════════════════════════
# MODEL DERIVATIVE — translation + polling
# ════════════════════════════════════════════════════════════

def start_translation(urn: str, token: str) -> dict:
    """Start DWG → SVF2 translation job."""
    r = requests.post(
        f"{APS_MD_URL}/job",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={
            "input": {"urn": urn},
            "output": {"formats": [{"type": "svf2", "views": ["2d", "3d"]}]},
        },
        timeout=30,
    )
    r.raise_for_status()
    result = r.json()
    logger.info("Translation started: %s", result.get("result", "?"))
    return result


def wait_for_translation(urn: str, token: str, timeout_s: int = 300) -> dict:
    """Poll manifest until translation is complete or timeout."""
    start = time.time()
    while time.time() - start < timeout_s:
        r = requests.get(
            f"{APS_MD_URL}/{urn}/manifest",
            headers=auth_headers(token),
            timeout=15,
        )
        if r.status_code != 200:
            time.sleep(5)
            continue
        manifest = r.json()
        progress = manifest.get("progress", "")
        status = manifest.get("status", "")
        logger.info("Translation: progress=%s status=%s", progress, status)

        if progress == "complete":
            if status == "success":
                return manifest
            elif status == "failed":
                raise RuntimeError(f"Translation failed: {json.dumps(manifest)[:500]}")

        time.sleep(5)

    raise TimeoutError(f"Translation timeout after {timeout_s}s")


# ════════════════════════════════════════════════════════════
# METADATA — extract geometry from properties
# ════════════════════════════════════════════════════════════

def get_viewable_guids(urn: str, token: str) -> List[Dict]:
    """Get list of viewable GUIDs from metadata."""
    r = requests.get(
        f"{APS_MD_URL}/{urn}/metadata",
        headers=auth_headers(token),
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("metadata", [])


def get_properties(urn: str, guid: str, token: str, max_retries: int = 10) -> List[Dict]:
    """
    Get all object properties for a viewable.
    Retries on 202 (processing) up to max_retries times.
    """
    url = f"{APS_MD_URL}/{urn}/metadata/{guid}/properties?forceget=true"
    for attempt in range(max_retries):
        r = requests.get(url, headers=auth_headers(token), timeout=60)
        if r.status_code == 200:
            return r.json().get("data", {}).get("collection", [])
        elif r.status_code == 202:
            logger.info("Properties processing (attempt %d/%d)...", attempt + 1, max_retries)
            time.sleep(10)
        else:
            logger.warning("Properties request failed: %s", r.status_code)
            time.sleep(5)
    logger.warning("Properties not ready after %d attempts", max_retries)
    return []


def extract_geometry(properties: List[Dict]) -> Dict[str, Any]:
    """
    Extract structural geometry from APS properties.
    Returns axes, dimensions, layers, emprise for the Eurocodes engine.
    """
    layers = Counter()
    axes_lines = []
    dimensions = []
    mur_count = 0
    texts = []

    for item in properties:
        p = item.get("properties", {})
        gen = p.get("General", {})
        geom = p.get("Geometry", {})
        text_props = p.get("Text", {})

        layer = gen.get("Layer", "")
        obj_type = gen.get("Name ", "")

        if layer:
            layers[layer] += 1

        # Axes
        if layer.lower() in ("axes", "axe", "axis", "a-axes", "grille"):
            length_str = geom.get("Length", "0")
            angle_str = geom.get("Angle", "0")
            try:
                length = float(length_str.replace(",", "."))
                angle = float(angle_str.replace(" deg", "").replace(",", "."))
            except (ValueError, AttributeError):
                length, angle = 0, 0
            if length > 0:
                axes_lines.append({"length_mm": length, "angle_deg": angle})

        # Dimensions (cotations)
        if obj_type in ("Rotated Dimension", "Aligned Dimension", "Linear Dimension"):
            measurement = text_props.get("Measurement", "")
            dim_scale = p.get("Primary Units", {}).get("Dim scale linear", "1")
            try:
                value = float(measurement.replace(",", ".")) if measurement else 0
                scale = float(dim_scale.replace(",", ".")) if dim_scale else 1
            except (ValueError, AttributeError):
                value, scale = 0, 1
            if value > 0:
                dimensions.append({
                    "value": value,
                    "scale": scale,
                    "layer": layer,
                })

        # Walls
        if layer.upper() in ("MUR", "MURS", "A-MUR", "WALL", "WALLS"):
            mur_count += 1

        # Texts (room labels, etc.)
        if obj_type in ("MText", "Text") and layer in ("Etiquettes de pièces", "TEXTES", "TEXT_3"):
            name = item.get("name", "")
            if name:
                texts.append(name)

    # ── Analyze axes to find grid ──
    axes_x = []  # horizontal (angle ~0 or ~180)
    axes_y = []  # vertical (angle ~90 or ~270)
    for ax in axes_lines:
        a = ax["angle_deg"] % 360
        if a < 10 or a > 350 or (170 < a < 190):
            axes_x.append(ax["length_mm"])
        elif (80 < a < 100) or (260 < a < 280):
            axes_y.append(ax["length_mm"])

    # ── Analyze dimensions to find portées ──
    dim_values = sorted(set(d["value"] for d in dimensions))
    # Filter structural portées (typically 300-800 cm)
    portees = [v for v in dim_values if 200 <= v <= 1200]
    # Filter wall thicknesses (typically 15-30 cm)
    mur_eps = [v for v in dim_values if 10 <= v <= 50]
    # Filter room dimensions (typically 200-600 cm)
    room_dims = [v for v in dim_values if 100 <= v <= 800]

    # ── Emprise from axes ──
    emprise_x = max(axes_x) if axes_x else 0  # in mm
    emprise_y = max(axes_y) if axes_y else 0  # in mm
    if emprise_x == 0 and emprise_y == 0:
        # Fallback: use longest axes regardless of direction
        all_lengths = [ax["length_mm"] for ax in axes_lines]
        if len(all_lengths) >= 2:
            all_lengths_sorted = sorted(set(all_lengths), reverse=True)
            emprise_x = all_lengths_sorted[0]
            emprise_y = all_lengths_sorted[1] if len(all_lengths_sorted) > 1 else all_lengths_sorted[0]

    # ── Estimate grid from axis count ──
    nb_axes_x = len(axes_x) if axes_x else 0
    nb_axes_y = len(axes_y) if axes_y else 0

    # ── Determine portée from dimensions ──
    portee_max = max(portees) / 100 if portees else 0  # cm → m
    portee_min = min(portees) / 100 if portees else 0

    # If no portées found in dimensions, estimate from axes
    if portee_max == 0 and nb_axes_x > 1 and emprise_x > 0:
        portee_max = (emprise_x / (nb_axes_x - 1)) / 1000  # mm → m
        portee_min = portee_max * 0.7

    return {
        "layers": dict(layers.most_common(20)),
        "nb_axes_x": nb_axes_x,
        "nb_axes_y": nb_axes_y,
        "axes_x_lengths_mm": sorted(set(axes_x)),
        "axes_y_lengths_mm": sorted(set(axes_y)),
        "emprise_x_mm": emprise_x,
        "emprise_y_mm": emprise_y,
        "emprise_x_m": round(emprise_x / 1000, 2),
        "emprise_y_m": round(emprise_y / 1000, 2),
        "nb_travees_x": max(nb_axes_x - 1, 1),
        "nb_travees_y": max(nb_axes_y - 1, 1),
        "portee_max_m": round(portee_max, 2),
        "portee_min_m": round(portee_min, 2),
        "dimensions_all_cm": sorted(dim_values),
        "portees_cm": portees,
        "epaisseurs_mur_cm": mur_eps,
        "room_dims_cm": room_dims,
        "nb_murs": mur_count,
        "nb_dimensions": len(dimensions),
        "nb_total_objects": len(properties),
        "room_labels": texts[:20],
    }


# ════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════

def parser_dwg_aps(filepath: str, nb_niveaux: int = None, ville: str = "Dakar") -> Dict[str, Any]:
    """
    Full pipeline: DWG file → APS → structured geometry for Eurocodes engine.

    Args:
        filepath: Path to DWG file on disk
        nb_niveaux: Number of levels (if known)
        ville: City name

    Returns:
        Dict with ok=True and geometry data, or ok=False with error message.
    """
    try:
        token = get_token()
        ensure_bucket(token)

        # Generate unique object key
        timestamp = int(time.time())
        filename = os.path.basename(filepath).replace(" ", "_")
        object_key = f"tijan_{timestamp}_{filename}"

        # Upload
        urn = upload_file(filepath, object_key, token)
        logger.info("URN: %s", urn)

        # Translate
        token = get_token()  # refresh if needed
        start_translation(urn, token)
        manifest = wait_for_translation(urn, token, timeout_s=300)

        # Get DWG metadata
        dwg_info = {}
        for deriv in manifest.get("derivatives", []):
            doc_info = deriv.get("properties", {}).get("Document Information", {})
            if doc_info:
                dwg_info = doc_info
                break

        # Get viewables and extract 2D properties
        token = get_token()
        viewables = get_viewable_guids(urn, token)
        logger.info("Viewables: %s", [(v["name"], v["role"]) for v in viewables])

        # Prefer 2D view for property extraction
        target_guid = None
        for v in viewables:
            if v.get("role") == "2d" and v.get("name") in ("2D View", "Model"):
                target_guid = v["guid"]
                break
        if not target_guid:
            for v in viewables:
                if v.get("role") == "2d":
                    target_guid = v["guid"]
                    break
        if not target_guid and viewables:
            target_guid = viewables[0]["guid"]

        if not target_guid:
            return {"ok": False, "message": "Aucune vue trouvée dans le DWG"}

        # Extract properties
        token = get_token()
        properties = get_properties(urn, target_guid, token)
        if not properties:
            return {"ok": False, "message": "Impossible d'extraire les propriétés du DWG"}

        # Analyze geometry
        geo = extract_geometry(properties)

        # Compute surface
        surface = (geo["emprise_x_m"] * geo["emprise_y_m"])
        if surface < 50:
            # Fallback: estimate from dimension data
            if geo["portees_cm"]:
                avg_portee = sum(geo["portees_cm"]) / len(geo["portees_cm"]) / 100
                surface = avg_portee * avg_portee * geo["nb_travees_x"] * geo["nb_travees_y"]

        # Build engine input
        donnees_moteur = {
            "nom": dwg_info.get("Name", filename).replace(".dwg", ""),
            "ville": ville,
            "nb_niveaux": nb_niveaux or 4,
            "hauteur_etage_m": 3.0,
            "surface_emprise_m2": round(surface, 1),
            "portee_max_m": geo["portee_max_m"] or 5.0,
            "portee_min_m": geo["portee_min_m"] or 4.0,
            "nb_travees_x": geo["nb_travees_x"],
            "nb_travees_y": geo["nb_travees_y"],
            "usage_principal": "residentiel",
            "classe_beton": "C30/37",
            "classe_acier": "HA500",
            "pression_sol_MPa": 0.15,
            "profondeur_fondation_m": 1.5,
            "distance_mer_km": 2.0,
            "zone_sismique": 1,
            "enrobage_mm": 30.0,
        }

        return {
            "ok": True,
            "source": "aps",
            "urn": urn,
            "viewable_guid": target_guid,
            "dwg_info": dwg_info,
            "geometrie": {
                "nb_axes_x": geo["nb_axes_x"],
                "nb_axes_y": geo["nb_axes_y"],
                "emprise_x_m": geo["emprise_x_m"],
                "emprise_y_m": geo["emprise_y_m"],
                "portee_max_m": geo["portee_max_m"],
                "portee_min_m": geo["portee_min_m"],
                "nb_travees_x": geo["nb_travees_x"],
                "nb_travees_y": geo["nb_travees_y"],
                "nb_murs": geo["nb_murs"],
                "nb_dimensions": geo["nb_dimensions"],
                "nb_total_objects": geo["nb_total_objects"],
                "portees_cm": geo["portees_cm"][:20],
                "epaisseurs_mur_cm": geo["epaisseurs_mur_cm"][:10],
                "layers": geo["layers"],
                "room_labels": geo["room_labels"],
            },
            "donnees_moteur": donnees_moteur,
        }

    except EnvironmentError as e:
        return {"ok": False, "message": str(e)}
    except TimeoutError as e:
        return {"ok": False, "message": f"Timeout traduction APS: {e}"}
    except requests.HTTPError as e:
        return {"ok": False, "message": f"Erreur API APS: {e}"}
    except Exception as e:
        logger.exception("APS parser error")
        return {"ok": False, "message": f"Erreur parsing APS: {e}"}


# ════════════════════════════════════════════════════════════
# CLI TEST
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        result = parser_dwg_aps(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python aps_parser_v2.py <fichier.dwg>")

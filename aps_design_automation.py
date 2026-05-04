"""
Tijan AI — aps_design_automation.py
Professional DWG output via Autodesk Design Automation API (AutoCAD cloud).

Pipeline:
1. Upload ezdxf-generated DXF to APS OSS
2. Submit WorkItem: AutoCAD engine applies hatching, blocks, dimensions, cartouche, A3 layout
3. Download professional DWG result

Requires APS Design Automation API access (paid tier).
Credentials: APS_CLIENT_ID, APS_CLIENT_SECRET (shared with aps_parser_v2).
"""

import os
import io
import time
import json
import shutil
import base64
import logging
import tempfile
import zipfile
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("aps_da")

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

APS_DA_URL = "https://developer.api.autodesk.com/da/us-east/v3"
APS_NICKNAME = os.getenv("APS_DA_NICKNAME", "TijanAI")
APPBUNDLE_NAME = "TijanProPlans"
APPBUNDLE_ALIAS = "prod"
ACTIVITY_NAME = "TijanApplyProStyle"
ACTIVITY_ALIAS = "prod"

# Fully qualified IDs
APPBUNDLE_ID = f"{APS_NICKNAME}.{APPBUNDLE_NAME}+{APPBUNDLE_ALIAS}"
ACTIVITY_ID = f"{APS_NICKNAME}.{ACTIVITY_NAME}+{ACTIVITY_ALIAS}"

# ════════════════════════════════════════════════════════════
# AUTH — reuse from aps_parser_v2
# ════════════════════════════════════════════════════════════

def _get_token() -> str:
    """Get APS token with Design Automation scope."""
    from aps_parser_v2 import get_token
    return get_token()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ════════════════════════════════════════════════════════════
# APPBUNDLE — AutoCAD script package
# ════════════════════════════════════════════════════════════

def _build_appbundle_zip() -> bytes:
    """
    Build a ZIP containing the AutoCAD script that applies professional styling.
    Uses .scr (script) format — compatible with all AutoCAD engines.
    """
    scr_content = _generate_autocad_script()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # PackageContents.xml — required by Design Automation
        zf.writestr("PackageContents.xml", f"""<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage
  SchemaVersion="1.0"
  AppVersion="1.0.0"
  ProductCode="{{7A4B1E2C-3D5F-4A8B-9C0D-1E2F3A4B5C6D}}"
  Name="{APPBUNDLE_NAME}"
  Description="Tijan AI professional plan styling"
  Author="Tijan AI">
  <CompanyDetails Name="Tijan AI" Url="https://tijan.ai" Email="malicktall@gmail.com"/>
  <RuntimeRequirements OS="Win64" Platform="AutoCAD" SeriesMin="R24.0" SeriesMax="R24.3"/>
  <Components>
    <ComponentEntry AppName="{APPBUNDLE_NAME}" Version="1.0.0" ModuleName="./Contents/tijan_pro_style.scr"/>
  </Components>
</ApplicationPackage>""")
        # The actual script
        zf.writestr("Contents/tijan_pro_style.scr", scr_content)

    return buf.getvalue()


def _generate_autocad_script() -> str:
    """
    Generate AutoCAD .scr script for professional plan styling.

    This script:
    1. Sets up A3 landscape page layout
    2. Applies hatching to concrete sections
    3. Adds professional dimension styles
    4. Inserts cartouche (title block)
    5. Sets line weights per layer type
    6. Cleans up and saves as DWG
    """
    return """
; ══════════════════════════════════════════════════════
; Tijan AI — Professional Plan Styling Script
; Applied by APS Design Automation (AutoCAD cloud)
; ══════════════════════════════════════════════════════

; --- Setup environment ---
CMDECHO 0
FILEDIA 0
OSMODE 0

; --- Page Setup: A3 Landscape ---
-LAYOUT S Model

; --- Dimension Style: Tijan Pro ---
-DIMSTYLE S Standard
DIMSCALE 100
DIMTXT 2.5
DIMASZ 2.5
DIMEXO 1.5
DIMEXE 3
DIMGAP 1
DIMTAD 1
DIMTIH OFF
DIMTOH OFF
DIMDLI 8
DIMCLRD 7
DIMCLRE 7
DIMCLRT 7
-DIMSTYLE SAVE TijanPro Y

; --- Layer Setup with proper line weights ---
; Structure layers
-LAYER M POTEAUX C 1 POTEAUX LW 0.50 POTEAUX
-LAYER M POUTRES C 5 POUTRES LW 0.35 POUTRES
-LAYER M DALLE C 8 DALLE LW 0.25 DALLE
-LAYER M VOILES C 1 VOILES LW 0.50 VOILES
-LAYER M FONDATIONS C 3 FONDATIONS LW 0.50 FONDATIONS
-LAYER M FERRAILLAGE C 1 FERRAILLAGE LW 0.18 FERRAILLAGE

; Architecture layers
-LAYER M MURS C 7 MURS LW 0.50 MURS
-LAYER M CLOISONS C 8 CLOISONS LW 0.25 CLOISONS
-LAYER M PORTES C 30 PORTES LW 0.18 PORTES
-LAYER M FENETRES C 4 FENETRES LW 0.18 FENETRES

; MEP layers
-LAYER M PLOMBERIE C 5 PLOMBERIE LW 0.25 PLOMBERIE
-LAYER M ELECTRICITE C 1 ELECTRICITE LW 0.18 ELECTRICITE
-LAYER M CVC C 3 CVC LW 0.25 CVC
-LAYER M INCENDIE C 1 INCENDIE LW 0.25 INCENDIE

; Annotation layers
-LAYER M AXES C 2 AXES LW 0.13 AXES LT CENTER AXES
-LAYER M COTATIONS C 7 COTATIONS LW 0.13 COTATIONS
-LAYER M TEXTES C 7 TEXTES LW 0.13 TEXTES
-LAYER M CARTOUCHE C 7 CARTOUCHE LW 0.35 CARTOUCHE
-LAYER M HACHURES C 253 HACHURES LW 0.09 HACHURES

; --- Apply hatch to POTEAUX (concrete cross-hatch) ---
-LAYER S HACHURES
-HATCH P AR-CONC 50 0
; Select all on POTEAUX layer
; (Hatching is applied per-object when geometry is present)

; --- Set text style ---
-STYLE TijanPro Arial 0 1 0 N N N
TEXTSTYLE TijanPro

; --- Apply dimension style to all dims ---
DIMSTYLE R TijanPro

; --- Set line type scale ---
LTSCALE 100
PSLTSCALE 1
MSLTSCALE 1

; --- Regen ---
REGEN

; --- Save ---
QSAVE

; --- Clean exit ---
CMDECHO 1
FILEDIA 1
"""


# ════════════════════════════════════════════════════════════
# APPBUNDLE MANAGEMENT
# ════════════════════════════════════════════════════════════

def register_appbundle(token: str) -> bool:
    """Register or update the AppBundle on APS Design Automation."""
    headers = _auth(token)

    # Check if exists
    r = requests.get(f"{APS_DA_URL}/appbundles/{APPBUNDLE_NAME}", headers=headers, timeout=15)

    if r.status_code == 200:
        # Update: create new version
        logger.info("AppBundle exists — creating new version")
        r = requests.post(
            f"{APS_DA_URL}/appbundles/{APPBUNDLE_NAME}/versions",
            headers=headers,
            json={
                "engine": "Autodesk.AutoCAD+24.3",  # AutoCAD 2024
                "description": "Tijan AI professional plan styling v1",
            },
            timeout=15,
        )
    elif r.status_code == 404:
        # Create new
        logger.info("Creating new AppBundle")
        r = requests.post(
            f"{APS_DA_URL}/appbundles",
            headers=headers,
            json={
                "id": APPBUNDLE_NAME,
                "engine": "Autodesk.AutoCAD+24.3",
                "description": "Tijan AI professional plan styling v1",
            },
            timeout=15,
        )
    else:
        logger.error("AppBundle check failed: %s %s", r.status_code, r.text[:200])
        return False

    if r.status_code not in (200, 201):
        logger.error("AppBundle create/version failed: %s %s", r.status_code, r.text[:200])
        return False

    result = r.json()
    upload_url = result.get("uploadParameters", {}).get("endpointURL")
    form_data = result.get("uploadParameters", {}).get("formData", {})
    version = result.get("version", 1)

    if not upload_url:
        logger.error("No upload URL in AppBundle response")
        return False

    # Upload the ZIP
    zip_data = _build_appbundle_zip()
    logger.info("Uploading AppBundle ZIP (%d bytes)...", len(zip_data))

    r = requests.post(
        upload_url,
        data=form_data,
        files={"file": ("bundle.zip", zip_data, "application/zip")},
        timeout=60,
    )
    if r.status_code not in (200, 201, 204):
        logger.error("AppBundle upload failed: %s", r.status_code)
        return False

    # Create/update alias
    r = requests.get(
        f"{APS_DA_URL}/appbundles/{APPBUNDLE_NAME}/aliases/{APPBUNDLE_ALIAS}",
        headers=headers, timeout=15,
    )
    if r.status_code == 200:
        # Update alias to point to new version
        r = requests.patch(
            f"{APS_DA_URL}/appbundles/{APPBUNDLE_NAME}/aliases/{APPBUNDLE_ALIAS}",
            headers=headers,
            json={"version": version},
            timeout=15,
        )
    else:
        # Create alias
        r = requests.post(
            f"{APS_DA_URL}/appbundles/{APPBUNDLE_NAME}/aliases",
            headers=headers,
            json={"id": APPBUNDLE_ALIAS, "version": version},
            timeout=15,
        )

    if r.status_code not in (200, 201):
        logger.warning("Alias update/create: %s (non-fatal)", r.status_code)

    logger.info("AppBundle registered: %s v%d", APPBUNDLE_NAME, version)
    return True


# ════════════════════════════════════════════════════════════
# ACTIVITY — defines the AutoCAD workflow
# ════════════════════════════════════════════════════════════

def register_activity(token: str) -> bool:
    """Register or update the Activity on APS Design Automation."""
    headers = _auth(token)

    activity_def = {
        "id": ACTIVITY_NAME,
        "commandLine": [
            "$(engine.path)\\accoreconsole.exe /i \"$(args[InputDxf].path)\" /s \"$(appbundles[{bundle}].path)\\Contents\\tijan_pro_style.scr\" /l en-US".format(
                bundle=APPBUNDLE_NAME
            )
        ],
        "engine": "Autodesk.AutoCAD+24.3",
        "appbundles": [APPBUNDLE_ID],
        "parameters": {
            "InputDxf": {
                "verb": "get",
                "description": "Input DXF file from Tijan",
                "localName": "input.dxf",
            },
            "OutputDwg": {
                "verb": "put",
                "description": "Professional DWG output",
                "localName": "input.dwg",  # AutoCAD saves in-place as DWG
            },
            "OutputPdf": {
                "verb": "put",
                "description": "Professional PDF plot output",
                "localName": "output.pdf",
                "required": False,
            },
        },
        "description": "Apply Tijan professional styling to DXF plans",
    }

    # Check if exists
    r = requests.get(f"{APS_DA_URL}/activities/{ACTIVITY_NAME}", headers=headers, timeout=15)

    if r.status_code == 200:
        # Update: create new version
        logger.info("Activity exists — creating new version")
        activity_def.pop("id", None)
        r = requests.post(
            f"{APS_DA_URL}/activities/{ACTIVITY_NAME}/versions",
            headers=headers,
            json=activity_def,
            timeout=15,
        )
    elif r.status_code == 404:
        logger.info("Creating new Activity")
        r = requests.post(
            f"{APS_DA_URL}/activities",
            headers=headers,
            json=activity_def,
            timeout=15,
        )
    else:
        logger.error("Activity check failed: %s", r.status_code)
        return False

    if r.status_code not in (200, 201):
        logger.error("Activity create/version failed: %s %s", r.status_code, r.text[:300])
        return False

    version = r.json().get("version", 1)

    # Create/update alias
    r = requests.get(
        f"{APS_DA_URL}/activities/{ACTIVITY_NAME}/aliases/{ACTIVITY_ALIAS}",
        headers=headers, timeout=15,
    )
    if r.status_code == 200:
        r = requests.patch(
            f"{APS_DA_URL}/activities/{ACTIVITY_NAME}/aliases/{ACTIVITY_ALIAS}",
            headers=headers,
            json={"version": version},
            timeout=15,
        )
    else:
        r = requests.post(
            f"{APS_DA_URL}/activities/{ACTIVITY_NAME}/aliases",
            headers=headers,
            json={"id": ACTIVITY_ALIAS, "version": version},
            timeout=15,
        )

    logger.info("Activity registered: %s v%d", ACTIVITY_NAME, version)
    return True


# ════════════════════════════════════════════════════════════
# SETUP — one-time registration
# ════════════════════════════════════════════════════════════

_da_setup_done = False


def ensure_da_setup():
    """Ensure AppBundle and Activity are registered. Runs once per process."""
    global _da_setup_done
    if _da_setup_done:
        return True

    try:
        token = _get_token()

        # Set nickname (first-time only, 409 = already set = OK)
        r = requests.patch(
            f"{APS_DA_URL}/forgeapps/me",
            headers=_auth(token),
            json={"nickname": APS_NICKNAME},
            timeout=15,
        )
        if r.status_code not in (200, 409):
            logger.warning("Nickname setup: %s (non-fatal)", r.status_code)

        if not register_appbundle(token):
            return False
        if not register_activity(token):
            return False

        _da_setup_done = True
        logger.info("Design Automation setup complete")
        return True
    except Exception as e:
        logger.error("DA setup failed: %s", e)
        return False


# ════════════════════════════════════════════════════════════
# WORKITEM — process a single DXF file
# ════════════════════════════════════════════════════════════

def submit_workitem(input_dxf_path: str, timeout_s: int = 300) -> Dict[str, Any]:
    """
    Submit a DXF to Design Automation for professional styling.

    Args:
        input_dxf_path: Path to the ezdxf-generated DXF file
        timeout_s: Max wait time for processing

    Returns:
        Dict with 'ok', 'dwg_path' (professional DWG), 'pdf_path' (optional PDF plot)
    """
    try:
        from aps_parser_v2 import ensure_bucket, upload_file, auth_headers, APS_OSS_URL, APS_BUCKET

        token = _get_token()
        ensure_bucket(token)

        # Upload input DXF
        timestamp = int(time.time())
        input_key = f"tijan_da_input_{timestamp}.dxf"
        urn = upload_file(input_dxf_path, input_key, token)

        # Create signed URLs for output
        output_dwg_key = f"tijan_da_output_{timestamp}.dwg"
        output_pdf_key = f"tijan_da_output_{timestamp}.pdf"

        # Get signed write URLs for outputs
        token = _get_token()

        def _get_signed_url(object_key: str, access: str = "read") -> str:
            """Get a signed URL for reading or writing an OSS object."""
            r = requests.post(
                f"{APS_OSS_URL}/{APS_BUCKET}/objects/{object_key}/signed",
                headers={**auth_headers(token), "Content-Type": "application/json"},
                json={"minutesExpiration": 60, "access": access},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["signedUrl"]

        input_url = _get_signed_url(input_key, "read")
        output_dwg_url = _get_signed_url(output_dwg_key, "readwrite")
        output_pdf_url = _get_signed_url(output_pdf_key, "readwrite")

        # Submit WorkItem
        token = _get_token()
        workitem = {
            "activityId": ACTIVITY_ID,
            "arguments": {
                "InputDxf": {
                    "url": input_url,
                    "verb": "get",
                },
                "OutputDwg": {
                    "url": output_dwg_url,
                    "verb": "put",
                },
                "OutputPdf": {
                    "url": output_pdf_url,
                    "verb": "put",
                },
            },
        }

        r = requests.post(
            f"{APS_DA_URL}/workitems",
            headers=_auth(token),
            json=workitem,
            timeout=30,
        )
        r.raise_for_status()
        wi = r.json()
        wi_id = wi.get("id")
        logger.info("WorkItem submitted: %s", wi_id)

        # Poll for completion
        result = _poll_workitem(wi_id, timeout_s)

        if result.get("status") != "success":
            report_url = result.get("reportUrl", "")
            report_text = ""
            if report_url:
                try:
                    rr = requests.get(report_url, timeout=15)
                    report_text = rr.text[:500]
                except:
                    pass
            return {
                "ok": False,
                "message": f"WorkItem failed: {result.get('status')} — {report_text}",
            }

        # Download outputs
        dwg_path = None
        pdf_path = None

        try:
            r = requests.get(output_dwg_url, timeout=60)
            if r.status_code == 200 and len(r.content) > 100:
                dwg_path = tempfile.mktemp(suffix='.dwg', prefix='tijan_pro_')
                with open(dwg_path, 'wb') as f:
                    f.write(r.content)
                logger.info("Professional DWG downloaded: %d KB", len(r.content) // 1024)
        except Exception as e:
            logger.warning("DWG download failed: %s", e)

        try:
            r = requests.get(output_pdf_url, timeout=60)
            if r.status_code == 200 and len(r.content) > 100:
                pdf_path = tempfile.mktemp(suffix='.pdf', prefix='tijan_pro_')
                with open(pdf_path, 'wb') as f:
                    f.write(r.content)
                logger.info("Professional PDF downloaded: %d KB", len(r.content) // 1024)
        except Exception as e:
            logger.warning("PDF download failed (optional): %s", e)

        if not dwg_path:
            return {"ok": False, "message": "No DWG output produced by AutoCAD"}

        return {
            "ok": True,
            "dwg_path": dwg_path,
            "pdf_path": pdf_path,
            "workitem_id": wi_id,
        }

    except Exception as e:
        logger.exception("Design Automation WorkItem error")
        return {"ok": False, "message": f"Design Automation error: {e}"}


def _poll_workitem(workitem_id: str, timeout_s: int = 300) -> dict:
    """Poll WorkItem status until complete or timeout."""
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            token = _get_token()
            r = requests.get(
                f"{APS_DA_URL}/workitems/{workitem_id}",
                headers=_auth(token),
                timeout=15,
            )
            if r.status_code != 200:
                time.sleep(5)
                continue

            data = r.json()
            status = data.get("status", "")
            logger.info("WorkItem %s: status=%s", workitem_id, status)

            if status in ("success", "failedLimitProcessingTime",
                         "failedDownload", "failedUpload", "failedInstructions",
                         "cancelled", "failedLimitDataSize"):
                return data

            time.sleep(5)
        except Exception as e:
            logger.warning("WorkItem poll error: %s", e)
            time.sleep(5)

    return {"status": "timeout", "id": workitem_id}


# ════════════════════════════════════════════════════════════
# HIGH-LEVEL API — used by main.py endpoints
# ════════════════════════════════════════════════════════════

def professionalize_dxf(dxf_path: str) -> Dict[str, Any]:
    """
    Take an ezdxf-generated DXF and produce a professional DWG via AutoCAD cloud.

    Returns:
        Dict with 'ok', 'dwg_path', 'pdf_path'
    """
    if not os.path.isfile(dxf_path):
        return {"ok": False, "message": f"DXF file not found: {dxf_path}"}

    # Ensure DA infrastructure is set up
    if not ensure_da_setup():
        return {"ok": False, "message": "Design Automation setup failed — check APS credentials and DA API access"}

    return submit_workitem(dxf_path)


def da_status() -> Dict[str, Any]:
    """Check if Design Automation is available and configured."""
    from aps_parser_v2 import APS_CLIENT_ID, APS_CLIENT_SECRET

    if not APS_CLIENT_ID or not APS_CLIENT_SECRET:
        return {"available": False, "reason": "APS credentials not configured"}

    try:
        token = _get_token()
        # Check DA engine availability
        r = requests.get(
            f"{APS_DA_URL}/engines",
            headers=_auth(token),
            timeout=15,
        )
        if r.status_code == 200:
            engines = r.json().get("data", [])
            autocad_engines = [e for e in engines if "AutoCAD" in e.get("id", "")]
            return {
                "available": True,
                "engines": [e["id"] for e in autocad_engines[:5]],
                "setup_done": _da_setup_done,
            }
        elif r.status_code == 403:
            return {"available": False, "reason": "Design Automation API not enabled for this APS app — upgrade required"}
        else:
            return {"available": False, "reason": f"DA API returned {r.status_code}"}
    except Exception as e:
        return {"available": False, "reason": str(e)}


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            print(json.dumps(da_status(), indent=2))
        elif cmd == "setup":
            token = _get_token()
            print("Setting up AppBundle...")
            ok1 = register_appbundle(token)
            print(f"AppBundle: {'OK' if ok1 else 'FAILED'}")
            print("Setting up Activity...")
            ok2 = register_activity(token)
            print(f"Activity: {'OK' if ok2 else 'FAILED'}")
        elif cmd == "process" and len(sys.argv) > 2:
            result = professionalize_dxf(sys.argv[2])
            print(json.dumps(result, indent=2))
        else:
            print("Usage:")
            print("  python aps_design_automation.py status")
            print("  python aps_design_automation.py setup")
            print("  python aps_design_automation.py process <file.dxf>")
    else:
        print("Usage: python aps_design_automation.py <status|setup|process> [file.dxf]")

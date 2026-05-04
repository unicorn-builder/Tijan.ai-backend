# Tijan AI — Project Memory

## Contexte
- **Fondateur:** Serigne Malick Tall (Malick), malicktall@gmail.com
- **Mission:** Premier fondateur non-technique a construire une licorne
- **Regle absolue:** Ne jamais suggerer d'embaucher ou de recruter un co-fondateur technique
- **Outils:** Claude Code (terminal), Claude mobile app, Cowork (desktop) — garder le contexte synchro partout

## What is Tijan?
Tijan AI is an **automated engineering bureau (bureau d'etudes automatise)** for West African construction projects. It generates structural calculations, MEP designs, BOQs, BIM plans, and EDGE certification reports — all Eurocode-compliant.

## Stack
- **Backend:** FastAPI 0.110.0 / Python 3.11 / Uvicorn (port 10000) on Render (build-ai-backend.onrender.com), repo ~/tijan-repo
- **Frontend:** React/Vite on Vercel (tijan.ai), repo ~/Downloads/tijan-frontend
- **Admin:** tijan-admin.vercel.app, repo ~/Downloads/tijan-admin
- **DB:** Supabase (projets, credits, payments, support tickets)
- **AI:** Anthropic Claude SDK + OpenAI (for parsing and chat)
- **PDF:** ReportLab + PyPDF + PyMuPDF
- **Office:** python-docx (Word), openpyxl (Excel)
- **CAD:** ezdxf (DXF), ODA + LibreDWG (DWG conversion), APS Design Automation (pro DWG output)
- **GitHub:** unicorn-builder/Tijan.ai-backend

## Architecture
- **32+ endpoints** covering: health, parsing, calculation, PDF/Excel/Word/DXF generation, chat, payments, translation
- **Lazy loading** — engine modules imported on first request
- **i18n** — French/English for all outputs
- **Multi-country** — Senegal, Cote d'Ivoire, Morocco, Nigeria, Ghana (auto-pricing by city)

## Key Files
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + all endpoints (~1843 lines) |
| `engine_structure_v2.py` | Structural calculations EC2/EC8 (~2000 lines) |
| `engine_mep_v2.py` | MEP calculations (~2000 lines) |
| `gen_*.py` | PDF/Excel/Word generators (FR + EN variants) |
| `generate_plans_*.py` | BA drawings, plumbing plans, architecture plans |
| `parse_plans.py` | DWG/DXF/PDF parameter extraction |
| `dwg_converter.py` | DWG to DXF conversion (ODA/LibreDWG/APS) |
| `aps_design_automation.py` | Professional DWG output via APS Design Automation |
| `prix_marche.py` | Market pricing database (5 countries) |
| `chat_engine.py` | LLM-based design assistant |
| `tijan_theme.py` | PDF branding/styling |

## Engineering Standards
- **Structural:** Eurocode 2 (EC2) for concrete, Eurocode 8 (EC8) for seismic
- **MEP:** French DTU standards, IT 246 (fire safety), IFC EDGE v3 (green certification)
- **Concrete classes:** C20/25 to C40/50 (auto-selected by project)
- **Steel:** HA400, HA500 (auto-selected)
- **Seismic zones:** Auto from country (Senegal zone 2, etc.)

## Regles de developpement
- Zero hardcoding — toutes les valeurs viennent des calculs reels
- Aucune fonction deboguee plus de 3 fois — reecrire si ca continue a echouer
- Monkey-patching de ReportLab Paragraph est INTERDIT
- JSX: pas de > au debut de ligne dans les balises <a>
- `from tijan_theme import *` n'exporte pas les variables prefixees `_`
- i18n: fichier i18n.jsx (pas .js), hook useLang/LangProvider, fonction t()
- Supabase RLS: utiliser auth.uid() = user_id + GRANT ALL explicite

## Anti-regression
- Toujours lancer `./scripts/pre_deploy_check.sh` avant git push
- 44 tests pytest doivent passer (tests/)
- Verifier `/version` endpoint apres deploy pour confirmer le bon commit

## Pipeline geometrie
- DXF → ezdxf direct (3966 murs Sakho valides)
- DWG → APS DXF output → ezdxf
- PDF vectoriel → pymupdf get_drawings() → coordonnees XY
- Layers Aasaman: A-WALL, A-DOOR, A-GLAZ, I-WALL

## Projet de reference
- Residence Papa Oumar Sakho, R+8, 32 unites, Dakar, Ref. 1711
- Beton C30/37 BPE 185,000 FCFA/m3, acier HA500B 520-540 FCFA/kg

## Testing
- `tests/test_endpoints.py` — endpoint tests (requires live backend)
- `tests/test_e2e.py` — end-to-end integration tests
- `tests/test_cors.py` — CORS verification
- `tests/test_dxf_pipeline.py` — DXF parsing
- `tests/test_pdf_geometry.py` — PDF geometry
- `scripts/pre_deploy_check.sh` — Pre-deployment gate (all test groups)
- **Base URL for tests:** https://build-ai-backend.onrender.com

## Deployment Flow
1. Push to `main` branch
2. Render auto-deploys (runs `build.sh` for ODA install + pip)
3. Starts `uvicorn main:app --host 0.0.0.0 --port 10000`

## CORS Origins
- tijan.ai, api.tijan.ai, admin.tijan.ai
- Vercel preview deployments
- localhost:5173/5174 (dev)

## Current Version
- **v6.1.0** (March 2026)

## Bug Fix History (April 2026)
### Stress test — 65+ bugs found and fixed:
- **engine_structure_v2.py:** Fixed column cross-section formula units, NRd capacity (removed wrong 0.8 factor), sqrt guard, VRd_c shear per EC2 6.2.2, pile capacity units, coffrage division-by-zero, seismic mass using actual loads, As_min per EC2 9.3.1.1, pile load using max()
- **engine_mep_v2.py:** Fixed EDGE ventilation ratio div/zero, documented peak flow coefficient, EDGE energy gain consistency, RIA length per IT 246, removed dead EDGE variables, fixed personnes_par_logement
- **main.py:** Fixed httpx import order, temp file resource leaks (6 endpoints), bare except clauses (9 locations), _parse_jobs thread safety, translate JSON parsing, input validation, guids empty check, httpx timeout, PayDunya env warnings
- **parse_plans.py:** Fixed PDF resource leaks, JSON parsing error handling
- **aps_parser_v2.py:** Thread-safe token cache, S3 finalization validation
- **chat_engine.py:** API key validation
- **extract_project_data.py:** None arithmetic protection
- **dwg_converter.py:** Path sanitization
- **gen_note_structure.py/en:** Proper exception logging
- **gen_mep.py/en:** EDGE attribute safety, cost ratio div/zero
- **gen_boq_xlsx.py:** C40/50 price lookup
- **generate_fiches_structure_v3.py:** Safe concrete class parsing

## Backlog (3 chantiers — rien d'autre)
1. **Plans professionnels via Autodesk Design Automation API** — DONE. `aps_design_automation.py` created. Endpoints `/generate-plans-structure-pro` and `/generate-plans-mep-pro` send ezdxf DXF to AutoCAD cloud for hatching, blocks, dimensions, cartouche, A3 layout. Falls back to basic DXF if DA unavailable. Parsing pipeline also improved: APS Model Derivative enriches geometry when ezdxf finds thin data (few walls/axes).
2. **Modification d'étude depuis le chat** — DONE. Already fully implemented in chat_engine.py + main.py /chat endpoint.
3. **Amélioration du design de la landing page** — DONE. Complete redesign with SVG icons, normes bar, premium visual polish.

## Preferences
- Malick veut etre performant partout — keep code clean, fast, and safe
- Always run `scripts/pre_deploy_check.sh` before pushing
- Use French for user-facing content, English for code/comments
- Ne jamais suggerer d'embaucher — Malick construit tout avec Claude

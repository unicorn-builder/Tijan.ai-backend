# Tijan AI — Vue d'ensemble projet

Document de synthèse : pitch business, stack technique, état du produit.
Dernière mise à jour : 15 avril 2026.

---

## 1. Pitch

### Mission
Construire le premier bureau d'études automatisé d'Afrique de l'Ouest.
Tijan AI génère en quelques minutes des livrables d'ingénierie complets
(calculs structure, MEP, BIM, BOQ, certification EDGE) à partir des plans
d'architecte, avec la même qualité qu'un BET traditionnel mais 100× plus vite
et 10× moins cher.

### Le problème
- En Afrique de l'Ouest, un projet immobilier attend en moyenne 6 à 12
  semaines ses notes de calcul structure + MEP. Coût BET : 3 à 8 % du
  montant construction.
- Les BET locaux sont rares, débordés, peu digitalisés. Les grands projets
  passent par des BET européens → délais + coût + difficultés de
  coordination.
- Rien n'est standardisé Eurocode dans la région alors que c'est la norme
  imposée pour la plupart des financements internationaux (IFC, AFD, BEI).

### La solution
Un moteur d'ingénierie qui prend en entrée les plans DWG/DXF/PDF de
l'architecte et produit automatiquement :

- Note de calcul structure Eurocode 2 / Eurocode 8 (BA, fondations,
  sismique) — 30-60 pages PDF.
- Note de calcul MEP (plomberie, électricité, CVC, sécurité incendie,
  courants faibles, ascenseurs, GTB) — 40-80 pages PDF.
- Plans d'exécution structure (coffrage, ferraillage, fondations) —
  planches A3.
- Plans d'exécution MEP (7 lots × N niveaux) — planches A3.
- Métré / BOQ Excel multi-pays (Sénégal, Côte d'Ivoire, Maroc, Nigeria,
  Ghana).
- Rapport EDGE v3 (certification IFC green building).
- Fichiers DWG/DXF exploitables directement par les entreprises.

Tout est généré en moins de 10 minutes, bilingue FR/EN, prix locaux
auto-adaptés à la ville.

### Positionnement
"Le Revit + robot-structure + MEP-calc du continent africain, mais en
SaaS — une API, pas un logiciel desktop à 50k€/licence."

### Traction
- Projet de référence validé : Résidence Papa Oumar Sakho (R+8, 32 unités,
  Dakar) — 3966 murs parsés correctement depuis DXF, calculs EC2/EC8 validés
  vs BET classique.
- Stack en production sur Render + Vercel + Supabase, 32+ endpoints en
  service, pipeline DWG → DXF → geometry fonctionnel.
- 44 tests pytest en CI, gate `pre_deploy_check.sh` avant chaque push.

### Fondateur
Serigne Malick Tall — premier fondateur non-technique qui construit une
licorne sans recruter de co-fondateur technique. Stack entièrement
développée avec Claude (Claude Code terminal + Cowork desktop + Claude
mobile, contexte synchronisé).

---

## 2. Stack technique

### Backend — `unicorn-builder/Tijan.ai-backend`
- FastAPI 0.110.0 / Python 3.11 / Uvicorn (port 10000).
- Déployé sur Render (`build-ai-backend.onrender.com`), `build.sh` pour
  install ODA + pip, uvicorn start.
- 32+ endpoints : health, parsing, calculation, PDF/Excel/Word/DXF
  generation, chat, payments, translation.
- Lazy loading des modules moteur pour startup rapide.

### Frontend — `unicorn-builder/tijan-frontend`
- React 18 + Vite 5 déployé sur Vercel (`tijan.ai`).
- Routing : `react-router-dom` v6. i18n custom FR/EN (`i18n.jsx`, hook
  `useLang`, fonction `t()`).
- Auth + storage + DB via Supabase.

### Admin — `unicorn-builder/tijan-admin`
- Même stack Vite/React, déployé sur `tijan-admin.vercel.app`.
- Pages : Dashboard, Projects, Users, Payments, Reviews, Support.

### Base de données
- Supabase (PostgreSQL managé).
- Tables principales : `projets`, `credits`, `payments`, `support_tickets`,
  `reviews`.
- RLS : `auth.uid() = user_id` + GRANT ALL explicite.
- Storage buckets : `project-files` (archi PDFs), `plans` (PDF/DXF
  générés, archivés par projet).

### Intelligence
- Anthropic Claude SDK pour le `chat_engine` et le parsing sémantique.
- OpenAI pour fallback parsing de plans.

### Génération de documents
- PDF : ReportLab + PyPDF + PyMuPDF.
- Word : python-docx.
- Excel : openpyxl.
- DXF : ezdxf (lecture + écriture).
- DWG → DXF : ODA File Converter (fast path local) + LibreDWG (fallback) +
  Autodesk Platform Services APS (cloud fallback).

### Pipeline géométrie
- DXF → `ezdxf` direct (3966 murs validés sur le projet Sakho).
- DWG → ODA DXF output → `ezdxf`.
- PDF vectoriel → `pymupdf.get_drawings()` → coordonnées XY.
- Layers Aasaman reconnus : `A-WALL`, `A-DOOR`, `A-GLAZ`, `I-WALL`.

### Standards techniques
- Structure : Eurocode 2 (béton) + Eurocode 8 (sismique).
- MEP : DTU français, IT 246 (sécurité incendie), IFC EDGE v3.
- Classes béton : C20/25 à C40/50 (auto-sélectionnées).
- Aciers : HA400, HA500 (auto-sélectionnés).
- Zones sismiques auto depuis le pays (Sénégal zone 2, etc.).

### Tests et CI
- `tests/test_endpoints.py` : couverture endpoints (backend live).
- `tests/test_e2e.py` : intégration bout-en-bout.
- `tests/test_cors.py` : vérif CORS.
- `tests/test_dxf_pipeline.py` : parsing DXF.
- `tests/test_pdf_geometry.py` : parsing PDF vectoriel.
- Gate : `scripts/pre_deploy_check.sh` lance tout avant push.

### Fichiers clés (backend)
| Fichier | Rôle |
|---|---|
| `main.py` | FastAPI app + tous les endpoints (~1843 lignes) |
| `engine_structure_v2.py` | Calculs EC2/EC8 (~2000 lignes) |
| `engine_mep_v2.py` | Calculs MEP (~2000 lignes) |
| `gen_*.py` | Générateurs PDF/Excel/Word FR+EN |
| `generate_plans_structure_mep.py` | Générateur planches A3 BA + MEP |
| `parse_plans.py` | Extraction params DWG/DXF/PDF |
| `dwg_converter.py` | Conversion DWG → DXF (ODA/LibreDWG/APS) |
| `prix_marche.py` | Base de prix 5 pays |
| `chat_engine.py` | Assistant LLM design |
| `tijan_theme.py` | Branding/style PDF |

### Couverture géographique (v6.1.0)
Sénégal, Côte d'Ivoire, Maroc, Nigeria, Ghana — pricing auto par ville.

### CORS & endpoints publics
- `tijan.ai`, `api.tijan.ai`, `admin.tijan.ai`.
- Previews Vercel acceptés.
- `localhost:5173/5174` pour dev.

---

## 3. Éléments business

### Produit livré par projet
Un projet = une exécution complète de la pipeline. L'utilisateur paie
1 crédit et reçoit l'intégralité des livrables ingénierie listés en §1.

### Modèle pricing
- Vente au crédit (1 projet = 1 crédit).
- Paiement via PayDunya (mobile money + cartes) sur les marchés West-Africa.
- Packs dégressifs pour promoteurs avec pipeline récurrent.

### Segments cibles
1. **Promoteurs immobiliers mid-market** (5-50 M€ de projets/an) — ne
   peuvent pas s'offrir un BET international mais refusent la qualité
   aléatoire d'un BET local.
2. **Bureaux d'architecture** — veulent livrer le dossier structure/MEP
   avec leurs plans pour gagner le marché.
3. **Banques et financeurs** (IFC, AFD, banques commerciales locales) —
   ont besoin de notes Eurocode conformes pour débloquer les prêts.
4. **Gouvernements et maîtrises d'ouvrage publiques** — projets écoles,
   hôpitaux, logement social.

### Proposition de valeur quantifiée
- Temps : 10 minutes vs 6-12 semaines.
- Coût : un crédit vs 3-8 % du montant construction.
- Conformité : Eurocode + EDGE garantis pour déblocage de financement.
- Traçabilité : tous les livrables archivés Supabase, re-téléchargeables.

### Mesures techniques de qualité
- 44 tests pytest, gate pré-push.
- Zéro hardcoding : toutes les valeurs viennent de calculs réels.
- Aucune fonction déboguée plus de 3 fois — réécrite sinon.
- Stress test avril 2026 : 65+ bugs trouvés et corrigés (units colonnes,
  NRd, VRd_c, pile capacity, seismic mass, As_min, etc.).

### Version actuelle
**v6.1.0** (mars 2026). Pipeline multi-DWG par niveau déployée aujourd'hui
(15 avril 2026) : chaque étage peut être un DWG séparé avec son propre
label de niveau.

---

## 4. État courant et chantiers ouverts

### Déployé aujourd'hui (15 avril 2026)
- Backend `/parse-multi` accepte un array `levels` explicite parallèle à
  `files` (commit `2022fae`).
- Frontend `NewProject` envoie désormais tous les DWG à `/parse-multi` avec
  les niveaux choisis par l'utilisateur (commit `ea5d042`).
- Frontend `Results` expose un bouton "Gérer les DWG par niveau" sur les
  onglets Plans Structure et Plans MEP pour ajouter/remplacer des DWG
  post-création.
- Structure terrasse affiche la vraie emprise du bâtiment (murs) + contour
  dalle + acrotère (commit `3a8ec39`), au lieu d'un simple rectangle
  paramétrique.

### En attente
- Tracé des réseaux (tuyaux, câbles) entre équipements et gaines
  techniques sur les plans MEP.
- Enrichissement MEP sur les étages amenity (peu de pièces humides →
  peu d'icônes actuellement).
- UI admin pour audit/correction des géométries par niveau côté back-office.

### Règles de dev (inchangeables)
- Zéro hardcoding.
- Aucune fonction déboguée > 3 fois — réécrite.
- Monkey-patching ReportLab Paragraph interdit.
- `from tijan_theme import *` n'exporte pas les variables `_préfixées`.
- JSX : pas de `>` en début de ligne dans balises `<a>`.
- Supabase RLS : `auth.uid() = user_id` + GRANT ALL explicite.
- Toujours lancer `./scripts/pre_deploy_check.sh` avant `git push`.
- `/version` à vérifier après deploy pour confirmer le SHA.

---

## 5. Contacts et ressources

- **Fondateur** : Serigne Malick Tall — malicktall@gmail.com
- **Repos GitHub** : `unicorn-builder/Tijan.ai-backend` /
  `unicorn-builder/tijan-frontend` / `unicorn-builder/tijan-admin`.
- **Sites** : `tijan.ai` (produit), `admin.tijan.ai` (admin),
  `build-ai-backend.onrender.com` (API).
- **Projet de référence** : Résidence Papa Oumar Sakho, R+8, 32 unités,
  Dakar — Réf. 1711. Béton C30/37 BPE 185 000 FCFA/m³, acier HA500B
  520-540 FCFA/kg.

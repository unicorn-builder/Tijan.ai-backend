# Tijan AI — Handover Multi-DWG (15 avril 2026)

## Contexte

Les plans Structure et MEP affichaient le même plan RDC pour tous les niveaux
(RDC, Étage courant, Sous-sol) sur un même projet. Diagnostic et fix ci-dessous.

## Root cause

`NewProject.jsx` (frontend, avant aujourd'hui) acceptait un drop multi-fichiers
dans la dropzone mais n'envoyait que le plus gros au backend :

```js
const fileToSend = allFiles.length > 1
  ? [...allFiles].sort((a, b) => b.size - a.size)[0]
  : mainFile
form.append('file', fileToSend)
fetch(`${BACKEND}/parse`, { method: 'POST', body: form })
```

Conséquence : tous les projets créés avant le commit `ea5d042` ne contiennent
qu'une seule géométrie dans `projets.dwg_geometry`, réutilisée par le
générateur de plans pour chaque niveau (avec quelques variations paramétriques
synthétiques). C'est un bug frontend, pas un oubli utilisateur.

## Fix déployé aujourd'hui

### Backend — `unicorn-builder/Tijan.ai-backend`

- Commit `2022fae` : `/parse-multi` accepte un champ `levels` (array parallèle
  à `files`) pour épingler chaque DWG à un niveau explicite
  (`SOUS_SOL` / `RDC` / `ETAGE_N` / `TERRASSE`). Fallback sur les heuristiques
  de nom de fichier si `levels` est omis. Le fast path ODA et le worker APS
  consomment tous les deux des 3-tuples `(filename, filepath, explicit_label)`.
- Commit `3a8ec39` : la page Terrasse du PDF Structure montre désormais la
  vraie emprise architecturale (murs en gris 45 % + contour dalle noir +
  acrotère pointillés orange) au lieu du bounding box paramétrique.

### Frontend — `unicorn-builder/tijan-frontend`

Commit `ea5d042` — deux changements :

1. **Création (`NewProject.jsx`)** : état `mainLevels[]` parallèle à `mainFiles[]`,
   auto-deviné depuis le nom de fichier, éditable via `<select>` par fichier
   (Sous-sol / RDC / Étage 1..40 / Terrasse). Quand ≥ 2 fichiers, on appelle
   `/parse-multi` avec `files` + `levels` au lieu de `/parse`. Gère le polling
   `/parse-status/:job_id` si Render tourne sans ODA.

2. **Édition (`Results.jsx`)** : nouveau composant `DwgLevelsManager` sur les
   cartes "Plans Structure (BA)" et "Plans MEP". Liste les niveaux déjà
   présents dans `dwg_geometry`, permet d'uploader des DWG additionnels ou
   de remplacement avec labels de niveau, merge dans `dwg_geometry`
   (overwrite par clé) et persiste dans `projets.dwg_geometry` via Supabase.

## État des projets existants

Tous les projets Aasaman (1 → 8) ont été créés avant `ea5d042` : leur
`dwg_geometry` ne contient qu'une seule clé. Deux options pour les corriger :

1. Recréer le projet depuis `/projects/new` en uploadant les DWG par niveau
   (recommandé si les DWG sont triés).
2. Ouvrir le projet existant → onglet "Plans Structure" ou "Plans MEP" →
   bouton `+ Gérer les DWG par niveau` → uploader les DWG manquants et
   choisir le niveau de chacun → regénérer les PDFs.

## Points de vérification

- Render deploy vert sur `build-ai-backend.onrender.com` incluant `3a8ec39`
  (endpoint `/version` doit renvoyer le SHA correspondant ou postérieur).
- Vercel deploy vert sur `tijan.ai` incluant `ea5d042` (le sélecteur de
  niveau par fichier et le bouton "Gérer les DWG par niveau" doivent
  apparaître).
- Table Supabase `projets` : colonne `dwg_geometry` (jsonb) accepte un dict
  multi-niveaux ; les projets neufs doivent avoir plusieurs clés.

## Ce qui reste ouvert

- Tracé des réseaux (tuyaux, câbles) entre équipements et gaine technique —
  reporté du fix de readability du 14 avril.
- Page MEP Plomberie sparse sur étages non-résidentiels (ex: RDC amenity
  avec piscine, salle sport, salle polyvalente) : peu de pièces humides
  donc peu d'icônes. Comportement attendu mais à éventuellement enrichir
  (équipements communs : poste incendie, bouche arrosage jardin, etc.).
- Pas encore de flow côté admin (`unicorn-builder/tijan-admin`) pour
  auditer ou corriger les géométries par niveau sur les projets clients.

## Commits à reviewer

| Repo | SHA | Message |
|------|-----|---------|
| Tijan.ai-backend | `2022fae` | parse-multi: honor explicit level labels from frontend |
| Tijan.ai-backend | `3a8ec39` | plans structure: terrasse montre la vraie emprise du bâtiment |
| tijan-frontend   | `ea5d042` | multi-DWG upload flow: per-level labels at creation + edit |

"""
Tijan AI — parse_dxf.py v4
Pipeline d'extraction géométrique depuis DWG/DXF ou IFC.

Règle produit :
  - DWG/DXF ou IFC valide → output complet (planches sur géométrie réelle)
  - Paramètres manuels     → output partiel (note de calcul + BOQ, pas de plans)
  - PDF/image/scan         → refus propre avec message explicatif

Dépendances Render :
  ezdxf>=1.1.0
  ifcopenshell (optionnel)
"""

import math
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

try:
    import ezdxf
    EZDXF_OK = True
except ImportError:
    EZDXF_OK = False

try:
    import ifcopenshell
    IFC_OK = True
except ImportError:
    IFC_OK = False


# ════════════════════════════════════════════════════════════
# TYPES D'INPUT
# ════════════════════════════════════════════════════════════

class TypeInput(Enum):
    DWG_DXF   = "dwg_dxf"
    IFC       = "ifc"
    PARAMETRES = "parametres"
    REFUSE    = "refuse"   # PDF, image, scan


class NiveauOutput(Enum):
    COMPLET = "complet"    # plans sur géométrie réelle + note + BOQ + IFC
    PARTIEL = "partiel"    # note de calcul + BOQ uniquement, pas de plans
    REFUSE  = "refuse"     # message d'erreur, rien livré


@dataclass
class DiagnosticInput:
    type_input: TypeInput
    niveau_output: NiveauOutput
    message_user: str          # affiché dans le frontend
    peut_parser: bool
    fichier_valide: bool = False


# ════════════════════════════════════════════════════════════
# DIAGNOSTIC — détermine ce qu'on peut faire avec l'input
# ════════════════════════════════════════════════════════════

MESSAGES = {
    TypeInput.DWG_DXF: (
        "✓ Fichier DWG/DXF détecté. "
        "Tijan va extraire la géométrie réelle et générer l'ensemble du dossier : "
        "plans structure + MEP sur votre géométrie, note de calcul, BOQ et IFC."
    ),
    TypeInput.IFC: (
        "✓ Fichier IFC détecté. "
        "Tijan va lire le modèle BIM et générer l'ensemble du dossier : "
        "plans structure + MEP, note de calcul, BOQ et export IFC enrichi."
    ),
    TypeInput.PARAMETRES: (
        "⚠ Saisie paramétrique. "
        "Sans fichier DWG/DXF ou IFC, Tijan ne peut pas garantir la qualité des plans "
        "sur votre géométrie réelle. Vous recevrez : note de calcul Eurocodes, BOQ détaillé "
        "et bilan EDGE. Les plans ne seront pas générés."
    ),
    TypeInput.REFUSE: (
        "✗ Format non supporté. "
        "Les fichiers PDF, images et scans ne permettent pas une extraction géométrique "
        "fiable. Fournissez un fichier DWG, DXF ou IFC pour obtenir des plans. "
        "Pour les calculs seuls (sans plans), utilisez la saisie paramétrique."
    ),
}

FORMATS_REFUSES = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff",
                   ".bmp", ".gif", ".webp", ".svg"}
FORMATS_DXF     = {".dxf", ".dwg"}
FORMATS_IFC     = {".ifc", ".ifczip"}


def diagnostiquer_input(filepath: str) -> DiagnosticInput:
    """
    Analyse un fichier uploadé et retourne le diagnostic.
    Appelé avant tout traitement.
    """
    import os
    ext = os.path.splitext(filepath)[1].lower()

    if ext in FORMATS_REFUSES:
        return DiagnosticInput(
            type_input=TypeInput.REFUSE,
            niveau_output=NiveauOutput.REFUSE,
            message_user=MESSAGES[TypeInput.REFUSE],
            peut_parser=False,
        )

    if ext in FORMATS_IFC:
        if not IFC_OK:
            return DiagnosticInput(
                type_input=TypeInput.IFC,
                niveau_output=NiveauOutput.REFUSE,
                message_user=(
                    "✗ ifcopenshell non installé sur ce serveur. "
                    "Utilisez un fichier DWG/DXF à la place."
                ),
                peut_parser=False,
            )
        return DiagnosticInput(
            type_input=TypeInput.IFC,
            niveau_output=NiveauOutput.COMPLET,
            message_user=MESSAGES[TypeInput.IFC],
            peut_parser=True,
        )

    if ext in FORMATS_DXF:
        if not EZDXF_OK:
            return DiagnosticInput(
                type_input=TypeInput.DWG_DXF,
                niveau_output=NiveauOutput.REFUSE,
                message_user=(
                    "✗ ezdxf non installé sur ce serveur. "
                    "Contactez support@tijan.ai"
                ),
                peut_parser=False,
            )
        # Vérifier que le fichier est bien un DWG/DXF lisible
        try:
            with open(filepath, 'rb') as f:
                header = f.read(6)
            if not header.startswith(b'AC'):
                return DiagnosticInput(
                    type_input=TypeInput.DWG_DXF,
                    niveau_output=NiveauOutput.REFUSE,
                    message_user=(
                        "✗ Fichier DWG/DXF corrompu ou version non supportée. "
                        "Ré-exportez depuis AutoCAD en version 2010 ou 2018."
                    ),
                    peut_parser=False,
                )
        except Exception:
            pass

        return DiagnosticInput(
            type_input=TypeInput.DWG_DXF,
            niveau_output=NiveauOutput.COMPLET,
            message_user=MESSAGES[TypeInput.DWG_DXF],
            peut_parser=True,
            fichier_valide=True,
        )

    # Extension inconnue
    return DiagnosticInput(
        type_input=TypeInput.REFUSE,
        niveau_output=NiveauOutput.REFUSE,
        message_user=(
            f"✗ Format '{ext}' non reconnu. "
            "Formats acceptés : DWG, DXF, IFC."
        ),
        peut_parser=False,
    )


def diagnostiquer_parametres() -> DiagnosticInput:
    """Diagnostic pour la saisie paramétrique (sans fichier)"""
    return DiagnosticInput(
        type_input=TypeInput.PARAMETRES,
        niveau_output=NiveauOutput.PARTIEL,
        message_user=MESSAGES[TypeInput.PARAMETRES],
        peut_parser=True,
    )


# ════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES GÉOMÉTRIE
# ════════════════════════════════════════════════════════════

@dataclass
class Axe:
    id: str
    direction: str   # "X" ou "Y"
    position: float  # mm
    label: str = ""


@dataclass
class PoteauExtrait:
    x: float; y: float
    section_b: float = 0.0
    section_h: float = 0.0
    layer: str = ""


@dataclass
class PoutreExtraite:
    x1: float; y1: float
    x2: float; y2: float
    largeur: float = 0.0


@dataclass
class GeometrieProjet:
    axes_x: List[Axe]              = field(default_factory=list)
    axes_y: List[Axe]              = field(default_factory=list)
    poteaux: List[PoteauExtrait]   = field(default_factory=list)
    poutres: List[PoutreExtraite]  = field(default_factory=list)
    emprise_x: float               = 0.0
    emprise_y: float               = 0.0
    origine_x: float               = 0.0
    origine_y: float               = 0.0
    portees_x: List[float]         = field(default_factory=list)
    portees_y: List[float]         = field(default_factory=list)
    unite: str                     = "mm"
    nb_niveaux_annote: int         = 0
    projet_nom: str                = ""
    source: str                    = "dxf"
    score_qualite: int             = 0   # 0-100


# ════════════════════════════════════════════════════════════
# MAPPING LAYERS DXF
# ════════════════════════════════════════════════════════════

PATTERNS_AXES = [
    r"ax(e[s]?)?$", r"grille", r"grid", r"ref", r"repere",
    r"a[-_]ax", r"struct.*ax", r"centre.*line",
]
PATTERNS_POTEAUX = [
    r"pot(eau[x]?)?", r"col(onne[s]?)?", r"pilier",
    r"struct.*pot", r"[pc]ot$",
]
PATTERNS_POUTRES = [
    r"poutr", r"beam", r"linteau",
    r"struct.*pou",
]

LONGUEUR_MIN_AXE = 800  # mm


# ════════════════════════════════════════════════════════════
# PARSER DXF/DWG
# ════════════════════════════════════════════════════════════

class ParserDXF:
    """
    Parser universel DWG/DXF → GeometrieProjet.
    3 passes : layers → axes → poteaux/poutres.
    Fallback géométrique si layers non nommés.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.doc = None
        self.msp = None
        self.geo = GeometrieProjet()
        self._layer_map: Dict[str, str] = {}

    def parse(self) -> GeometrieProjet:
        if not EZDXF_OK:
            raise ImportError("ezdxf requis. Ajouter dans requirements.txt.")

        self.doc = ezdxf.readfile(self.filepath)
        self.msp = self.doc.modelspace()
        self.geo.source = "dxf"

        self._detecter_unite()
        self._mapper_layers()
        self._extraire_nom()
        self._extraire_axes()
        self._extraire_poteaux()
        self._extraire_poutres()
        self._calculer_emprise()
        self._calculer_portees()
        self._detecter_niveaux()
        self._calculer_score()

        return self.geo

    # ── Unité ──────────────────────────────────────────────
    def _detecter_unite(self):
        try:
            insunits = self.doc.header.get("$INSUNITS", 4)
            self.geo.unite = "m" if insunits == 6 else "mm"
        except Exception:
            coords = []
            for e in self.msp:
                try:
                    if hasattr(e.dxf, 'start'):
                        coords.append(abs(e.dxf.start.x))
                except Exception:
                    pass
            self.geo.unite = "m" if (coords and max(coords) < 200) else "mm"

    def _mm(self, v: float) -> float:
        return v * 1000 if self.geo.unite == "m" else v

    # ── Mapping layers ─────────────────────────────────────
    def _mapper_layers(self):
        for layer in self.doc.layers:
            name = layer.dxf.name.lower()
            for pat in PATTERNS_AXES:
                if re.search(pat, name):
                    self._layer_map[layer.dxf.name] = "axe"; break
            for pat in PATTERNS_POTEAUX:
                if re.search(pat, name):
                    self._layer_map[layer.dxf.name] = "poteau"; break
            for pat in PATTERNS_POUTRES:
                if re.search(pat, name):
                    self._layer_map[layer.dxf.name] = "poutre"; break

    def _type(self, entity) -> Optional[str]:
        try:
            return self._layer_map.get(entity.dxf.layer)
        except Exception:
            return None

    # ── Nom projet ────────────────────────────────────────
    def _extraire_nom(self):
        for e in self.msp:
            if e.dxftype() not in ("TEXT", "MTEXT"):
                continue
            try:
                t = (e.plain_mtext() if e.dxftype() == "MTEXT"
                     else e.dxf.text).strip()
                if 8 < len(t) < 80 and not re.search(r"\d{4,}", t):
                    self.geo.projet_nom = t
                    break
            except Exception:
                pass

    # ── Axes ──────────────────────────────────────────────
    def _extraire_axes(self):
        candidates = []

        for e in self.msp:
            if e.dxftype() not in ("LINE", "XLINE"):
                continue
            par_layer = self._type(e) == "axe"
            par_tiret = False
            try:
                lt = e.dxf.linetype.upper()
                par_tiret = any(k in lt for k in
                                ["DASH", "CENTER", "CHAIN", "DOT"])
            except Exception:
                pass

            if par_layer or par_tiret:
                try:
                    x1 = self._mm(e.dxf.start.x)
                    y1 = self._mm(e.dxf.start.y)
                    x2 = self._mm(e.dxf.end.x)
                    y2 = self._mm(e.dxf.end.y)
                    L = math.hypot(x2-x1, y2-y1)
                    if L > LONGUEUR_MIN_AXE:
                        candidates.append((x1, y1, x2, y2, L))
                except Exception:
                    pass

        # Fallback : lignes les plus longues
        if len(candidates) < 3:
            candidates = self._lignes_longues()

        axes_h, axes_v = [], []
        for x1, y1, x2, y2, L in candidates:
            angle = math.degrees(math.atan2(abs(y2-y1), abs(x2-x1)))
            if angle < 15:
                axes_h.append((y1+y2)/2)
            elif angle > 75:
                axes_v.append((x1+x2)/2)

        axes_h = self._dedup(sorted(set(axes_h)))
        axes_v = self._dedup(sorted(set(axes_v)))

        lettres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, pos in enumerate(axes_v):
            self.geo.axes_x.append(
                Axe(str(i+1), "X", pos, str(i+1)))
        for j, pos in enumerate(axes_h):
            lbl = lettres[j] if j < 26 else f"Y{j}"
            self.geo.axes_y.append(Axe(lbl, "Y", pos, lbl))

    def _lignes_longues(self):
        toutes = []
        for e in self.msp:
            if e.dxftype() != "LINE":
                continue
            try:
                x1 = self._mm(e.dxf.start.x)
                y1 = self._mm(e.dxf.start.y)
                x2 = self._mm(e.dxf.end.x)
                y2 = self._mm(e.dxf.end.y)
                L = math.hypot(x2-x1, y2-y1)
                toutes.append((x1, y1, x2, y2, L))
            except Exception:
                pass
        toutes.sort(key=lambda t: -t[4])
        return toutes[:25]

    def _dedup(self, vals: List[float], tol: float = 80.0) -> List[float]:
        if not vals: return []
        res = [vals[0]]
        for v in vals[1:]:
            if v - res[-1] > tol:
                res.append(v)
        return res

    # ── Poteaux ───────────────────────────────────────────
    def _extraire_poteaux(self):
        found = []

        # Blocs INSERT sur layer poteau
        for e in self.msp:
            if e.dxftype() == "INSERT" and self._type(e) == "poteau":
                try:
                    cx = self._mm(e.dxf.insert.x)
                    cy = self._mm(e.dxf.insert.y)
                    b, h = self._section_bloc(e)
                    found.append(PoteauExtrait(cx, cy, b, h, e.dxf.layer))
                except Exception:
                    pass

        # LWPOLYLINE rectangulaires
        for e in self.msp:
            if e.dxftype() != "LWPOLYLINE":
                continue
            if self._type(e) not in ("poteau", None):
                continue
            try:
                pts = list(e.get_points())
                if len(pts) < 4:
                    continue
                xs = [self._mm(p[0]) for p in pts]
                ys = [self._mm(p[1]) for p in pts]
                w = max(xs)-min(xs)
                h = max(ys)-min(ys)
                if 150 <= w <= 800 and 150 <= h <= 800:
                    found.append(PoteauExtrait(
                        (min(xs)+max(xs))/2,
                        (min(ys)+max(ys))/2,
                        round(w/50)*50,
                        round(h/50)*50,
                        e.dxf.layer
                    ))
            except Exception:
                pass

        # Fallback intersections axes
        if len(found) < 3 and self.geo.axes_x and self.geo.axes_y:
            for ax in self.geo.axes_x:
                for ay in self.geo.axes_y:
                    found.append(PoteauExtrait(ax.position, ay.position))

        self.geo.poteaux = found

    def _section_bloc(self, entity) -> Tuple[float, float]:
        try:
            for att in entity.attribs:
                m = re.search(r"(\d+)[xX×](\d+)", att.dxf.text.upper())
                if m:
                    b, h = float(m.group(1)), float(m.group(2))
                    if b < 200: b *= 10; h *= 10
                    return b, h
        except Exception:
            pass
        return 0.0, 0.0

    # ── Poutres ───────────────────────────────────────────
    def _extraire_poutres(self):
        for e in self.msp:
            if e.dxftype() != "LWPOLYLINE":
                continue
            if self._type(e) != "poutre":
                continue
            try:
                pts = list(e.get_points())
                xs = [self._mm(p[0]) for p in pts]
                ys = [self._mm(p[1]) for p in pts]
                w, h = max(xs)-min(xs), max(ys)-min(ys)
                if max(w,h)/max(min(w,h),1) > 3:
                    self.geo.poutres.append(PoutreExtraite(
                        min(xs), min(ys), max(xs), max(ys), min(w,h)))
            except Exception:
                pass

    # ── Emprise et portées ────────────────────────────────
    def _calculer_emprise(self):
        all_x, all_y = [], []
        for e in self.msp:
            try:
                if e.dxftype() == "LINE":
                    all_x += [self._mm(e.dxf.start.x), self._mm(e.dxf.end.x)]
                    all_y += [self._mm(e.dxf.start.y), self._mm(e.dxf.end.y)]
                elif e.dxftype() == "LWPOLYLINE":
                    for p in e.get_points():
                        all_x.append(self._mm(p[0]))
                        all_y.append(self._mm(p[1]))
            except Exception:
                pass
        if all_x and all_y:
            self.geo.origine_x = min(all_x)
            self.geo.origine_y = min(all_y)
            self.geo.emprise_x = max(all_x)-min(all_x)
            self.geo.emprise_y = max(all_y)-min(all_y)

    def _calculer_portees(self):
        if len(self.geo.axes_x) >= 2:
            pos = sorted(a.position for a in self.geo.axes_x)
            self.geo.portees_x = [pos[i+1]-pos[i] for i in range(len(pos)-1)]
        if len(self.geo.axes_y) >= 2:
            pos = sorted(a.position for a in self.geo.axes_y)
            self.geo.portees_y = [pos[i+1]-pos[i] for i in range(len(pos)-1)]

    def _detecter_niveaux(self):
        niveaux = set()
        for e in self.msp:
            if e.dxftype() not in ("TEXT", "MTEXT"):
                continue
            try:
                txt = (e.plain_mtext() if e.dxftype() == "MTEXT"
                       else e.dxf.text) or ""
                for m in re.findall(r"[+\-](\d+)[.,]\d{2}", txt):
                    niveaux.add(int(m))
            except Exception:
                pass
        if niveaux:
            self.geo.nb_niveaux_annote = max(niveaux) // 3

    def _calculer_score(self):
        score = 0
        if self.geo.axes_x:            score += 25
        if self.geo.axes_y:            score += 25
        if self.geo.portees_x:         score += 15
        if len(self.geo.poteaux) >= 4: score += 15
        if self.geo.emprise_x > 0:     score += 10
        if self.geo.nb_niveaux_annote: score += 5
        if self.geo.projet_nom:        score += 5
        self.geo.score_qualite = score


# ════════════════════════════════════════════════════════════
# PARSER IFC
# ════════════════════════════════════════════════════════════

class ParserIFC:
    """
    Parser IFC → GeometrieProjet.
    Lit les entités IfcColumn, IfcBeam, IfcSlab, IfcGrid.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.geo = GeometrieProjet()

    def parse(self) -> GeometrieProjet:
        if not IFC_OK:
            raise ImportError("ifcopenshell requis.")

        ifc = ifcopenshell.open(self.filepath)
        self.geo.source = "ifc"

        self._extraire_nom(ifc)
        self._extraire_grid(ifc)
        self._extraire_colonnes(ifc)
        self._extraire_poutres(ifc)
        self._calculer_emprise_ifc()
        self._calculer_portees()
        self._detecter_niveaux_ifc(ifc)
        self._calculer_score()

        return self.geo

    def _extraire_nom(self, ifc):
        try:
            projets = ifc.by_type("IfcProject")
            if projets:
                self.geo.projet_nom = projets[0].Name or ""
        except Exception:
            pass

    def _extraire_grid(self, ifc):
        try:
            for grid in ifc.by_type("IfcGrid"):
                for u_axes in (grid.UAxes or []):
                    try:
                        seg = u_axes.AxisCurve
                        if hasattr(seg, 'Points'):
                            coords = [p.Coordinates for p in seg.Points]
                            if len(coords) >= 2:
                                # Axe X ou Y selon orientation
                                dx = abs(coords[-1][0]-coords[0][0])
                                dy = abs(coords[-1][1]-coords[0][1])
                                pos = (coords[0][0]+coords[-1][0])/2 * 1000
                                if dx > dy:
                                    self.geo.axes_y.append(
                                        Axe(u_axes.AxisTag, "Y", pos, u_axes.AxisTag))
                                else:
                                    self.geo.axes_x.append(
                                        Axe(u_axes.AxisTag, "X", pos, u_axes.AxisTag))
                    except Exception:
                        pass
        except Exception:
            pass

    def _extraire_colonnes(self, ifc):
        try:
            for col in ifc.by_type("IfcColumn"):
                try:
                    placement = col.ObjectPlacement
                    if hasattr(placement, 'RelativePlacement'):
                        loc = placement.RelativePlacement.Location
                        x = loc.Coordinates[0] * 1000  # m → mm
                        y = loc.Coordinates[1] * 1000
                        self.geo.poteaux.append(PoteauExtrait(x, y))
                except Exception:
                    pass
        except Exception:
            pass

    def _extraire_poutres(self, ifc):
        try:
            for beam in ifc.by_type("IfcBeam"):
                try:
                    placement = beam.ObjectPlacement
                    if hasattr(placement, 'RelativePlacement'):
                        loc = placement.RelativePlacement.Location
                        x = loc.Coordinates[0] * 1000
                        y = loc.Coordinates[1] * 1000
                        self.geo.poutres.append(
                            PoutreExtraite(x, y, x+5000, y))
                except Exception:
                    pass
        except Exception:
            pass

    def _calculer_emprise_ifc(self):
        if self.geo.poteaux:
            xs = [p.x for p in self.geo.poteaux]
            ys = [p.y for p in self.geo.poteaux]
            self.geo.origine_x = min(xs)
            self.geo.origine_y = min(ys)
            self.geo.emprise_x = max(xs)-min(xs)
            self.geo.emprise_y = max(ys)-min(ys)

    def _calculer_portees(self):
        if len(self.geo.axes_x) >= 2:
            pos = sorted(a.position for a in self.geo.axes_x)
            self.geo.portees_x = [pos[i+1]-pos[i] for i in range(len(pos)-1)]
        if len(self.geo.axes_y) >= 2:
            pos = sorted(a.position for a in self.geo.axes_y)
            self.geo.portees_y = [pos[i+1]-pos[i] for i in range(len(pos)-1)]

    def _detecter_niveaux_ifc(self, ifc):
        try:
            niveaux = ifc.by_type("IfcBuildingStorey")
            self.geo.nb_niveaux_annote = len(niveaux)
        except Exception:
            pass

    def _calculer_score(self):
        score = 0
        if self.geo.axes_x:            score += 25
        if self.geo.axes_y:            score += 25
        if self.geo.portees_x:         score += 15
        if len(self.geo.poteaux) >= 4: score += 15
        if self.geo.emprise_x > 0:     score += 10
        if self.geo.nb_niveaux_annote: score += 5
        if self.geo.projet_nom:        score += 5
        self.geo.score_qualite = score


# ════════════════════════════════════════════════════════════
# CONVERTISSEUR GÉOMÉTRIE → PARAMÈTRES MOTEUR
# ════════════════════════════════════════════════════════════

DEFAULTS_DAKAR = {
    "ville": "Dakar",
    "beton": "C30/37",
    "acier": "HA500",
    "pression_sol_MPa": 0.15,
    "profondeur_fondation_m": 1.5,
    "distance_mer_km": 2.0,
    "zone_sismique": 1,
    "enrobage_mm": 30.0,
    "usage": "residentiel",
    "nb_niveaux": 4,
    "hauteur_etage_m": 3.00,
}


def geo_vers_donnees(geo: GeometrieProjet, overrides: dict = None) -> dict:
    """
    Convertit une GeometrieProjet en dict compatible DonneesProjet du moteur v3.
    """
    cfg = dict(DEFAULTS_DAKAR)
    if overrides:
        cfg.update(overrides)

    portees = geo.portees_x + geo.portees_y
    portee_max = max(portees) if portees else 5000.0
    portee_min = min([p for p in portees if p > 500]) if portees else 4000.0

    surface = geo.emprise_x * geo.emprise_y / 1e6
    if surface < 50:
        nx = max(len(geo.axes_x)-1, 1)
        ny = max(len(geo.axes_y)-1, 1)
        surface = (portee_max/1000) * (portee_min/1000) * nx * ny

    nb_niv = geo.nb_niveaux_annote if geo.nb_niveaux_annote >= 2 else cfg["nb_niveaux"]

    return {
        "nom": geo.projet_nom or "Projet importé",
        "ville": cfg["ville"],
        "nb_niveaux": nb_niv,
        "hauteur_etage_m": cfg["hauteur_etage_m"],
        "surface_emprise_m2": round(surface, 1),
        "portee_max_m": round(portee_max/1000, 2),
        "portee_min_m": round(portee_min/1000, 2),
        "nb_travees_x": max(len(geo.axes_x)-1, 1),
        "nb_travees_y": max(len(geo.axes_y)-1, 1),
        "usage_principal": cfg["usage"],
        "classe_beton": cfg["beton"],
        "classe_acier": cfg["acier"],
        "pression_sol_MPa": cfg["pression_sol_MPa"],
        "profondeur_fondation_m": cfg["profondeur_fondation_m"],
        "distance_mer_km": cfg["distance_mer_km"],
        "zone_sismique": cfg["zone_sismique"],
        "enrobage_mm": cfg["enrobage_mm"],
    }


# ════════════════════════════════════════════════════════════
# CONSTRUCTEUR GÉOMÉTRIE DEPUIS PARAMÈTRES
# ════════════════════════════════════════════════════════════

def geo_depuis_parametres(portees_x: List[float], portees_y: List[float],
                           nb_niveaux: int = 4,
                           projet_nom: str = "Projet") -> GeometrieProjet:
    """
    Construit une GeometrieProjet depuis des paramètres numériques.
    Utilisé uniquement pour la saisie paramétrique (output partiel).
    """
    geo = GeometrieProjet()
    geo.source = "parametres"
    geo.projet_nom = projet_nom
    geo.nb_niveaux_annote = nb_niveaux
    geo.portees_x = portees_x
    geo.portees_y = portees_y

    x = 0.0
    for i, p in enumerate(portees_x):
        geo.axes_x.append(Axe(str(i+1), "X", x, str(i+1)))
        x += p
    geo.axes_x.append(Axe(str(len(portees_x)+1), "X", x, str(len(portees_x)+1)))

    y = 0.0
    lettres = "ABCDEFGHIJKLM"
    for j, p in enumerate(portees_y):
        geo.axes_y.append(Axe(lettres[j], "Y", y, lettres[j]))
        y += p
    geo.axes_y.append(Axe(lettres[len(portees_y)], "Y", y, lettres[len(portees_y)]))

    geo.emprise_x = sum(portees_x)
    geo.emprise_y = sum(portees_y)
    geo.score_qualite = 50  # partiel par définition

    return geo


# ════════════════════════════════════════════════════════════
# POINT D'ENTRÉE UNIFIÉ
# ════════════════════════════════════════════════════════════

def traiter_fichier(filepath: str, overrides: dict = None) -> dict:
    """
    Pipeline complet depuis un fichier uploadé.
    Retourne un dict avec diagnostic + géométrie + paramètres moteur.
    """
    diag = diagnostiquer_input(filepath)

    if not diag.peut_parser:
        return {
            "ok": False,
            "niveau_output": diag.niveau_output.value,
            "message": diag.message_user,
            "geo": None,
            "donnees_moteur": None,
        }

    # Parser selon type
    try:
        if diag.type_input == TypeInput.DWG_DXF:
            geo = ParserDXF(filepath).parse()
        elif diag.type_input == TypeInput.IFC:
            geo = ParserIFC(filepath).parse()
        else:
            return {"ok": False, "message": "Type d'input non géré."}
    except Exception as e:
        return {
            "ok": False,
            "niveau_output": NiveauOutput.REFUSE.value,
            "message": f"Erreur lors du parsing : {str(e)}",
            "geo": None,
            "donnees_moteur": None,
        }

    donnees = geo_vers_donnees(geo, overrides)

    return {
        "ok": True,
        "niveau_output": diag.niveau_output.value,
        "message": diag.message_user,
        "geo": geo,
        "donnees_moteur": donnees,
        "score_qualite": geo.score_qualite,
        "source": geo.source,
        "emprise_m2": round(geo.emprise_x * geo.emprise_y / 1e6, 1),
        "nb_axes_x": len(geo.axes_x),
        "nb_axes_y": len(geo.axes_y),
        "nb_poteaux": len(geo.poteaux),
        "portees_x_m": [round(p/1000, 2) for p in geo.portees_x],
        "portees_y_m": [round(p/1000, 2) for p in geo.portees_y],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = traiter_fichier(sys.argv[1])
        print(f"OK: {res['ok']}")
        print(f"Niveau output: {res.get('niveau_output')}")
        print(f"Message: {res.get('message')}")
        if res.get('geo'):
            geo = res['geo']
            print(f"Axes X: {len(geo.axes_x)} | Y: {len(geo.axes_y)}")
            print(f"Poteaux: {len(geo.poteaux)}")
            print(f"Score qualité: {geo.score_qualite}%")
    else:
        # Test diagnostic
        for ext in [".pdf", ".dwg", ".ifc", ".png", ".dxf"]:
            diag = diagnostiquer_input(f"test{ext}")
            print(f"{ext:8} → {diag.niveau_output.value:10} | {diag.message_user[:60]}")

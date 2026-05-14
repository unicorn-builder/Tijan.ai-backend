"""Extract room labels directly from the architect's PDF annotations.

Architectural plans typically annotate each room (CHAMBRE, SDB, CUISINE, etc.)
as native text with precise coordinates. This is far more reliable than CV
contour detection for identifying *which* regions are interior rooms.

This module parses a PDF page with pdfplumber, identifies room-label words,
merges multi-word labels (e.g. "SALLE" + "DE" + "JEUX"), and returns a
list of room dicts compatible with wall_aware_placer:
    {name, x, y, area_m2, bbox_mm, aspect}
with coordinates in the PDF's native top-down point system.
"""
from __future__ import annotations
import math
import re
from typing import List, Dict, Optional


ROOM_KEYWORDS = (
    'chambre', 'sdb', 'wc', 'cuisine', 'salon', 'sejour', 'séjour',
    'salle', 'dressing', 'buanderie', 'hall', 'palier',
    'bureau', 'dégagement', 'degagement', 'sas', 'toilette', 'parent',
    'lingerie', 'douche', 'bain', 'office', 'jeu', 'sport', 'gym',
    'lavabo', 'entree', 'entrée',
)

# Words that, if they appear alone, should NOT trigger a room detection
NOISE_WORDS = ('projet', 'plan', 'construction', 'immeuble', 'usage', 'échelle',
               'echelle', 'date', 'etage', 'étage', 'date', 'accessible',
               'habitation', 'dakar', 'mermoz', 'senegal', 'sénégal')


def _is_room_word(text: str) -> bool:
    t = text.lower().strip()
    if not t or any(n in t for n in NOISE_WORDS):
        return False
    return any(k in t for k in ROOM_KEYWORDS)


def _word_box(w: dict) -> tuple:
    return w['x0'], w['top'], w['x1'], w['bottom']


def _merge_adjacent(words: List[dict],
                    max_gap_x: float = 25,
                    max_gap_y: float = 5) -> List[dict]:
    """Merge words that are on (approximately) the same baseline and close."""
    if not words:
        return []
    # Sort reading order: top, then x0
    ws = sorted(words, key=lambda w: (round(w['top']), w['x0']))
    merged: List[dict] = []
    for w in ws:
        if not merged:
            merged.append({**w, 'text': w['text']})
            continue
        m = merged[-1]
        # Same line (close tops)?
        if abs(w['top'] - m['top']) <= max_gap_y and (w['x0'] - m['x1']) <= max_gap_x:
            m['text'] = f"{m['text']} {w['text']}"
            m['x1'] = w['x1']
            m['bottom'] = max(m['bottom'], w['bottom'])
            m['top'] = min(m['top'], w['top'])
        else:
            merged.append({**w})
    return merged


def _classify_for_area(name: str) -> float:
    """Fallback area (m²) for a room given its name. Used when we can't infer
    area from walls — just a reasonable default to feed the filter/size logic."""
    n = name.lower()
    if 'sdb' in n or 'wc' in n or 'douche' in n:
        return 4.0
    if 'dressing' in n or 'degagement' in n or 'dégagement' in n or 'sas' in n:
        return 3.5
    if 'palier' in n or 'hall' in n:
        return 5.0
    if 'cuisine' in n or 'office' in n:
        return 10.0
    if 'salon' in n or 'sejour' in n or 'séjour' in n or 'salle' in n or 'sport' in n or 'jeu' in n:
        return 40.0
    if 'chambre' in n:
        return 16.0
    if 'buanderie' in n or 'lingerie' in n:
        return 6.0
    if 'bureau' in n:
        return 12.0
    return 10.0


def _bbox_from_area_and_walls(cx: float, cy: float, area_m2: float,
                              walls: Optional[List[dict]] = None,
                              mm_per_pt: float = 1.0) -> list:
    """Derive a rectangular bbox in the same unit as (cx, cy).

    Strategy:
      - Start with a square bbox sized from area_m2 (area in m² → side in mm →
        convert to points via mm_per_pt).
      - If walls are provided, tighten the bbox by shrinking toward the
        nearest wall on each side of the centroid.
    """
    side_mm = math.sqrt(area_m2 * 1e6)
    side_pt = side_mm / mm_per_pt
    bx = cx - side_pt / 2
    by = cy - side_pt / 2
    bw = bh = side_pt

    if walls:
        # Find nearest wall intercept in each direction from centroid
        d_up = d_dn = d_lf = d_rt = side_pt  # default half-side
        for w in walls:
            s, e = w['start'], w['end']
            # Horizontal wall (near-constant y)?
            if abs(e[1] - s[1]) < abs(e[0] - s[0]) * 0.3:
                y = (s[1] + e[1]) / 2
                x0, x1 = min(s[0], e[0]), max(s[0], e[0])
                if x0 <= cx <= x1:
                    if y < cy and (cy - y) < d_up:
                        d_up = cy - y
                    elif y > cy and (y - cy) < d_dn:
                        d_dn = y - cy
            # Vertical wall (near-constant x)?
            elif abs(e[0] - s[0]) < abs(e[1] - s[1]) * 0.3:
                x = (s[0] + e[0]) / 2
                y0, y1 = min(s[1], e[1]), max(s[1], e[1])
                if y0 <= cy <= y1:
                    if x < cx and (cx - x) < d_lf:
                        d_lf = cx - x
                    elif x > cx and (x - cx) < d_rt:
                        d_rt = x - cx
        # Clamp to reasonable fractions of the default side
        d_up = min(d_up, side_pt); d_dn = min(d_dn, side_pt)
        d_lf = min(d_lf, side_pt); d_rt = min(d_rt, side_pt)
        bx = cx - d_lf
        by = cy - d_up
        bw = d_lf + d_rt
        bh = d_up + d_dn

    return [bx, by, bw, bh]


def extract_rooms_from_pdf(pdf_path: str, page_idx: int = 0,
                           walls: Optional[List[dict]] = None,
                           mm_per_pt: float = 1.0) -> List[dict]:
    """Return a list of room dicts with PDF-point coordinates (top-down Y).

    Each dict has: name, x, y, area_m2, bbox_mm (misnomer for back-compat —
    it is actually in the same unit as walls: PDF points).
    """
    import pdfplumber
    rooms: List[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx >= len(pdf.pages):
            return rooms
        page = pdf.pages[page_idx]
        words = page.extract_words()
        # Keep only room-related words
        room_words = [w for w in words if _is_room_word(w['text'])]
        merged = _merge_adjacent(room_words)
        for w in merged:
            name = w['text'].strip()
            cx = (w['x0'] + w['x1']) / 2
            cy = (w['top'] + w['bottom']) / 2
            area = _classify_for_area(name)
            bbox = _bbox_from_area_and_walls(cx, cy, area, walls=walls,
                                             mm_per_pt=mm_per_pt)
            aspect = max(bbox[2], bbox[3]) / max(1e-6, min(bbox[2], bbox[3]))
            rooms.append({
                'name': name,
                'x': cx, 'y': cy,
                'area_m2': area,
                'bbox_mm': bbox,  # in same unit as x/y (PDF points here)
                'aspect': round(aspect, 2),
            })
    return rooms

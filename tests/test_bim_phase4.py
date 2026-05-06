#!/usr/bin/env python3
"""
test_bim_phase4.py — Test complet du pipeline BIM Phase 4

Génère un dossier BIM pour la Résidence Papa Oumar Sakho R+8:
  - 6 appartements par étage courant (A, B, C, D + studios E, F)
  - Bâtiment pentagonal (façade NW en biais)
  - 10 niveaux: SS, RDC, R+1 à R+7, R+8 (terrasse)
  - Pipeline complet: Building → équipements → routage MEP → clash → PDF

Usage:
    cd ~/tijan-repo
    python tests/test_bim_phase4.py

Output:
    tests/output/dossier_bim_sakho_phase4.pdf
"""
import os
import sys
import time

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bim_model import (
    Building, Level, Room, Wall, Point,
    RoomType, WallType, EquipmentType, NetworkType,
)
from room_rules import place_equipment_in_room
from mep_router import route_mep
from bim_clash import detect_clashes
from generate_plans_bim import generer_dossier_bim

# ══════════════════════════════════════════════════════════════
# SAKHO R+8 — FAITHFUL GEOMETRY
# ══════════════════════════════════════════════════════════════

# Pentagonal building outline (meters):
#   (0,0) → (28,0) → (28,50) → (16,50) → (0,22)
# Facade NW en biais: de (0,22) à (16,50)

BUILDING_WIDTH = 28.0
BUILDING_DEPTH_E = 50.0   # East side (full depth)
BUILDING_DEPTH_W = 22.0   # West side (shorter — angled facade)

# Common vertical axes
WALL_X = [0.0, 7.0, 14.0, 21.0, 28.0]  # 4 travées de 7m
# Common horizontal axes
WALL_Y_BOTTOM = 0.0
WALL_Y_CIRC = 10.0   # Couloir de circulation
WALL_Y_MID = 25.0
WALL_Y_TOP = BUILDING_DEPTH_E


def _pentagon_walls(level: Level):
    """Create the pentagonal exterior facade + interior grid walls."""
    walls = []

    # ── Exterior facades ──
    facade_pts = [
        (Point(0, 0), Point(28, 0)),                 # South
        (Point(28, 0), Point(28, 50)),                # East
        (Point(28, 50), Point(16, 50)),               # North
        (Point(16, 50), Point(0, 22)),                # NW angled
        (Point(0, 22), Point(0, 0)),                  # West
    ]
    for start, end in facade_pts:
        walls.append(Wall(start=start, end=end,
                          thickness_m=0.25, type=WallType.FACADE))

    # ── Interior structural walls (porteurs) ──
    # Vertical structural walls at x=7, x=14, x=21
    for x in [7.0, 14.0, 21.0]:
        y_top = min(50.0, 22.0 + (x / 16.0) * 28.0) if x < 16 else 50.0
        walls.append(Wall(start=Point(x, 0), end=Point(x, y_top),
                          thickness_m=0.20, type=WallType.PORTEUR))

    # Horizontal structural wall — circulation corridor
    walls.append(Wall(start=Point(0, 10), end=Point(28, 10),
                      thickness_m=0.20, type=WallType.PORTEUR))

    # Horizontal wall — midpoint
    walls.append(Wall(start=Point(0, 22), end=Point(28, 22),
                      thickness_m=0.15, type=WallType.CLOISON))

    level.walls = walls
    return walls


def _make_room(name: str, room_type: RoomType,
               x0: float, y0: float, x1: float, y1: float) -> Room:
    """Create a rectangular room with polygon and area."""
    room = Room(
        type=room_type,
        name=name,
        label=name,
        polygon=[Point(x0, y0), Point(x1, y0),
                 Point(x1, y1), Point(x0, y1)],
    )
    room._area_m2 = abs(x1 - x0) * abs(y1 - y0)
    return room


def _typical_floor_rooms(level: Level, floor_name: str):
    """Create 6 apartments per typical floor.

    Layout (south to north):
        y=0 to y=10:  Apparts A (x=0-7), B (x=7-14), C (x=14-21), D (x=21-28)
                       Each has: séjour, chambre, cuisine, SDB, WC
        y=10 to y=12: Couloir de circulation (full width)
        y=12 to y=22: Studios E (x=0-14) and F (x=14-28)
                       Each has: séjour/chambre, kitchenette, SDB
    """
    rooms = []

    # ── Circulation corridor ──
    rooms.append(_make_room(
        f"Couloir {floor_name}", RoomType.COULOIR,
        0, 10, 28, 12))

    # ── Escalier + Ascenseur (center) ──
    rooms.append(_make_room(
        f"Escalier {floor_name}", RoomType.ESCALIER,
        12, 10, 16, 12))

    # ══ APPARTEMENTS A, B, C, D (y=0 à y=10) ══
    appart_x = [(0, 7), (7, 14), (14, 21), (21, 28)]
    appart_names = ["A", "B", "C", "D"]

    for (x0, x1), apt_name in zip(appart_x, appart_names):
        prefix = f"Apt {apt_name} {floor_name}"

        # Séjour (grande pièce, 60% de la largeur)
        rooms.append(_make_room(
            f"{prefix} — Séjour", RoomType.SEJOUR,
            x0, 0, x0 + 4.2, 6))

        # Chambre
        rooms.append(_make_room(
            f"{prefix} — Chambre", RoomType.CHAMBRE,
            x0, 6, x0 + 4.2, 10))

        # Cuisine
        rooms.append(_make_room(
            f"{prefix} — Cuisine", RoomType.CUISINE,
            x0 + 4.2, 0, x1, 4))

        # SDB
        rooms.append(_make_room(
            f"{prefix} — SDB", RoomType.SDB,
            x0 + 4.2, 4, x1, 7))

        # WC
        rooms.append(_make_room(
            f"{prefix} — WC", RoomType.WC,
            x0 + 4.2, 7, x1, 10))

    # ══ STUDIOS E et F (y=12 à y=22) ══
    studio_x = [(0, 14), (14, 28)]
    studio_names = ["E", "F"]

    for (x0, x1), studio_name in zip(studio_x, studio_names):
        prefix = f"Studio {studio_name} {floor_name}"
        mid_x = (x0 + x1) / 2

        # Séjour/Chambre (pièce principale)
        rooms.append(_make_room(
            f"{prefix} — Séjour", RoomType.SEJOUR,
            x0, 12, mid_x, 22))

        # Kitchenette
        rooms.append(_make_room(
            f"{prefix} — Cuisine", RoomType.CUISINE,
            mid_x, 12, x1, 17))

        # SDB (avec WC intégré)
        rooms.append(_make_room(
            f"{prefix} — SDB", RoomType.SDB,
            mid_x, 17, x1, 22))

    level.rooms = rooms


def _rdc_rooms(level: Level):
    """RDC: Hall d'entrée + commerce + local technique + gardien."""
    rooms = []

    # Hall d'entrée
    rooms.append(_make_room("Hall d'entrée", RoomType.HALL, 10, 0, 18, 8))

    # Commerce 1
    rooms.append(_make_room("Commerce 1", RoomType.COMMERCE, 0, 0, 10, 10))

    # Commerce 2
    rooms.append(_make_room("Commerce 2", RoomType.COMMERCE, 18, 0, 28, 10))

    # Local technique
    rooms.append(_make_room("Local Technique", RoomType.LOCAL_TECHNIQUE,
                            0, 10, 7, 15))

    # Loge gardien
    rooms.append(_make_room("Loge Gardien", RoomType.BUREAU, 7, 10, 14, 15))

    # Couloir distribution
    rooms.append(_make_room("Couloir RDC", RoomType.COULOIR, 14, 10, 28, 15))

    # Escalier
    rooms.append(_make_room("Escalier RDC", RoomType.ESCALIER, 12, 8, 16, 10))

    level.rooms = rooms


def _terrasse_rooms(level: Level):
    """Terrasse: local technique + terrasse accessible."""
    rooms = []
    rooms.append(_make_room("Terrasse Accessible", RoomType.TERRASSE,
                            0, 0, 28, 40))
    rooms.append(_make_room("Local CTA", RoomType.LOCAL_TECHNIQUE,
                            0, 40, 14, 50))
    rooms.append(_make_room("Machinerie Asc.", RoomType.LOCAL_TECHNIQUE,
                            14, 40, 28, 50))
    level.rooms = rooms


def build_sakho() -> Building:
    """Build the full Résidence Papa Oumar Sakho R+8."""
    building = Building(
        name="Résidence Papa Oumar Sakho",
        city="Dakar",
        country="Senegal",
        usage="residentiel",
        reference="1711",
        classe_beton="C30/37",
        classe_acier="HA500",
        zone_sismique=2,
        pression_sol_MPa=0.15,
        distance_mer_km=5.0,
        source_format="test_script",
    )

    # ── Sous-Sol ──
    ss = building.add_level(name="Sous-Sol", index=-1, height_m=3.0)
    ss.elevation_m = -3.0
    _pentagon_walls(ss)
    ss.rooms = [
        _make_room("Parking SS", RoomType.PARKING, 0, 0, 28, 40),
        _make_room("Local CTA SS", RoomType.LOCAL_TECHNIQUE, 0, 40, 14, 50),
        _make_room("Réserve", RoomType.RANGEMENT, 14, 40, 28, 50),
    ]

    # ── RDC ──
    rdc = building.add_level(name="RDC", index=0, height_m=4.0)
    _pentagon_walls(rdc)
    _rdc_rooms(rdc)

    # ── Étages 1 à 7 (courants) ──
    for i in range(1, 8):
        lvl = building.add_level(name=f"R+{i}", index=i, height_m=3.0)
        lvl.elevation_m = 4.0 + (i - 1) * 3.0
        _pentagon_walls(lvl)
        _typical_floor_rooms(lvl, f"R+{i}")

    # ── R+8 (Terrasse) ──
    r8 = building.add_level(name="R+8 Terrasse", index=8, height_m=3.0)
    r8.elevation_m = 4.0 + 7 * 3.0
    _pentagon_walls(r8)
    _terrasse_rooms(r8)

    # Set axes on all levels
    for lvl in building.levels:
        lvl.axes_x = list(WALL_X)
        lvl.axes_y = [0.0, 10.0, 22.0, 50.0]
        lvl.axis_labels_x = ["1", "2", "3", "4", "5"]
        lvl.axis_labels_y = ["A", "B", "C", "D"]

    return building


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _walls_from_polygon(room: Room) -> list:
    """Create Wall objects from a room's polygon edges.

    This is needed because the test constructs rooms independently from
    level walls. In production, Building.from_params_dict links walls
    to rooms by ID, but here we generate walls on the fly.
    """
    if not room.polygon or len(room.polygon) < 3:
        return []

    walls = []
    pts = room.polygon
    n = len(pts)
    for i in range(n):
        start = pts[i]
        end = pts[(i + 1) % n]
        # Determine wall type heuristically
        is_exterior = (start.x == 0 or start.x == 28 or
                       start.y == 0 or start.y == 50 or
                       end.x == 0 or end.x == 28 or
                       end.y == 0 or end.y == 50)
        w = Wall(
            start=start, end=end,
            thickness_m=0.25 if is_exterior else 0.15,
            type=WallType.FACADE if is_exterior else WallType.CLOISON,
            room_left_id=room.id,
        )
        walls.append(w)
    return walls


# ══════════════════════════════════════════════════════════════
# MAIN — RUN FULL PIPELINE
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("TIJAN AI — Test Pipeline BIM Phase 4")
    print("Résidence Papa Oumar Sakho R+8 — Dakar")
    print("=" * 60)

    # Step 1: Build
    print("\n▶ [1/5] Construction du Building...")
    t0 = time.time()
    building = build_sakho()
    total_rooms = sum(len(l.rooms) for l in building.levels)
    print(f"  ✓ {len(building.levels)} niveaux, {total_rooms} pièces")
    print(f"    (dont 6 appartements × 7 étages = 42 unités)")

    # Step 2: Equipment placement
    # Build per-room walls from polygon edges (since test walls aren't linked by ID)
    print("\n▶ [2/5] Placement des équipements...")
    for level in building.levels:
        for room in level.rooms:
            room_walls = _walls_from_polygon(room)
            room.equipment = place_equipment_in_room(room, room_walls)
    total_equip = sum(len(r.equipment)
                      for l in building.levels for r in l.rooms)
    print(f"  ✓ {total_equip} équipements placés")

    # Step 3: MEP routing
    print("\n▶ [3/5] Routage MEP (4 lots)...")
    building = route_mep(building)
    total_segs = sum(len(r.network_segments)
                     for l in building.levels for r in l.rooms)
    total_segs += sum(len(l.network_segments) for l in building.levels)
    print(f"  ✓ {total_segs} segments routés")

    # Step 4: Clash detection
    print("\n▶ [4/5] Détection des conflits...")
    report = detect_clashes(building, lang="fr")
    print(f"  ✓ {report.total_clashes} conflits détectés")
    print(f"    Critiques: {report.hard_count}")
    print(f"    Dégagements: {report.soft_count}")
    print(f"    Croisements: {report.crossing_count}")

    # Step 5: Generate dossier PDF
    print("\n▶ [5/5] Génération du dossier BIM PDF...")
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dossier_bim_sakho_phase4.pdf")

    result = generer_dossier_bim(
        output_path=out_path,
        building=building,
        lang="fr",
    )

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"✓ DOSSIER GÉNÉRÉ EN {elapsed:.1f}s")
    print(f"  Pages: {result['pages']}")
    print(f"  Sublots: {len(result['sublots'])}")
    print(f"  Niveaux: {len(result['levels'])}")
    print(f"  Conflits: {result.get('clash_summary', {})}")
    print(f"  Fichier: {out_path}")
    print(f"  Taille: {os.path.getsize(out_path) / 1024:.0f} KB")
    print(f"{'=' * 60}")

    # Quick sanity checks
    assert result["pages"] > 50, f"Expected 50+ pages, got {result['pages']}"
    assert total_equip > 1000, f"Expected 1000+ equip, got {total_equip}"
    assert total_segs > 500, f"Expected 500+ segments, got {total_segs}"
    print("\n✓ Tous les contrôles passés !")

    return out_path


if __name__ == "__main__":
    pdf_path = main()
    # Open the PDF on macOS
    if sys.platform == "darwin":
        os.system(f'open "{pdf_path}"')

"""
Build a faithful Sakho R+8 geometry from the architectural plans.
Building has a pentagonal footprint (angled NW edge).
Typical floor: 4 apartments (A, B, C, D) + central circulation.
"""
from bim_model import (Building, Level, Room, Wall, Point,
                       RoomType, WallType, EquipmentType, NetworkType)
from room_rules import place_equipment_in_room
from mep_router import route_mep
from generate_plans_bim import generer_dossier_bim

# ─── BUILDING OUTLINE ───
# Pentagonal footprint (meters), from the Sakho plans:
#   - South edge: 28m (axes A→I)
#   - East edge: 50m (axes 1→19)
#   - NW edge angled (property boundary)
#
# Vertices (clockwise from bottom-left):
BUILDING_POLY = [
    Point(0, 0),       # SW corner (axis A/1)
    Point(28, 0),      # SE corner (axis I/1)
    Point(28, 50),     # NE corner (axis I/19)
    Point(16, 50),     # N edge (narrower at top, axis ~F/19)
    Point(0, 22),      # NW angle point (axis A/~7)
]

def make_walls_from_polygon(pts, room_id, wall_type=WallType.FACADE, thickness=0.20):
    """Create walls from a closed polygon."""
    walls = []
    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]
        walls.append(Wall(
            start=Point(p1.x, p1.y), end=Point(p2.x, p2.y),
            thickness_m=thickness, type=wall_type,
            room_left_id=room_id
        ))
    return walls

def polygon_center(pts):
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    return Point(cx, cy)

def polygon_area(pts):
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i].x * pts[j].y
        area -= pts[j].x * pts[i].y
    return abs(area) / 2.0


# ─── SOUS-SOL (Basement) ───
def make_sous_sol():
    level = Level(name="Sous-Sol", elevation_m=-3.0, rooms=[], walls=[])
    # Parking + local technique
    rooms = [
        ("Parking", RoomType.PARKING,
         [Point(0, 0), Point(28, 0), Point(28, 18), Point(0, 18)]),
        ("Rampe", RoomType.COULOIR,
         [Point(0, 18), Point(8, 18), Point(8, 22), Point(0, 22)]),
        ("Local Technique", RoomType.LOCAL_TECHNIQUE,
         [Point(8, 18), Point(16, 18), Point(16, 22), Point(8, 22)]),
        ("Escalier SS", RoomType.ESCALIER,
         [Point(16, 18), Point(20, 18), Point(20, 22), Point(16, 22)]),
    ]
    for name, rtype, poly in rooms:
        room = Room(type=rtype, name=name, polygon=poly,
                    _area_m2=polygon_area(poly))
        walls = make_walls_from_polygon(poly, room.id, WallType.PORTEUR, 0.25)
        level.walls.extend(walls)
        room_walls = [w for w in walls if w.room_left_id == room.id]
        room.equipment = place_equipment_in_room(room, room_walls, lang='fr')
        level.rooms.append(room)
    return level


# ─── REZ-DE-CHAUSSEE ───
def make_rdc():
    level = Level(name="RDC", elevation_m=0.0, rooms=[], walls=[])
    rooms = [
        # Commercial spaces
        ("Commerce 1", RoomType.COMMERCE,
         [Point(0, 0), Point(14, 0), Point(14, 10), Point(0, 10)]),
        ("Commerce 2", RoomType.COMMERCE,
         [Point(14, 0), Point(28, 0), Point(28, 10), Point(14, 10)]),
        # Hall d'entrée + piscine level
        ("Hall", RoomType.HALL,
         [Point(10, 10), Point(18, 10), Point(18, 18), Point(10, 18)]),
        ("Restaurant", RoomType.SEJOUR,
         [Point(0, 10), Point(10, 10), Point(10, 18), Point(0, 18)]),
        ("Piscine / Terrasse", RoomType.TERRASSE,
         [Point(18, 10), Point(28, 10), Point(28, 18), Point(18, 18)]),
        # Suite RDC
        ("Suite RDC - Séjour", RoomType.SEJOUR,
         [Point(16, 18), Point(28, 18), Point(28, 30), Point(16, 30)]),
        ("Suite RDC - Chambre", RoomType.CHAMBRE,
         [Point(16, 30), Point(28, 30), Point(28, 38), Point(16, 38)]),
        ("Suite RDC - SDB", RoomType.SDB,
         [Point(16, 38), Point(22, 38), Point(22, 42), Point(16, 42)]),
        ("Suite RDC - WC", RoomType.WC,
         [Point(22, 38), Point(25, 38), Point(25, 42), Point(22, 42)]),
        # Escalier + ascenseur
        ("Escalier", RoomType.ESCALIER,
         [Point(12, 18), Point(16, 18), Point(16, 24), Point(12, 24)]),
        ("Ascenseur", RoomType.ASCENSEUR,
         [Point(12, 24), Point(16, 24), Point(16, 27), Point(12, 27)]),
        # Couloir
        ("Couloir", RoomType.COULOIR,
         [Point(8, 18), Point(12, 18), Point(12, 22), Point(0, 22), Point(0, 18), Point(8, 18)]),
    ]
    for name, rtype, poly in rooms:
        room = Room(type=rtype, name=name, polygon=poly,
                    _area_m2=polygon_area(poly))
        wt = WallType.FACADE if rtype in (RoomType.COMMERCE, RoomType.HALL) else WallType.CLOISON
        walls = make_walls_from_polygon(poly, room.id, wt, 0.20)
        level.walls.extend(walls)
        room_walls = [w for w in walls if w.room_left_id == room.id]
        room.equipment = place_equipment_in_room(room, room_walls, lang='fr')
        level.rooms.append(room)
    return level


# ─── ETAGE COURANT (Typical floor R+1 to R+7) ───
def make_etage_courant(name, elevation):
    level = Level(name=name, elevation_m=elevation, rooms=[], walls=[])

    # Building outline walls (facade)
    facade_walls = make_walls_from_polygon(BUILDING_POLY, "", WallType.FACADE, 0.25)
    level.walls.extend(facade_walls)

    # ── 4 apartments per floor ──
    # Appart A — bottom-left (south-west)
    appart_a = [
        ("A-Séjour", RoomType.SEJOUR,
         [Point(0, 0), Point(12, 0), Point(12, 8), Point(0, 8)]),
        ("A-Cuisine", RoomType.CUISINE,
         [Point(0, 8), Point(5, 8), Point(5, 12), Point(0, 12)]),
        ("A-Chambre 1", RoomType.CHAMBRE,
         [Point(5, 8), Point(12, 8), Point(12, 12), Point(5, 12)]),
        ("A-Chambre 2", RoomType.CHAMBRE,
         [Point(0, 12), Point(7, 12), Point(7, 17), Point(0, 17)]),
        ("A-SDB", RoomType.SDB,
         [Point(7, 12), Point(11, 12), Point(11, 15), Point(7, 15)]),
        ("A-WC", RoomType.WC,
         [Point(7, 15), Point(10, 15), Point(10, 17), Point(7, 17)]),
        ("A-Dressing", RoomType.DRESSING,
         [Point(0, 17), Point(5, 17), Point(5, 20), Point(0, 20)]),
        ("A-Couloir", RoomType.COULOIR,
         [Point(5, 17), Point(12, 17), Point(12, 22), Point(5, 22), Point(5, 20), Point(0, 20), Point(0, 22)]),
    ]

    # Appart B — bottom-right (south-east)
    appart_b = [
        ("B-Séjour", RoomType.SEJOUR,
         [Point(15, 0), Point(28, 0), Point(28, 8), Point(15, 8)]),
        ("B-Cuisine", RoomType.CUISINE,
         [Point(22, 8), Point(28, 8), Point(28, 12), Point(22, 12)]),
        ("B-Chambre 1", RoomType.CHAMBRE,
         [Point(15, 8), Point(22, 8), Point(22, 12), Point(15, 12)]),
        ("B-Chambre 2", RoomType.CHAMBRE,
         [Point(20, 12), Point(28, 12), Point(28, 17), Point(20, 17)]),
        ("B-SDB", RoomType.SDB,
         [Point(16, 12), Point(20, 12), Point(20, 15), Point(16, 15)]),
        ("B-WC", RoomType.WC,
         [Point(16, 15), Point(19, 15), Point(19, 17), Point(16, 17)]),
        ("B-Dressing", RoomType.DRESSING,
         [Point(23, 17), Point(28, 17), Point(28, 20), Point(23, 20)]),
        ("B-Couloir", RoomType.COULOIR,
         [Point(15, 12), Point(16, 12), Point(16, 22), Point(15, 22)]),
    ]

    # Appart C — top-right (north-east)
    appart_c = [
        ("C-Séjour", RoomType.SEJOUR,
         [Point(16, 32), Point(28, 32), Point(28, 42), Point(16, 42)]),
        ("C-Cuisine", RoomType.CUISINE,
         [Point(22, 42), Point(28, 42), Point(28, 46), Point(22, 46)]),
        ("C-Chambre 1", RoomType.CHAMBRE,
         [Point(16, 42), Point(22, 42), Point(22, 47), Point(16, 47)]),
        ("C-Chambre 2", RoomType.CHAMBRE,
         [Point(20, 47), Point(28, 47), Point(28, 50), Point(20, 50)]),
        ("C-SDB", RoomType.SDB,
         [Point(16, 47), Point(20, 47), Point(20, 50), Point(16, 50)]),
        ("C-Couloir", RoomType.COULOIR,
         [Point(16, 27), Point(28, 27), Point(28, 32), Point(16, 32)]),
    ]

    # Appart D — top-left (north-west, affected by angled edge)
    # NW angle: line from (0, 22) to (16, 50)
    # At y=32: x_edge = 0 + (32-22)/(50-22) * 16 = 10/28 * 16 ≈ 5.7
    # At y=38: x_edge = (38-22)/(50-22) * 16 ≈ 9.1
    # At y=44: x_edge = (44-22)/(50-22) * 16 ≈ 12.6
    appart_d = [
        ("D-Séjour", RoomType.SEJOUR,
         [Point(6, 32), Point(14, 32), Point(14, 40), Point(9, 40)]),
        ("D-Cuisine", RoomType.CUISINE,
         [Point(9, 40), Point(14, 40), Point(14, 44), Point(11, 44)]),
        ("D-Chambre 1", RoomType.CHAMBRE,
         [Point(11, 44), Point(16, 44), Point(16, 50), Point(14, 50)]),
        ("D-SDB", RoomType.SDB,
         [Point(6, 40), Point(9, 40), Point(9, 44), Point(8, 44)]),
        ("D-WC", RoomType.WC,
         [Point(4, 32), Point(6, 32), Point(6, 35), Point(4, 35)]),
        ("D-Couloir", RoomType.COULOIR,
         [Point(2, 27), Point(14, 27), Point(14, 32), Point(4, 32), Point(2, 27)]),
    ]

    # Central circulation
    circulation = [
        ("Escalier", RoomType.ESCALIER,
         [Point(12, 22), Point(16, 22), Point(16, 27), Point(12, 27)]),
        ("Ascenseur", RoomType.ASCENSEUR,
         [Point(14, 22), Point(16, 22), Point(16, 24), Point(14, 24)]),
        ("Palier", RoomType.COULOIR,
         [Point(12, 20), Point(16, 20), Point(16, 22), Point(12, 22)]),
    ]

    all_rooms = appart_a + appart_b + appart_c + appart_d + circulation

    for rname, rtype, poly in all_rooms:
        room = Room(type=rtype, name=rname, polygon=poly,
                    _area_m2=polygon_area(poly))
        wt = WallType.CLOISON
        if rtype in (RoomType.ESCALIER, RoomType.ASCENSEUR):
            wt = WallType.PORTEUR
        walls = make_walls_from_polygon(poly, room.id, wt, 0.15)
        level.walls.extend(walls)
        room_walls = [w for w in walls if w.room_left_id == room.id]
        room.equipment = place_equipment_in_room(room, room_walls, lang='fr')
        level.rooms.append(room)

    return level


# ─── R+8 (dernier étage, plus petit) ───
def make_r8():
    level = Level(name="R+8", elevation_m=24.0, rooms=[], walls=[])
    rooms = [
        ("Penthouse - Séjour", RoomType.SEJOUR,
         [Point(10, 20), Point(28, 20), Point(28, 35), Point(10, 35)]),
        ("Penthouse - Chambre", RoomType.CHAMBRE,
         [Point(14, 35), Point(28, 35), Point(28, 42), Point(14, 42)]),
        ("Penthouse - Cuisine", RoomType.CUISINE,
         [Point(10, 35), Point(14, 35), Point(14, 42), Point(10, 42)]),
        ("Penthouse - SDB", RoomType.SDB,
         [Point(14, 42), Point(20, 42), Point(20, 46), Point(14, 46)]),
        ("Penthouse - WC", RoomType.WC,
         [Point(20, 42), Point(24, 42), Point(24, 46), Point(20, 46)]),
        ("Terrasse", RoomType.TERRASSE,
         [Point(0, 20), Point(10, 20), Point(10, 35), Point(0, 22)]),
        ("Escalier R8", RoomType.ESCALIER,
         [Point(12, 14), Point(16, 14), Point(16, 20), Point(12, 20)]),
    ]
    for name, rtype, poly in rooms:
        room = Room(type=rtype, name=name, polygon=poly,
                    _area_m2=polygon_area(poly))
        walls = make_walls_from_polygon(poly, room.id, WallType.FACADE, 0.20)
        level.walls.extend(walls)
        room_walls = [w for w in walls if w.room_left_id == room.id]
        room.equipment = place_equipment_in_room(room, room_walls, lang='fr')
        level.rooms.append(room)
    return level


# ─── ASSEMBLE BUILDING ───
b = Building(name="Résidence Papa Oumar Sakho",
             city="Dakar", country="Sénégal",
             reference="1711", levels=[])

# Sous-sol
b.levels.append(make_sous_sol())
# RDC
b.levels.append(make_rdc())
# Etages courants R+1 à R+7
for i in range(1, 8):
    b.levels.append(make_etage_courant(f"R+{i}", i * 3.0))
# R+8
b.levels.append(make_r8())

print(f"Building: {len(b.levels)} levels")
for l in b.levels:
    eq_count = sum(len(r.equipment) for r in l.rooms)
    print(f"  {l.name}: {len(l.rooms)} rooms, {eq_count} equipment")

# Route MEP
print("\nRouting MEP networks...")
b = route_mep(b)

total_eq = sum(len(r.equipment) for l in b.levels for r in l.rooms)
total_seg = sum(len(r.network_segments) for l in b.levels for r in l.rooms)
total_seg += sum(len(l.network_segments) for l in b.levels)
print(f"\nTotal: {total_eq} equipment, {total_seg} segments")

# Generate dossier
output = '/sessions/zen-modest-hopper/dossier_bim_sakho_v2.pdf'
print(f"\nGenerating BIM dossier...")
result = generer_dossier_bim(output, b, lang='fr')
print(f"Done: {result['pages']} pages → {output}")
print(f"Trades: {result['trades']}")

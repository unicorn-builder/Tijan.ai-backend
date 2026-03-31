"""
mep_generator.py — Generate MEP plans on real Sakho DXF geometry
Outputs per lot: PDF + DXF. One sub-lot per sheet, all levels.
"""
import json, math, re, os
from datetime import datetime
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
import ezdxf

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
OUT = '/Users/serignetall/tijan-repo/mep_output'
GEOM_DIR = '/Users/serignetall/tijan-repo'
A3L = landscape(A3)
W, H = A3L

# Level files in order
LEVELS = [
    ('SOUS_SOL',   'Sous-Sol / Parking'),
    ('RDC',        'Rez-de-Chaussée'),
    ('ETAGES_1_7', 'Étages 1 à 7 (courant)'),
    ('ETAGE_8',    'Étage 8'),
    ('TERRASSE',   'Terrasse'),
]

# Colors
C = {
    'noir':    colors.HexColor("#111111"),
    'gris':    colors.HexColor("#AAAAAA"),
    'gris_m':  colors.HexColor("#555555"),
    'blanc':   colors.white,
    'vert':    colors.HexColor("#43A956"),
    'bleu':    colors.HexColor("#2196F3"),
    'bleu_f':  colors.HexColor("#0D47A1"),
    'rouge':   colors.HexColor("#E53935"),
    'orange':  colors.HexColor("#FF9800"),
    'cyan':    colors.HexColor("#00BCD4"),
    'jaune':   colors.HexColor("#FFC107"),
    'vert_f':  colors.HexColor("#2E7D32"),
    'marron':  colors.HexColor("#795548"),
    'rose':    colors.HexColor("#E91E63"),
    'violet':  colors.HexColor("#9C27B0"),
}

# ══════════════════════════════════════════════════════════════
# GEOMETRY HELPERS
# ══════════════════════════════════════════════════════════════
def load_geom(level_key):
    path = f'{GEOM_DIR}/sakho_{level_key.lower()}_geom.json'
    with open(path) as f:
        return json.load(f)

def get_bounds(geom):
    xs, ys = [], []
    for item in geom.get('walls',[]) + geom.get('windows',[]) + geom.get('doors',[]):
        if item['type'] == 'line':
            xs += [item['start'][0], item['end'][0]]
            ys += [item['start'][1], item['end'][1]]
        elif item['type'] == 'polyline':
            for p in item['points']: xs.append(p[0]); ys.append(p[1])
        elif item['type'] in ('circle','arc'):
            xs += [item['center'][0]-item['radius'], item['center'][0]+item['radius']]
            ys += [item['center'][1]-item['radius'], item['center'][1]+item['radius']]
    if not xs: return 0,0,1,1
    return min(xs), min(ys), max(xs), max(ys)

def make_transform(geom, margin=18*mm, bottom_reserve=38*mm):
    xn, yn, xx, yx = get_bounds(geom)
    dw, dh = xx-xn, yx-yn
    aw = W - 2*margin
    ah = H - margin - bottom_reserve - margin
    sc = min(aw/dw, ah/dh) if dw>0 and dh>0 else 1
    ow = margin + (aw - dw*sc)/2
    oh = bottom_reserve + (ah - dh*sc)/2
    tx = lambda x: ow + (x - xn)*sc
    ty = lambda y: oh + (y - yn)*sc
    return tx, ty, sc

# ══════════════════════════════════════════════════════════════
# DRAWING HELPERS (PDF)
# ══════════════════════════════════════════════════════════════
def draw_arch(c, geom, tx, ty):
    """Draw walls, windows, doors as light background"""
    # Walls
    c.setStrokeColor(C['gris_m']); c.setLineWidth(0.6)
    for item in geom.get('walls',[]):
        _draw_item(c, item, tx, ty)
    # Windows
    c.setStrokeColor(colors.HexColor("#90CAF9")); c.setLineWidth(0.3)
    for item in geom.get('windows',[]):
        _draw_item(c, item, tx, ty)
    # Doors
    c.setStrokeColor(colors.HexColor("#BCAAA4")); c.setLineWidth(0.25)
    for item in geom.get('doors',[]):
        _draw_item(c, item, tx, ty)
    # Structure
    c.setStrokeColor(colors.HexColor("#BDBDBD")); c.setLineWidth(0.4)
    for item in geom.get('structure',[]):
        _draw_item(c, item, tx, ty)

def _draw_item(c, item, tx, ty):
    if item['type'] == 'line':
        c.line(tx(item['start'][0]), ty(item['start'][1]), tx(item['end'][0]), ty(item['end'][1]))
    elif item['type'] == 'polyline':
        pts = item['points']
        for i in range(len(pts)-1):
            c.line(tx(pts[i][0]), ty(pts[i][1]), tx(pts[i+1][0]), ty(pts[i+1][1]))
        if item.get('closed') and len(pts)>2:
            c.line(tx(pts[-1][0]), ty(pts[-1][1]), tx(pts[0][0]), ty(pts[0][1]))
    elif item['type'] == 'circle':
        c.circle(tx(item['center'][0]), ty(item['center'][1]), item['radius']*0.01, fill=0, stroke=1)

def draw_labels(c, rooms, tx, ty, sz=3.5):
    c.setFillColor(colors.HexColor("#999999")); c.setFont("Helvetica", sz)
    for r in rooms:
        if not re.match(r'^\d', r['name']):
            c.drawCentredString(tx(r['x']), ty(r['y']), r['name'])

def border(c):
    c.setStrokeColor(C['noir']); c.setLineWidth(0.5)
    c.rect(8*mm, 8*mm, W-16*mm, H-16*mm)

def cartouche(c, titre, page, total, niveau=""):
    cw, ch = 195*mm, 30*mm
    cx, cy = W-cw-8*mm, 6*mm
    c.setFillColor(C['blanc']); c.setStrokeColor(C['noir']); c.setLineWidth(0.7)
    c.rect(cx, cy, cw, ch, fill=1, stroke=1)
    c1, c2 = 38*mm, 120*mm
    c.setLineWidth(0.3)
    c.line(cx+c1, cy, cx+c1, cy+ch)
    c.line(cx+c2, cy, cx+c2, cy+ch)
    c.line(cx+c1, cy+ch/2, cx+cw, cy+ch/2)
    c.setFillColor(C['vert']); c.setFont("Helvetica-Bold", 11)
    c.drawString(cx+3*mm, cy+ch-10*mm, "TIJAN AI")
    c.setFillColor(C['gris']); c.setFont("Helvetica", 5.5)
    c.drawString(cx+3*mm, cy+ch-15*mm, "Engineering Intelligence")
    c.drawString(cx+3*mm, cy+5*mm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.setFillColor(C['noir']); c.setFont("Helvetica-Bold", 8)
    c.drawString(cx+c1+3*mm, cy+ch-10*mm, "Résidence SAKHO — Dakar")
    c.setFillColor(C['vert']); c.setFont("Helvetica-Bold", 7)
    c.drawString(cx+c1+3*mm, cy+ch/2+3*mm, titre)
    c.setFillColor(C['noir']); c.setFont("Helvetica", 6)
    c.drawString(cx+c1+3*mm, cy+ch/2-8*mm, niveau)
    c.setFillColor(C['gris']); c.setFont("Helvetica", 6)
    c.drawString(cx+c2+3*mm, cy+ch-10*mm, "Éch: 1/100")
    c.drawString(cx+c2+3*mm, cy+5*mm, f"Pl. {page}/{total}")

def legend_box(c, items, x=10*mm, y=None):
    if y is None: y = H - 10*mm
    lw = 60*mm
    lh = (len(items)+1)*5.5*mm + 3*mm
    c.setFillColor(colors.Color(1,1,1,0.92)); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
    c.rect(x, y-lh, lw, lh, fill=1, stroke=1)
    c.setFillColor(C['noir']); c.setFont("Helvetica-Bold", 6)
    c.drawString(x+3*mm, y-5.5*mm, "LÉGENDE")
    c.line(x+2*mm, y-7*mm, x+lw-2*mm, y-7*mm)
    for i, (col, label, style) in enumerate(items):
        iy = y - (i+2)*5.5*mm
        if style == 'line':
            c.setStrokeColor(col); c.setLineWidth(1.5); c.line(x+3*mm, iy+2, x+13*mm, iy+2)
        elif style == 'dash':
            c.setStrokeColor(col); c.setLineWidth(1); c.setDash(3,2)
            c.line(x+3*mm, iy+2, x+13*mm, iy+2); c.setDash()
        elif style == 'circle':
            c.setFillColor(col); c.circle(x+8*mm, iy+2, 2.5, fill=1, stroke=0)
        elif style == 'rect':
            c.setFillColor(col); c.rect(x+3*mm, iy, 10*mm, 4, fill=1, stroke=0)
        c.setFillColor(C['noir']); c.setFont("Helvetica", 5)
        c.drawString(x+15*mm, iy, label)

# ══════════════════════════════════════════════════════════════
# ROOM CLASSIFICATION
# ══════════════════════════════════════════════════════════════
def classify(rooms):
    wet, living, service = [], [], []
    for r in rooms:
        n = r['name'].lower().strip()
        if re.match(r'^\d', n): continue
        if any(k in n for k in ['sdb','wc','toil','douche']):
            wet.append({**r, 'rt':'wet'})
        elif any(k in n for k in ['cuisine','kitch','buanderie']):
            wet.append({**r, 'rt':'kitchen'})
        elif any(k in n for k in ['salon','chambre','sejour','bureau','sam','bar','gym','depot','restaurant','magasin','salle']):
            living.append({**r, 'rt':'living'})
        elif any(k in n for k in ['hall','palier','asc','dgt','sas','dressing','terrasse','balcon','jardin','piscine','vide','porche','circulation','espace','bac']):
            service.append({**r, 'rt':'service'})
        else:
            living.append({**r, 'rt':'other'})
    return wet, living, service

# ══════════════════════════════════════════════════════════════
# DXF GENERATION HELPER
# ══════════════════════════════════════════════════════════════
def write_dxf(geom_list, layers_config, output_path, mep_entities_fn):
    """
    Create a DXF file with architecture as background + MEP layers.
    geom_list: list of (geom_data, level_label) tuples
    layers_config: dict of layer_name -> (color_index, description)
    mep_entities_fn: function(dxf_msp, geom, level_label) that adds MEP entities
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.new('ARCH_MURS', dxfattribs={'color': 8})  # grey
    doc.layers.new('ARCH_FENETRES', dxfattribs={'color': 4})  # cyan
    doc.layers.new('ARCH_PORTES', dxfattribs={'color': 30})  # brown
    doc.layers.new('ARCH_LABELS', dxfattribs={'color': 9})  # light grey
    for lname, (cidx, _) in layers_config.items():
        doc.layers.new(lname, dxfattribs={'color': cidx})
    
    y_offset = 0
    for geom, level_label in geom_list:
        xn, yn, xx, yx = get_bounds(geom)
        dw, dh = xx-xn, yx-yn
        if dw < 1: continue
        
        # Offset each level vertically
        def ox(x): return x - xn
        def oy(y): return y - yn + y_offset
        
        # Draw architecture
        for item in geom.get('walls', []):
            if item['type'] == 'line':
                msp.add_line((ox(item['start'][0]), oy(item['start'][1])), 
                           (ox(item['end'][0]), oy(item['end'][1])),
                           dxfattribs={'layer': 'ARCH_MURS'})
            elif item['type'] == 'polyline':
                pts = [(ox(p[0]), oy(p[1])) for p in item['points']]
                if item.get('closed'):
                    pts.append(pts[0])
                msp.add_lwpolyline(pts, dxfattribs={'layer': 'ARCH_MURS'})
        
        for item in geom.get('windows', []):
            if item['type'] == 'line':
                msp.add_line((ox(item['start'][0]), oy(item['start'][1])),
                           (ox(item['end'][0]), oy(item['end'][1])),
                           dxfattribs={'layer': 'ARCH_FENETRES'})
            elif item['type'] == 'polyline':
                pts = [(ox(p[0]), oy(p[1])) for p in item['points']]
                msp.add_lwpolyline(pts, dxfattribs={'layer': 'ARCH_FENETRES'})
        
        # Room labels
        for r in geom.get('rooms', []):
            if not re.match(r'^\d', r['name']):
                msp.add_text(r['name'], height=200, 
                           dxfattribs={'layer': 'ARCH_LABELS', 'insert': (ox(r['x']), oy(r['y']))})
        
        # Level label
        msp.add_text(level_label, height=500,
                   dxfattribs={'layer': 'ARCH_LABELS', 'insert': (ox(xn)-2000, oy(yn)+dh/2)})
        
        # MEP entities
        mep_entities_fn(msp, geom, level_label, ox, oy)
        
        y_offset += dh + 15000  # gap between levels
    
    doc.saveas(output_path)

# ══════════════════════════════════════════════════════════════
# LOT 1: PLOMBERIE
# ══════════════════════════════════════════════════════════════
def generate_plomberie():
    print("\n=== LOT 1: PLOMBERIE ===")
    pdf_path = f'{OUT}/LOT_PLOMBERIE_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 3  # 3 sub-sheets per level: EF, EC/drainage, sanitaires
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            # Fallback: use palier positions
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        
        # ── Sheet A: Alimentation Eau Froide ──
        page += 1
        border(c); cartouche(c, "PLOMBERIE — Alimentation Eau Froide", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for sx, sy in shafts:
            px, py = tx(sx), ty(sy)
            c.setFillColor(C['bleu']); c.setStrokeColor(C['bleu_f']); c.setLineWidth(0.6)
            c.circle(px, py, 3.5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(px, py-1.5, "EF")
            c.setFillColor(C['bleu_f']); c.setFont("Helvetica", 3)
            c.drawString(px+5, py+2, "CM EF DN50")
        
        for wr in wet:
            wx, wy = tx(wr['x']), ty(wr['y'])
            if shafts:
                ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                rpx, rpy = tx(ns[0]), ty(ns[1])
                c.setStrokeColor(C['bleu']); c.setLineWidth(0.7)
                # L-shaped routing
                c.line(rpx, rpy, rpx, wy)
                c.line(rpx, wy, wx, wy)
            # Fixture
            n = wr['name'].lower()
            if 'sdb' in n or 'douche' in n:
                c.setFillColor(C['blanc']); c.setStrokeColor(C['bleu']); c.setLineWidth(0.5)
                c.circle(wx, wy, 2.5, fill=1, stroke=1)
                c.setFillColor(C['bleu']); c.setFont("Helvetica", 2.5)
                c.drawCentredString(wx, wy-1, "●")
            elif 'wc' in n or 'toil' in n:
                c.setFillColor(C['bleu']); c.circle(wx, wy, 2, fill=1, stroke=0)
            elif 'cuisine' in n or 'kitch' in n:
                c.setFillColor(C['bleu']); c.rect(wx-2.5, wy-1.5, 5, 3, fill=1, stroke=0)
            elif 'buanderie' in n:
                c.setFillColor(C['cyan']); c.rect(wx-2, wy-2, 4, 4, fill=1, stroke=0)
        
        legend_box(c, [
            (C['bleu'], "Colonne montante EF DN50", 'circle'),
            (C['bleu'], "Réseau distribution EF", 'line'),
            (C['bleu'], "Point d'eau SDB/Douche", 'circle'),
            (C['bleu'], "WC / Toilettes", 'circle'),
            (C['bleu'], "Évier cuisine", 'rect'),
            (C['cyan'], "Machine à laver", 'rect'),
        ])
        c.showPage()
        
        # ── Sheet B: Eau Chaude ──
        page += 1
        border(c); cartouche(c, "PLOMBERIE — Alimentation Eau Chaude", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for sx, sy in shafts:
            px, py = tx(sx), ty(sy)
            c.setFillColor(C['rouge']); c.setStrokeColor(colors.HexColor("#B71C1C")); c.setLineWidth(0.6)
            c.circle(px, py, 3.5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(px, py-1.5, "EC")
            c.setFillColor(colors.HexColor("#B71C1C")); c.setFont("Helvetica", 3)
            c.drawString(px+5, py+2, "CM EC DN32")
        
        for wr in wet:
            wx, wy = tx(wr['x']), ty(wr['y'])
            n = wr['name'].lower()
            if any(k in n for k in ['sdb','douche','cuisine','kitch','buanderie']):
                if shafts:
                    ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                    rpx, rpy = tx(ns[0]), ty(ns[1])
                    c.setStrokeColor(C['rouge']); c.setLineWidth(0.5); c.setDash(3,1.5)
                    c.line(rpx, rpy, rpx, wy); c.line(rpx, wy, wx, wy)
                    c.setDash()
                c.setFillColor(C['blanc']); c.setStrokeColor(C['rouge']); c.setLineWidth(0.5)
                c.circle(wx, wy, 2.5, fill=1, stroke=1)
        
        legend_box(c, [
            (C['rouge'], "Colonne montante EC DN32", 'circle'),
            (C['rouge'], "Réseau distribution EC", 'dash'),
            (C['rouge'], "Point desserte EC", 'circle'),
        ])
        c.showPage()
        
        # ── Sheet C: Évacuations EU/EP ──
        page += 1
        border(c); cartouche(c, "PLOMBERIE — Évacuations EU/EP", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for sx, sy in shafts:
            px, py = tx(sx), ty(sy)
            c.setFillColor(C['marron']); c.setStrokeColor(C['noir']); c.setLineWidth(0.6)
            c.circle(px, py, 3.5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(px, py-1.5, "EU")
            c.setFillColor(C['marron']); c.setFont("Helvetica", 3)
            c.drawString(px+5, py+2, "CE EU DN100")
        
        for wr in wet:
            wx, wy = tx(wr['x']), ty(wr['y'])
            if shafts:
                ns = min(shafts, key=lambda s: (s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                rpx, rpy = tx(ns[0]), ty(ns[1])
                c.setStrokeColor(C['marron']); c.setLineWidth(0.5); c.setDash(4,2)
                c.line(wx, wy, rpx, wy); c.line(rpx, wy, rpx, rpy)
                c.setDash()
            c.setFillColor(C['marron']); c.circle(wx, wy, 2, fill=1, stroke=0)
        
        # Sanitary fixtures from DXF
        c.setStrokeColor(C['bleu']); c.setLineWidth(0.2)
        for item in geom.get('sanitary',[]):
            _draw_item(c, item, tx, ty)
        
        legend_box(c, [
            (C['marron'], "Chute EU DN100", 'circle'),
            (C['marron'], "Collecteur évacuation", 'dash'),
            (C['marron'], "Siphon de sol / regard", 'circle'),
            (C['bleu'], "Appareil sanitaire (DXF)", 'line'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")
    
    # DXF
    dxf_path = f'{OUT}/LOT_PLOMBERIE_Sakho.dxf'
    layers = {
        'PLB_EAU_FROIDE':   (5, 'Alimentation eau froide'),   # blue
        'PLB_EAU_CHAUDE':   (1, 'Alimentation eau chaude'),   # red
        'PLB_EVACUATION':   (30, 'Évacuations EU/EP'),        # brown
        'PLB_APPAREILS':    (4, 'Appareils sanitaires'),      # cyan
    }
    def plb_mep(msp, geom, lvl, ox, oy):
        wet, _, service = classify(geom['rooms'])
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        for sx,sy in shafts:
            msp.add_circle((ox(sx), oy(sy)), 500, dxfattribs={'layer':'PLB_EAU_FROIDE'})
            msp.add_text("CM EF DN50", height=200, dxfattribs={'layer':'PLB_EAU_FROIDE','insert':(ox(sx)+600, oy(sy)+200)})
            msp.add_circle((ox(sx)+1500, oy(sy)), 500, dxfattribs={'layer':'PLB_EAU_CHAUDE'})
            msp.add_text("CM EC DN32", height=200, dxfattribs={'layer':'PLB_EAU_CHAUDE','insert':(ox(sx)+2200, oy(sy)+200)})
            msp.add_circle((ox(sx)+750, oy(sy)-1500), 500, dxfattribs={'layer':'PLB_EVACUATION'})
            msp.add_text("CE EU DN100", height=200, dxfattribs={'layer':'PLB_EVACUATION','insert':(ox(sx)+1500, oy(sy)-1300)})
        for wr in wet:
            n = wr['name'].lower()
            if shafts:
                ns = min(shafts, key=lambda s:(s[0]-wr['x'])**2+(s[1]-wr['y'])**2)
                msp.add_line((ox(ns[0]),oy(ns[1])),(ox(ns[0]),oy(wr['y'])), dxfattribs={'layer':'PLB_EAU_FROIDE'})
                msp.add_line((ox(ns[0]),oy(wr['y'])),(ox(wr['x']),oy(wr['y'])), dxfattribs={'layer':'PLB_EAU_FROIDE'})
                if any(k in n for k in ['sdb','douche','cuisine','kitch','buanderie']):
                    msp.add_line((ox(ns[0])+200,oy(ns[1])),(ox(ns[0])+200,oy(wr['y'])+200), dxfattribs={'layer':'PLB_EAU_CHAUDE'})
                    msp.add_line((ox(ns[0])+200,oy(wr['y'])+200),(ox(wr['x'])+200,oy(wr['y'])+200), dxfattribs={'layer':'PLB_EAU_CHAUDE'})
                msp.add_line((ox(wr['x']),oy(wr['y'])-200),(ox(ns[0]),oy(wr['y'])-200), dxfattribs={'layer':'PLB_EVACUATION'})
            msp.add_circle((ox(wr['x']),oy(wr['y'])), 300, dxfattribs={'layer':'PLB_APPAREILS'})
            msp.add_text(wr['name'], height=150, dxfattribs={'layer':'PLB_APPAREILS','insert':(ox(wr['x'])+400, oy(wr['y']))})
    
    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, plb_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 2: ÉLECTRICITÉ
# ══════════════════════════════════════════════════════════════
def generate_electricite():
    print("\n=== LOT 2: ÉLECTRICITÉ ===")
    pdf_path = f'{OUT}/LOT_ELECTRICITE_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 3
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        all_r = wet + living + service
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower() or 'palier' in r['name'].lower()]
        
        # ── Sheet A: Éclairage ──
        page += 1
        border(c); cartouche(c, "ÉLECTRICITÉ — Plan d'éclairage", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            # Luminaire
            c.setStrokeColor(C['jaune']); c.setFillColor(colors.HexColor("#FFF8E1"))
            c.setLineWidth(0.4)
            c.circle(rx, ry+5, 2.5, fill=1, stroke=1)
            c.setStrokeColor(C['jaune']); c.setLineWidth(0.3)
            c.line(rx-1.5, ry+5, rx+1.5, ry+5)
            c.line(rx, ry+3.5, rx, ry+6.5)
            # Switch
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','cuisine','kitch','sdb','wc','toil','restaurant','magasin','salle']):
                c.setFillColor(colors.HexColor("#FFF9C4")); c.setStrokeColor(C['orange']); c.setLineWidth(0.3)
                c.circle(rx-7, ry+2, 1.5, fill=1, stroke=1)
        
        legend_box(c, [
            (C['jaune'], "Luminaire plafonnier", 'circle'),
            (colors.HexColor("#FFF9C4"), "Interrupteur simple", 'circle'),
        ])
        c.showPage()
        
        # ── Sheet B: Prises de courant ──
        page += 1
        border(c); cartouche(c, "ÉLECTRICITÉ — Prises de courant", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            c.setFillColor(C['orange']); c.setStrokeColor(C['noir']); c.setLineWidth(0.15)
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','restaurant']):
                for dx,dy in [(-6,-3),(6,-3),(-6,3),(6,3)]:
                    c.rect(rx+dx-1.2, ry+dy-0.8, 2.4, 1.6, fill=1, stroke=1)
            elif any(k in n for k in ['cuisine','kitch']):
                for dx,dy in [(-6,-3),(6,-3),(-6,3),(6,3),(0,-5),(0,5)]:
                    c.rect(rx+dx-1.2, ry+dy-0.8, 2.4, 1.6, fill=1, stroke=1)
                c.setFillColor(C['rouge']); c.setFont("Helvetica", 2)
                c.drawCentredString(rx, ry-8, "32A")
            elif any(k in n for k in ['sdb','wc','toil','douche']):
                c.rect(rx+4, ry-0.8, 2.4, 1.6, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica", 1.5)
            elif any(k in n for k in ['hall','palier','dgt','sas','circulation']):
                c.rect(rx+4, ry-0.8, 2.4, 1.6, fill=1, stroke=1)
        
        legend_box(c, [
            (C['orange'], "Prise 2P+T 16A", 'rect'),
            (C['rouge'], "Prise spécialisée 32A", 'rect'),
        ])
        c.showPage()
        
        # ── Sheet C: Distribution / TGBT ──
        page += 1
        border(c); cartouche(c, "ÉLECTRICITÉ — Distribution / TGBT", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        # TGBT
        if shafts:
            px, py = tx(shafts[0][0]), ty(shafts[0][1])
            c.setFillColor(C['vert']); c.setStrokeColor(C['noir']); c.setLineWidth(0.6)
            c.rect(px-6, py-12, 12, 8, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(px, py-10, "TD")
            # Cable tray to halls
            halls = sorted([r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt'])], key=lambda r: r['y'])
            if halls:
                c.setStrokeColor(C['orange']); c.setLineWidth(1.5)
                prev_x, prev_y = px, py-8
                for h in halls:
                    hx, hy = tx(h['x']), ty(h['y'])
                    c.line(prev_x, prev_y, hx, hy)
                    prev_x, prev_y = hx, hy
        
        # Circuits to rooms
        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            if shafts:
                ppx, ppy = tx(shafts[0][0]), ty(shafts[0][1])
                c.setStrokeColor(C['orange']); c.setLineWidth(0.2); c.setDash(1,1)
                c.line(ppx, ppy-8, rx, ry); c.setDash()
        
        legend_box(c, [
            (C['vert'], "Tableau divisionnaire (TD)", 'rect'),
            (C['orange'], "Chemin de câbles", 'line'),
            (C['orange'], "Circuit terminal", 'dash'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")
    
    # DXF
    dxf_path = f'{OUT}/LOT_ELECTRICITE_Sakho.dxf'
    layers = {
        'ELEC_ECLAIRAGE': (2, 'Éclairage'),      # yellow
        'ELEC_PRISES':    (30, 'Prises'),          # orange
        'ELEC_DISTRIB':   (3, 'Distribution'),     # green
    }
    def elec_mep(msp, geom, lvl, ox, oy):
        wet, living, service = classify(geom['rooms'])
        all_r = wet+living+service
        for r in all_r:
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            msp.add_circle((ox(r['x']),oy(r['y'])+500), 250, dxfattribs={'layer':'ELEC_ECLAIRAGE'})
            msp.add_text("LUM", height=150, dxfattribs={'layer':'ELEC_ECLAIRAGE','insert':(ox(r['x'])+300, oy(r['y'])+500)})
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','cuisine','kitch']):
                for dx,dy in [(-800,-400),(800,-400),(-800,400),(800,400)]:
                    msp.add_lwpolyline([(ox(r['x'])+dx-100,oy(r['y'])+dy-70),(ox(r['x'])+dx+100,oy(r['y'])+dy-70),(ox(r['x'])+dx+100,oy(r['y'])+dy+70),(ox(r['x'])+dx-100,oy(r['y'])+dy+70),(ox(r['x'])+dx-100,oy(r['y'])+dy-70)], dxfattribs={'layer':'ELEC_PRISES'})
    
    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, elec_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 3: CVC
# ══════════════════════════════════════════════════════════════
def generate_cvc():
    print("\n=== LOT 3: CVC ===")
    pdf_path = f'{OUT}/LOT_CVC_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 2
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        terrasses = [r for r in service if any(k in r['name'].lower() for k in ['terrasse','balcon'])]
        
        # ── Sheet A: Climatisation (splits) ──
        page += 1
        border(c); cartouche(c, "CVC — Climatisation / Splits", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for r in living:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','gym','restaurant','salle','magasin']):
                c.setFillColor(C['cyan']); c.setStrokeColor(C['bleu_f']); c.setLineWidth(0.35)
                c.rect(rx-4.5, ry+7, 9, 2.5, fill=1, stroke=1)
                c.setFillColor(C['bleu_f']); c.setFont("Helvetica", 2.2)
                if 'salon' in n or 'sejour' in n or 'sam' in n or 'restaurant' in n:
                    c.drawCentredString(rx, ry+11.5, "18000 BTU")
                elif 'chambre' in n:
                    c.drawCentredString(rx, ry+11.5, "12000 BTU")
                else:
                    c.drawCentredString(rx, ry+11.5, "9000 BTU")
                # Refrigerant line to outdoor
                if terrasses:
                    near = min(terrasses, key=lambda t:(t['x']-r['x'])**2+(t['y']-r['y'])**2)
                    c.setStrokeColor(C['cyan']); c.setLineWidth(0.3); c.setDash(2,1)
                    c.line(rx, ry+8, tx(near['x']), ty(near['y'])); c.setDash()
                    c.setFillColor(colors.HexColor("#B2EBF2")); c.setStrokeColor(C['cyan']); c.setLineWidth(0.3)
                    c.rect(tx(near['x'])-3, ty(near['y'])-2, 6, 4, fill=1, stroke=1)
        
        legend_box(c, [
            (C['cyan'], "Split mural (unité int.)", 'rect'),
            (colors.HexColor("#B2EBF2"), "Unité extérieure", 'rect'),
            (C['cyan'], "Ligne frigorifique", 'dash'),
        ])
        c.showPage()
        
        # ── Sheet B: Ventilation VMC ──
        page += 1
        border(c); cartouche(c, "CVC — Ventilation / VMC", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for r in wet:
            rx, ry = tx(r['x']), ty(r['y'])
            c.setStrokeColor(C['vert_f']); c.setFillColor(colors.HexColor("#C8E6C9"))
            c.setLineWidth(0.4)
            c.circle(rx, ry+4, 2.5, fill=1, stroke=1)
            # Arrow
            c.setStrokeColor(C['vert_f']); c.setLineWidth(0.5)
            c.line(rx, ry+6.5, rx, ry+9)
            path = c.beginPath()
            path.moveTo(rx, ry+10.5); path.lineTo(rx-1.5, ry+8.5); path.lineTo(rx+1.5, ry+8.5)
            path.close(); c.setFillColor(C['vert_f']); c.drawPath(path, fill=1, stroke=0)
        
        # VMC duct
        halls = sorted([r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt'])], key=lambda r: r['y'])
        if len(halls) >= 2:
            c.setStrokeColor(C['vert_f']); c.setLineWidth(1.2); c.setDash(5,2)
            for i in range(len(halls)-1):
                c.line(tx(halls[i]['x']), ty(halls[i]['y']), tx(halls[i+1]['x']), ty(halls[i+1]['y']))
            c.setDash()
        
        legend_box(c, [
            (C['vert_f'], "Bouche extraction VMC", 'circle'),
            (C['vert_f'], "Gaine VMC", 'dash'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")
    
    # DXF
    dxf_path = f'{OUT}/LOT_CVC_Sakho.dxf'
    layers = {
        'CVC_SPLITS':      (4, 'Climatisation splits'),    # cyan
        'CVC_FRIGORIFIQUE': (4, 'Lignes frigorifiques'),
        'CVC_VMC':          (3, 'Ventilation VMC'),         # green
    }
    def cvc_mep(msp, geom, lvl, ox, oy):
        wet, living, service = classify(geom['rooms'])
        for r in living:
            n = r['name'].lower()
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','gym','restaurant']):
                pts = [(ox(r['x'])-600,oy(r['y'])+800),(ox(r['x'])+600,oy(r['y'])+800),(ox(r['x'])+600,oy(r['y'])+1100),(ox(r['x'])-600,oy(r['y'])+1100),(ox(r['x'])-600,oy(r['y'])+800)]
                msp.add_lwpolyline(pts, dxfattribs={'layer':'CVC_SPLITS'})
                if 'salon' in n or 'sejour' in n: label = "18000 BTU"
                elif 'chambre' in n: label = "12000 BTU"
                else: label = "9000 BTU"
                msp.add_text(label, height=150, dxfattribs={'layer':'CVC_SPLITS','insert':(ox(r['x'])-500,oy(r['y'])+1200)})
        for r in wet:
            msp.add_circle((ox(r['x']),oy(r['y'])+400), 250, dxfattribs={'layer':'CVC_VMC'})
            msp.add_text("VMC", height=150, dxfattribs={'layer':'CVC_VMC','insert':(ox(r['x'])+300, oy(r['y'])+400)})
    
    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, cvc_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 4: SÉCURITÉ INCENDIE
# ══════════════════════════════════════════════════════════════
def generate_securite_incendie():
    print("\n=== LOT 4: SÉCURITÉ INCENDIE ===")
    pdf_path = f'{OUT}/LOT_SECURITE_INCENDIE_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 2
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        all_r = wet + living + service
        exits = [r for r in service if any(k in r['name'].lower() for k in ['palier','hall','sas'])]
        
        # ── Sheet A: Détection + Alarme ──
        page += 1
        border(c); cartouche(c, "SÉCURITÉ INCENDIE — Détection & Alarme", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            # Détecteur fumée
            c.setFillColor(C['blanc']); c.setStrokeColor(C['rouge']); c.setLineWidth(0.5)
            c.circle(rx, ry-5, 2.5, fill=1, stroke=1)
            c.setFillColor(C['rouge']); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(rx, ry-6.5, "DF")
        
        for r in exits:
            rx, ry = tx(r['x']), ty(r['y'])
            # DM
            c.setFillColor(C['rouge']); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
            c.rect(rx-7, ry-2.5, 4, 4, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2.5)
            c.drawCentredString(rx-5, ry-1.5, "DM")
            # Sirène
            c.setFillColor(C['orange']); c.setStrokeColor(C['noir']); c.setLineWidth(0.25)
            c.circle(rx-8, ry+6, 2.5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2.5)
            c.drawCentredString(rx-8, ry+5, "S")
        
        # Alarm circuit
        if len(exits) >= 2:
            se = sorted(exits, key=lambda r: r['y'])
            c.setStrokeColor(C['rouge']); c.setLineWidth(0.7); c.setDash(3,2)
            for i in range(len(se)-1):
                c.line(tx(se[i]['x']), ty(se[i]['y'])-5, tx(se[i+1]['x']), ty(se[i+1]['y'])-5)
            c.setDash()
        
        legend_box(c, [
            (C['rouge'], "Détecteur de fumée (DF)", 'circle'),
            (C['rouge'], "Déclencheur manuel (DM)", 'rect'),
            (C['orange'], "Sirène d'alarme", 'circle'),
            (C['rouge'], "Boucle alarme incendie", 'dash'),
        ])
        c.showPage()
        
        # ── Sheet B: Moyens d'extinction + BAES ──
        page += 1
        border(c); cartouche(c, "SÉCURITÉ INCENDIE — Extinction & Éclairage sécurité", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)
        
        stairs = [r for r in service if 'palier' in r['name'].lower()]
        for r in stairs:
            rx, ry = tx(r['x']), ty(r['y'])
            # RIA
            c.setFillColor(C['blanc']); c.setStrokeColor(C['rouge']); c.setLineWidth(0.7)
            c.circle(rx+9, ry+4, 3.5, fill=1, stroke=1)
            c.setFillColor(C['rouge']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(rx+9, ry+2.5, "R")
        
        for i, r in enumerate(exits):
            rx, ry = tx(r['x']), ty(r['y'])
            # Extincteur (every other exit)
            if i % 2 == 0:
                c.setFillColor(C['rouge']); c.setStrokeColor(C['noir']); c.setLineWidth(0.25)
                path = c.beginPath()
                path.moveTo(rx+7, ry+4); path.lineTo(rx+5, ry-1); path.lineTo(rx+9, ry-1)
                path.close(); c.drawPath(path, fill=1, stroke=0)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2.5)
                c.drawCentredString(rx+7, ry, "E")
            # BAES
            c.setFillColor(C['vert']); c.setStrokeColor(C['noir']); c.setLineWidth(0.25)
            c.rect(rx+4, ry-8, 5, 3, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
            c.drawCentredString(rx+6.5, ry-7, "BAES")
        
        legend_box(c, [
            (C['rouge'], "RIA (Robinet Inc. Armé)", 'circle'),
            (C['rouge'], "Extincteur CO2/poudre", 'circle'),
            (C['vert'], "BAES (éclairage sécurité)", 'rect'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")
    
    # DXF
    dxf_path = f'{OUT}/LOT_SECURITE_INCENDIE_Sakho.dxf'
    layers = {
        'SSI_DETECTION':   (1, 'Détection incendie'),     # red
        'SSI_ALARME':      (30, 'Alarme incendie'),        # orange
        'SSI_EXTINCTION':  (1, 'Moyens extinction'),
        'SSI_BAES':        (3, 'Éclairage sécurité'),      # green
    }
    def ssi_mep(msp, geom, lvl, ox, oy):
        wet, living, service = classify(geom['rooms'])
        all_r = wet+living+service
        for r in all_r:
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            msp.add_circle((ox(r['x']),oy(r['y'])-500), 250, dxfattribs={'layer':'SSI_DETECTION'})
            msp.add_text("DF", height=150, dxfattribs={'layer':'SSI_DETECTION','insert':(ox(r['x'])+300, oy(r['y'])-500)})
        exits = [r for r in service if any(k in r['name'].lower() for k in ['palier','hall','sas'])]
        for r in exits:
            msp.add_lwpolyline([(ox(r['x'])-600,oy(r['y'])-300),(ox(r['x'])-200,oy(r['y'])-300),(ox(r['x'])-200,oy(r['y'])+100),(ox(r['x'])-600,oy(r['y'])+100),(ox(r['x'])-600,oy(r['y'])-300)], dxfattribs={'layer':'SSI_ALARME'})
            msp.add_text("DM", height=150, dxfattribs={'layer':'SSI_ALARME','insert':(ox(r['x'])-550, oy(r['y'])-200)})
            msp.add_lwpolyline([(ox(r['x'])+400,oy(r['y'])-800),(ox(r['x'])+900,oy(r['y'])-800),(ox(r['x'])+900,oy(r['y'])-500),(ox(r['x'])+400,oy(r['y'])-500),(ox(r['x'])+400,oy(r['y'])-800)], dxfattribs={'layer':'SSI_BAES'})
            msp.add_text("BAES", height=120, dxfattribs={'layer':'SSI_BAES','insert':(ox(r['x'])+420, oy(r['y'])-750)})
        for r in [r for r in service if 'palier' in r['name'].lower()]:
            msp.add_circle((ox(r['x'])+1000,oy(r['y'])+400), 350, dxfattribs={'layer':'SSI_EXTINCTION'})
            msp.add_text("RIA", height=200, dxfattribs={'layer':'SSI_EXTINCTION','insert':(ox(r['x'])+700, oy(r['y'])+400)})
    
    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, ssi_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 5: COURANTS FAIBLES
# ══════════════════════════════════════════════════════════════
def generate_courants_faibles():
    print("\n=== LOT 5: COURANTS FAIBLES ===")
    pdf_path = f'{OUT}/LOT_COURANTS_FAIBLES_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 3

    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        all_r = wet + living + service
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        halls = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt','sas'])]

        # ── Sheet A: Réseau informatique (RJ45 / Fibre) ──
        page += 1
        border(c); cartouche(c, "COURANTS FAIBLES — Réseau informatique", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        # Baie de brassage near shaft
        if shafts:
            px, py = tx(shafts[0][0]), ty(shafts[0][1])
            c.setFillColor(C['violet']); c.setStrokeColor(C['noir']); c.setLineWidth(0.6)
            c.rect(px-5, py+15, 10, 7, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 3.5)
            c.drawCentredString(px, py+17, "BAIE")
            c.setFillColor(C['violet']); c.setFont("Helvetica", 2.5)
            c.drawCentredString(px, py+23.5, "Baie brassage 19\"")

        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue

            # RJ45 outlets
            nb_rj45 = 0
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar']):
                nb_rj45 = 2
            elif any(k in n for k in ['cuisine','kitch','restaurant','magasin','salle']):
                nb_rj45 = 2
            elif any(k in n for k in ['hall','palier','sas']):
                nb_rj45 = 1

            for j in range(nb_rj45):
                ox_off = -5 + j * 10
                c.setFillColor(C['violet']); c.setStrokeColor(C['noir']); c.setLineWidth(0.2)
                c.rect(rx+ox_off-1.5, ry-4, 3, 2.5, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 1.8)
                c.drawCentredString(rx+ox_off, ry-3.2, "RJ")

            # Cable run from baie
            if nb_rj45 > 0 and shafts:
                ppx, ppy = tx(shafts[0][0]), ty(shafts[0][1])
                c.setStrokeColor(C['violet']); c.setLineWidth(0.2); c.setDash(1,1)
                c.line(ppx, ppy+15, rx, ry-2); c.setDash()

        legend_box(c, [
            (C['violet'], "Baie de brassage 19\"", 'rect'),
            (C['violet'], "Prise RJ45 Cat.6", 'rect'),
            (C['violet'], "Câblage VDI", 'dash'),
        ])
        c.showPage()

        # ── Sheet B: Vidéosurveillance ──
        page += 1
        border(c); cartouche(c, "COURANTS FAIBLES — Vidéosurveillance", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        # NVR near shaft
        if shafts:
            px, py = tx(shafts[0][0]), ty(shafts[0][1])
            c.setFillColor(colors.HexColor("#4A148C")); c.setStrokeColor(C['noir']); c.setLineWidth(0.5)
            c.rect(px-5, py+15, 10, 6, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(px, py+17, "NVR")

        # Cameras at halls, paliers, entrances, parking
        cam_rooms = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','sas','porche','circulation'])]
        # Also at parking/sous-sol specific rooms
        cam_rooms += [r for r in all_r if any(k in r['name'].lower() for k in ['stationnement','parking','entrée'])]

        for r in cam_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            # Camera symbol (triangle)
            c.setFillColor(colors.HexColor("#7B1FA2")); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
            path = c.beginPath()
            path.moveTo(rx, ry+8); path.lineTo(rx-3, ry+3); path.lineTo(rx+3, ry+3)
            path.close(); c.drawPath(path, fill=1, stroke=0)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
            c.drawCentredString(rx, ry+4.5, "C")
            # Cable to NVR
            if shafts:
                ppx, ppy = tx(shafts[0][0]), ty(shafts[0][1])
                c.setStrokeColor(colors.HexColor("#7B1FA2")); c.setLineWidth(0.2); c.setDash(2,1)
                c.line(ppx, ppy+15, rx, ry+5); c.setDash()

        # Exterior cameras at terrasses/balcons (fewer)
        ext_rooms = [r for r in service if any(k in r['name'].lower() for k in ['terrasse','balcon'])]
        for i, r in enumerate(ext_rooms):
            if i % 3 == 0:  # 1 camera every 3 terrasses
                rx, ry = tx(r['x']), ty(r['y'])
                c.setFillColor(colors.HexColor("#CE93D8")); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
                path = c.beginPath()
                path.moveTo(rx, ry+8); path.lineTo(rx-3, ry+3); path.lineTo(rx+3, ry+3)
                path.close(); c.drawPath(path, fill=1, stroke=0)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
                c.drawCentredString(rx, ry+4.5, "E")

        legend_box(c, [
            (colors.HexColor("#4A148C"), "NVR (enregistreur)", 'rect'),
            (colors.HexColor("#7B1FA2"), "Caméra intérieure IP", 'circle'),
            (colors.HexColor("#CE93D8"), "Caméra extérieure IP", 'circle'),
            (colors.HexColor("#7B1FA2"), "Câble réseau caméra", 'dash'),
        ])
        c.showPage()

        # ── Sheet C: Contrôle d'accès + Interphonie ──
        page += 1
        border(c); cartouche(c, "COURANTS FAIBLES — Contrôle d'accès & Interphonie", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        # Access points at halls, entries, paliers
        access_rooms = [r for r in service if any(k in r['name'].lower() for k in ['hall','sas','porche'])]
        for r in access_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            # Badge reader (diamond)
            c.setFillColor(colors.HexColor("#00695C")); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
            path = c.beginPath()
            path.moveTo(rx+8, ry+6); path.lineTo(rx+11, ry+3); path.lineTo(rx+8, ry); path.lineTo(rx+5, ry+3)
            path.close(); c.drawPath(path, fill=1, stroke=0)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
            c.drawCentredString(rx+8, ry+2, "BA")

        # Interphones at paliers
        interph_rooms = [r for r in service if 'palier' in r['name'].lower()]
        for r in interph_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            c.setFillColor(colors.HexColor("#00897B")); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
            c.rect(rx-8, ry+5, 4, 5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
            c.drawCentredString(rx-6, ry+7, "IP")

        # Interphones inside apartments (living rooms)
        for r in living:
            n = r['name'].lower()
            if 'salon' in n or 'sejour' in n:
                rx, ry = tx(r['x']), ty(r['y'])
                c.setFillColor(colors.HexColor("#4DB6AC")); c.setStrokeColor(C['noir']); c.setLineWidth(0.2)
                c.rect(rx+8, ry+5, 3.5, 4.5, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 1.8)
                c.drawCentredString(rx+9.8, ry+6.5, "IP")

        legend_box(c, [
            (colors.HexColor("#00695C"), "Lecteur de badge (accès)", 'circle'),
            (colors.HexColor("#00897B"), "Interphone palier", 'rect'),
            (colors.HexColor("#4DB6AC"), "Combiné interphone appt.", 'rect'),
        ])
        c.showPage()

    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

    # DXF
    dxf_path = f'{OUT}/LOT_COURANTS_FAIBLES_Sakho.dxf'
    layers = {
        'CFA_VDI':       (6, 'Réseau informatique VDI'),   # magenta
        'CFA_VIDEO':     (6, 'Vidéosurveillance'),
        'CFA_ACCES':     (4, 'Contrôle accès'),             # cyan
        'CFA_INTERPH':   (4, 'Interphonie'),
    }
    def cfa_mep(msp, geom, lvl, ox, oy):
        wet, living, service = classify(geom['rooms'])
        all_r = wet+living+service
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        # Baie
        if shafts:
            sx, sy = shafts[0]
            msp.add_lwpolyline([(ox(sx)-500,oy(sy)+1500),(ox(sx)+500,oy(sy)+1500),(ox(sx)+500,oy(sy)+2200),(ox(sx)-500,oy(sy)+2200),(ox(sx)-500,oy(sy)+1500)], dxfattribs={'layer':'CFA_VDI'})
            msp.add_text("BAIE 19\"", height=150, dxfattribs={'layer':'CFA_VDI','insert':(ox(sx)-400, oy(sy)+1600)})
        # RJ45
        for r in all_r:
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','cuisine','kitch','hall','restaurant','magasin','salle']):
                msp.add_lwpolyline([(ox(r['x'])-150,oy(r['y'])-400),(ox(r['x'])+150,oy(r['y'])-400),(ox(r['x'])+150,oy(r['y'])-150),(ox(r['x'])-150,oy(r['y'])-150),(ox(r['x'])-150,oy(r['y'])-400)], dxfattribs={'layer':'CFA_VDI'})
                msp.add_text("RJ45", height=100, dxfattribs={'layer':'CFA_VDI','insert':(ox(r['x'])-130, oy(r['y'])-350)})
        # Cameras
        cam_rooms = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','sas','porche','circulation'])]
        for r in cam_rooms:
            msp.add_circle((ox(r['x']),oy(r['y'])+600), 200, dxfattribs={'layer':'CFA_VIDEO'})
            msp.add_text("CAM", height=120, dxfattribs={'layer':'CFA_VIDEO','insert':(ox(r['x'])+250, oy(r['y'])+600)})
        # Access control
        access_rooms = [r for r in service if any(k in r['name'].lower() for k in ['hall','sas','porche'])]
        for r in access_rooms:
            msp.add_circle((ox(r['x'])+800,oy(r['y'])+300), 200, dxfattribs={'layer':'CFA_ACCES'})
            msp.add_text("BA", height=120, dxfattribs={'layer':'CFA_ACCES','insert':(ox(r['x'])+1050, oy(r['y'])+300)})
        # Interphones
        for r in [r for r in service if 'palier' in r['name'].lower()]:
            msp.add_lwpolyline([(ox(r['x'])-800,oy(r['y'])+500),(ox(r['x'])-400,oy(r['y'])+500),(ox(r['x'])-400,oy(r['y'])+1000),(ox(r['x'])-800,oy(r['y'])+1000),(ox(r['x'])-800,oy(r['y'])+500)], dxfattribs={'layer':'CFA_INTERPH'})
            msp.add_text("INTERPH", height=120, dxfattribs={'layer':'CFA_INTERPH','insert':(ox(r['x'])-780, oy(r['y'])+600)})

    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, cfa_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 6: ASCENSEURS
# ══════════════════════════════════════════════════════════════
def generate_ascenseurs():
    print("\n=== LOT 6: ASCENSEURS ===")
    pdf_path = f'{OUT}/LOT_ASCENSEURS_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 1  # 1 sheet per level

    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])

        page += 1
        border(c); cartouche(c, "ASCENSEURS — Implantation & Gaines", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        # Find elevator rooms
        asc_rooms = [r for r in service if 'asc' in r['name'].lower()]
        palier_rooms = [r for r in service if 'palier' in r['name'].lower()]

        for r in asc_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            # Elevator shaft (large outlined rectangle)
            c.setFillColor(colors.HexColor("#E3F2FD")); c.setStrokeColor(C['bleu_f']); c.setLineWidth(1)
            c.rect(rx-8, ry-8, 16, 16, fill=1, stroke=1)
            # Cabin outline
            c.setStrokeColor(C['bleu']); c.setLineWidth(0.5); c.setDash(2,1)
            c.rect(rx-5, ry-5, 10, 10, fill=0, stroke=1); c.setDash()
            # Cross for shaft
            c.setStrokeColor(C['bleu_f']); c.setLineWidth(0.3)
            c.line(rx-8, ry-8, rx+8, ry+8)
            c.line(rx-8, ry+8, rx+8, ry-8)
            # Label
            c.setFillColor(C['bleu_f']); c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(rx, ry-12, "ASC")
            c.setFont("Helvetica", 2.5)
            c.drawCentredString(rx, ry-15, "1300×950 / 630kg")
            c.drawCentredString(rx, ry-18, "1.0 m/s")

        # Palier d'ascenseur annotation
        for r in palier_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            c.setStrokeColor(C['bleu']); c.setLineWidth(0.4); c.setDash(3,2)
            c.rect(rx-10, ry-6, 20, 12, fill=0, stroke=1); c.setDash()
            c.setFillColor(C['bleu']); c.setFont("Helvetica", 2.5)
            c.drawCentredString(rx, ry+8, "Palier asc.")

        # Machinerie annotation for etage 8 and terrasse
        if lkey in ('ETAGE_8', 'TERRASSE'):
            for r in living + service:
                if 'machinerie' in r['name'].lower():
                    rx, ry = tx(r['x']), ty(r['y'])
                    c.setFillColor(colors.HexColor("#FFECB3")); c.setStrokeColor(C['orange']); c.setLineWidth(0.8)
                    c.rect(rx-12, ry-8, 24, 16, fill=1, stroke=1)
                    c.setFillColor(C['noir']); c.setFont("Helvetica-Bold", 3.5)
                    c.drawCentredString(rx, ry+2, "MACHINERIE")
                    c.setFont("Helvetica", 2.5)
                    c.drawCentredString(rx, ry-3, "Treuil + Armoire cde")

        legend_box(c, [
            (C['bleu_f'], "Gaine ascenseur", 'rect'),
            (C['bleu'], "Cabine (1300×950mm)", 'dash'),
            (C['bleu'], "Palier ascenseur", 'dash'),
            (C['orange'], "Local machinerie", 'rect'),
        ])
        c.showPage()

    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

    # DXF
    dxf_path = f'{OUT}/LOT_ASCENSEURS_Sakho.dxf'
    layers = {
        'ASC_GAINE':      (5, 'Gaine ascenseur'),        # blue
        'ASC_CABINE':     (5, 'Cabine ascenseur'),
        'ASC_PALIER':     (4, 'Palier ascenseur'),        # cyan
        'ASC_MACHINERIE': (30, 'Local machinerie'),       # orange
    }
    def asc_mep(msp, geom, lvl, ox, oy):
        _, living, service = classify(geom['rooms'])
        asc_rooms = [r for r in service if 'asc' in r['name'].lower()]
        for r in asc_rooms:
            # Shaft
            msp.add_lwpolyline([(ox(r['x'])-650,oy(r['y'])-475),(ox(r['x'])+650,oy(r['y'])-475),(ox(r['x'])+650,oy(r['y'])+475),(ox(r['x'])-650,oy(r['y'])+475),(ox(r['x'])-650,oy(r['y'])-475)], dxfattribs={'layer':'ASC_GAINE'})
            # Cabin
            msp.add_lwpolyline([(ox(r['x'])-450,oy(r['y'])-350),(ox(r['x'])+450,oy(r['y'])-350),(ox(r['x'])+450,oy(r['y'])+350),(ox(r['x'])-450,oy(r['y'])+350),(ox(r['x'])-450,oy(r['y'])-350)], dxfattribs={'layer':'ASC_CABINE'})
            # Cross
            msp.add_line((ox(r['x'])-650,oy(r['y'])-475),(ox(r['x'])+650,oy(r['y'])+475), dxfattribs={'layer':'ASC_GAINE'})
            msp.add_line((ox(r['x'])-650,oy(r['y'])+475),(ox(r['x'])+650,oy(r['y'])-475), dxfattribs={'layer':'ASC_GAINE'})
            msp.add_text("ASC 630kg", height=200, dxfattribs={'layer':'ASC_GAINE','insert':(ox(r['x'])-600, oy(r['y'])-700)})
        for r in [r for r in service if 'palier' in r['name'].lower()]:
            msp.add_lwpolyline([(ox(r['x'])-1000,oy(r['y'])-600),(ox(r['x'])+1000,oy(r['y'])-600),(ox(r['x'])+1000,oy(r['y'])+600),(ox(r['x'])-1000,oy(r['y'])+600),(ox(r['x'])-1000,oy(r['y'])-600)], dxfattribs={'layer':'ASC_PALIER'})
        for r in living+service:
            if 'machinerie' in r['name'].lower():
                msp.add_lwpolyline([(ox(r['x'])-1200,oy(r['y'])-800),(ox(r['x'])+1200,oy(r['y'])-800),(ox(r['x'])+1200,oy(r['y'])+800),(ox(r['x'])-1200,oy(r['y'])+800),(ox(r['x'])-1200,oy(r['y'])-800)], dxfattribs={'layer':'ASC_MACHINERIE'})
                msp.add_text("MACHINERIE", height=250, dxfattribs={'layer':'ASC_MACHINERIE','insert':(ox(r['x'])-1000, oy(r['y']))})

    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, asc_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# LOT 7: AUTOMATISATION / GTB (GTC/BMS)
# ══════════════════════════════════════════════════════════════
def generate_automatisation():
    print("\n=== LOT 7: AUTOMATISATION / GTB ===")
    pdf_path = f'{OUT}/LOT_AUTOMATISATION_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total_pages = len(LEVELS) * 2

    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        all_r = wet + living + service
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        halls = [r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt','sas'])]

        # Colors for automation
        COL_KNX = colors.HexColor("#1565C0")
        COL_BUS = colors.HexColor("#42A5F5")
        COL_SENSOR = colors.HexColor("#FF7043")
        COL_ACTUATOR = colors.HexColor("#66BB6A")
        COL_PANEL = colors.HexColor("#37474F")

        # ── Sheet A: Bus KNX / BACnet + Contrôleurs ──
        page += 1
        border(c); cartouche(c, "AUTOMATISATION — Bus KNX & Contrôleurs", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        # Automate / Contrôleur principal near shaft
        if shafts:
            px, py = tx(shafts[0][0]), ty(shafts[0][1])
            c.setFillColor(COL_PANEL); c.setStrokeColor(C['noir']); c.setLineWidth(0.7)
            c.rect(px-7, py+18, 14, 8, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 3.5)
            c.drawCentredString(px, py+21, "CTRL")
            c.setFillColor(COL_PANEL); c.setFont("Helvetica", 2.5)
            c.drawCentredString(px, py+27.5, "Automate KNX")

        # Bus KNX through corridors
        if len(halls) >= 2:
            sh = sorted(halls, key=lambda r: r['y'])
            c.setStrokeColor(COL_KNX); c.setLineWidth(1.8)
            for i in range(len(sh)-1):
                c.line(tx(sh[i]['x']), ty(sh[i]['y'])+3, tx(sh[i+1]['x']), ty(sh[i+1]['y'])+3)
            # Connect to controller
            if shafts:
                ppx, ppy = tx(shafts[0][0]), ty(shafts[0][1])
                c.line(ppx, ppy+18, tx(sh[0]['x']), ty(sh[0]['y'])+3)

        # Sub-controllers at each palier
        for r in [r for r in service if 'palier' in r['name'].lower()]:
            rx, ry = tx(r['x']), ty(r['y'])
            c.setFillColor(COL_BUS); c.setStrokeColor(C['noir']); c.setLineWidth(0.4)
            c.rect(rx+8, ry+8, 6, 5, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2.5)
            c.drawCentredString(rx+11, ry+9.5, "SC")

        # Branch lines from bus to each apartment area
        for r in living:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['salon','sejour','sam']):
                # Sub-panel per apartment
                c.setFillColor(colors.HexColor("#78909C")); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
                c.rect(rx+8, ry+8, 5, 4, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
                c.drawCentredString(rx+10.5, ry+9.2, "AP")
                # Branch line
                if halls:
                    near_h = min(halls, key=lambda h: (h['x']-r['x'])**2+(h['y']-r['y'])**2)
                    c.setStrokeColor(COL_BUS); c.setLineWidth(0.4); c.setDash(2,1)
                    c.line(tx(near_h['x']), ty(near_h['y'])+3, rx+10.5, ry+10); c.setDash()

        legend_box(c, [
            (COL_PANEL, "Automate principal KNX", 'rect'),
            (COL_KNX, "Bus KNX/TP (câble vert)", 'line'),
            (COL_BUS, "Sous-contrôleur palier", 'rect'),
            (colors.HexColor("#78909C"), "Actuateur appt. (AP)", 'rect'),
            (COL_BUS, "Branche bus secondaire", 'dash'),
        ])
        c.showPage()

        # ── Sheet B: Capteurs & Actionneurs ──
        page += 1
        border(c); cartouche(c, "AUTOMATISATION — Capteurs & Actionneurs", page, total_pages, llabel)
        draw_arch(c, geom, tx, ty); draw_labels(c, geom['rooms'], tx, ty, 3)

        for r in all_r:
            rx, ry = tx(r['x']), ty(r['y'])
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue

            # Presence sensor (PIR) in halls/circulations
            if any(k in n for k in ['hall','palier','dgt','sas','circulation','porche']):
                c.setFillColor(COL_SENSOR); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
                c.circle(rx-6, ry+6, 2, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 2)
                c.drawCentredString(rx-6, ry+5, "P")

            # Temperature sensor in living rooms
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar','restaurant','salle']):
                c.setFillColor(COL_SENSOR); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
                path = c.beginPath()
                path.moveTo(rx-7, ry-3); path.lineTo(rx-4, ry-3); path.lineTo(rx-4, ry-7); path.lineTo(rx-7, ry-7)
                path.close(); c.drawPath(path, fill=1, stroke=0)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 1.8)
                c.drawCentredString(rx-5.5, ry-5.8, "T°")

            # Light actuator (dimmer) in living rooms
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam','bar']):
                c.setFillColor(COL_ACTUATOR); c.setStrokeColor(C['noir']); c.setLineWidth(0.3)
                c.rect(rx+6, ry-6, 4, 3.5, fill=1, stroke=1)
                c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 1.8)
                c.drawCentredString(rx+8, ry-5, "DIM")

            # Motorized shutter actuator near windows in chambres/salon
            if any(k in n for k in ['chambre','salon','sejour']):
                c.setFillColor(colors.HexColor("#A5D6A7")); c.setStrokeColor(C['noir']); c.setLineWidth(0.2)
                c.rect(rx-9, ry+8, 4, 3, fill=1, stroke=1)
                c.setFillColor(C['noir']); c.setFont("Helvetica-Bold", 1.5)
                c.drawCentredString(rx-7, ry+9, "VR")

        # Energy meter near TGBT/shaft
        if shafts:
            px, py = tx(shafts[0][0]), ty(shafts[0][1])
            c.setFillColor(colors.HexColor("#FFA726")); c.setStrokeColor(C['noir']); c.setLineWidth(0.5)
            c.rect(px-6, py-22, 12, 6, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(px, py-20, "CPT E")
            c.setFillColor(colors.HexColor("#FFA726")); c.setFont("Helvetica", 2.5)
            c.drawCentredString(px, py-14.5, "Compteur énergie")

            # Water meter
            c.setFillColor(colors.HexColor("#42A5F5")); c.setStrokeColor(C['noir']); c.setLineWidth(0.5)
            c.rect(px+14, py-22, 12, 6, fill=1, stroke=1)
            c.setFillColor(C['blanc']); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(px+20, py-20, "CPT W")
            c.setFillColor(colors.HexColor("#42A5F5")); c.setFont("Helvetica", 2.5)
            c.drawCentredString(px+20, py-14.5, "Compteur eau")

        legend_box(c, [
            (COL_SENSOR, "Détecteur présence (PIR)", 'circle'),
            (COL_SENSOR, "Sonde température", 'rect'),
            (COL_ACTUATOR, "Variateur éclairage (DIM)", 'rect'),
            (colors.HexColor("#A5D6A7"), "Moteur volet roulant (VR)", 'rect'),
            (colors.HexColor("#FFA726"), "Compteur énergie", 'rect'),
            (colors.HexColor("#42A5F5"), "Compteur eau", 'rect'),
        ])
        c.showPage()

    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

    # DXF
    dxf_path = f'{OUT}/LOT_AUTOMATISATION_Sakho.dxf'
    layers = {
        'GTB_BUS':        (5, 'Bus KNX/BACnet'),         # blue
        'GTB_CTRL':       (8, 'Contrôleurs'),             # grey
        'GTB_CAPTEURS':   (30, 'Capteurs'),               # orange
        'GTB_ACTIONNEURS':(3, 'Actionneurs'),              # green
        'GTB_COMPTEURS':  (2, 'Compteurs énergie/eau'),    # yellow
    }
    def gtb_mep(msp, geom, lvl, ox, oy):
        wet, living, service = classify(geom['rooms'])
        all_r = wet+living+service
        shafts = [(r['x'],r['y']) for r in service if 'asc' in r['name'].lower()]
        if not shafts:
            shafts = [(r['x'],r['y']) for r in service if 'palier' in r['name'].lower()]
        # Controller
        if shafts:
            sx, sy = shafts[0]
            msp.add_lwpolyline([(ox(sx)-700,oy(sy)+1800),(ox(sx)+700,oy(sy)+1800),(ox(sx)+700,oy(sy)+2600),(ox(sx)-700,oy(sy)+2600),(ox(sx)-700,oy(sy)+1800)], dxfattribs={'layer':'GTB_CTRL'})
            msp.add_text("CTRL KNX", height=200, dxfattribs={'layer':'GTB_CTRL','insert':(ox(sx)-600, oy(sy)+2000)})
        # Bus through halls
        halls = sorted([r for r in service if any(k in r['name'].lower() for k in ['hall','palier','dgt'])], key=lambda r: r['y'])
        for i in range(len(halls)-1):
            msp.add_line((ox(halls[i]['x']),oy(halls[i]['y'])+300),(ox(halls[i+1]['x']),oy(halls[i+1]['y'])+300), dxfattribs={'layer':'GTB_BUS'})
        # Sensors & actuators
        for r in all_r:
            n = r['name'].lower()
            if any(k in n for k in ['terrasse','balcon','jardin','piscine','vide','espace','bac']): continue
            if any(k in n for k in ['hall','palier','dgt','sas','circulation']):
                msp.add_circle((ox(r['x'])-600,oy(r['y'])+600), 200, dxfattribs={'layer':'GTB_CAPTEURS'})
                msp.add_text("PIR", height=100, dxfattribs={'layer':'GTB_CAPTEURS','insert':(ox(r['x'])-500, oy(r['y'])+600)})
            if any(k in n for k in ['chambre','salon','sejour','bureau','sam']):
                msp.add_lwpolyline([(ox(r['x'])-700,oy(r['y'])-300),(ox(r['x'])-300,oy(r['y'])-300),(ox(r['x'])-300,oy(r['y'])-700),(ox(r['x'])-700,oy(r['y'])-700),(ox(r['x'])-700,oy(r['y'])-300)], dxfattribs={'layer':'GTB_CAPTEURS'})
                msp.add_text("T", height=100, dxfattribs={'layer':'GTB_CAPTEURS','insert':(ox(r['x'])-600, oy(r['y'])-600)})
                msp.add_lwpolyline([(ox(r['x'])+600,oy(r['y'])-600),(ox(r['x'])+1000,oy(r['y'])-600),(ox(r['x'])+1000,oy(r['y'])-250),(ox(r['x'])+600,oy(r['y'])-250),(ox(r['x'])+600,oy(r['y'])-600)], dxfattribs={'layer':'GTB_ACTIONNEURS'})
                msp.add_text("DIM", height=100, dxfattribs={'layer':'GTB_ACTIONNEURS','insert':(ox(r['x'])+620, oy(r['y'])-550)})
        # Compteurs
        if shafts:
            sx, sy = shafts[0]
            msp.add_lwpolyline([(ox(sx)-600,oy(sy)-2200),(ox(sx)+600,oy(sy)-2200),(ox(sx)+600,oy(sy)-1600),(ox(sx)-600,oy(sy)-1600),(ox(sx)-600,oy(sy)-2200)], dxfattribs={'layer':'GTB_COMPTEURS'})
            msp.add_text("CPT ENERGIE", height=150, dxfattribs={'layer':'GTB_COMPTEURS','insert':(ox(sx)-550, oy(sy)-2100)})

    geom_list = [(load_geom(k), l) for k,l in LEVELS if len(load_geom(k)['walls'])>=5]
    write_dxf(geom_list, layers, dxf_path, gtb_mep)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
# GENERATE RVT NOTE
# ══════════════════════════════════════════════════════════════
def generate_rvt_note():
    """Generate a README explaining RVT availability"""
    note = """# Formats de livraison — Plans MEP Résidence SAKHO

## Fichiers disponibles

### LOT 1 — PLOMBERIE
- `LOT_PLOMBERIE_Sakho.pdf` — Eau Froide / Eau Chaude / Évacuations EU-EP (3 planches × 5 niveaux)
- `LOT_PLOMBERIE_Sakho.dxf` — Layers: PLB_EAU_FROIDE, PLB_EAU_CHAUDE, PLB_EVACUATION, PLB_APPAREILS

### LOT 2 — ÉLECTRICITÉ
- `LOT_ELECTRICITE_Sakho.pdf` — Éclairage / Prises / Distribution-TGBT (3 planches × 5 niveaux)
- `LOT_ELECTRICITE_Sakho.dxf` — Layers: ELEC_ECLAIRAGE, ELEC_PRISES, ELEC_DISTRIB

### LOT 3 — CVC
- `LOT_CVC_Sakho.pdf` — Climatisation splits / Ventilation VMC (2 planches × 5 niveaux)
- `LOT_CVC_Sakho.dxf` — Layers: CVC_SPLITS, CVC_FRIGORIFIQUE, CVC_VMC

### LOT 4 — SÉCURITÉ INCENDIE
- `LOT_SECURITE_INCENDIE_Sakho.pdf` — Détection-Alarme / Extinction-BAES (2 planches × 5 niveaux)
- `LOT_SECURITE_INCENDIE_Sakho.dxf` — Layers: SSI_DETECTION, SSI_ALARME, SSI_EXTINCTION, SSI_BAES

### LOT 5 — COURANTS FAIBLES
- `LOT_COURANTS_FAIBLES_Sakho.pdf` — Réseau VDI / Vidéosurveillance / Contrôle accès-Interphonie (3 planches × 5 niveaux)
- `LOT_COURANTS_FAIBLES_Sakho.dxf` — Layers: CFA_VDI, CFA_VIDEO, CFA_ACCES, CFA_INTERPH

### LOT 6 — ASCENSEURS
- `LOT_ASCENSEURS_Sakho.pdf` — Gaines, cabines, paliers, machinerie (1 planche × 5 niveaux)
- `LOT_ASCENSEURS_Sakho.dxf` — Layers: ASC_GAINE, ASC_CABINE, ASC_PALIER, ASC_MACHINERIE

### LOT 7 — AUTOMATISATION / GTB
- `LOT_AUTOMATISATION_Sakho.pdf` — Bus KNX-contrôleurs / Capteurs-actionneurs (2 planches × 5 niveaux)
- `LOT_AUTOMATISATION_Sakho.dxf` — Layers: GTB_BUS, GTB_CTRL, GTB_CAPTEURS, GTB_ACTIONNEURS, GTB_COMPTEURS

## Niveaux couverts (chaque lot)
1. Sous-Sol / Parking
2. Rez-de-Chaussée
3. Étages 1 à 7 (étage courant)
4. Étage 8
5. Terrasse

## Format RVT (Revit)
Les fichiers .rvt ne peuvent pas être générés programmatiquement sans licence Autodesk Revit.

**Import DXF dans Revit (recommandé) :**
1. Revit > Insérer > Importer CAO > sélectionner le .dxf
2. Positionner sur le niveau correspondant
3. Les layers sont pré-nommés pour faciliter le mapping des familles MEP Revit

**Layers normalisés :**
- `ARCH_*` : fond de plan architectural
- `PLB_*` : plomberie
- `ELEC_*` : électricité
- `CVC_*` : climatisation / ventilation
- `SSI_*` : sécurité incendie
- `CFA_*` : courants faibles
- `ASC_*` : ascenseurs
- `GTB_*` : automatisation / GTB
"""
    with open(f'{OUT}/LISEZ_MOI_formats.md', 'w') as f:
        f.write(note)
    print(f"\n  Note formats: {OUT}/LISEZ_MOI_formats.md")

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("GÉNÉRATION PLANS MEP — Résidence SAKHO")
    print("=" * 60)
    generate_plomberie()
    generate_electricite()
    generate_cvc()
    generate_securite_incendie()
    generate_courants_faibles()
    generate_ascenseurs()
    generate_automatisation()
    generate_rvt_note()
    print("\n" + "=" * 60)
    print("TERMINÉ")
    print("=" * 60)

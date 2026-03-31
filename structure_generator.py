"""
structure_generator.py — Plans Structure sur géométrie DXF réelle Sakho
Lots:
  1. Plan de coffrage (poteaux + poutres + dalles) — 1 planche/niveau
  2. Ferraillage poteaux — 1 planche/niveau
  3. Ferraillage poutres — 1 planche/niveau  
  4. Fondations — 1 planche (sous-sol)
  5. Voiles & contreventement — 1 planche/niveau
"""
import json, math, re, os
from datetime import datetime
from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
import ezdxf

OUT = '/Users/serignetall/tijan-repo/mep_output'
GEOM_DIR = '/Users/serignetall/tijan-repo'
A3L = landscape(A3)
W, H = A3L

LEVELS = [
    ('SOUS_SOL',   'Sous-Sol / Parking'),
    ('RDC',        'Rez-de-Chaussée'),
    ('ETAGES_1_7', 'Étages 1 à 7 (courant)'),
    ('ETAGE_8',    'Étage 8'),
    ('TERRASSE',   'Terrasse'),
]

# Colors
NOIR   = colors.HexColor("#111111")
GRIS   = colors.HexColor("#AAAAAA")
GRIS_M = colors.HexColor("#555555")
GRIS_L = colors.HexColor("#CCCCCC")
BLANC  = colors.white
VERT   = colors.HexColor("#43A956")
VERT_P = colors.HexColor("#E8F5E9")
ROUGE  = colors.HexColor("#CC3333")
BLEU_B = colors.HexColor("#D6E4F0")
BLEU   = colors.HexColor("#2196F3")
ORANGE = colors.HexColor("#FF9800")

# Structural grid from DXF analysis (Étages 1-7, block gauche)
# Vertical axes X positions (relative to region)
AXES_X = [637650, 642680, 644480, 645910, 648740, 651570, 657970, 659000, 661500]
# Horizontal axes Y positions (unique, sorted)
AXES_Y_RAW = [-489143, -488411, -485626, -477266, -474966, -472936, -469506, -467006,
              -465376, -461246, -456816, -455066, -452536, -449791, -448491, -447506,
              -444376, -442076, -439246, -438146, -434616]
AXES_Y = sorted(set(AXES_Y_RAW))

# ══════════════════════════════════════════════════════════════
# COMMON
# ══════════════════════════════════════════════════════════════
def load_geom(key):
    with open(f'{GEOM_DIR}/sakho_{key.lower()}_geom.json') as f:
        return json.load(f)

def get_bounds(geom):
    xs, ys = [], []
    for item in geom.get('walls',[]) + geom.get('windows',[]) + geom.get('doors',[]):
        if item['type'] == 'line':
            xs += [item['start'][0], item['end'][0]]; ys += [item['start'][1], item['end'][1]]
        elif item['type'] == 'polyline':
            for p in item['points']: xs.append(p[0]); ys.append(p[1])
    if not xs: return 0,0,1,1
    return min(xs),min(ys),max(xs),max(ys)

def make_transform(geom, margin=18*mm, bottom_reserve=38*mm):
    xn,yn,xx,yx = get_bounds(geom)
    dw,dh = xx-xn, yx-yn
    aw, ah = W-2*margin, H-margin-bottom_reserve-margin
    sc = min(aw/dw, ah/dh) if dw>0 and dh>0 else 1
    ow = margin + (aw - dw*sc)/2
    oh = bottom_reserve + (ah - dh*sc)/2
    return lambda x: ow+(x-xn)*sc, lambda y: oh+(y-yn)*sc, sc

def draw_arch(c, geom, tx, ty, opacity=0.35):
    c.setStrokeColor(GRIS_L); c.setLineWidth(0.4)
    for item in geom.get('walls',[]):
        _draw(c, item, tx, ty)
    c.setStrokeColor(colors.HexColor("#B3D4FC")); c.setLineWidth(0.2)
    for item in geom.get('windows',[]):
        _draw(c, item, tx, ty)

def _draw(c, item, tx, ty):
    if item['type']=='line':
        c.line(tx(item['start'][0]),ty(item['start'][1]),tx(item['end'][0]),ty(item['end'][1]))
    elif item['type']=='polyline':
        pts=item['points']
        for i in range(len(pts)-1):
            c.line(tx(pts[i][0]),ty(pts[i][1]),tx(pts[i+1][0]),ty(pts[i+1][1]))
        if item.get('closed') and len(pts)>2:
            c.line(tx(pts[-1][0]),ty(pts[-1][1]),tx(pts[0][0]),ty(pts[0][1]))

def draw_labels(c, rooms, tx, ty, sz=3):
    c.setFillColor(colors.HexColor("#AAAAAA")); c.setFont("Helvetica",sz)
    for r in rooms:
        if not re.match(r'^\d', r['name']):
            c.drawCentredString(tx(r['x']),ty(r['y']),r['name'])

def border(c):
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(8*mm,8*mm,W-16*mm,H-16*mm)

def cartouche(c, titre, page, total, niveau=""):
    cw,ch = 195*mm, 30*mm; cx,cy = W-cw-8*mm, 6*mm
    c.setFillColor(BLANC); c.setStrokeColor(NOIR); c.setLineWidth(0.7)
    c.rect(cx,cy,cw,ch,fill=1,stroke=1)
    c1,c2 = 38*mm, 120*mm
    c.setLineWidth(0.3)
    c.line(cx+c1,cy,cx+c1,cy+ch); c.line(cx+c2,cy,cx+c2,cy+ch)
    c.line(cx+c1,cy+ch/2,cx+cw,cy+ch/2)
    c.setFillColor(VERT); c.setFont("Helvetica-Bold",11)
    c.drawString(cx+3*mm,cy+ch-10*mm,"TIJAN AI")
    c.setFillColor(GRIS); c.setFont("Helvetica",5.5)
    c.drawString(cx+3*mm,cy+ch-15*mm,"Engineering Intelligence")
    c.drawString(cx+3*mm,cy+5*mm,f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold",8)
    c.drawString(cx+c1+3*mm,cy+ch-10*mm,"Résidence SAKHO — Dakar")
    c.setFillColor(VERT); c.setFont("Helvetica-Bold",7)
    c.drawString(cx+c1+3*mm,cy+ch/2+3*mm,titre)
    c.setFillColor(NOIR); c.setFont("Helvetica",6)
    c.drawString(cx+c1+3*mm,cy+ch/2-8*mm,niveau)
    c.setFillColor(GRIS); c.setFont("Helvetica",6)
    c.drawString(cx+c2+3*mm,cy+ch-10*mm,"Éch: 1/100")
    c.drawString(cx+c2+3*mm,cy+5*mm,f"Pl. {page}/{total}")

def legend_box(c, items, x=10*mm, y=None):
    if y is None: y=H-10*mm
    lw=60*mm; lh=(len(items)+1)*5.5*mm+3*mm
    c.setFillColor(colors.Color(1,1,1,0.92)); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
    c.rect(x,y-lh,lw,lh,fill=1,stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold",6)
    c.drawString(x+3*mm,y-5.5*mm,"LÉGENDE")
    c.line(x+2*mm,y-7*mm,x+lw-2*mm,y-7*mm)
    for i,(col,label,style) in enumerate(items):
        iy=y-(i+2)*5.5*mm
        if style=='line':
            c.setStrokeColor(col); c.setLineWidth(1.5); c.line(x+3*mm,iy+2,x+13*mm,iy+2)
        elif style=='dash':
            c.setStrokeColor(col); c.setLineWidth(1); c.setDash(3,2)
            c.line(x+3*mm,iy+2,x+13*mm,iy+2); c.setDash()
        elif style=='circle':
            c.setFillColor(col); c.circle(x+8*mm,iy+2,2.5,fill=1,stroke=0)
        elif style=='rect':
            c.setFillColor(col); c.rect(x+3*mm,iy,10*mm,4,fill=1,stroke=0)
        c.setFillColor(NOIR); c.setFont("Helvetica",5)
        c.drawString(x+15*mm,iy,label)

def classify(rooms):
    wet,living,service=[],[],[]
    for r in rooms:
        n=r['name'].lower().strip()
        if re.match(r'^\d',n): continue
        if any(k in n for k in ['sdb','wc','toil','douche','cuisine','kitch','buanderie']):
            wet.append(r)
        elif any(k in n for k in ['hall','palier','asc','dgt','sas','terrasse','balcon','jardin','piscine','vide','porche','circulation']):
            service.append(r)
        else:
            living.append(r)
    return wet,living,service

def draw_axis_label(c, x, y, label):
    r=4.5*mm
    c.setStrokeColor(NOIR); c.setLineWidth(0.4); c.setFillColor(BLANC)
    c.circle(x,y,r,fill=1,stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold",7)
    tw=c.stringWidth(str(label),"Helvetica-Bold",7)
    c.drawString(x-tw/2,y-2.5,str(label))

# ══════════════════════════════════════════════════════════════
# STRUCTURAL GRID DRAWING
# ══════════════════════════════════════════════════════════════
def draw_structural_grid(c, geom, tx, ty):
    """Draw structural axes from DXF data"""
    # Get bounds to know which axes are in range
    xn,yn,xx,yx = get_bounds(geom)
    
    # Draw axes from DXF geom structure data
    struct = geom.get('structure',[])
    
    # Also draw axes extracted from the geometry
    # For the typical floor, we use known axis positions
    # Filter axes that fall within this geometry's bounds
    relevant_x = [x for x in AXES_X if xn-5000 < x < xx+5000]
    relevant_y = [y for y in AXES_Y if yn-5000 < y < yx+5000]
    
    if relevant_x and relevant_y:
        min_y_page = ty(min(relevant_y)) - 12*mm
        max_y_page = ty(max(relevant_y)) + 12*mm
        min_x_page = tx(min(relevant_x)) - 12*mm
        max_x_page = tx(max(relevant_x)) + 12*mm
        
        # Vertical axes
        c.setStrokeColor(GRIS); c.setLineWidth(0.25); c.setDash(6,3)
        for i, ax in enumerate(relevant_x):
            px = tx(ax)
            c.line(px, min_y_page, px, max_y_page)
            # Label at bottom
            label = chr(65+i) if i < 26 else str(i+1)
            draw_axis_label(c, px, min_y_page - 6*mm, label)
        
        # Horizontal axes
        for i, ay in enumerate(relevant_y):
            py = ty(ay)
            c.line(min_x_page, py, max_x_page, py)
            label = str(i+1)
            draw_axis_label(c, min_x_page - 6*mm, py, label)
        c.setDash()

def draw_poteaux(c, geom, tx, ty, poteau_size_mm=300):
    """Draw columns at axis intersections"""
    xn,yn,xx,yx = get_bounds(geom)
    relevant_x = [x for x in AXES_X if xn-2000 < x < xx+2000]
    relevant_y = [y for y in AXES_Y if yn-2000 < y < yx+2000]
    
    # Also draw real poteaux from geometry
    for item in geom.get('structure',[]):
        if item['type']=='polyline':
            pts=item['points']
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            cx_dxf=(min(xs)+max(xs))/2; cy_dxf=(min(ys)+max(ys))/2
            w_dxf=max(xs)-min(xs); h_dxf=max(ys)-min(ys)
            px,py=tx(cx_dxf),ty(cy_dxf)
            # Draw filled rectangle
            pw=(w_dxf if w_dxf>50 else 300)*0.01*mm
            ph=(h_dxf if h_dxf>50 else 300)*0.01*mm
            pw=max(pw,1.5); ph=max(ph,1.5)
            c.setFillColor(NOIR); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
            c.rect(px-pw/2,py-ph/2,pw,ph,fill=1,stroke=1)
    
    # Draw poteaux at grid intersections where both axes exist
    if relevant_x and relevant_y:
        half = poteau_size_mm * 0.003  # scaled
        for ax in relevant_x:
            for ay in relevant_y:
                px, py = tx(ax), ty(ay)
                # Check if this intersection is roughly inside the building footprint
                if xn+1000 < ax < xx-1000 and yn+1000 < ay < yx-1000:
                    c.setFillColor(NOIR); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
                    c.rect(px-half, py-half, 2*half, 2*half, fill=1, stroke=1)

def draw_poutres(c, geom, tx, ty):
    """Draw beams between columns"""
    xn,yn,xx,yx = get_bounds(geom)
    relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
    relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
    
    if not relevant_x or not relevant_y: return
    
    # Poutres principales (along X axes = horizontal beams)
    c.setStrokeColor(NOIR); c.setLineWidth(1.2)
    for ay in relevant_y:
        for i in range(len(relevant_x)-1):
            x1, x2 = relevant_x[i], relevant_x[i+1]
            py = ty(ay)
            c.line(tx(x1), py, tx(x2), py)
    
    # Poutres secondaires (along Y axes = vertical beams)
    c.setStrokeColor(GRIS_M); c.setLineWidth(0.8)
    for ax in relevant_x:
        for i in range(len(relevant_y)-1):
            y1, y2 = relevant_y[i], relevant_y[i+1]
            px = tx(ax)
            c.line(px, ty(y1), px, ty(y2))

def draw_dalles(c, geom, tx, ty):
    """Draw slab panels with hatching"""
    xn,yn,xx,yx = get_bounds(geom)
    relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
    relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
    
    if len(relevant_x) < 2 or len(relevant_y) < 2: return
    
    c.setStrokeColor(GRIS_L); c.setLineWidth(0.15)
    for i in range(len(relevant_x)-1):
        for j in range(len(relevant_y)-1):
            x1,x2 = tx(relevant_x[i]), tx(relevant_x[i+1])
            y1,y2 = ty(relevant_y[j]), ty(relevant_y[j+1])
            # Light diagonal hatching
            step = 4
            cx_mid = (x1+x2)/2; cy_mid = (y1+y2)/2
            for k in range(int((x2-x1)/step)+int((y2-y1)/step)+2):
                sx = x1 + k*step
                sy = y1
                ex = x1
                ey = y1 + k*step
                # Clip to panel
                if sx > x2: ey += sx-x2; sx = x2
                if ey > y2: sx += ey-y2; ey = y2
                if sx >= x1 and sx <= x2 and ex >= x1 and ex <= x2 and sy >= y1 and sy <= y2 and ey >= y1 and ey <= y2:
                    c.line(sx,sy,ex,ey)
            
            # Panel label
            c.setFillColor(colors.HexColor("#CCCCCC")); c.setFont("Helvetica",2.5)
            c.drawCentredString(cx_mid, cy_mid+2, f"D ep.20")
            # Portée
            span_x = (relevant_x[i+1]-relevant_x[i])/1000
            span_y = (relevant_y[j+1]-relevant_y[j])/1000
            if span_x > 0.5 and span_y > 0.5:
                c.drawCentredString(cx_mid, cy_mid-2, f"{span_x:.1f}×{span_y:.1f}m")

# ══════════════════════════════════════════════════════════════
# LOT STRUCTURE — COFFRAGE
# ══════════════════════════════════════════════════════════════
def generate_coffrage():
    print("\n=== STRUCTURE — COFFRAGE ===")
    pdf_path = f'{OUT}/LOT_COFFRAGE_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total = len(LEVELS)
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        page += 1
        border(c); cartouche(c, "PLAN DE COFFRAGE", page, total, llabel)
        
        # Architecture light background
        draw_arch(c, geom, tx, ty)
        draw_labels(c, geom['rooms'], tx, ty, 2.5)
        
        # Structural grid
        draw_structural_grid(c, geom, tx, ty)
        
        # Dalles (hatched panels)
        draw_dalles(c, geom, tx, ty)
        
        # Poutres
        draw_poutres(c, geom, tx, ty)
        
        # Poteaux (filled squares on top)
        draw_poteaux(c, geom, tx, ty)
        
        # Annotations
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
        xn,yn,xx,yx = get_bounds(geom)
        relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
        relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
        
        # Beam labels on a few main spans
        if len(relevant_x) >= 2 and len(relevant_y) >= 1:
            for i in range(min(3, len(relevant_x)-1)):
                span = (relevant_x[i+1] - relevant_x[i]) / 1000
                mid_x = tx((relevant_x[i] + relevant_x[i+1]) / 2)
                ref_y = ty(relevant_y[0]) + 5
                c.setFillColor(NOIR); c.setFont("Helvetica", 3)
                c.drawCentredString(mid_x, ref_y, f"PP 25×50 L={span:.1f}m")
        
        # Notes
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawString(12*mm, 42*mm, f"Béton C30/37 — Acier HA500 — Enrobage 30mm")
        c.drawString(12*mm, 38*mm, f"Dalle ep. 20cm — Poteaux 30×30cm — Poutres 25×50cm")
        
        legend_box(c, [
            (NOIR, "Poteau BA 30×30cm", 'rect'),
            (NOIR, "Poutre principale 25×50", 'line'),
            (GRIS_M, "Poutre secondaire 20×40", 'line'),
            (GRIS_L, "Dalle BA ep. 20cm (hachure)", 'rect'),
            (GRIS, "Axe trame structurelle", 'dash'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# LOT STRUCTURE — FERRAILLAGE POTEAUX
# ══════════════════════════════════════════════════════════════
def generate_ferraillage_poteaux():
    print("\n=== STRUCTURE — FERRAILLAGE POTEAUX ===")
    pdf_path = f'{OUT}/LOT_FERRAILLAGE_POTEAUX_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total = len(LEVELS)
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        page += 1
        border(c); cartouche(c, "FERRAILLAGE POTEAUX", page, total, llabel)
        draw_arch(c, geom, tx, ty)
        draw_structural_grid(c, geom, tx, ty)
        
        xn,yn,xx,yx = get_bounds(geom)
        relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
        relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
        
        # Draw poteaux with rebar indication
        if relevant_x and relevant_y:
            for ax in relevant_x:
                for ay in relevant_y:
                    if xn+1000 < ax < xx-1000 and yn+1000 < ay < yx-1000:
                        px, py = tx(ax), ty(ay)
                        half = 3.5
                        # Outer rectangle (concrete section)
                        c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
                        c.rect(px-half, py-half, 2*half, 2*half, fill=1, stroke=1)
                        # Inner rectangle (enrobage)
                        enr = 0.8
                        c.setStrokeColor(GRIS_M); c.setLineWidth(0.2); c.setDash(1,1)
                        c.rect(px-half+enr, py-half+enr, 2*(half-enr), 2*(half-enr), fill=0, stroke=1)
                        c.setDash()
                        # Rebar dots (4HA16 corners + 4HA16 mid)
                        c.setFillColor(NOIR)
                        inner = half - enr - 0.3
                        for dx, dy in [(-inner,-inner),(inner,-inner),(inner,inner),(-inner,inner)]:
                            c.circle(px+dx, py+dy, 0.6, fill=1, stroke=0)
                        # Label
                        c.setFillColor(ROUGE); c.setFont("Helvetica", 2)
                        c.drawCentredString(px, py-half-2.5, "8HA16")
                        c.setFillColor(GRIS_M); c.setFont("Helvetica", 1.8)
                        c.drawCentredString(px, py-half-4.5, "Cad.HA8/15")
        
        # Detail box — section type
        dx, dy = W - 75*mm, H - 15*mm
        bw, bh = 60*mm, 60*mm
        c.setFillColor(BLANC); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.rect(dx, dy-bh, bw, bh, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(dx+bw/2, dy-8, "SECTION POTEAU TYPE")
        
        # Draw enlarged section
        sec_cx, sec_cy = dx+bw/2, dy-bh/2-2*mm
        sec_s = 18*mm
        c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
        c.rect(sec_cx-sec_s/2, sec_cy-sec_s/2, sec_s, sec_s, fill=1, stroke=1)
        enr_s = 2*mm
        c.setStrokeColor(GRIS_M); c.setLineWidth(0.3); c.setDash(2,1)
        c.rect(sec_cx-sec_s/2+enr_s, sec_cy-sec_s/2+enr_s, sec_s-2*enr_s, sec_s-2*enr_s, fill=0, stroke=1)
        c.setDash()
        # Rebars
        c.setFillColor(NOIR)
        rb_r = 1.2*mm
        inner_s = sec_s/2 - enr_s - rb_r
        for ddx, ddy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            c.circle(sec_cx+ddx*inner_s, sec_cy+ddy*inner_s, rb_r, fill=1, stroke=0)
        for ddx, ddy in [(0,-1),(0,1),(-1,0),(1,0)]:
            c.circle(sec_cx+ddx*inner_s, sec_cy+ddy*inner_s, rb_r, fill=1, stroke=0)
        # Stirrups
        c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
        c.rect(sec_cx-inner_s-rb_r, sec_cy-inner_s-rb_r, 2*(inner_s+rb_r), 2*(inner_s+rb_r), fill=0, stroke=1)
        # Dimensions
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
        c.drawCentredString(sec_cx, sec_cy-sec_s/2-4*mm, "300 mm")
        c.saveState()
        c.translate(sec_cx-sec_s/2-4*mm, sec_cy); c.rotate(90)
        c.drawCentredString(0,0,"300 mm"); c.restoreState()
        # Legend
        c.setFillColor(NOIR); c.setFont("Helvetica", 4.5)
        c.drawString(dx+3*mm, dy-bh+12*mm, "8HA16 (As=16.1cm²)")
        c.drawString(dx+3*mm, dy-bh+7*mm, "Cadres HA8 esp.15cm")
        c.drawString(dx+3*mm, dy-bh+2*mm, "C30/37 — Enr. 30mm")
        
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawString(12*mm, 42*mm, f"Béton C30/37 — fck=30MPa — Acier HA500 — fyk=500MPa")
        c.drawString(12*mm, 38*mm, f"Enrobage 30mm (XC2) — Cadres HA8 espacement 15cm en zone courante, 10cm en zone critique")
        
        legend_box(c, [
            (BLEU_B, "Section poteau BA", 'rect'),
            (NOIR, "Armatures longitudinales", 'circle'),
            (ROUGE, "Cadres / Étriers", 'line'),
            (GRIS, "Axe trame structurelle", 'dash'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# LOT STRUCTURE — FERRAILLAGE POUTRES
# ══════════════════════════════════════════════════════════════
def generate_ferraillage_poutres():
    print("\n=== STRUCTURE — FERRAILLAGE POUTRES ===")
    pdf_path = f'{OUT}/LOT_FERRAILLAGE_POUTRES_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total = len(LEVELS)
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        page += 1
        border(c); cartouche(c, "FERRAILLAGE POUTRES", page, total, llabel)
        draw_arch(c, geom, tx, ty)
        draw_structural_grid(c, geom, tx, ty)
        
        xn,yn,xx,yx = get_bounds(geom)
        relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
        relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
        
        # Draw poutres with rebar annotation
        if relevant_x and relevant_y:
            # Main beams (horizontal)
            c.setStrokeColor(NOIR); c.setLineWidth(1.5)
            for ay in relevant_y:
                for i in range(len(relevant_x)-1):
                    x1, x2 = relevant_x[i], relevant_x[i+1]
                    py = ty(ay)
                    px1, px2 = tx(x1), tx(x2)
                    c.line(px1, py, px2, py)
                    # Beam label at midpoint
                    mid = (px1+px2)/2
                    span = (x2-x1)/1000
                    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 2.5)
                    c.drawCentredString(mid, py+3, f"PP 25×50")
                    c.setFillColor(GRIS_M); c.setFont("Helvetica", 2)
                    c.drawCentredString(mid, py-3.5, f"3HA16 inf / 2HA14 sup")
            
            # Secondary beams (vertical)
            c.setStrokeColor(GRIS_M); c.setLineWidth(0.8)
            for ax in relevant_x:
                for i in range(len(relevant_y)-1):
                    y1, y2 = relevant_y[i], relevant_y[i+1]
                    px = tx(ax)
                    py1, py2 = ty(y1), ty(y2)
                    c.line(px, py1, px, py2)
        
        # Poteaux
        draw_poteaux(c, geom, tx, ty)
        
        # Detail box — poutre type elevation
        dx, dy = W - 80*mm, H - 15*mm
        bw, bh = 72*mm, 55*mm
        c.setFillColor(BLANC); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.rect(dx, dy-bh, bw, bh, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(dx+bw/2, dy-8, "POUTRE PRINCIPALE TYPE")
        
        # Beam elevation
        bx = dx+6*mm; by = dy-bh+18*mm
        beam_w = 58*mm; beam_h = 14*mm
        c.setFillColor(colors.HexColor("#F5F5F5")); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
        c.rect(bx, by, beam_w, beam_h, fill=1, stroke=1)
        # Bottom bars (red)
        c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
        for j in range(3):
            yb = by + 2*mm + j*1.5*mm
            c.line(bx+2, yb, bx+beam_w-2, yb)
        # Top bars
        for j in range(2):
            yt = by + beam_h - 2*mm - j*1.5*mm
            c.line(bx+2, yt, bx+beam_w-2, yt)
        # Stirrups
        c.setStrokeColor(GRIS_M); c.setLineWidth(0.25)
        nb_etr = 12
        for i in range(nb_etr+1):
            ex = bx + 2 + i * (beam_w-4) / nb_etr
            c.line(ex, by+2*mm, ex, by+beam_h-2*mm)
        # Dimensions
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawCentredString(bx+beam_w/2, by-4*mm, "Portée 5.0m")
        c.setFont("Helvetica", 3.5)
        c.drawString(bx+beam_w+2*mm, by+beam_h/2, "500")
        c.drawString(bx+beam_w+2*mm, by+2*mm, "250")
        # Rebar labels
        c.setFillColor(ROUGE); c.setFont("Helvetica", 3.5)
        c.drawString(dx+3*mm, dy-bh+10*mm, "Inf: 3HA16 (6.03cm²)")
        c.drawString(dx+3*mm, dy-bh+6*mm, "Sup: 2HA14 (3.08cm²)")
        c.drawString(dx+3*mm, dy-bh+2*mm, "Étr: HA8 esp.20cm (15 z.crit.)")
        
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawString(12*mm, 42*mm, f"PP = Poutre Principale 25×50cm — PS = Poutre Secondaire 20×40cm")
        c.drawString(12*mm, 38*mm, f"C30/37 — HA500 — Enrobage 30mm — Étriers HA8")
        
        legend_box(c, [
            (NOIR, "Poutre principale (PP)", 'line'),
            (GRIS_M, "Poutre secondaire (PS)", 'line'),
            (ROUGE, "Armatures longitudinales", 'line'),
            (NOIR, "Poteau BA", 'rect'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# LOT STRUCTURE — FONDATIONS
# ══════════════════════════════════════════════════════════════
def generate_fondations():
    print("\n=== STRUCTURE — FONDATIONS ===")
    pdf_path = f'{OUT}/LOT_FONDATIONS_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    
    # Only sous-sol level for plan + a coupe page
    geom = load_geom('SOUS_SOL')
    tx, ty, sc = make_transform(geom)
    
    # Page 1: Plan de fondations
    border(c); cartouche(c, "PLAN DE FONDATIONS — Semelles isolées", 1, 2, "Sous-Sol / Parking")
    draw_arch(c, geom, tx, ty)
    draw_labels(c, geom['rooms'], tx, ty, 2.5)
    draw_structural_grid(c, geom, tx, ty)
    
    xn,yn,xx,yx = get_bounds(geom)
    relevant_x = [x for x in AXES_X if xn-5000 < x < xx+5000]
    relevant_y = [y for y in AXES_Y if yn-5000 < y < yx+5000]
    
    # Draw semelles at each column position
    if relevant_x and relevant_y:
        for ax in relevant_x:
            for ay in relevant_y:
                if xn-2000 < ax < xx+2000 and yn-2000 < ay < yx+2000:
                    px, py = tx(ax), ty(ay)
                    sem_half = 5  # larger than poteau
                    # Semelle (dashed outline)
                    c.setStrokeColor(ROUGE); c.setLineWidth(0.5); c.setDash(3,1.5)
                    c.rect(px-sem_half, py-sem_half, 2*sem_half, 2*sem_half, fill=0, stroke=1)
                    c.setDash()
                    # Poteau inside
                    pot_half = 2
                    c.setFillColor(NOIR); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
                    c.rect(px-pot_half, py-pot_half, 2*pot_half, 2*pot_half, fill=1, stroke=1)
    
    # Longrines between semelles (connecting beams)
    if relevant_x and relevant_y:
        c.setStrokeColor(colors.HexColor("#8D6E63")); c.setLineWidth(0.8); c.setDash(5,2)
        for ay in relevant_y:
            for i in range(len(relevant_x)-1):
                if xn-2000 < relevant_x[i] < xx+2000 and xn-2000 < relevant_x[i+1] < xx+2000 and yn-2000 < ay < yx+2000:
                    c.line(tx(relevant_x[i]), ty(ay), tx(relevant_x[i+1]), ty(ay))
        for ax in relevant_x:
            for i in range(len(relevant_y)-1):
                if xn-2000 < ax < xx+2000 and yn-2000 < relevant_y[i] < yx+2000 and yn-2000 < relevant_y[i+1] < yx+2000:
                    c.line(tx(ax), ty(relevant_y[i]), tx(ax), ty(relevant_y[i+1]))
        c.setDash()
    
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
    c.drawString(12*mm, 42*mm, "Semelles isolées 1.50×1.50×0.40m — Longrines 25×40cm")
    c.drawString(12*mm, 38*mm, "C30/37 — HA500 — Sol: σ=0.15 MPa — Assise -1.50m/TN")
    
    legend_box(c, [
        (NOIR, "Poteau BA 30×30cm", 'rect'),
        (ROUGE, "Semelle isolée 1.5×1.5m", 'dash'),
        (colors.HexColor("#8D6E63"), "Longrine 25×40cm", 'dash'),
        (GRIS, "Axe trame structurelle", 'dash'),
    ])
    c.showPage()
    
    # Page 2: Coupe type fondation
    border(c); cartouche(c, "COUPE TYPE FONDATION", 2, 2, "Détail")
    
    # Draw a foundation cross-section
    cx, cy = W/2, H/2 + 10*mm
    scale_f = 2.5  # mm per cm
    
    # Ground level
    c.setStrokeColor(colors.HexColor("#8D6E63")); c.setLineWidth(1)
    c.line(cx-120*mm, cy+30*mm, cx+120*mm, cy+30*mm)
    c.setFillColor(colors.HexColor("#8D6E63")); c.setFont("Helvetica-Bold", 7)
    c.drawString(cx+125*mm, cy+29*mm, "TN 0.00")
    
    # Excavation
    c.setFillColor(colors.HexColor("#FFF3E0")); c.setStrokeColor(colors.HexColor("#8D6E63")); c.setLineWidth(0.5)
    exc_w = 80*mm; exc_h = 45*mm
    c.rect(cx-exc_w/2, cy+30*mm-exc_h, exc_w, exc_h, fill=1, stroke=1)
    
    # Béton de propreté
    bp_h = 3*mm
    c.setFillColor(GRIS_L); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(cx-exc_w/2+5*mm, cy+30*mm-exc_h, exc_w-10*mm, bp_h, fill=1, stroke=1)
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
    c.drawCentredString(cx, cy+30*mm-exc_h+bp_h+3, "Béton propreté ep.5cm")
    
    # Semelle
    sem_w = 60*mm; sem_h = 16*mm
    sem_y = cy+30*mm-exc_h+bp_h
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    c.rect(cx-sem_w/2, sem_y, sem_w, sem_h, fill=1, stroke=1)
    # Rebars in semelle
    c.setStrokeColor(ROUGE); c.setLineWidth(0.6)
    for j in range(5):
        yb = sem_y + 3*mm + j*2.5*mm
        c.line(cx-sem_w/2+3*mm, yb, cx+sem_w/2-3*mm, yb)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(cx, sem_y+sem_h/2, "SEMELLE 150×150×40")
    
    # Poteau on semelle
    pot_w = 12*mm; pot_h = 90*mm
    pot_y = sem_y + sem_h
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    c.rect(cx-pot_w/2, pot_y, pot_w, pot_h, fill=1, stroke=1)
    # Rebars in poteau
    c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
    c.line(cx-pot_w/2+2*mm, pot_y, cx-pot_w/2+2*mm, pot_y+pot_h)
    c.line(cx+pot_w/2-2*mm, pot_y, cx+pot_w/2-2*mm, pot_y+pot_h)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
    c.drawCentredString(cx, pot_y+pot_h/2, "P 30×30")
    
    # Dalle on top
    dalle_w = 100*mm; dalle_h = 8*mm
    c.setFillColor(colors.HexColor("#E0E0E0")); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(cx-dalle_w/2, pot_y+pot_h, dalle_w, dalle_h, fill=1, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawCentredString(cx, pot_y+pot_h+dalle_h+4, "Dalle RDC ep.20cm")
    
    # Dimensions
    c.setStrokeColor(GRIS_M); c.setLineWidth(0.3)
    # Semelle width
    dim_y = sem_y - 5*mm
    c.line(cx-sem_w/2, dim_y, cx+sem_w/2, dim_y)
    c.line(cx-sem_w/2, dim_y-2, cx-sem_w/2, dim_y+2)
    c.line(cx+sem_w/2, dim_y-2, cx+sem_w/2, dim_y+2)
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
    c.drawCentredString(cx, dim_y-5, "1500 mm")
    
    # Height annotations
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawString(cx+sem_w/2+5*mm, sem_y+sem_h/2, "400mm")
    c.drawString(cx+pot_w/2+5*mm, pot_y+pot_h/2, "h.étage 3.00m")
    c.drawString(cx+125*mm, cy+30*mm-exc_h-3, "-1.50m")
    
    # Notes
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
    c.drawString(12*mm, 55*mm, "Sol : σ adm = 0.15 MPa (Dakar — latérite)")
    c.drawString(12*mm, 50*mm, "Béton fondation : C30/37 — Acier : HA500")
    c.drawString(12*mm, 45*mm, "Enrobage fondation : 50mm (XC2 + contact sol)")
    c.drawString(12*mm, 40*mm, "Semelle armée : nappe inf. HA12 esp.15cm × 2 sens")
    
    c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} (2 pages)")

# ══════════════════════════════════════════════════════════════
# LOT STRUCTURE — VOILES / CONTREVENTEMENT
# ══════════════════════════════════════════════════════════════
def generate_voiles():
    print("\n=== STRUCTURE — VOILES & CONTREVENTEMENT ===")
    pdf_path = f'{OUT}/LOT_VOILES_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0
    total = len(LEVELS)
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        wet, living, service = classify(geom['rooms'])
        page += 1
        border(c); cartouche(c, "VOILES BA & CONTREVENTEMENT", page, total, llabel)
        draw_arch(c, geom, tx, ty)
        draw_labels(c, geom['rooms'], tx, ty, 2.5)
        draw_structural_grid(c, geom, tx, ty)
        
        # Identify shear wall positions — around elevator shafts and stairwells
        asc_rooms = [r for r in service if 'asc' in r['name'].lower()]
        palier_rooms = [r for r in service if 'palier' in r['name'].lower()]
        
        # Draw voiles around ascenseurs (elevator shafts = core walls)
        for r in asc_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            # Thick walls around shaft
            c.setFillColor(colors.HexColor("#FFCDD2")); c.setStrokeColor(ROUGE); c.setLineWidth(1.5)
            c.rect(rx-10, ry-10, 20, 20, fill=1, stroke=1)
            # Cross hatching
            c.setStrokeColor(ROUGE); c.setLineWidth(0.3)
            c.line(rx-10, ry-10, rx+10, ry+10)
            c.line(rx-10, ry+10, rx+10, ry-10)
            c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(rx, ry-13, "VOILE NOYAU")
            c.setFont("Helvetica", 2.5)
            c.drawCentredString(rx, ry-16, "ep.20cm BA")
        
        # Draw voiles at paliers (stairwell walls)
        for r in palier_rooms:
            rx, ry = tx(r['x']), ty(r['y'])
            c.setFillColor(colors.HexColor("#FFE0B2")); c.setStrokeColor(ORANGE); c.setLineWidth(1.2)
            c.rect(rx-8, ry-8, 16, 16, fill=1, stroke=1)
            c.setStrokeColor(ORANGE); c.setLineWidth(0.3)
            c.line(rx-8, ry-8, rx+8, ry+8)
            c.line(rx-8, ry+8, rx+8, ry-8)
            c.setFillColor(ORANGE); c.setFont("Helvetica-Bold", 3)
            c.drawCentredString(rx, ry-11, "VOILE CAGE")
            c.setFont("Helvetica", 2.5)
            c.drawCentredString(rx, ry-14, "ep.20cm BA")
        
        # Peripheral bracing walls (at building edges, some selected walls)
        xn,yn,xx,yx = get_bounds(geom)
        relevant_x = [x for x in AXES_X if xn+1000 < x < xx-1000]
        relevant_y = [y for y in AXES_Y if yn+1000 < y < yx-1000]
        
        if relevant_x and relevant_y:
            # End walls (first and last X axis)
            for ax in [relevant_x[0], relevant_x[-1]]:
                px = tx(ax)
                py1, py2 = ty(relevant_y[0]), ty(relevant_y[-1])
                c.setStrokeColor(ROUGE); c.setLineWidth(2)
                c.line(px, py1, px, py2)
            # End walls (first and last Y axis)
            for ay in [relevant_y[0], relevant_y[-1]]:
                py = ty(ay)
                px1, px2 = tx(relevant_x[0]), tx(relevant_x[-1])
                c.setStrokeColor(ROUGE); c.setLineWidth(2)
                c.line(px1, py, px2, py)
        
        # Poteaux
        draw_poteaux(c, geom, tx, ty)
        
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawString(12*mm, 42*mm, "Voiles noyau (ascenseur) : ep.20cm, HA verticaux + horizontaux")
        c.drawString(12*mm, 38*mm, "Voiles cage escalier : ep.20cm BA — Contreventement périmétrique")
        
        legend_box(c, [
            (colors.HexColor("#FFCDD2"), "Voile noyau (ascenseur)", 'rect'),
            (colors.HexColor("#FFE0B2"), "Voile cage escalier", 'rect'),
            (ROUGE, "Voile périphérique", 'line'),
            (NOIR, "Poteau BA", 'rect'),
            (GRIS, "Axe trame", 'dash'),
        ])
        c.showPage()
    
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# DXF EXPORT
# ══════════════════════════════════════════════════════════════
def generate_structure_dxf():
    print("\n=== STRUCTURE — DXF EXPORT ===")
    
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.new('ARCH_MURS', dxfattribs={'color': 8})
    doc.layers.new('STR_AXES', dxfattribs={'color': 8, 'linetype': 'DASHED'})
    doc.layers.new('STR_POTEAUX', dxfattribs={'color': 7})
    doc.layers.new('STR_POUTRES_PP', dxfattribs={'color': 7})
    doc.layers.new('STR_POUTRES_PS', dxfattribs={'color': 8})
    doc.layers.new('STR_DALLES', dxfattribs={'color': 9})
    doc.layers.new('STR_SEMELLES', dxfattribs={'color': 1})
    doc.layers.new('STR_LONGRINES', dxfattribs={'color': 30})
    doc.layers.new('STR_VOILES', dxfattribs={'color': 1})
    doc.layers.new('STR_LABELS', dxfattribs={'color': 9})
    
    y_offset = 0
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        xn,yn,xx,yx = get_bounds(geom)
        dw,dh = xx-xn, yx-yn
        if dw < 1: continue
        
        ox = lambda x: x - xn
        oy = lambda y: y - yn + y_offset
        
        # Walls
        for item in geom.get('walls',[]):
            if item['type']=='line':
                msp.add_line((ox(item['start'][0]),oy(item['start'][1])),(ox(item['end'][0]),oy(item['end'][1])), dxfattribs={'layer':'ARCH_MURS'})
            elif item['type']=='polyline':
                pts=[(ox(p[0]),oy(p[1])) for p in item['points']]
                if item.get('closed'): pts.append(pts[0])
                msp.add_lwpolyline(pts, dxfattribs={'layer':'ARCH_MURS'})
        
        # Level label
        msp.add_text(llabel, height=500, dxfattribs={'layer':'STR_LABELS','insert':(ox(xn)-2000, oy(yn)+dh/2)})
        
        # Axes
        rel_x = [x for x in AXES_X if xn-5000<x<xx+5000]
        rel_y = [y for y in AXES_Y if yn-5000<y<yx+5000]
        for ax in rel_x:
            msp.add_line((ox(ax),oy(yn)-2000),(ox(ax),oy(yx)+2000), dxfattribs={'layer':'STR_AXES'})
        for ay in rel_y:
            msp.add_line((ox(xn)-2000,oy(ay)),(ox(xx)+2000,oy(ay)), dxfattribs={'layer':'STR_AXES'})
        
        # Poteaux at intersections
        for ax in rel_x:
            for ay in rel_y:
                if xn+1000<ax<xx-1000 and yn+1000<ay<yx-1000:
                    half=150
                    pts=[(ox(ax)-half,oy(ay)-half),(ox(ax)+half,oy(ay)-half),(ox(ax)+half,oy(ay)+half),(ox(ax)-half,oy(ay)+half),(ox(ax)-half,oy(ay)-half)]
                    msp.add_lwpolyline(pts, dxfattribs={'layer':'STR_POTEAUX'})
                    msp.add_text("P30×30",height=100, dxfattribs={'layer':'STR_LABELS','insert':(ox(ax)+200,oy(ay)-300)})
        
        # Poutres principales
        for ay in rel_y:
            for i in range(len(rel_x)-1):
                if xn+1000<rel_x[i]<xx-1000 and xn+1000<rel_x[i+1]<xx-1000 and yn+1000<ay<yx-1000:
                    msp.add_line((ox(rel_x[i]),oy(ay)),(ox(rel_x[i+1]),oy(ay)), dxfattribs={'layer':'STR_POUTRES_PP'})
        
        # Poutres secondaires
        for ax in rel_x:
            for i in range(len(rel_y)-1):
                if xn+1000<ax<xx-1000 and yn+1000<rel_y[i]<yx-1000 and yn+1000<rel_y[i+1]<yx-1000:
                    msp.add_line((ox(ax),oy(rel_y[i])),(ox(ax),oy(rel_y[i+1])), dxfattribs={'layer':'STR_POUTRES_PS'})
        
        # Semelles (sous-sol only)
        if lkey == 'SOUS_SOL':
            for ax in rel_x:
                for ay in rel_y:
                    if xn-2000<ax<xx+2000 and yn-2000<ay<yx+2000:
                        half=750
                        pts=[(ox(ax)-half,oy(ay)-half),(ox(ax)+half,oy(ay)-half),(ox(ax)+half,oy(ay)+half),(ox(ax)-half,oy(ay)+half),(ox(ax)-half,oy(ay)-half)]
                        msp.add_lwpolyline(pts, dxfattribs={'layer':'STR_SEMELLES'})
            # Longrines
            for ay in rel_y:
                for i in range(len(rel_x)-1):
                    if xn-2000<rel_x[i]<xx+2000 and xn-2000<rel_x[i+1]<xx+2000 and yn-2000<ay<yx+2000:
                        msp.add_line((ox(rel_x[i]),oy(ay)),(ox(rel_x[i+1]),oy(ay)), dxfattribs={'layer':'STR_LONGRINES'})
        
        # Voiles at asc/palier positions
        wet,living,service = classify(geom['rooms'])
        for r in service:
            n = r['name'].lower()
            if 'asc' in n:
                half=1000
                pts=[(ox(r['x'])-half,oy(r['y'])-half),(ox(r['x'])+half,oy(r['y'])-half),(ox(r['x'])+half,oy(r['y'])+half),(ox(r['x'])-half,oy(r['y'])+half),(ox(r['x'])-half,oy(r['y'])-half)]
                msp.add_lwpolyline(pts, dxfattribs={'layer':'STR_VOILES'})
                msp.add_text("VOILE NOYAU ep.20",height=200, dxfattribs={'layer':'STR_VOILES','insert':(ox(r['x'])-900,oy(r['y']))})
        
        y_offset += dh + 15000
    
    dxf_path = f'{OUT}/LOT_STRUCTURE_Sakho.dxf'
    doc.saveas(dxf_path)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("="*60)
    print("GÉNÉRATION PLANS STRUCTURE — Résidence SAKHO")
    print("="*60)
    generate_coffrage()
    generate_ferraillage_poteaux()
    generate_ferraillage_poutres()
    generate_fondations()
    generate_voiles()
    generate_structure_dxf()
    print("\n"+"="*60)
    print("TERMINÉ")
    print("="*60)

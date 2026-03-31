"""
structure_generator_v2.py — Lots structure manquants
  6. Ferraillage dalles
  7. Escaliers (coffrage + ferraillage)
  8. Coupes générales (élévation bâtiment)
  9. Nomenclature des armatures
  10. Détails constructifs
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
A4P = A4
W4, H4 = A4P

LEVELS = [
    ('SOUS_SOL',   'Sous-Sol / Parking'),
    ('RDC',        'Rez-de-Chaussée'),
    ('ETAGES_1_7', 'Étages 1 à 7 (courant)'),
    ('ETAGE_8',    'Étage 8'),
    ('TERRASSE',   'Terrasse'),
]

NOIR   = colors.HexColor("#111111")
GRIS   = colors.HexColor("#AAAAAA")
GRIS_M = colors.HexColor("#555555")
GRIS_L = colors.HexColor("#CCCCCC")
GRIS5  = colors.HexColor("#E8E8E8")
BLANC  = colors.white
VERT   = colors.HexColor("#43A956")
VERT_P = colors.HexColor("#E8F5E9")
ROUGE  = colors.HexColor("#CC3333")
BLEU_B = colors.HexColor("#D6E4F0")
BLEU   = colors.HexColor("#2196F3")
ORANGE = colors.HexColor("#FF9800")

AXES_X = [637650, 642680, 644480, 645910, 648740, 651570, 657970, 659000, 661500]
AXES_Y = sorted(set([-489143,-488411,-485626,-477266,-474966,-472936,-469506,-467006,
              -465376,-461246,-456816,-455066,-452536,-449791,-448491,-447506,
              -444376,-442076,-439246,-438146,-434616]))

def load_geom(key):
    with open(f'{GEOM_DIR}/sakho_{key.lower()}_geom.json') as f:
        return json.load(f)

def get_bounds(geom):
    xs, ys = [], []
    for item in geom.get('walls',[]) + geom.get('windows',[]) + geom.get('doors',[]):
        if item['type']=='line':
            xs+=[item['start'][0],item['end'][0]]; ys+=[item['start'][1],item['end'][1]]
        elif item['type']=='polyline':
            for p in item['points']: xs.append(p[0]); ys.append(p[1])
    if not xs: return 0,0,1,1
    return min(xs),min(ys),max(xs),max(ys)

def make_transform(geom, margin=18*mm, bottom_reserve=38*mm, page_w=None, page_h=None):
    pw = page_w or W; ph = page_h or H
    xn,yn,xx,yx = get_bounds(geom)
    dw,dh = xx-xn, yx-yn
    aw, ah = pw-2*margin, ph-margin-bottom_reserve-margin
    sc = min(aw/dw, ah/dh) if dw>0 and dh>0 else 1
    ow = margin + (aw - dw*sc)/2
    oh = bottom_reserve + (ah - dh*sc)/2
    return lambda x: ow+(x-xn)*sc, lambda y: oh+(y-yn)*sc, sc

def draw_arch(c, geom, tx, ty):
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

def border(c, pw=None, ph=None):
    pw=pw or W; ph=ph or H
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(8*mm,8*mm,pw-16*mm,ph-16*mm)

def cartouche(c, titre, page, total, niveau="", pw=None):
    pw=pw or W
    cw,ch = 195*mm, 30*mm; cx,cy = pw-cw-8*mm, 6*mm
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
    c.drawString(cx+c2+3*mm,cy+ch-10*mm,"Éch: variable")
    c.drawString(cx+c2+3*mm,cy+5*mm,f"Pl. {page}/{total}")

def legend_box(c, items, x=10*mm, y=None, pw=None):
    if y is None: y=(pw or H)-10*mm if pw else H-10*mm
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

def draw_structural_grid(c, geom, tx, ty):
    xn,yn,xx,yx = get_bounds(geom)
    rel_x = [x for x in AXES_X if xn-5000<x<xx+5000]
    rel_y = [y for y in AXES_Y if yn-5000<y<yx+5000]
    if not rel_x or not rel_y: return
    min_yp = ty(min(rel_y))-12*mm; max_yp = ty(max(rel_y))+12*mm
    min_xp = tx(min(rel_x))-12*mm; max_xp = tx(max(rel_x))+12*mm
    c.setStrokeColor(GRIS); c.setLineWidth(0.25); c.setDash(6,3)
    for i,ax in enumerate(rel_x):
        px=tx(ax); c.line(px,min_yp,px,max_yp)
        r=4.5*mm; c.setFillColor(BLANC); c.circle(px,min_yp-6*mm,r,fill=1,stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold",7)
        label=chr(65+i)
        c.drawCentredString(px,min_yp-6*mm-2.5,label)
    for i,ay in enumerate(rel_y):
        py=ty(ay); c.line(min_xp,py,max_xp,py)
        c.setFillColor(BLANC); c.circle(min_xp-6*mm,py,4.5*mm,fill=1,stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold",7)
        c.drawCentredString(min_xp-6*mm,py-2.5,str(i+1))
    c.setDash()

def classify(rooms):
    wet,living,service=[],[],[]
    for r in rooms:
        n=r['name'].lower().strip()
        if re.match(r'^\d',n): continue
        if any(k in n for k in ['sdb','wc','toil','douche','cuisine','kitch','buanderie']): wet.append(r)
        elif any(k in n for k in ['hall','palier','asc','dgt','sas','terrasse','balcon','jardin','piscine','vide','porche','circulation']): service.append(r)
        else: living.append(r)
    return wet,living,service

# ══════════════════════════════════════════════════════════════
# LOT 6: FERRAILLAGE DALLES
# ══════════════════════════════════════════════════════════════
def generate_ferraillage_dalles():
    print("\n=== STRUCTURE — FERRAILLAGE DALLES ===")
    pdf_path = f'{OUT}/LOT_FERRAILLAGE_DALLES_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0; total = len(LEVELS)
    
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        tx, ty, sc = make_transform(geom)
        page += 1
        border(c); cartouche(c, "FERRAILLAGE DALLES", page, total, llabel)
        draw_arch(c, geom, tx, ty)
        draw_labels(c, geom['rooms'], tx, ty, 2.5)
        draw_structural_grid(c, geom, tx, ty)
        
        xn,yn,xx,yx = get_bounds(geom)
        rel_x = [x for x in AXES_X if xn+1000<x<xx-1000]
        rel_y = [y for y in AXES_Y if yn+1000<y<yx-1000]
        
        if len(rel_x) >= 2 and len(rel_y) >= 2:
            for i in range(len(rel_x)-1):
                for j in range(len(rel_y)-1):
                    x1,x2 = tx(rel_x[i]), tx(rel_x[i+1])
                    y1,y2 = ty(rel_y[j]), ty(rel_y[j+1])
                    cx_mid = (x1+x2)/2; cy_mid = (y1+y2)/2
                    pw = x2-x1; ph = y2-y1
                    
                    if pw < 5 or ph < 5: continue
                    
                    # Panel fill
                    c.setFillColor(colors.HexColor("#F3E5F5")); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
                    c.rect(x1, y1, pw, ph, fill=1, stroke=1)
                    
                    # Nappe inférieure direction X (red arrows)
                    c.setStrokeColor(ROUGE); c.setLineWidth(0.4)
                    nb_bars_x = max(2, int(ph / 6))
                    for k in range(nb_bars_x):
                        yb = y1 + (k+1) * ph / (nb_bars_x+1)
                        c.line(x1+2, yb, x2-2, yb)
                    
                    # Nappe inférieure direction Y (blue lines)
                    c.setStrokeColor(BLEU); c.setLineWidth(0.3)
                    nb_bars_y = max(2, int(pw / 6))
                    for k in range(nb_bars_y):
                        xb = x1 + (k+1) * pw / (nb_bars_y+1)
                        c.line(xb, y1+2, xb, y2-2)
                    
                    # Panel annotation
                    span_x = (rel_x[i+1]-rel_x[i])/1000
                    span_y = (rel_y[j+1]-rel_y[j])/1000
                    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 2.5)
                    c.drawCentredString(cx_mid, cy_mid+3, f"Dalle ep.20cm")
                    c.setFont("Helvetica", 2)
                    c.drawCentredString(cx_mid, cy_mid-1, f"Nappe inf X: HA10 esp.15")
                    c.drawCentredString(cx_mid, cy_mid-4, f"Nappe inf Y: HA10 esp.15")
                    
                    # Chapeaux on supports (thicker lines at edges)
                    c.setStrokeColor(colors.HexColor("#FF6F00")); c.setLineWidth(0.7)
                    chap_len = min(pw, ph) * 0.25
                    # Top edge chapeaux
                    for k in range(max(1,int(pw/8))):
                        xc = x1 + (k+1)*pw/(int(pw/8)+1)
                        c.line(xc, y2, xc, y2-chap_len)
                    # Bottom edge
                    for k in range(max(1,int(pw/8))):
                        xc = x1 + (k+1)*pw/(int(pw/8)+1)
                        c.line(xc, y1, xc, y1+chap_len)
        
        # Detail box
        dx, dy = W-78*mm, H-15*mm; bw, bh = 70*mm, 55*mm
        c.setFillColor(BLANC); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.rect(dx, dy-bh, bw, bh, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(dx+bw/2, dy-8, "COUPE DALLE TYPE")
        
        # Cross section of slab
        sx, sy = dx+10*mm, dy-bh+12*mm
        sw, sh = 50*mm, 16*mm
        c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
        c.rect(sx, sy, sw, sh, fill=1, stroke=1)
        # Bottom rebar
        c.setStrokeColor(ROUGE); c.setLineWidth(0.5)
        for k in range(8):
            xr = sx+4*mm + k*6*mm
            c.circle(xr, sy+3*mm, 0.8*mm, fill=1, stroke=0)
            c.setFillColor(NOIR); c.setFillColor(ROUGE)
        c.setFillColor(NOIR)
        # Top rebar (chapeaux)
        c.setStrokeColor(colors.HexColor("#FF6F00")); c.setLineWidth(0.5)
        c.line(sx+2*mm, sy+sh-3*mm, sx+sw*0.3, sy+sh-3*mm)
        c.line(sx+sw*0.7, sy+sh-3*mm, sx+sw-2*mm, sy+sh-3*mm)
        # Labels
        c.setFillColor(NOIR); c.setFont("Helvetica", 4)
        c.drawString(dx+3*mm, dy-bh+8*mm, "Inf: HA10 esp.15 (2 sens)")
        c.drawString(dx+3*mm, dy-bh+4*mm, "Chapeaux: HA10 esp.15 (L/4)")
        c.drawCentredString(dx+bw/2, sy+sh/2, "ep. 200mm")
        
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4)
        c.drawString(12*mm, 42*mm, "Dalle BA ep.20cm — C30/37 — HA500 — Enrobage 25mm")
        c.drawString(12*mm, 38*mm, "Nappe inférieure: HA10 esp.15cm (2 sens) — Chapeaux sur appuis: HA10 esp.15cm longueur L/4")
        
        legend_box(c, [
            (ROUGE, "Nappe inf. direction X", 'line'),
            (BLEU, "Nappe inf. direction Y", 'line'),
            (colors.HexColor("#FF6F00"), "Chapeaux sur appuis", 'line'),
            (colors.HexColor("#F3E5F5"), "Panneau de dalle", 'rect'),
            (GRIS, "Axe trame structurelle", 'dash'),
        ])
        c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# LOT 7: ESCALIERS
# ══════════════════════════════════════════════════════════════
def generate_escaliers():
    print("\n=== STRUCTURE — ESCALIERS ===")
    pdf_path = f'{OUT}/LOT_ESCALIERS_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    page = 0; total = 3  # plan + coupe + ferraillage
    
    # Page 1: Plan d'implantation escaliers sur étage courant
    geom = load_geom('ETAGES_1_7')
    tx, ty, sc = make_transform(geom)
    page += 1
    border(c); cartouche(c, "ESCALIERS — Plan d'implantation", page, total, "Étage courant")
    draw_arch(c, geom, tx, ty)
    draw_labels(c, geom['rooms'], tx, ty, 2.5)
    
    wet,living,service = classify(geom['rooms'])
    paliers = [r for r in service if 'palier' in r['name'].lower()]
    
    for r in paliers:
        rx, ry = tx(r['x']), ty(r['y'])
        # Stair outline
        c.setFillColor(colors.HexColor("#FFF3E0")); c.setStrokeColor(ORANGE); c.setLineWidth(1)
        c.rect(rx-12, ry-8, 24, 16, fill=1, stroke=1)
        # Steps
        c.setStrokeColor(ORANGE); c.setLineWidth(0.3)
        nb_steps = 8
        for k in range(nb_steps):
            sx = rx-12 + (k+1)*24/(nb_steps+1)
            c.line(sx, ry-8, sx, ry+8)
        # Arrow (direction montée)
        c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.line(rx-8, ry, rx+8, ry)
        path = c.beginPath()
        path.moveTo(rx+10, ry); path.lineTo(rx+7, ry+2); path.lineTo(rx+7, ry-2)
        path.close(); c.setFillColor(NOIR); c.drawPath(path, fill=1, stroke=0)
        # Label
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 3)
        c.drawCentredString(rx, ry-11, "ESCALIER")
        c.setFont("Helvetica", 2.5)
        c.drawCentredString(rx, ry-14, "2 volées / 18 marches")
    
    legend_box(c, [
        (colors.HexColor("#FFF3E0"), "Cage d'escalier", 'rect'),
        (ORANGE, "Marches (contremarche 17cm)", 'line'),
        (NOIR, "Sens de montée", 'line'),
    ])
    c.showPage()
    
    # Page 2: Coupe escalier type
    page += 1
    border(c); cartouche(c, "ESCALIERS — Coupe type", page, total, "Détail")
    
    cx, cy = W/2, H/2+15*mm
    # Draw stair cross-section
    h_etage = 80*mm  # height represents 3.0m
    l_palier = 25*mm
    l_volee = 55*mm
    ep_paillasse = 4*mm
    h_marche = h_etage / 9  # 9 marches per volée
    g_marche = l_volee / 9
    
    # Volée 1 (montante gauche)
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    path = c.beginPath()
    x0 = cx - l_volee - l_palier/2
    y0 = cy - h_etage/2
    path.moveTo(x0, y0)
    # Steps
    for k in range(9):
        path.lineTo(x0 + k*g_marche, y0 + (k+1)*h_marche)
        path.lineTo(x0 + (k+1)*g_marche, y0 + (k+1)*h_marche)
    # Palier intermédiaire
    path.lineTo(x0 + l_volee + l_palier, y0 + h_etage/2 + h_marche)
    # Underside
    path.lineTo(x0 + l_volee + l_palier, y0 + h_etage/2 + h_marche - ep_paillasse)
    path.lineTo(x0 + l_volee, y0 + h_etage/2 - ep_paillasse)
    path.lineTo(x0, y0 - ep_paillasse)
    path.close()
    c.drawPath(path, fill=1, stroke=1)
    
    # Volée 2 (retour droite)
    path2 = c.beginPath()
    x1 = cx + l_palier/2 + l_volee
    y1 = cy + h_etage/2
    path2.moveTo(x1, y1)
    for k in range(9):
        path2.lineTo(x1 - k*g_marche, y1 - (k+1)*h_marche + h_marche)
        path2.lineTo(x1 - (k+1)*g_marche, y1 - (k+1)*h_marche + h_marche)
    path2.lineTo(x1 - l_volee - l_palier, y1 - h_etage/2 - h_marche + h_marche)
    path2.lineTo(x1 - l_volee - l_palier, y1 - h_etage/2 - ep_paillasse)
    path2.lineTo(x1 - l_volee, y1 - ep_paillasse)
    path2.lineTo(x1, y1 - ep_paillasse)
    path2.close()
    c.drawPath(path2, fill=1, stroke=1)
    
    # Rebar in paillasse
    c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
    # Volée 1 bottom bars
    c.line(x0+2, y0-ep_paillasse+1.5, x0+l_volee-2, y0+h_etage/2-ep_paillasse+1.5)
    c.line(x0+2, y0-ep_paillasse+3, x0+l_volee-2, y0+h_etage/2-ep_paillasse+3)
    
    # Dimensions
    c.setStrokeColor(GRIS_M); c.setLineWidth(0.3)
    # Height
    dim_x = cx - l_volee - l_palier/2 - 15*mm
    c.line(dim_x, cy-h_etage/2, dim_x, cy+h_etage/2)
    c.line(dim_x-2, cy-h_etage/2, dim_x+2, cy-h_etage/2)
    c.line(dim_x-2, cy+h_etage/2, dim_x+2, cy+h_etage/2)
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
    c.saveState(); c.translate(dim_x-4, cy); c.rotate(90)
    c.drawCentredString(0, 0, "h = 3.00 m"); c.restoreState()
    
    # Step dimensions
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawString(x0 + l_volee/2 - 15, y0 + h_etage/4 + 8, "9 marches")
    c.drawString(x0 + l_volee/2 - 20, y0 + h_etage/4 + 2, "h=16.7cm / g=27cm")
    
    # Labels
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(cx, cy-h_etage/2-15*mm, "Palier bas")
    c.drawCentredString(cx, cy+h_etage/2+10*mm, "Palier haut")
    c.drawCentredString(cx - l_volee/2 - l_palier/2, cy+5, "Palier intermédiaire")
    
    # Notes
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 5)
    c.drawString(12*mm, 55*mm, "Escalier 2 volées droites — 2 × 9 marches = 18 marches")
    c.drawString(12*mm, 50*mm, "Hauteur marche: h = 16.7 cm — Giron: g = 27 cm — 2h+g = 60.4 cm ✓")
    c.drawString(12*mm, 45*mm, "Paillasse ep. 18 cm — C30/37 — HA500")
    c.drawString(12*mm, 40*mm, "Armatures paillasse: 5HA12 nappe inf. + HA8 esp.20 répartition")
    
    c.showPage()
    
    # Page 3: Ferraillage escalier (détail)
    page += 1
    border(c); cartouche(c, "ESCALIERS — Ferraillage paillasse", page, total, "Détail")
    
    # Enlarged paillasse section
    bx, by = 60*mm, 60*mm
    bw, bh = W-120*mm, H-120*mm
    
    # Draw paillasse outline (angled)
    angle = math.atan2(3.0, 2.7)  # slope
    paille_len = bw * 0.8
    
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    # Simplified rectangular paillasse section
    sx, sy = bx+20*mm, by+bh/2
    sw, sh = paille_len, 20*mm
    c.rect(sx, sy-sh/2, sw, sh, fill=1, stroke=1)
    
    # Bottom bars (5HA12)
    c.setStrokeColor(ROUGE); c.setLineWidth(0.8)
    c.setFillColor(ROUGE)
    for k in range(5):
        yb = sy - sh/2 + 3*mm + k * (sh-6*mm) / 4
        if k < 3:  # Only bottom 3 are main
            c.line(sx+3*mm, sy-sh/2+3*mm, sx+sw-3*mm, sy-sh/2+3*mm)
    # Main rebar lines
    for k in range(5):
        yb = sy - sh/2 + 3*mm
        xb = sx + 5*mm + k * (sw-10*mm)/4
        c.circle(xb, yb, 1.2*mm, fill=1, stroke=0)
    
    # Top bars (2HA10)
    c.setStrokeColor(BLEU); c.setLineWidth(0.6)
    for k in range(3):
        yt = sy + sh/2 - 3*mm
        xb = sx + 10*mm + k * (sw-20*mm)/2
        c.setFillColor(BLEU)
        c.circle(xb, yt, 1*mm, fill=1, stroke=0)
    
    # Stirrups / repartition
    c.setStrokeColor(GRIS_M); c.setLineWidth(0.4)
    nb_rep = int(sw / 8*mm)
    for k in range(nb_rep):
        xr = sx + 5*mm + k * (sw-10*mm) / (nb_rep-1)
        c.line(xr, sy-sh/2+2*mm, xr, sy+sh/2-2*mm)
    
    # Dimension annotations
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(sx+sw/2, sy+sh/2+10*mm, "COUPE PAILLASSE TYPE")
    c.setFont("Helvetica", 6)
    c.drawCentredString(sx+sw/2, sy-sh/2-8*mm, f"Épaisseur: 180 mm")
    c.drawString(sx+sw+5*mm, sy, "180mm")
    
    # Rebar schedule
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    tab_y = by + 30*mm
    c.drawString(bx+20*mm, tab_y+15*mm, "NOMENCLATURE ARMATURES ESCALIER")
    
    # Table
    headers = ["Pos.", "Désignation", "Diamètre", "Esp./Nb", "Longueur", "Total"]
    data = [
        ["1", "Armature principale paillasse", "HA12", "5 barres", "3.80 m", "19.0 ml"],
        ["2", "Armature répartition", "HA8", "esp. 20cm", "1.20 m", "18.0 ml"],
        ["3", "Armature chapeau palier", "HA10", "3 barres", "1.50 m", "4.5 ml"],
        ["4", "Armature constructive sup.", "HA10", "2 barres", "3.80 m", "7.6 ml"],
    ]
    col_w = [12*mm, 55*mm, 20*mm, 22*mm, 22*mm, 22*mm]
    rh = 6*mm
    tx_tab = bx + 20*mm
    # Header
    hx = tx_tab
    c.setFillColor(VERT_P); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
    for cw_val in col_w:
        c.rect(hx, tab_y, cw_val, rh, fill=1, stroke=1)
        hx += cw_val
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
    hx = tx_tab
    for h_text, cw_val in zip(headers, col_w):
        c.drawCentredString(hx+cw_val/2, tab_y+2, h_text)
        hx += cw_val
    # Rows
    for j, row in enumerate(data):
        ry_tab = tab_y - (j+1)*rh
        hx = tx_tab
        for val, cw_val in zip(row, col_w):
            c.setFillColor(BLANC)
            c.rect(hx, ry_tab, cw_val, rh, fill=1, stroke=1)
            c.setFillColor(NOIR); c.setFont("Helvetica", 5)
            c.drawCentredString(hx+cw_val/2, ry_tab+2, val)
            hx += cw_val
    
    c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} ({page} pages)")

# ══════════════════════════════════════════════════════════════
# LOT 8: COUPES GÉNÉRALES
# ══════════════════════════════════════════════════════════════
def generate_coupes():
    print("\n=== STRUCTURE — COUPES GÉNÉRALES ===")
    pdf_path = f'{OUT}/LOT_COUPES_GENERALES_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    
    # Page 1: Coupe longitudinale (tous niveaux)
    border(c); cartouche(c, "COUPE LONGITUDINALE A-A", 1, 2, "Tous niveaux")
    
    cx, cy_base = 50*mm, 50*mm
    h_etage = 22*mm  # represents 3.0m
    h_ss = 18*mm     # sous-sol 2.5m
    
    niveaux = [
        ("Sous-Sol", h_ss, GRIS_L),
        ("RDC", h_etage, colors.HexColor("#E8F5E9")),
        ("Étage 1", h_etage, BLEU_B),
        ("Étage 2", h_etage, BLEU_B),
        ("Étage 3", h_etage, BLEU_B),
        ("Étage 4", h_etage, BLEU_B),
        ("Étage 5", h_etage, BLEU_B),
        ("Étage 6", h_etage, BLEU_B),
        ("Étage 7", h_etage, BLEU_B),
        ("Étage 8", h_etage, colors.HexColor("#FFF3E0")),
        ("Terrasse", 8*mm, colors.HexColor("#FFECB3")),
    ]
    
    bldg_w = W - 120*mm
    total_h = sum(h for _,h,_ in niveaux)
    
    # Ground line
    c.setStrokeColor(colors.HexColor("#8D6E63")); c.setLineWidth(1.5)
    gnd_y = cy_base + h_ss
    c.line(cx-20*mm, gnd_y, cx+bldg_w+20*mm, gnd_y)
    c.setFillColor(colors.HexColor("#8D6E63")); c.setFont("Helvetica-Bold", 6)
    c.drawString(cx+bldg_w+22*mm, gnd_y-3, "±0.00 TN")
    
    # Draw each level
    y_current = cy_base
    for i, (name, h, col) in enumerate(niveaux):
        c.setFillColor(col); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.rect(cx, y_current, bldg_w, h, fill=1, stroke=1)
        
        # Level name
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
        c.drawString(cx+3*mm, y_current+h/2-2, name)
        
        # Poteaux at edges
        c.setFillColor(GRIS_M)
        pot_w = 3*mm
        c.rect(cx, y_current, pot_w, h, fill=1, stroke=0)
        c.rect(cx+bldg_w-pot_w, y_current, pot_w, h, fill=1, stroke=0)
        
        # Interior poteaux (spaced ~5m)
        nb_int = max(1, int(bldg_w / 35*mm))
        for k in range(1, nb_int):
            px = cx + k * bldg_w / nb_int
            c.rect(px-pot_w/2, y_current, pot_w, h, fill=1, stroke=0)
        
        # Dalle line (thick at top of level)
        c.setStrokeColor(NOIR); c.setLineWidth(1.5)
        c.line(cx, y_current+h, cx+bldg_w, y_current+h)
        
        # Elevation mark
        if y_current >= gnd_y:
            elev = (y_current - gnd_y) / h_etage * 3.0
        else:
            elev = -(gnd_y - y_current) / h_ss * 2.5
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4.5)
        c.drawString(cx+bldg_w+5*mm, y_current+h-3, f"+{elev:.2f}" if elev >= 0 else f"{elev:.2f}")
        
        y_current += h
    
    # Top elevation
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
    top_elev = h_ss / h_ss * (-2.5) + sum(h for _,h,_ in niveaux[1:]) / h_etage * 3.0
    c.drawString(cx+bldg_w+5*mm, y_current-3, f"+{30.5:.2f}")
    
    # Fondation
    c.setFillColor(colors.HexColor("#D7CCC8")); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    fond_h = 6*mm
    c.rect(cx-5*mm, cy_base-fond_h, bldg_w+10*mm, fond_h, fill=1, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica", 4)
    c.drawCentredString(cx+bldg_w/2, cy_base-fond_h/2-2, "FONDATIONS — Semelles isolées + longrines")
    
    # Notes
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 4.5)
    c.drawString(12*mm, 42*mm, "R+10 (SS + RDC + 8 étages + Terrasse) — Hauteur totale ≈ 30.50m")
    c.drawString(12*mm, 38*mm, "Hauteur sous plafond: 2.80m (RDC), 2.70m (étages) — Dalle ep.20cm")
    
    c.showPage()
    
    # Page 2: Coupe transversale
    border(c); cartouche(c, "COUPE TRANSVERSALE B-B", 2, 2, "Tous niveaux")
    
    # Similar but narrower building width
    bldg_w2 = W - 180*mm
    cx2 = (W - bldg_w2) / 2
    
    y_current = cy_base
    c.setStrokeColor(colors.HexColor("#8D6E63")); c.setLineWidth(1.5)
    c.line(cx2-20*mm, gnd_y, cx2+bldg_w2+20*mm, gnd_y)
    c.setFillColor(colors.HexColor("#8D6E63")); c.setFont("Helvetica-Bold", 6)
    c.drawString(cx2+bldg_w2+22*mm, gnd_y-3, "±0.00 TN")
    
    for i, (name, h, col) in enumerate(niveaux):
        c.setFillColor(col); c.setStrokeColor(NOIR); c.setLineWidth(0.5)
        c.rect(cx2, y_current, bldg_w2, h, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
        c.drawString(cx2+3*mm, y_current+h/2-2, name)
        # Poteaux
        c.setFillColor(GRIS_M)
        c.rect(cx2, y_current, 3*mm, h, fill=1, stroke=0)
        c.rect(cx2+bldg_w2-3*mm, y_current, 3*mm, h, fill=1, stroke=0)
        # Voile noyau central
        c.setFillColor(colors.HexColor("#FFCDD2"))
        c.rect(cx2+bldg_w2/2-4*mm, y_current, 8*mm, h, fill=1, stroke=0)
        c.setStrokeColor(NOIR); c.setLineWidth(1.5)
        c.line(cx2, y_current+h, cx2+bldg_w2, y_current+h)
        c.setFillColor(GRIS_M); c.setFont("Helvetica", 4.5)
        if y_current >= gnd_y:
            elev = (y_current-gnd_y)/h_etage*3.0
        else:
            elev = -(gnd_y-y_current)/h_ss*2.5
        c.drawString(cx2+bldg_w2+5*mm, y_current+h-3, f"+{elev:.2f}" if elev>=0 else f"{elev:.2f}")
        y_current += h
    
    c.setFillColor(colors.HexColor("#D7CCC8")); c.setStrokeColor(NOIR); c.setLineWidth(0.8)
    c.rect(cx2-5*mm, cy_base-fond_h, bldg_w2+10*mm, fond_h, fill=1, stroke=1)
    
    # Voile noyau label
    c.setFillColor(ROUGE); c.setFont("Helvetica-Bold", 5)
    c.drawString(cx2+bldg_w2/2+6*mm, cy_base+total_h/2, "Noyau BA")
    c.drawString(cx2+bldg_w2/2+6*mm, cy_base+total_h/2-5, "(voile ep.20)")
    
    c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} (2 pages)")

# ══════════════════════════════════════════════════════════════
# LOT 9: NOMENCLATURE DES ARMATURES
# ══════════════════════════════════════════════════════════════
def generate_nomenclature():
    print("\n=== STRUCTURE — NOMENCLATURE ARMATURES ===")
    pdf_path = f'{OUT}/LOT_NOMENCLATURE_ACIERS_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    
    border(c); cartouche(c, "NOMENCLATURE GÉNÉRALE DES ARMATURES", 1, 2, "Récapitulatif tous niveaux")
    
    # Table header
    tx_t = 20*mm; ty_t = H - 25*mm
    cols = [15*mm, 50*mm, 22*mm, 22*mm, 22*mm, 25*mm, 25*mm, 25*mm, 28*mm]
    headers = ["Pos.", "Élément", "Section", "Arm. long.", "Arm. trans.", "Nb/niveau", "× Niveaux", "Total (ml)", "Poids (kg)"]
    rh = 7*mm
    
    # Header row
    hx = tx_t
    for cw, hd in zip(cols, headers):
        c.setFillColor(VERT_P); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
        c.rect(hx, ty_t, cw, rh, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(hx+cw/2, ty_t+2, hd)
        hx += cw
    
    # Data rows
    data = [
        ["1", "Poteau 30×30", "30×30cm", "8HA16", "Cad HA8/15", "~80", "10", "12800", "20480"],
        ["2", "Poutre principale", "25×50cm", "3HA16+2HA14", "Étr HA8/20", "~60", "10", "21000", "25200"],
        ["3", "Poutre secondaire", "20×40cm", "3HA14+2HA12", "Étr HA8/20", "~50", "10", "15000", "13350"],
        ["4", "Dalle ep.20cm", "—", "HA10/15 ×2", "—", "~500m²", "10", "33000", "20460"],
        ["5", "Chapeaux dalle", "—", "HA10/15", "—", "~200ml", "10", "8000", "4960"],
        ["6", "Voile noyau asc.", "ep.20cm", "HA12/15 ×2", "HA8/20", "~40m²", "10", "5400", "4806"],
        ["7", "Voile cage esc.", "ep.20cm", "HA12/15 ×2", "HA8/20", "~30m²", "10", "4000", "3560"],
        ["8", "Escalier paillasse", "ep.18cm", "5HA12", "HA8/20", "2 volées", "10", "760", "677"],
        ["9", "Semelle isolée", "150×150×40", "HA12/15 ×2", "—", "~80", "1", "2400", "2136"],
        ["10", "Longrine", "25×40cm", "4HA12+2HA10", "Étr HA8/20", "~200ml", "1", "1400", "1246"],
        ["—", "", "", "", "", "", "", "", ""],
        ["", "TOTAL ESTIMÉ", "", "", "", "", "", "103 760 ml", "96 875 kg"],
        ["", "", "", "", "", "", "", "", "≈ 97 t"],
    ]
    
    for j, row in enumerate(data):
        ry = ty_t - (j+1)*rh
        hx = tx_t
        is_total = "TOTAL" in str(row[1])
        for val, cw in zip(row, cols):
            c.setFillColor(VERT_P if is_total else BLANC)
            c.setStrokeColor(NOIR); c.setLineWidth(0.2)
            c.rect(hx, ry, cw, rh, fill=1, stroke=1)
            c.setFillColor(NOIR)
            c.setFont("Helvetica-Bold" if is_total else "Helvetica", 5)
            c.drawCentredString(hx+cw/2, ry+2, val)
            hx += cw
    
    # Notes
    c.setFillColor(GRIS_M); c.setFont("Helvetica", 4.5)
    ny = ty_t - (len(data)+2)*rh
    c.drawString(tx_t, ny, "Notes:")
    c.drawString(tx_t, ny-6*mm, "• Quantités estimées pour R+10 (SS + RDC + 8 étages + Terrasse)")
    c.drawString(tx_t, ny-11*mm, "• Ratio acier ≈ 97 t / 5000 m² bâti = 19.4 kg/m² (conforme pour résidentiel R+10)")
    c.drawString(tx_t, ny-16*mm, "• Béton estimé: fondations ~120 m³ + structure ~750 m³ = ~870 m³ total")
    c.drawString(tx_t, ny-21*mm, "• Poids unitaires: HA8=0.395kg/ml, HA10=0.617kg/ml, HA12=0.888kg/ml, HA14=1.21kg/ml, HA16=1.58kg/ml")
    
    c.showPage()
    
    # Page 2: Récapitulatif par niveau
    border(c); cartouche(c, "RÉCAPITULATIF ACIERS PAR NIVEAU", 2, 2, "Synthèse")
    
    ty_t2 = H - 25*mm
    cols2 = [40*mm, 25*mm, 25*mm, 25*mm, 25*mm, 25*mm, 30*mm]
    headers2 = ["Niveau", "Poteaux (kg)", "Poutres (kg)", "Dalles (kg)", "Voiles (kg)", "Escal. (kg)", "Total (kg)"]
    
    hx = tx_t
    for cw, hd in zip(cols2, headers2):
        c.setFillColor(VERT_P); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
        c.rect(hx, ty_t2, cw, rh, fill=1, stroke=1)
        c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(hx+cw/2, ty_t2+2, hd)
        hx += cw
    
    niv_data = [
        ["Fondations", "—", "—", "—", "—", "—", "3 382"],
        ["Sous-Sol", "2 048", "2 520", "2 095", "836", "68", "7 567"],
        ["RDC", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 1", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 2", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 3", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 4", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 5", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 6", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 7", "2 048", "3 855", "2 542", "836", "68", "9 349"],
        ["Étage 8", "1 536", "2 891", "1 907", "627", "68", "7 029"],
        ["Terrasse", "—", "—", "1 200", "—", "—", "1 200"],
        ["", "", "", "", "", "", ""],
        ["TOTAL", "20 016", "36 351", "25 538", "8 315", "748", "96 875"],
    ]
    
    for j, row in enumerate(niv_data):
        ry = ty_t2 - (j+1)*rh
        hx = tx_t
        is_total = "TOTAL" in str(row[0])
        for val, cw in zip(row, cols2):
            c.setFillColor(VERT_P if is_total else BLANC)
            c.setStrokeColor(NOIR); c.setLineWidth(0.2)
            c.rect(hx, ry, cw, rh, fill=1, stroke=1)
            c.setFillColor(NOIR)
            c.setFont("Helvetica-Bold" if is_total else "Helvetica", 5)
            c.drawCentredString(hx+cw/2, ry+2, val)
            hx += cw
    
    c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} (2 pages)")

# ══════════════════════════════════════════════════════════════
# LOT 10: DÉTAILS CONSTRUCTIFS
# ══════════════════════════════════════════════════════════════
def generate_details():
    print("\n=== STRUCTURE — DÉTAILS CONSTRUCTIFS ===")
    pdf_path = f'{OUT}/LOT_DETAILS_CONSTRUCTIFS_Sakho.pdf'
    c = pdfcanvas.Canvas(pdf_path, pagesize=A3L)
    
    # Page 1: Noeud poteau-poutre + about de poutre
    border(c); cartouche(c, "DÉTAILS CONSTRUCTIFS — Nœuds & Abouts", 1, 2, "Détails types")
    
    # ── Detail 1: Noeud poteau-poutre ──
    d1x, d1y = 30*mm, H/2+20*mm
    d1w, d1h = W/2-40*mm, H/2-40*mm
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(d1x, d1y, d1w, d1h, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(d1x+d1w/2, d1y+d1h-8, "DÉTAIL 1: NŒUD POTEAU-POUTRE")
    
    # Draw junction
    jx, jy = d1x+d1w/2, d1y+d1h/2-5*mm
    pot_w, pot_h = 18*mm, 50*mm
    beam_w, beam_h = 60*mm, 14*mm
    
    # Poteau
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(jx-pot_w/2, jy-pot_h/2, pot_w, pot_h, fill=1, stroke=1)
    # Poutre
    c.rect(jx-beam_w/2, jy-beam_h/2, beam_w, beam_h, fill=1, stroke=1)
    
    # Poteau rebars (vertical)
    c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
    for dx in [-pot_w/2+2*mm, -pot_w/4, 0, pot_w/4, pot_w/2-2*mm]:
        c.line(jx+dx, jy-pot_h/2+2, jx+dx, jy+pot_h/2-2)
    # Poutre rebars (horizontal)
    for dy in [-beam_h/2+2*mm, 0, beam_h/2-2*mm]:
        c.line(jx-beam_w/2+2, jy+dy, jx+beam_w/2-2, jy+dy)
    # Ancrage hooks
    c.setStrokeColor(ROUGE); c.setLineWidth(0.6)
    for dy in [-beam_h/2+2*mm, beam_h/2-2*mm]:
        c.line(jx-pot_w/2+3*mm, jy+dy, jx-pot_w/2+3*mm, jy+dy+(5*mm if dy<0 else -5*mm))
    
    # Cadres zone critique (denser)
    c.setStrokeColor(GRIS_M); c.setLineWidth(0.3)
    for k in range(8):
        yk = jy - pot_h/2 + 3*mm + k * 3*mm
        if abs(yk - jy) < beam_h/2 + 3*mm:
            continue  # skip in beam zone
        c.line(jx-pot_w/2+1.5*mm, yk, jx+pot_w/2-1.5*mm, yk)
    
    # Annotations
    c.setFillColor(NOIR); c.setFont("Helvetica", 4.5)
    c.drawString(jx+pot_w/2+3*mm, jy+pot_h/4, "Cadres HA8/10cm")
    c.drawString(jx+pot_w/2+3*mm, jy+pot_h/4-5*mm, "(zone critique)")
    c.drawString(jx+beam_w/2+3*mm, jy, "PP 25×50")
    c.drawString(jx+beam_w/2+3*mm, jy-5*mm, "3HA16 inf.")
    c.drawString(jx-pot_w/2-25*mm, jy+pot_h/4, "P 30×30")
    c.drawString(jx-pot_w/2-25*mm, jy+pot_h/4-5*mm, "8HA16")
    
    # ── Detail 2: About de poutre ──
    d2x = W/2+10*mm
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(d2x, d1y, d1w, d1h, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(d2x+d1w/2, d1y+d1h-8, "DÉTAIL 2: ABOUT DE POUTRE SUR POTEAU")
    
    ax, ay = d2x+d1w/2, d1y+d1h/2-5*mm
    # Poteau
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(ax-pot_w/2, ay-pot_h/3, pot_w, pot_h*0.7, fill=1, stroke=1)
    # Poutre (only one side)
    c.rect(ax+pot_w/2, ay-beam_h/2, beam_w/2, beam_h, fill=1, stroke=1)
    # Rebars with hooks
    c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
    # Bottom bar with hook into column
    c.line(ax+pot_w/2, ay-beam_h/2+2*mm, ax+pot_w/2+beam_w/2-2, ay-beam_h/2+2*mm)
    c.line(ax+pot_w/2, ay-beam_h/2+2*mm, ax-pot_w/4, ay-beam_h/2+2*mm)
    c.line(ax-pot_w/4, ay-beam_h/2+2*mm, ax-pot_w/4, ay+5*mm)  # hook up
    # Top bar
    c.line(ax+pot_w/2, ay+beam_h/2-2*mm, ax+pot_w/2+beam_w/2-2, ay+beam_h/2-2*mm)
    c.line(ax+pot_w/2, ay+beam_h/2-2*mm, ax-pot_w/4, ay+beam_h/2-2*mm)
    c.line(ax-pot_w/4, ay+beam_h/2-2*mm, ax-pot_w/4, ay-5*mm)  # hook down
    
    # Annotations
    c.setFillColor(NOIR); c.setFont("Helvetica", 4.5)
    c.drawString(ax+pot_w/2+beam_w/2+3*mm, ay, "Ancrage ≥ 40Ø")
    c.drawString(ax+pot_w/2+beam_w/2+3*mm, ay-5*mm, "Crochet 90° dans poteau")
    
    # ── Bottom section: joint de dilatation + note ──
    d3y = 50*mm
    d3h = H/2 - 40*mm
    
    # Detail 3: Joint de dilatation
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(d1x, d3y, d1w, d3h, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(d1x+d1w/2, d3y+d3h-8, "DÉTAIL 3: JOINT DE DILATATION")
    
    jdx = d1x+d1w/2; jdy = d3y+d3h/2
    # Two slabs with gap
    gap = 4*mm
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(jdx-50*mm, jdy-5*mm, 50*mm-gap/2, 10*mm, fill=1, stroke=1)
    c.rect(jdx+gap/2, jdy-5*mm, 50*mm-gap/2, 10*mm, fill=1, stroke=1)
    # Joint material
    c.setFillColor(colors.HexColor("#FFEB3B")); c.setStrokeColor(NOIR); c.setLineWidth(0.3)
    c.rect(jdx-gap/2, jdy-5*mm, gap, 10*mm, fill=1, stroke=1)
    # Sealant on top
    c.setFillColor(colors.HexColor("#616161"))
    c.rect(jdx-gap/2-1*mm, jdy+5*mm, gap+2*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(NOIR); c.setFont("Helvetica", 4.5)
    c.drawString(jdx+55*mm, jdy+5*mm, "Mastic polyuréthane")
    c.drawString(jdx+55*mm, jdy, "Polystyrène expansé 20mm")
    c.drawString(jdx+55*mm, jdy-5*mm, "Joint tous les 25-30m")
    
    # Detail 4: Notes générales
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(d2x, d3y, d1w, d3h, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(d2x+d1w/2, d3y+d3h-8, "NOTES GÉNÉRALES")
    
    notes = [
        "• Béton: C30/37 — fck = 30 MPa — γc = 1.5",
        "• Acier: HA500 — fyk = 500 MPa — γs = 1.15",
        "• Enrobage: 30mm (XC2) — 50mm sur fondations",
        "• Recouvrement: Ls = 40Ø (zone courante)",
        "• Cadres zone critique: esp. 10cm sur h+500mm",
        "• Cadres zone courante: esp. 15-20cm",
        "• Ancrage poutre dans poteau: ≥ 40Ø + crochet",
        "• Normes: EC2 (NF EN 1992-1-1) + EC8 zone 1",
        "• Classe exposition: XC2 (humidité, Dakar)",
        "• Contrôle béton: essais 28j obligatoires",
        "• Tolérances: ±20mm positionnement armatures",
    ]
    c.setFont("Helvetica", 5)
    for i, note in enumerate(notes):
        c.drawString(d2x+5*mm, d3y+d3h-20-i*6*mm, note)
    
    c.showPage()
    
    # Page 2: Détails complémentaires
    border(c); cartouche(c, "DÉTAILS CONSTRUCTIFS — Compléments", 2, 2, "Détails types")
    
    # Appui dalle sur poutre
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(30*mm, H/2+20*mm, W/2-40*mm, H/2-40*mm, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(W/4, H-28*mm, "DÉTAIL 4: APPUI DALLE SUR POUTRE")
    
    # Draw
    apx, apy = W/4, H*3/4-10*mm
    # Poutre section
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(apx-12*mm, apy-20*mm, 24*mm, 40*mm, fill=1, stroke=1)
    # Dalle (thinner, on top of poutre)
    c.setFillColor(colors.HexColor("#E1BEE7")); c.setStrokeColor(NOIR)
    c.rect(apx-50*mm, apy+20*mm, 100*mm, 8*mm, fill=1, stroke=1)
    # Chapeau rebar over support
    c.setStrokeColor(ROUGE); c.setLineWidth(0.7)
    c.line(apx-30*mm, apy+20*mm+6*mm, apx+30*mm, apy+20*mm+6*mm)
    # Bottom rebar in dalle
    c.line(apx-50*mm+2, apy+20*mm+2*mm, apx+50*mm-2, apy+20*mm+2*mm)
    # Labels
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawString(apx+55*mm, apy+24*mm, "Dalle ep.200mm")
    c.drawString(apx+55*mm, apy+20*mm, "Chapeau HA10 esp.15 L=L/4")
    c.drawString(apx+55*mm, apy, "Poutre 250×500mm")
    c.drawString(apx+55*mm, apy-5*mm, "Enrobage 30mm")
    
    # Arrêt de coulage
    d5x = W/2+10*mm
    c.setStrokeColor(NOIR); c.setLineWidth(0.5)
    c.rect(d5x, H/2+20*mm, W/2-40*mm, H/2-40*mm, fill=0, stroke=1)
    c.setFillColor(NOIR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(d5x+(W/2-40*mm)/2, H-28*mm, "DÉTAIL 5: REPRISE DE BÉTONNAGE")
    
    rbx, rby = d5x+(W/2-40*mm)/2, H*3/4-10*mm
    # Dalle with construction joint
    c.setFillColor(BLEU_B); c.setStrokeColor(NOIR); c.setLineWidth(0.6)
    c.rect(rbx-50*mm, rby-5*mm, 45*mm, 10*mm, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#B3E5FC"))
    c.rect(rbx-5*mm, rby-5*mm, 55*mm, 10*mm, fill=1, stroke=1)
    # Joint line
    c.setStrokeColor(NOIR); c.setLineWidth(1)
    c.line(rbx-5*mm, rby-5*mm, rbx-5*mm, rby+5*mm)
    # Rebars through joint
    c.setStrokeColor(ROUGE); c.setLineWidth(0.6)
    c.line(rbx-50*mm+2, rby-3*mm, rbx+50*mm-2, rby-3*mm)
    c.line(rbx-50*mm+2, rby+3*mm, rbx+50*mm-2, rby+3*mm)
    # Labels
    c.setFillColor(NOIR); c.setFont("Helvetica", 5)
    c.drawString(rbx+55*mm, rby+3*mm, "Armatures continues")
    c.drawString(rbx+55*mm, rby-3*mm, "à travers le joint")
    c.drawString(rbx-50*mm, rby-12*mm, "Surface piquée + nettoyée")
    c.drawString(rbx-50*mm, rby-17*mm, "Produit d'accrochage")
    c.setFont("Helvetica-Bold", 5)
    c.drawString(rbx-50*mm, rby+15*mm, "1ère phase")
    c.drawString(rbx+5*mm, rby+15*mm, "2ème phase")
    
    c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} (2 pages)")

# ══════════════════════════════════════════════════════════════
# DXF structure complement
# ══════════════════════════════════════════════════════════════
def update_structure_dxf():
    print("\n=== STRUCTURE — Mise à jour DXF ===")
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    doc.layers.new('ARCH_MURS', dxfattribs={'color': 8})
    doc.layers.new('STR_AXES', dxfattribs={'color': 8})
    doc.layers.new('STR_POTEAUX', dxfattribs={'color': 7})
    doc.layers.new('STR_POUTRES_PP', dxfattribs={'color': 7})
    doc.layers.new('STR_POUTRES_PS', dxfattribs={'color': 8})
    doc.layers.new('STR_DALLES', dxfattribs={'color': 6})
    doc.layers.new('STR_DALLES_FERRAILLAGE', dxfattribs={'color': 1})
    doc.layers.new('STR_SEMELLES', dxfattribs={'color': 1})
    doc.layers.new('STR_LONGRINES', dxfattribs={'color': 30})
    doc.layers.new('STR_VOILES', dxfattribs={'color': 1})
    doc.layers.new('STR_ESCALIERS', dxfattribs={'color': 30})
    doc.layers.new('STR_LABELS', dxfattribs={'color': 9})
    
    y_offset = 0
    for lkey, llabel in LEVELS:
        geom = load_geom(lkey)
        if len(geom['walls']) < 5: continue
        xn,yn,xx,yx = get_bounds(geom)
        dw,dh = xx-xn, yx-yn
        if dw < 1: continue
        ox = lambda x: x-xn; oy = lambda y: y-yn+y_offset
        
        # Walls
        for item in geom.get('walls',[]):
            if item['type']=='line':
                msp.add_line((ox(item['start'][0]),oy(item['start'][1])),(ox(item['end'][0]),oy(item['end'][1])), dxfattribs={'layer':'ARCH_MURS'})
            elif item['type']=='polyline':
                pts=[(ox(p[0]),oy(p[1])) for p in item['points']]
                if item.get('closed'): pts.append(pts[0])
                msp.add_lwpolyline(pts, dxfattribs={'layer':'ARCH_MURS'})
        
        msp.add_text(llabel, height=500, dxfattribs={'layer':'STR_LABELS','insert':(ox(xn)-2000,oy(yn)+dh/2)})
        
        rel_x = [x for x in AXES_X if xn-5000<x<xx+5000]
        rel_y = [y for y in AXES_Y if yn-5000<y<yx+5000]
        
        # Axes
        for ax in rel_x:
            msp.add_line((ox(ax),oy(yn)-2000),(ox(ax),oy(yx)+2000), dxfattribs={'layer':'STR_AXES'})
        for ay in rel_y:
            msp.add_line((ox(xn)-2000,oy(ay)),(ox(xx)+2000,oy(ay)), dxfattribs={'layer':'STR_AXES'})
        
        # Poteaux, poutres
        for ax in rel_x:
            for ay in rel_y:
                if xn+1000<ax<xx-1000 and yn+1000<ay<yx-1000:
                    h=150
                    msp.add_lwpolyline([(ox(ax)-h,oy(ay)-h),(ox(ax)+h,oy(ay)-h),(ox(ax)+h,oy(ay)+h),(ox(ax)-h,oy(ay)+h),(ox(ax)-h,oy(ay)-h)], dxfattribs={'layer':'STR_POTEAUX'})
        for ay in rel_y:
            for i in range(len(rel_x)-1):
                if xn+1000<rel_x[i]<xx-1000 and xn+1000<rel_x[i+1]<xx-1000 and yn+1000<ay<yx-1000:
                    msp.add_line((ox(rel_x[i]),oy(ay)),(ox(rel_x[i+1]),oy(ay)), dxfattribs={'layer':'STR_POUTRES_PP'})
        for ax in rel_x:
            for i in range(len(rel_y)-1):
                if xn+1000<ax<xx-1000 and yn+1000<rel_y[i]<yx-1000 and yn+1000<rel_y[i+1]<yx-1000:
                    msp.add_line((ox(ax),oy(rel_y[i])),(ox(ax),oy(rel_y[i+1])), dxfattribs={'layer':'STR_POUTRES_PS'})
        
        # Dalle panels
        for i in range(len(rel_x)-1):
            for j in range(len(rel_y)-1):
                if xn+1000<rel_x[i]<xx-1000 and xn+1000<rel_x[i+1]<xx-1000 and yn+1000<rel_y[j]<yx-1000 and yn+1000<rel_y[j+1]<yx-1000:
                    msp.add_lwpolyline([(ox(rel_x[i]),oy(rel_y[j])),(ox(rel_x[i+1]),oy(rel_y[j])),(ox(rel_x[i+1]),oy(rel_y[j+1])),(ox(rel_x[i]),oy(rel_y[j+1])),(ox(rel_x[i]),oy(rel_y[j]))], dxfattribs={'layer':'STR_DALLES'})
                    cx_d = (rel_x[i]+rel_x[i+1])/2; cy_d = (rel_y[j]+rel_y[j+1])/2
                    msp.add_text("D ep.20", height=100, dxfattribs={'layer':'STR_DALLES','insert':(ox(cx_d)-200,oy(cy_d))})
        
        # Voiles
        wet,living,service = classify(geom['rooms'])
        for r in service:
            if 'asc' in r['name'].lower():
                h=1000
                msp.add_lwpolyline([(ox(r['x'])-h,oy(r['y'])-h),(ox(r['x'])+h,oy(r['y'])-h),(ox(r['x'])+h,oy(r['y'])+h),(ox(r['x'])-h,oy(r['y'])+h),(ox(r['x'])-h,oy(r['y'])-h)], dxfattribs={'layer':'STR_VOILES'})
                msp.add_text("VOILE NOYAU", height=200, dxfattribs={'layer':'STR_VOILES','insert':(ox(r['x'])-900,oy(r['y']))})
        
        # Escaliers
        for r in service:
            if 'palier' in r['name'].lower():
                msp.add_lwpolyline([(ox(r['x'])-1200,oy(r['y'])-800),(ox(r['x'])+1200,oy(r['y'])-800),(ox(r['x'])+1200,oy(r['y'])+800),(ox(r['x'])-1200,oy(r['y'])+800),(ox(r['x'])-1200,oy(r['y'])-800)], dxfattribs={'layer':'STR_ESCALIERS'})
                msp.add_text("ESCALIER", height=200, dxfattribs={'layer':'STR_ESCALIERS','insert':(ox(r['x'])-1000,oy(r['y']))})
        
        # Semelles (sous-sol)
        if lkey == 'SOUS_SOL':
            for ax in rel_x:
                for ay in rel_y:
                    if xn-2000<ax<xx+2000 and yn-2000<ay<yx+2000:
                        h=750
                        msp.add_lwpolyline([(ox(ax)-h,oy(ay)-h),(ox(ax)+h,oy(ay)-h),(ox(ax)+h,oy(ay)+h),(ox(ax)-h,oy(ay)+h),(ox(ax)-h,oy(ay)-h)], dxfattribs={'layer':'STR_SEMELLES'})
        
        y_offset += dh + 15000
    
    dxf_path = f'{OUT}/LOT_STRUCTURE_COMPLET_Sakho.dxf'
    doc.saveas(dxf_path)
    print(f"  DXF: {dxf_path}")

# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("="*60)
    print("STRUCTURE COMPLÉMENTS — Résidence SAKHO")
    print("="*60)
    generate_ferraillage_dalles()
    generate_escaliers()
    generate_coupes()
    generate_nomenclature()
    generate_details()
    update_structure_dxf()
    print("\n"+"="*60)
    print("TERMINÉ")
    print("="*60)

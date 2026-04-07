"""
gen_schemas_mep_iso.py — Schemas de principe MEP Tijan AI

Produit un PDF professionnel avec 10 schemas blocs (un par lot) montrant les
composants principaux et leurs interactions. Mise en page soignee : grille
4 colonnes x 6 rangees, routage orthogonal des connecteurs avec trunk
fan-out, libelles sur fond blanc pour eviter tout chevauchement.
"""
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, PageBreak)
from reportlab.graphics.shapes import (Drawing, Rect, Circle, Line, String,
                                        Group, Polygon, PolyLine)

from tijan_theme import (VERT, VERT_DARK, VERT_LIGHT, NOIR, GRIS1, GRIS2, GRIS3,
                         BLANC, BLEU, BLEU_LT, ORANGE, ORANGE_LT, ROUGE,
                         ML, MR, CW, W, S, HeaderFooter,
                         p, fmt_n, section_title, table_style, _current_lang)


def _T(fr, en):
    return en if _current_lang == 'en' else fr


# ─────────────────────────────────────────────────────────────────────
#  Grille et constantes visuelles
# ─────────────────────────────────────────────────────────────────────
PAD      = 9 * mm
H_TITLE  = 11 * mm
CONTENT_W = 180   # mm
CONTENT_H = 130   # mm

# Colonnes (x en mm) et rangees (y en mm) pour des placements propres
# Largeurs de nodes typiques : 38mm pour corps, hauteurs 14-18mm
COL = {'A': 6, 'B': 52, 'C': 100, 'D': 148}
ROW = {'1': 108, '2': 90, '3': 72, '4': 54, '5': 36, '6': 18}

NODE_COLORS = {
    'power':   (colors.HexColor('#FFF1DC'), ORANGE),
    'water':   (colors.HexColor('#E4F1FB'), BLEU),
    'hvac':    (colors.HexColor('#E4F1FB'), VERT_DARK),
    'fire':    (colors.HexColor('#FEE8E4'), ROUGE),
    'low':     (colors.HexColor('#E8F4EA'), VERT),
    'gtb':     (colors.HexColor('#E8F4EA'), VERT_DARK),
    'neutral': (colors.HexColor('#F4F4F4'), colors.HexColor('#555555')),
}

SHADOW = colors.Color(0, 0, 0, alpha=0.10)


# ─────────────────────────────────────────────────────────────────────
#  Nodes
# ─────────────────────────────────────────────────────────────────────
def _node(x=0, y=0, w=38, h=16, id='', title='', sub='', color='neutral',
          col=None, row=None):
    if col is not None:
        x = COL[col]
    if row is not None:
        y = ROW[row]
    return {'id': id, 'x': x, 'y': y, 'w': w, 'h': h,
            'title': title, 'sub': sub, 'color': color}


def _node_rect(d, n):
    fill, stroke = NODE_COLORS.get(n.get('color', 'neutral'), NODE_COLORS['neutral'])
    x = PAD + n['x'] * mm
    y = PAD + n['y'] * mm
    w = n['w'] * mm
    h = n['h'] * mm
    # Drop shadow
    d.add(Rect(x + 0.8 * mm, y - 0.8 * mm, w, h, rx=2.5, ry=2.5,
               fillColor=SHADOW, strokeColor=None))
    # Body
    d.add(Rect(x, y, w, h, rx=2.5, ry=2.5,
               fillColor=fill, strokeColor=stroke, strokeWidth=1.3))
    title = n.get('title', '')
    sub = n.get('sub', '')
    cx = x + w / 2
    cy = y + h / 2
    if sub:
        d.add(String(cx, cy + 1.6, title,
                     fontName='Helvetica-Bold', fontSize=8.4,
                     textAnchor='middle', fillColor=NOIR))
        d.add(String(cx, cy - 7.0, sub,
                     fontName='Helvetica', fontSize=6.8,
                     textAnchor='middle', fillColor=colors.HexColor('#444444')))
    else:
        d.add(String(cx, cy - 2.5, title,
                     fontName='Helvetica-Bold', fontSize=8.6,
                     textAnchor='middle', fillColor=NOIR))


def _anchor(node, side):
    x = PAD + node['x'] * mm
    y = PAD + node['y'] * mm
    w = node['w'] * mm
    h = node['h'] * mm
    if side == 'r': return x + w, y + h / 2
    if side == 'l': return x, y + h / 2
    if side == 't': return x + w / 2, y + h
    if side == 'b': return x + w / 2, y
    return x + w / 2, y + h / 2


# ─────────────────────────────────────────────────────────────────────
#  Edges : routage orthogonal + fleche + label fond blanc
# ─────────────────────────────────────────────────────────────────────
def _arrow_head(d, x, y, dx, dy, color):
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    size = 2.6 * mm
    bx, by = x - ux * size, y - uy * size
    px, py = -uy * size * 0.55, ux * size * 0.55
    d.add(Polygon(points=[x, y, bx + px, by + py, bx - px, by - py],
                  fillColor=color, strokeColor=color, strokeWidth=0.4))


def _edge_label(d, lx, ly, text, color):
    if not text:
        return
    tw = len(text) * 3.2 + 5
    d.add(Rect(lx - tw / 2, ly - 4, tw, 8,
               fillColor=BLANC, strokeColor=None))
    d.add(String(lx, ly - 2, text,
                 fontName='Helvetica', fontSize=6.6,
                 textAnchor='middle', fillColor=color))


def _draw_edge(d, nodes_by_id, e):
    src = nodes_by_id[e['src']]
    dst = nodes_by_id[e['dst']]
    color = e.get('color') or colors.HexColor('#555555')
    style = e.get('style', 'solid')
    src_side = e.get('src_side', 'r')
    dst_side = e.get('dst_side', 'l')
    sx, sy = _anchor(src, src_side)
    dx, dy = _anchor(dst, dst_side)

    # Routage orthogonal
    midx_mm = e.get('midx_mm')
    midy_mm = e.get('midy_mm')
    label_pos = 'v'  # vertical segment by default

    if src_side in ('r', 'l') and dst_side in ('r', 'l'):
        if midx_mm is not None:
            mx = PAD + midx_mm * mm
        else:
            mx = (sx + dx) / 2
        pts = [sx, sy, mx, sy, mx, dy, dx, dy]
        last = (1 if dx >= mx else -1, 0)
        lab_x, lab_y = mx, (sy + dy) / 2
    elif src_side in ('t', 'b') and dst_side in ('t', 'b'):
        if midy_mm is not None:
            my = PAD + midy_mm * mm
        else:
            my = (sy + dy) / 2
        pts = [sx, sy, sx, my, dx, my, dx, dy]
        last = (0, 1 if dy >= my else -1)
        lab_x, lab_y = (sx + dx) / 2, my
    else:
        # Mixte (ex: b → l) : dog-leg en L simple
        pts = [sx, sy, dx, sy, dx, dy]
        last = (0, 1 if dy >= sy else -1)
        lab_x, lab_y = dx, (sy + dy) / 2

    if style == 'dashed':
        d.add(PolyLine(points=pts, strokeColor=color, strokeWidth=1.2,
                       strokeDashArray=[3, 2], strokeLineCap=1))
    else:
        d.add(PolyLine(points=pts, strokeColor=color, strokeWidth=1.5,
                       strokeLineCap=1))

    _arrow_head(d, dx, dy, last[0], last[1], color)
    _edge_label(d, lab_x, lab_y, e.get('label', ''), color)


# ─────────────────────────────────────────────────────────────────────
#  Diagramme
# ─────────────────────────────────────────────────────────────────────
def _make_diagram(title, nodes, edges, legend=None):
    W_pts = CONTENT_W * mm + 2 * PAD
    H_pts = CONTENT_H * mm + 2 * PAD + H_TITLE
    d = Drawing(W_pts, H_pts)
    # Fond carte + bordure douce
    d.add(Rect(PAD * 0.35, PAD * 0.35,
               W_pts - PAD * 0.7, H_pts - PAD * 0.7,
               rx=4, ry=4,
               fillColor=colors.HexColor('#FAFBFC'),
               strokeColor=GRIS2, strokeWidth=0.6))
    # Bandeau titre
    d.add(Rect(PAD * 0.35, H_pts - PAD * 0.35 - H_TITLE,
               W_pts - PAD * 0.7, H_TITLE,
               fillColor=colors.HexColor('#F0F5F1'),
               strokeColor=None))
    d.add(String(W_pts / 2, H_pts - PAD * 0.35 - H_TITLE + 3, title,
                 fontName='Helvetica-Bold', fontSize=10.5,
                 textAnchor='middle', fillColor=VERT_DARK))
    # Nodes
    nodes_by_id = {n['id']: n for n in nodes}
    for n in nodes:
        _node_rect(d, n)
    # Edges
    for e in edges:
        _draw_edge(d, nodes_by_id, e)
    # Legende optionnelle en bas
    if legend:
        ly = PAD + 2
        lx = PAD + 4
        for label, col in legend:
            d.add(Line(lx, ly + 2, lx + 10, ly + 2,
                       strokeColor=col, strokeWidth=1.6))
            d.add(String(lx + 13, ly, label,
                         fontName='Helvetica', fontSize=6.8, fillColor=NOIR))
            lx += 13 + len(label) * 3.3 + 10
    return d


# ─────────────────────────────────────────────────────────────────────
#  Helpers tables
# ─────────────────────────────────────────────────────────────────────
def _kv_table(rows):
    data = [[Paragraph(_T("Parametre", "Parameter"), S['th_l']),
             Paragraph(_T("Valeur", "Value"), S['th_l'])]] + [
        [p(k), p(v)] for k, v in rows
    ]
    t = Table(data, colWidths=[CW * 0.55, CW * 0.45])
    t.setStyle(table_style())
    return t


# ─────────────────────────────────────────────────────────────────────
#  1. ELECTRICITE
# ─────────────────────────────────────────────────────────────────────
def _diag_electricite(rm):
    e = rm.electrique
    nb = min(max(int(getattr(rm.params, 'nb_niveaux', 4)), 1), 6)
    ROWS_TD = ['1', '2', '3', '4', '5', '6'][:nb]
    nodes = [
        _node(id='tr',   col='A', row='2', title='TR',
              sub=f"{e.transfo_kva} kVA", color='power'),
        _node(id='gen',  col='A', row='4', title=_T('Groupe', 'Genset'),
              sub=f"{e.groupe_electrogene_kva} kVA", color='neutral'),
        _node(id='ats',  col='B', row='3', title='ATS',
              sub=_T('Inverseur', 'Transfer sw.'), color='neutral'),
        _node(id='tgbt', col='C', row='3', w=40, h=22, title='TGBT',
              sub=f"{e.puissance_totale_kva:.0f} kVA", color='low'),
    ]
    # Colonne montante = noeud vertical haut
    nodes.append(_node(id='col', x=154, y=ROW['5'], w=20, h=ROW['1'] + 16 - ROW['5'],
                       title=_T('Colonne', 'Riser'),
                       sub=f"{e.section_colonne_mm2} mm²", color='low'))
    for i, r in enumerate(ROWS_TD):
        nid = f'td{i}'
        # Decalage fin pour eviter superposition avec la colonne
        nodes.append(_node(id=nid, x=COL['D'] + 28, y=ROW[r], w=28, h=12,
                           title=f"TD N{i+1}", color='low'))
    edges = [
        {'src': 'tr',   'dst': 'ats',  'color': ORANGE, 'label': 'HTA/BT'},
        {'src': 'gen',  'dst': 'ats',  'color': NOIR,   'label': _T('Secours','Backup')},
        {'src': 'ats',  'dst': 'tgbt', 'color': ORANGE},
        {'src': 'tgbt', 'dst': 'col',  'color': NOIR,   'label': 'BT'},
    ]
    for i in range(nb):
        edges.append({'src': 'col', 'dst': f'td{i}', 'color': NOIR})
    return _make_diagram(
        _T("1. Electricite — Distribution principale",
           "1. Electrical — Main distribution"),
        nodes, edges,
        legend=[(_T('Energie','Power'), ORANGE),
                (_T('Liaison BT','LV link'), NOIR)])


# ─────────────────────────────────────────────────────────────────────
#  2. PLOMBERIE
# ─────────────────────────────────────────────────────────────────────
def _diag_plomberie(rm):
    pl = rm.plomberie
    nb = min(max(int(getattr(rm.params, 'nb_niveaux', 4)), 1), 6)
    ROWS_N = ['1', '2', '3', '4', '5', '6'][:nb]
    nodes = [
        _node(id='cit',  col='A', row='2', w=40, h=22,
              title=_T('Citerne', 'Tank'),
              sub=f"{pl.volume_citerne_m3:.0f} m³", color='water'),
        _node(id='pmp',  col='B', row='2', w=38, h=16,
              title=_T('Surpresseur', 'Booster'),
              sub=f"{pl.debit_surpresseur_m3h:.0f} m³/h", color='water'),
        _node(id='ces',  col='A', row='5', w=40, h=14,
              title='CESI',
              sub=f"{pl.nb_chauffe_eau_solaire} {_T('unites','units')}",
              color='fire'),
        _node(id='col',  x=100, y=ROW['5'], w=20, h=ROW['1'] + 16 - ROW['5'],
              title=_T('Colonne', 'Riser'),
              sub=f"DN{pl.diam_colonne_montante_mm}", color='water'),
        _node(id='ev',   col='B', row='6', w=38, h=12,
              title=_T('Evac. EU/EV', 'Drain stack'),
              sub='PVC DN100', color='neutral'),
    ]
    for i, r in enumerate(ROWS_N):
        nid = f'nv{i}'
        nodes.append(_node(id=nid, col='D', row=r, w=36, h=12,
                           title=f"N{i+1} — {_T('Nourrice','Manifold')}",
                           color='water'))
    edges = [
        {'src': 'cit', 'dst': 'pmp', 'color': BLEU, 'label': _T('Aspir.','Suct.')},
        {'src': 'pmp', 'dst': 'col', 'color': BLEU, 'label': _T('Refoul.','Disch.')},
        {'src': 'ces', 'dst': 'col', 'color': ORANGE, 'label': 'ECS'},
    ]
    for i in range(nb):
        edges.append({'src': 'col', 'dst': f'nv{i}', 'color': BLEU})
    edges.append({'src': 'col', 'dst': 'ev', 'color': GRIS3, 'style': 'dashed',
                  'label': _T('Evac.','Drain')})
    return _make_diagram(
        _T("2. Plomberie — Eau froide / ECS / Evacuation",
           "2. Plumbing — Cold water / DHW / Drainage"),
        nodes, edges,
        legend=[(_T('Eau froide','Cold water'), BLEU),
                ('ECS', ORANGE),
                (_T('Evacuation','Drainage'), GRIS3)])


# ─────────────────────────────────────────────────────────────────────
#  3. CLIMATISATION
# ─────────────────────────────────────────────────────────────────────
def _diag_clim(rm):
    c = rm.cvc
    nodes = [
        _node(id='ue',  col='A', row='2', w=40, h=20,
              title=_T('Unites Ext.', 'Outdoor'),
              sub=f"{c.puissance_frigorifique_kw:.0f} kW", color='hvac'),
        _node(id='lf',  col='B', row='2', w=38, h=16,
              title=_T('Liaisons frigo', 'Refrig. lines'),
              sub=_T('Cuivre isole','Insul. copper'), color='neutral'),
        _node(id='sj',  col='C', row='1', w=40, h=14,
              title=_T('Splits sejour', 'Living splits'),
              sub=f"× {c.nb_splits_sejour}", color='hvac'),
        _node(id='ch',  col='C', row='3', w=40, h=14,
              title=_T('Splits chambre', 'Bedroom splits'),
              sub=f"× {c.nb_splits_chambre}", color='hvac'),
        _node(id='cas', col='C', row='5', w=40, h=14,
              title=_T('Cassettes', 'Cassettes'),
              sub=f"× {c.nb_cassettes}", color='hvac'),
        _node(id='cnd', col='D', row='5', w=40, h=14,
              title=_T('Condensats', 'Condensate'),
              sub='PVC DN32', color='water'),
    ]
    edges = [
        {'src': 'ue', 'dst': 'lf', 'color': BLEU},
        {'src': 'lf', 'dst': 'sj', 'color': BLEU, 'label': 'R410A'},
        {'src': 'lf', 'dst': 'ch', 'color': BLEU, 'label': 'R410A'},
        {'src': 'lf', 'dst': 'cas','color': BLEU, 'label': 'R410A'},
        {'src': 'sj', 'dst': 'cnd','color': GRIS3, 'style': 'dashed'},
        {'src': 'ch', 'dst': 'cnd','color': GRIS3, 'style': 'dashed'},
        {'src': 'cas','dst': 'cnd','color': GRIS3, 'style': 'dashed'},
    ]
    return _make_diagram(
        _T("3. Climatisation — Detente directe DRV",
           "3. HVAC — VRF direct expansion"),
        nodes, edges,
        legend=[(_T('Frigo','Refrig.'), BLEU),
                (_T('Condensats','Condensate'), GRIS3)])


# ─────────────────────────────────────────────────────────────────────
#  4. VENTILATION
# ─────────────────────────────────────────────────────────────────────
def _diag_vent(rm):
    c = rm.cvc
    nodes = [
        _node(id='vmc', col='A', row='2', w=40, h=18,
              title=f"VMC {c.type_vmc}",
              sub=f"× {c.nb_vmc} {_T('caissons','units')}", color='hvac'),
        _node(id='gp',  col='B', row='2', w=38, h=16,
              title=_T('Gaines princ.', 'Main ducts'),
              sub=_T('Galva isolee','Insul. galv.'), color='neutral'),
        _node(id='cuis',col='C', row='1', w=40, h=14,
              title=_T('Bouches cuisine', 'Kitchen vents'),
              color='hvac'),
        _node(id='sdb', col='C', row='3', w=40, h=14,
              title=_T('Bouches SdB/WC', 'Bath/WC vents'),
              color='hvac'),
        _node(id='amen',col='C', row='5', w=40, h=14,
              title=_T('Entree air neuf', 'Fresh air'),
              color='hvac'),
        _node(id='rej', col='D', row='5', w=40, h=14,
              title=_T('Rejet toiture', 'Roof exhaust'),
              color='neutral'),
    ]
    edges = [
        {'src': 'vmc', 'dst': 'gp',  'color': BLEU},
        {'src': 'gp',  'dst': 'cuis','color': BLEU, 'label': _T('Extr.','Exh.')},
        {'src': 'gp',  'dst': 'sdb', 'color': BLEU, 'label': _T('Extr.','Exh.')},
        {'src': 'amen','dst': 'gp',  'color': VERT, 'label': _T('Air neuf','Fresh')},
        {'src': 'gp',  'dst': 'rej', 'color': GRIS3, 'style': 'dashed',
         'label': _T('Rejet','Exhaust')},
    ]
    return _make_diagram(
        _T("4. Ventilation — Schema aeraulique",
           "4. Ventilation — Air-flow schematic"),
        nodes, edges,
        legend=[(_T('Extraction','Exhaust'), BLEU),
                (_T('Air neuf','Fresh air'), VERT),
                (_T('Rejet','Discharge'), GRIS3)])


# ─────────────────────────────────────────────────────────────────────
#  5. CCTV
# ─────────────────────────────────────────────────────────────────────
def _diag_cctv(rm):
    cf = rm.courants_faibles
    nodes = [
        _node(id='nvr', col='A', row='2', w=40, h=20,
              title='NVR', sub=_T('Enregistreur','Recorder'), color='low'),
        _node(id='sw',  col='B', row='2', w=38, h=18,
              title='Switch PoE',
              sub=f"{cf.nb_cameras_int + cf.nb_cameras_ext} ports", color='low'),
        _node(id='cint',col='C', row='1', w=40, h=14,
              title=_T('Cameras int.', 'Indoor cams'),
              sub=f"× {cf.nb_cameras_int}", color='low'),
        _node(id='cext',col='C', row='3', w=40, h=14,
              title=_T('Cameras ext.', 'Outdoor cams'),
              sub=f"× {cf.nb_cameras_ext}", color='low'),
        _node(id='mon', col='A', row='5', w=40, h=14,
              title=_T('Poste super.', 'Workstation'),
              sub='HDMI', color='neutral'),
    ]
    edges = [
        {'src': 'nvr', 'dst': 'sw',  'color': VERT_DARK, 'label': 'LAN'},
        {'src': 'sw',  'dst': 'cint','color': VERT_DARK, 'label': 'PoE'},
        {'src': 'sw',  'dst': 'cext','color': VERT_DARK, 'label': 'PoE'},
        {'src': 'nvr', 'dst': 'mon', 'color': NOIR,       'label': 'HDMI'},
    ]
    return _make_diagram(
        _T("5. CCTV — Videosurveillance IP",
           "5. CCTV — IP video surveillance"),
        nodes, edges,
        legend=[('LAN/PoE', VERT_DARK), ('HDMI', NOIR)])


# ─────────────────────────────────────────────────────────────────────
#  6. SONORISATION
# ─────────────────────────────────────────────────────────────────────
def _diag_sono(rm):
    nodes = [
        _node(id='src', col='A', row='2', w=40, h=16,
              title=_T('Sources', 'Sources'), sub='Mic / BGM', color='low'),
        _node(id='cons',col='B', row='2', w=38, h=16,
              title=_T('Console', 'Mixer'), color='low'),
        _node(id='amp', col='C', row='2', w=40, h=16,
              title=_T('Ampli matrice', 'Matrix amp'),
              sub='100V', color='low'),
        _node(id='z1',  col='D', row='1', w=40, h=12,
              title=_T('Zone hall', 'Lobby'), color='low'),
        _node(id='z2',  col='D', row='3', w=40, h=12,
              title=_T('Zone couloirs', 'Corridors'), color='low'),
        _node(id='z3',  col='D', row='5', w=40, h=12,
              title=_T('Zone parking', 'Parking'), color='low'),
    ]
    edges = [
        {'src': 'src', 'dst': 'cons','color': VERT_DARK, 'label': 'XLR'},
        {'src': 'cons','dst': 'amp', 'color': VERT_DARK},
        {'src': 'amp', 'dst': 'z1',  'color': VERT_DARK, 'label': '100V'},
        {'src': 'amp', 'dst': 'z2',  'color': VERT_DARK, 'label': '100V'},
        {'src': 'amp', 'dst': 'z3',  'color': VERT_DARK, 'label': '100V'},
    ]
    return _make_diagram(
        _T("6. Sonorisation — Diffusion 100V multi-zones",
           "6. PA system — 100V multi-zone"),
        nodes, edges,
        legend=[(_T('Signal audio','Audio'), VERT_DARK)])


# ─────────────────────────────────────────────────────────────────────
#  7. DETECTION INCENDIE
# ─────────────────────────────────────────────────────────────────────
def _diag_di(rm):
    si = rm.securite_incendie
    nodes = [
        _node(id='ecs', col='B', row='3', w=40, h=22,
              title='ECS', sub=f"{si.centrale_zones} {_T('zones','zones')}",
              color='fire'),
        _node(id='det', col='A', row='1', w=44, h=14,
              title=_T('Detecteurs fumee', 'Smoke det.'),
              sub=f"× {si.nb_detecteurs_fumee}", color='fire'),
        _node(id='dm',  col='A', row='3', w=44, h=14,
              title=_T('Decl. manuels', 'Manual CP'),
              sub=f"× {si.nb_declencheurs_manuels}", color='fire'),
        _node(id='sir', col='C', row='1', w=44, h=14,
              title=_T('Sirenes UGA', 'Sounders UGA'),
              sub=f"× {si.nb_sirenes}", color='fire'),
        _node(id='des', col='C', row='3', w=44, h=14,
              title=_T('Desenfumage', 'Smoke extr.'),
              sub=_T('Requis','Required') if si.desenfumage_requis
                  else _T('Non requis','Not req.'),
              color='fire'),
        _node(id='gtb', col='C', row='5', w=44, h=14,
              title=_T('Report GTB', 'BMS report'),
              sub='TCP/IP', color='gtb'),
    ]
    edges = [
        {'src': 'det', 'dst': 'ecs', 'color': ROUGE},
        {'src': 'dm',  'dst': 'ecs', 'color': ROUGE},
        {'src': 'ecs', 'dst': 'sir', 'color': ROUGE, 'label': 'UGA'},
        {'src': 'ecs', 'dst': 'des', 'color': ROUGE, 'label': _T('Cmd','Cmd')},
        {'src': 'ecs', 'dst': 'gtb', 'color': VERT_DARK, 'style': 'dashed'},
    ]
    return _make_diagram(
        _T("7. Detection incendie — SSI categorie A",
           "7. Fire detection — SSI Cat. A"),
        nodes, edges,
        legend=[(_T('Boucle SSI','Fire loop'), ROUGE),
                (_T('Report GTB','BMS report'), VERT_DARK)])


# ─────────────────────────────────────────────────────────────────────
#  8. EXTINCTION INCENDIE
# ─────────────────────────────────────────────────────────────────────
def _diag_ext(rm):
    si = rm.securite_incendie
    nodes = [
        _node(id='bac', col='A', row='2', w=40, h=20,
              title=_T('Bache feu', 'Fire tank'),
              sub='120 m³', color='water'),
        _node(id='pmp', col='B', row='2', w=38, h=16,
              title=_T('Pompe incendie', 'Fire pump'),
              sub=_T('Diesel + Elec','Diesel + Elec'), color='fire'),
        _node(id='cs',  x=100, y=ROW['5'], w=22, h=ROW['1'] + 18 - ROW['5'],
              title=_T('Colonne', 'Riser'),
              sub=_T('seche','dry'), color='fire'),
        _node(id='ria', col='D', row='1', w=40, h=14,
              title='RIA', sub=f"{si.longueur_ria_ml:.0f} ml", color='fire'),
        _node(id='spr', col='D', row='3', w=40, h=14,
              title=_T('Sprinklers', 'Sprinklers'),
              sub=f"× {si.nb_tetes_sprinkler}", color='fire'),
        _node(id='ext', col='D', row='5', w=40, h=14,
              title=_T('Extincteurs', 'Extinguishers'),
              sub=f"CO2 {si.nb_extincteurs_co2} / P {si.nb_extincteurs_poudre}",
              color='fire'),
    ]
    edges = [
        {'src': 'bac', 'dst': 'pmp', 'color': BLEU, 'label': _T('Aspir.','Suct.')},
        {'src': 'pmp', 'dst': 'cs',  'color': BLEU, 'label': _T('Refoul.','Disch.')},
        {'src': 'cs',  'dst': 'ria', 'color': BLEU},
        {'src': 'cs',  'dst': 'spr', 'color': BLEU},
    ]
    return _make_diagram(
        _T("8. Extinction incendie — RIA + Colonne seche + Sprinklers",
           "8. Fire suppression — Hose reels + Dry riser + Sprinklers"),
        nodes, edges,
        legend=[(_T('Eau sous pression','Pressurized water'), BLEU)])


# ─────────────────────────────────────────────────────────────────────
#  9. CONTROLE D'ACCES + INTERPHONE
# ─────────────────────────────────────────────────────────────────────
def _diag_acc(rm):
    cf = rm.courants_faibles
    nodes = [
        _node(id='ctrl',col='A', row='2', w=40, h=20,
              title=_T('Controleur', 'Controller'),
              sub='IP', color='low'),
        _node(id='lec', col='C', row='1', w=44, h=14,
              title=_T('Lecteurs badge', 'Card readers'),
              sub=f"× {cf.nb_portes_controle_acces}", color='low'),
        _node(id='ven', col='C', row='3', w=44, h=14,
              title=_T('Ventouses/gaches', 'Locks/strikes'),
              sub='24V', color='low'),
        _node(id='bds', col='C', row='5', w=44, h=14,
              title=_T('Boutons sortie', 'Exit buttons'),
              color='low'),
        _node(id='int', col='D', row='2', w=40, h=14,
              title=_T('Interphones', 'Intercoms'),
              sub=f"× {cf.nb_interphones}", color='low'),
        _node(id='gtb', col='A', row='5', w=40, h=14,
              title='GTB',
              sub=_T('Supervision','Supervision'), color='gtb'),
    ]
    edges = [
        {'src': 'ctrl','dst': 'lec', 'color': VERT_DARK, 'label': 'OSDP'},
        {'src': 'ctrl','dst': 'ven', 'color': NOIR,       'label': '24V'},
        {'src': 'ctrl','dst': 'bds', 'color': NOIR},
        {'src': 'ctrl','dst': 'int', 'color': VERT_DARK, 'label': 'SIP',
         'midx_mm': 140},
        {'src': 'ctrl','dst': 'gtb', 'color': VERT_DARK, 'style': 'dashed',
         'label': 'BACnet'},
    ]
    return _make_diagram(
        _T("9. Controle d'acces / Interphone",
           "9. Access control / Intercom"),
        nodes, edges,
        legend=[(_T('Bus IP','IP bus'), VERT_DARK),
                (_T('24V','24V'), NOIR)])


# ─────────────────────────────────────────────────────────────────────
#  10. GTB / BMS
# ─────────────────────────────────────────────────────────────────────
def _diag_gtb(rm):
    a = rm.automatisation
    nodes = [
        _node(id='sup', x=72, y=ROW['1'], w=44, h=16,
              title=_T('Superviseur', 'Supervisor'),
              sub=a.protocole, color='gtb'),
        _node(id='bus', x=26, y=ROW['3'], w=136, h=12,
              title=_T('Bus terrain', 'Field bus'),
              sub=f"{a.nb_points_controle} pts", color='gtb'),
        # Consommateurs en bas, repartis
        _node(id='ele', x=6,  y=ROW['5'], w=36, h=14,
              title=_T('Eclairage','Lighting'), color='low'),
        _node(id='cvc', x=48, y=ROW['5'], w=36, h=14,
              title='CVC', color='hvac'),
        _node(id='ene', x=90, y=ROW['5'], w=36, h=14,
              title=_T('Energie','Energy'), color='power'),
        _node(id='inc', x=6,  y=ROW['6'] - 16, w=36, h=14,
              title='SSI', color='fire'),
        _node(id='acc', x=48, y=ROW['6'] - 16, w=36, h=14,
              title=_T('Acces','Access'), color='low'),
        _node(id='asc', x=90, y=ROW['6'] - 16, w=36, h=14,
              title=_T('Ascenseurs','Lifts'), color='neutral'),
    ]
    edges = [
        {'src': 'sup', 'dst': 'bus',
         'src_side': 'b', 'dst_side': 't'},
        {'src': 'bus', 'dst': 'ele', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK},
        {'src': 'bus', 'dst': 'cvc', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK},
        {'src': 'bus', 'dst': 'ene', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK},
        {'src': 'bus', 'dst': 'inc', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK, 'style': 'dashed'},
        {'src': 'bus', 'dst': 'acc', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK, 'style': 'dashed'},
        {'src': 'bus', 'dst': 'asc', 'src_side': 'b', 'dst_side': 't',
         'color': VERT_DARK, 'style': 'dashed'},
    ]
    return _make_diagram(
        _T("10. GTB / BMS — Supervision centrale",
           "10. BMS — Central supervision"),
        nodes, edges,
        legend=[(_T('Bus GTB','BMS bus'), VERT_DARK)])


# ─────────────────────────────────────────────────────────────────────
#  Tables recap par lot
# ─────────────────────────────────────────────────────────────────────
def _t_elec(rm):
    e = rm.electrique
    return _kv_table([
        (_T("Puissance totale", "Total power"), f"{e.puissance_totale_kva:.0f} kVA"),
        (_T("Transformateur", "Transformer"), f"{e.transfo_kva} kVA"),
        (_T("Groupe electrogene", "Backup genset"), f"{e.groupe_electrogene_kva} kVA"),
        (_T("Compteurs", "Meters"), f"{e.nb_compteurs}"),
        (_T("Section colonne", "Riser section"), f"{e.section_colonne_mm2} mm²"),
    ])

def _t_plomb(rm):
    pl = rm.plomberie
    return _kv_table([
        (_T("Logements", "Apartments"), f"{pl.nb_logements}"),
        (_T("Besoin", "Demand"), f"{pl.besoin_total_m3_j:.1f} m³/j"),
        (_T("Citerne", "Tank"), f"{pl.volume_citerne_m3:.0f} m³"),
        (_T("Surpresseur", "Booster"), f"{pl.debit_surpresseur_m3h:.0f} m³/h"),
        (_T("Colonne", "Riser"), f"DN{pl.diam_colonne_montante_mm}"),
        ("CESI", f"{pl.nb_chauffe_eau_solaire}"),
    ])

def _t_clim(rm):
    c = rm.cvc
    return _kv_table([
        (_T("Puissance frigo", "Cooling power"), f"{c.puissance_frigorifique_kw:.0f} kW"),
        (_T("Splits sejour", "Living units"), f"{c.nb_splits_sejour}"),
        (_T("Splits chambre", "Bedroom units"), f"{c.nb_splits_chambre}"),
        (_T("Cassettes", "Cassettes"), f"{c.nb_cassettes}"),
    ])

def _t_vent(rm):
    c = rm.cvc
    return _kv_table([
        (_T("Type VMC", "MVHR type"), c.type_vmc),
        (_T("Caissons VMC", "Units"), f"{c.nb_vmc}"),
    ])

def _t_cf(rm):
    cf = rm.courants_faibles
    return _kv_table([
        (_T("Cameras int.", "Indoor cams"), f"{cf.nb_cameras_int}"),
        (_T("Cameras ext.", "Outdoor cams"), f"{cf.nb_cameras_ext}"),
        (_T("Prises RJ45", "RJ45 ports"), f"{cf.nb_prises_rj45}"),
        (_T("Baies serveur", "Server racks"), f"{cf.baies_serveur}"),
    ])

def _t_si(rm):
    si = rm.securite_incendie
    return _kv_table([
        (_T("Categorie ERP", "ERP category"), si.categorie_erp),
        (_T("Detecteurs fumee", "Smoke detectors"), f"{si.nb_detecteurs_fumee}"),
        (_T("Decl. manuels", "Manual call pts"), f"{si.nb_declencheurs_manuels}"),
        (_T("Sirenes", "Sounders"), f"{si.nb_sirenes}"),
        (_T("RIA", "Hose reels"), f"{si.longueur_ria_ml:.0f} ml"),
        (_T("Sprinklers", "Sprinklers"), f"{si.nb_tetes_sprinkler}"),
    ])

def _t_acc(rm):
    cf = rm.courants_faibles
    return _kv_table([
        (_T("Portes contr. acces", "Access doors"), f"{cf.nb_portes_controle_acces}"),
        (_T("Interphones", "Intercoms"), f"{cf.nb_interphones}"),
    ])

def _t_gtb(rm):
    a = rm.automatisation
    return _kv_table([
        (_T("Niveau", "Level"), a.niveau),
        (_T("Protocole", "Protocol"), a.protocole),
        (_T("Points", "Points"), f"{a.nb_points_controle}"),
        ('BMS', _T("Requis","Required") if a.bms_requis else _T("Optionnel","Optional")),
    ])


# ─────────────────────────────────────────────────────────────────────
#  Entree principale
# ─────────────────────────────────────────────────────────────────────
def _section(story, num, title_fr, title_en, table, drawing,
             caption_fr, caption_en, last=False):
    story.extend(section_title(num, _T(title_fr, title_en)))
    story.append(table)
    story.append(Spacer(1, 3 * mm))
    story.append(drawing)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(_T(caption_fr, caption_en), S['body_j']))
    if not last:
        story.append(PageBreak())


def generer_schemas_mep_iso(rm, params: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=ML, rightMargin=MR,
                            topMargin=22 * mm, bottomMargin=18 * mm,
                            title=_T("Schemas de principe MEP",
                                     "MEP Schematic Diagrams"),
                            author='Tijan AI')

    project_name = params.get('nom') or _T("Projet", "Project")
    ville = params.get('ville') or 'Dakar'
    pays = params.get('pays') or 'Senegal'
    sub = f"{project_name} — {ville}, {pays}"

    story = []
    story.append(Paragraph(
        _T("Schemas de principe MEP", "MEP Schematic Diagrams"),
        S['titre']))
    story.append(Paragraph(sub, S['sous_titre']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(_T(
        "Schemas blocs detailles pour les 10 lots techniques. Chaque diagramme "
        "presente les composants principaux et leurs interactions, avec les "
        "valeurs issues du moteur MEP Tijan AI.",
        "Detailed block diagrams for the 10 technical packages. Each diagram "
        "shows the main components and their interactions, with values produced "
        "by the Tijan AI MEP engine."),
        S['body_j']))
    story.append(Spacer(1, 4 * mm))

    sections = [
        ('1', 'Electricite', 'Electrical', _t_elec(rm), _diag_electricite(rm),
         "Distribution principale TR + Genset via inverseur de source vers TGBT, "
         "puis colonne montante BT alimentant les tableaux divisionnaires d'etage.",
         "Main distribution TR + Genset via ATS to MSB, then LV riser feeding "
         "floor distribution boards."),
        ('2', 'Plomberie', 'Plumbing', _t_plomb(rm), _diag_plomberie(rm),
         "Aspiration depuis citerne, surpresseur, colonne montante DN dimensionnee, "
         "nourrices d'etage et evacuation EU/EV en colonne separee.",
         "Suction from tank, booster pump, sized DN riser, floor manifolds and "
         "separate WW/SW drainage stack."),
        ('3', 'Climatisation', 'HVAC', _t_clim(rm), _diag_clim(rm),
         "Systeme detente directe DRV : unites exterieures en toiture, liaisons "
         "frigorifiques cuivre, unites interieures par espace, evacuation condensats.",
         "VRF direct expansion system: rooftop outdoor units, copper refrigerant "
         "lines, indoor units per space, condensate drainage."),
        ('4', 'Ventilation', 'Ventilation', _t_vent(rm), _diag_vent(rm),
         "Caissons VMC, gaines galva isolees, bouches d'extraction cuisine et SdB, "
         "entrees d'air neuf et rejet en toiture.",
         "MVHR units, insulated galvanized ducts, kitchen and bath exhaust grilles, "
         "fresh air inlets and roof exhaust."),
        ('5', 'CCTV', 'CCTV', _t_cf(rm), _diag_cctv(rm),
         "Architecture IP : NVR central, switch PoE alimentant les cameras int. et "
         "ext., poste de supervision.",
         "IP architecture: central NVR, PoE switch feeding indoor and outdoor cams, "
         "supervision workstation."),
        ('6', 'Sonorisation', 'PA system',
         _kv_table([(_T("Architecture","Architecture"),"100V multi-zones"),
                    (_T("Source","Source"),"BGM + Mic")]),
         _diag_sono(rm),
         "Architecture 100V multi-zones : sources audio, console, ampli matrice, "
         "zones HP independantes (hall, couloirs, parking).",
         "100V multi-zone architecture: audio sources, mixer, matrix amplifier, "
         "independent speaker zones (lobby, corridors, parking)."),
        ('7', 'Detection incendie', 'Fire detection', _t_si(rm), _diag_di(rm),
         "Centrale ECS, detecteurs fumee adressables, declencheurs manuels, "
         "sirenes UGA, commande desenfumage et report d'alarmes vers GTB.",
         "Addressable FACP, smoke detectors, manual call points, UGA sounders, "
         "smoke extraction command and BMS alarm reporting."),
        ('8', 'Extinction incendie', 'Fire suppression', _t_si(rm), _diag_ext(rm),
         "Bache feu, pompe incendie diesel + electrique, colonne seche, RIA, "
         "sprinklers et extincteurs portatifs CO2 / poudre.",
         "Fire tank, diesel + electric fire pump, dry riser, hose reels, sprinklers "
         "and portable CO2 / powder extinguishers."),
        ('9', "Controle d'acces / Interphone", 'Access / Intercom',
         _t_acc(rm), _diag_acc(rm),
         "Controleur IP, lecteurs badge OSDP, ventouses 24V, boutons de sortie, "
         "interphones SIP et report GTB en BACnet.",
         "IP controller, OSDP card readers, 24V mag locks, exit buttons, SIP "
         "intercoms and BMS reporting over BACnet."),
        ('10', 'GTB / BMS', 'BMS', _t_gtb(rm), _diag_gtb(rm),
         "Superviseur central, bus terrain, automates par lot. Interconnexion avec "
         "tous les autres lots (eclairage, CVC, energie, SSI, acces, ascenseurs).",
         "Central supervisor, field bus, package controllers. Interconnection with "
         "all other packages (lighting, HVAC, energy, fire, access, lifts)."),
    ]

    for i, (num, tfr, ten, tab, drw, cfr, cen) in enumerate(sections):
        _section(story, num, tfr, ten, tab, drw, cfr, cen,
                 last=(i == len(sections) - 1))

    hf = HeaderFooter(project_name,
                      _T("Schemas de principe MEP", "MEP Schematic Diagrams"))
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    pdf = buf.getvalue()
    buf.close()
    return pdf

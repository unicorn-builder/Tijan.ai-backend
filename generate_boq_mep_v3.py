"""
generate_boq_mep_v3.py — BOQ MEP & Automation
Tijan AI — 3 niveaux : Basic / High-End / Luxury
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from datetime import datetime
import io

NOIR = colors.HexColor("#111111"); GRIS = colors.HexColor("#888888")
GRIS_CLAIR = colors.HexColor("#E5E5E5"); FOND = colors.HexColor("#FAFAFA")
BLANC = colors.white; VERT = colors.HexColor("#43A956"); VERT_PALE = colors.HexColor("#F0FAF1")

def gs():
    return {
        'brand': ParagraphStyle('b', fontSize=8, textColor=VERT, fontName='Helvetica-Bold', spaceAfter=2),
        'title': ParagraphStyle('t', fontSize=16, textColor=NOIR, fontName='Helvetica-Bold', spaceAfter=4),
        'sub':   ParagraphStyle('s', fontSize=9, textColor=GRIS, spaceAfter=8),
        'h2':    ParagraphStyle('h2', fontSize=11, textColor=VERT, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5),
        'h3':    ParagraphStyle('h3', fontSize=9, textColor=NOIR, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3),
        'small': ParagraphStyle('sm', fontSize=7.5, textColor=GRIS, spaceAfter=2),
        'disc':  ParagraphStyle('d', fontSize=7, textColor=GRIS, spaceAfter=2),
    }

def hf(canvas, doc, nom, date_str):
    canvas.saveState(); w, h = A4
    canvas.setFillColor(VERT); canvas.setFont('Helvetica-Bold', 8); canvas.drawString(15*mm, h-12*mm, "TIJAN AI")
    canvas.setFillColor(GRIS); canvas.setFont('Helvetica', 7.5)
    canvas.drawString(15*mm, h-17*mm, f"{nom}  —  BOQ MEP & Automation — 3 Niveaux de Gamme")
    canvas.setStrokeColor(GRIS_CLAIR); canvas.line(15*mm, h-19*mm, w-15*mm, h-19*mm)
    canvas.line(15*mm, 14*mm, w-15*mm, 14*mm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(15*mm, 10*mm, f"Tijan AI — {date_str} | Prix indicatifs marche Dakar. Verifier avant usage contractuel.")
    canvas.drawRightString(w-15*mm, 10*mm, f"Page {doc.page}"); canvas.restoreState()

def lot_t(data, cw):
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),VERT),('TEXTCOLOR',(0,0),(-1,0),BLANC),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
        ('GRID',(0,0),(-1,-1),0.3,GRIS_CLAIR),('ROWBACKGROUNDS',(0,1),(-1,-1),[BLANC,FOND]),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),5),('ALIGN',(2,0),(-1,-1),'RIGHT'),
    ]))
    return t

def generer_boq_mep(resultats, buf, params_dict=None):
    params = {}
    if params_dict:
        params = vars(params_dict) if hasattr(params_dict, '__dict__') else params_dict

    date_str = datetime.now().strftime("%d/%m/%Y")
    nom = params.get('nom', 'Projet Tijan')
    ville = params.get('ville', 'Dakar').capitalize()
    nb_niveaux = params.get('nb_niveaux', 5)
    surface_emprise = params.get('surface_emprise_m2', 500)
    surface_totale = surface_emprise * nb_niveaux
    nb_logements = max(1, int(surface_totale / 120))

    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=25*mm, bottomMargin=20*mm, title=f"BOQ MEP — {nom}", author="Tijan AI")
    def _hf(c,d): hf(c,d,nom,date_str)
    st = gs(); story = []

    # Page de garde
    story.append(Spacer(1,10*mm))
    story.append(Paragraph("TIJAN AI", st['brand']))
    story.append(Paragraph("BOQ MEP & AUTOMATION — 3 NIVEAUX DE GAMME", st['title']))
    story.append(Paragraph("Basic | High-End | Luxury — Electricite | Plomberie | CVC | Domotique", st['sub']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=VERT))
    story.append(Spacer(1,6*mm))

    entete = [["Projet",nom],["Localisation",f"{ville}, Senegal"],
              ["Description",f"R+{nb_niveaux-1} — {nb_niveaux} niveaux"],
              ["Surface totale",f"{surface_totale:,} m²"],["Logements estimes",str(nb_logements)],["Date",date_str]]
    t = Table(entete, colWidths=[50*mm,125*mm])
    t.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),9),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('TEXTCOLOR',(0,0),(0,-1),VERT),('GRID',(0,0),(-1,-1),0.3,GRIS_CLAIR),
        ('BACKGROUND',(0,0),(-1,-1),FOND),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)]))
    story.append(t); story.append(PageBreak())

    # LOT ELECTRICITE
    story.append(Paragraph("ELECTRICITE", st['h2']))
    story.append(HRFlowable(width="100%",thickness=0.5,color=GRIS_CLAIR))
    elec = [
        ["Ref","Designation","U","Qte","Prix BASIC","Total BASIC","Prix H-END","Total H-END","Prix LUXURY","Total LUXURY"],
        ["EL-01",f"Transformateur HTA/BT {int((nb_logements*8*0.65+nb_logements*3*0.7+60+50)*1.2/100)*100} kVA","u","1","45 000 000",f"{45000000:,}","55 000 000",f"{55000000:,}","85 000 000",f"{85000000:,}"],
        ["EL-02",f"Groupe electrogene secours","u","1","28 000 000",f"{28000000:,}","38 000 000",f"{38000000:,}","52 000 000",f"{52000000:,}"],
        ["EL-03","TGBT 4000A — 22 departs","u","1","12 500 000",f"{12500000:,}","16 000 000",f"{16000000:,}","22 000 000",f"{22000000:,}"],
        ["EL-04",f"Tableaux divisionnaires par niveau ({nb_niveaux} niveaux)","u",str(nb_niveaux),"850 000",f"{850000*nb_niveaux:,}","1 200 000",f"{1200000*nb_niveaux:,}","1 800 000",f"{1800000*nb_niveaux:,}"],
        ["EL-05",f"Tableaux logements ({nb_logements} logements)","u",str(nb_logements),"180 000",f"{180000*nb_logements:,}","280 000",f"{280000*nb_logements:,}","420 000",f"{420000*nb_logements:,}"],
        ["EL-06","Cable U1000 R2V 3x185mm² (colonne montante)","ml",str(nb_niveaux*30),"45 000",f"{45000*nb_niveaux*30:,}","45 000",f"{45000*nb_niveaux*30:,}","45 000",f"{45000*nb_niveaux*30:,}"],
        ["EL-07","Cablage distribution NYM-J 3x2.5 a 3x6mm²","ml",str(nb_logements*150),"850",f"{850*nb_logements*150:,}","1 200",f"{1200*nb_logements*150:,}","1 800",f"{1800*nb_logements*150:,}"],
        ["EL-08","Eclairage communs (luminaires LED)","u",str(nb_niveaux*20),"35 000",f"{35000*nb_niveaux*20:,}","65 000",f"{65000*nb_niveaux*20:,}","120 000",f"{120000*nb_niveaux*20:,}"],
        ["EL-09",f"Eclairage logements","ens",str(nb_logements),"450 000",f"{450000*nb_logements:,}","850 000",f"{850000*nb_logements:,}","1 800 000",f"{1800000*nb_logements:,}"],
        ["EL-10","BAES + signalisation securite","u",str(nb_niveaux*10),"45 000",f"{45000*nb_niveaux*10:,}","65 000",f"{65000*nb_niveaux*10:,}","95 000",f"{95000*nb_niveaux*10:,}"],
        ["EL-11","Paratonnerre ESE + mise a la terre","ens","1","2 500 000","2 500 000","3 500 000","3 500 000","5 000 000","5 000 000"],
        ["EL-12",f"Compteurs divisionnaires par logement","u",str(nb_logements),"180 000",f"{180000*nb_logements:,}","250 000",f"{250000*nb_logements:,}","380 000",f"{380000*nb_logements:,}"],
    ]
    story.append(lot_t(elec, [12*mm,55*mm,8*mm,10*mm,18*mm,20*mm,18*mm,20*mm,18*mm,20*mm]))
    story.append(PageBreak())

    # LOT PLOMBERIE
    story.append(Paragraph("PLOMBERIE", st['h2']))
    story.append(HRFlowable(width="100%",thickness=0.5,color=GRIS_CLAIR))
    plomb = [
        ["Ref","Designation","U","Qte","Prix BASIC","Total BASIC","Prix H-END","Total H-END","Prix LUXURY","Total LUXURY"],
        ["PL-01","Citerne enterree 50m³ beton etanche","u","1","8 500 000","8 500 000","8 500 000","8 500 000","12 000 000","12 000 000"],
        ["PL-02","Bache incendie 12m³ acier inox","u","1","4 500 000","4 500 000","6 500 000","6 500 000","9 000 000","9 000 000"],
        ["PL-03","Groupe surpresseur 2 pompes 6m³/h","u","1","3 200 000","3 200 000","4 500 000","4 500 000","7 500 000","7 500 000"],
        ["PL-04","Pompe incendie principale + secours","ens","1","4 800 000","4 800 000","6 500 000","6 500 000","9 500 000","9 500 000"],
        ["PL-05","Colonne montante EF DN63 acier galva","ml",str(nb_niveaux*3),"18 000",f"{18000*nb_niveaux*3:,}","22 000",f"{22000*nb_niveaux*3:,}","28 000",f"{28000*nb_niveaux*3:,}"],
        ["PL-06","Colonne montante ECS DN40 cuivre","ml",str(nb_niveaux*3),"28 000",f"{28000*nb_niveaux*3:,}","35 000",f"{35000*nb_niveaux*3:,}","45 000",f"{45000*nb_niveaux*3:,}"],
        ["PL-07",f"Chauffe-eau solaire 200L + capteurs ({nb_logements} unites)","u",str(nb_logements),"1 800 000",f"{1800000*nb_logements:,}","2 800 000",f"{2800000*nb_logements:,}","4 500 000",f"{4500000*nb_logements:,}"],
        ["PL-08","Reseau EU/EV PVC — colonnes + horizontaux","ml",str(nb_niveaux*40),"8 500",f"{8500*nb_niveaux*40:,}","10 000",f"{10000*nb_niveaux*40:,}","12 000",f"{12000*nb_niveaux*40:,}"],
        ["PL-09","Reseau EP PVC DN125 — 4 descentes","ml",str(nb_niveaux*3),"12 000",f"{12000*nb_niveaux*3:,}","15 000",f"{15000*nb_niveaux*3:,}","18 000",f"{18000*nb_niveaux*3:,}"],
        ["PL-10","RIA par palier","u",str(nb_niveaux),"350 000",f"{350000*nb_niveaux:,}","500 000",f"{500000*nb_niveaux:,}","750 000",f"{750000*nb_niveaux:,}"],
        ["PL-11",f"Equipements sanitaires logement","ens",str(nb_logements),"1 800 000",f"{1800000*nb_logements:,}","3 500 000",f"{3500000*nb_logements:,}","8 500 000",f"{8500000*nb_logements:,}"],
        ["PL-12","Robinetterie complete par logement","ens",str(nb_logements),"450 000",f"{450000*nb_logements:,}","950 000",f"{950000*nb_logements:,}","2 800 000",f"{2800000*nb_logements:,}"],
    ]
    story.append(lot_t(plomb, [12*mm,55*mm,8*mm,10*mm,18*mm,20*mm,18*mm,20*mm,18*mm,20*mm]))
    story.append(PageBreak())

    # LOT CVC
    story.append(Paragraph("CVC", st['h2']))
    story.append(HRFlowable(width="100%",thickness=0.5,color=GRIS_CLAIR))
    cvc = [
        ["Ref","Designation","U","Qte","Prix BASIC","Total BASIC","Prix H-END","Total H-END","Prix LUXURY","Total LUXURY"],
        ["CV-01",f"Split inverter 18 000 BTU sejour ({nb_logements} unites)","u",str(nb_logements),"850 000",f"{850000*nb_logements:,}","1 200 000",f"{1200000*nb_logements:,}","2 200 000",f"{2200000*nb_logements:,}"],
        ["CV-02",f"Split inverter 9 000 BTU chambre ({nb_logements*3} unites)","u",str(nb_logements*3),"480 000",f"{480000*nb_logements*3:,}","720 000",f"{720000*nb_logements*3:,}","1 350 000",f"{1350000*nb_logements*3:,}"],
        ["CV-03",f"VMC double flux 150m³/h par logement","u",str(nb_logements),"650 000",f"{650000*nb_logements:,}","1 100 000",f"{1100000*nb_logements:,}","1 800 000",f"{1800000*nb_logements:,}"],
        ["CV-04","CTA centrale 8 000 m³/h communs","u","1","8 500 000","8 500 000","12 000 000","12 000 000","18 000 000","18 000 000"],
        ["CV-05","Extracteurs parking sous-sol (4 unites)","u","4","850 000","3 400 000","1 200 000","4 800 000","1 800 000","7 200 000"],
        ["CV-06","Desenfumage cage escalier (2 ventilateurs)","u","2","1 800 000","3 600 000","2 500 000","5 000 000","3 500 000","7 000 000"],
        ["CV-07","Reseau gaines CVC galva isolees","ml",str(nb_niveaux*40),"8 500",f"{8500*nb_niveaux*40:,}","12 000",f"{12000*nb_niveaux*40:,}","18 000",f"{18000*nb_niveaux*40:,}"],
        ["CV-08",f"Regulation CVC par logement (thermostat)","u",str(nb_logements),"85 000",f"{85000*nb_logements:,}","180 000",f"{180000*nb_logements:,}","420 000",f"{420000*nb_logements:,}"],
    ]
    story.append(lot_t(cvc, [12*mm,55*mm,8*mm,10*mm,18*mm,20*mm,18*mm,20*mm,18*mm,20*mm]))
    story.append(PageBreak())

    # LOT DOMOTIQUE
    story.append(Paragraph("DOMOTIQUE & BMS", st['h2']))
    story.append(HRFlowable(width="100%",thickness=0.5,color=GRIS_CLAIR))
    dom = [
        ["Ref","Designation","U","Qte","Prix BASIC","Total BASIC","Prix H-END","Total H-END","Prix LUXURY","Total LUXURY"],
        ["BM-01","Serveur BMS + logiciel Niagara N4","u","1","4 500 000","4 500 000","8 500 000","8 500 000","18 000 000","18 000 000"],
        ["BM-02","Switch coeur de reseau 48 ports PoE+","u","1","1 800 000","1 800 000","3 500 000","3 500 000","6 500 000","6 500 000"],
        ["BM-03",f"Switchs d'etage 24 ports ({nb_niveaux} niveaux)","u",str(nb_niveaux),"450 000",f"{450000*nb_niveaux:,}","850 000",f"{850000*nb_niveaux:,}","1 800 000",f"{1800000*nb_niveaux:,}"],
        ["BM-04",f"Points d'acces WiFi 6 (paliers + logements)","u",str(nb_niveaux+nb_logements),"180 000",f"{180000*(nb_niveaux+nb_logements):,}","350 000",f"{350000*(nb_niveaux+nb_logements):,}","650 000",f"{650000*(nb_niveaux+nb_logements):,}"],
        ["BM-05","Cablage Cat. 6A + fibre backbone","ens","1","3 500 000","3 500 000","5 500 000","5 500 000","8 500 000","8 500 000"],
        ["BM-06","Interphone video IP portier principal","u","2","850 000","1 700 000","1 500 000","3 000 000","3 500 000","7 000 000"],
        ["BM-07",f"Combinés video par logement","u",str(nb_logements),"180 000",f"{180000*nb_logements:,}","350 000",f"{350000*nb_logements:,}","750 000",f"{750000*nb_logements:,}"],
        ["BM-08","CCTV 16 cameras 4K + NVR","ens","1","2 800 000","2 800 000","4 500 000","4 500 000","8 500 000","8 500 000"],
        ["BM-09","Controle acces badge NFC — portes communes","u","12","280 000","3 360 000","450 000","5 400 000","850 000","10 200 000"],
        ["BM-10","Detection incendie SSI cat. A","ens","1","8 500 000","8 500 000","12 000 000","12 000 000","18 000 000","18 000 000"],
        ["BM-11",f"Systeme KNX logements (actionneurs + capteurs)","ens",str(nb_logements),"350 000",f"{350000*nb_logements:,}","850 000",f"{850000*nb_logements:,}","2 800 000",f"{2800000*nb_logements:,}"],
        ["BM-12","Dashboard energie + app residents","ens","1","2 500 000","2 500 000","4 500 000","4 500 000","9 500 000","9 500 000"],
    ]
    story.append(lot_t(dom, [12*mm,55*mm,8*mm,10*mm,18*mm,20*mm,18*mm,20*mm,18*mm,20*mm]))
    story.append(PageBreak())

    # RÉCAPITULATIF
    story.append(Paragraph("RECAPITULATIF COMPARATIF — 3 NIVEAUX", st['h2']))
    story.append(HRFlowable(width="100%",thickness=0.5,color=GRIS_CLAIR))

    def tot(items): return sum(int(r[5].replace(',','').replace(' ','')) for r in items[1:] if len(r)>5 and r[5].replace(',','').replace(' ','').isdigit())
    def toth(items): return sum(int(r[7].replace(',','').replace(' ','')) for r in items[1:] if len(r)>7 and r[7].replace(',','').replace(' ','').isdigit())
    def totl(items): return sum(int(r[9].replace(',','').replace(' ','')) for r in items[1:] if len(r)>9 and r[9].replace(',','').replace(' ','').isdigit())

    te,teh,tel = tot(elec),toth(elec),totl(elec)
    tp,tph,tpl = tot(plomb),toth(plomb),totl(plomb)
    tc,tch,tcl = tot(cvc),toth(cvc),totl(cvc)
    td,tdh,tdl = tot(dom),toth(dom),totl(dom)
    impr_b = int((te+tp+tc+td)*0.08); impr_h = int((teh+tph+tch+tdh)*0.08); impr_l = int((tel+tpl+tcl+tdl)*0.08)
    total_b = te+tp+tc+td+impr_b; total_h = teh+tph+tch+tdh+impr_h; total_l = tel+tpl+tcl+tdl+impr_l

    recap = [
        ["LOT","BASIC (FCFA)","HIGH-END (FCFA)","LUXURY (FCFA)","Ecart H/B","Ecart L/B"],
        ["ELECTRICITE",f"{te:,}",f"{teh:,}",f"{tel:,}",f"+{int((teh/te-1)*100)}%",f"+{int((tel/te-1)*100)}%"],
        ["PLOMBERIE",f"{tp:,}",f"{tph:,}",f"{tpl:,}",f"+{int((tph/tp-1)*100)}%",f"+{int((tpl/tp-1)*100)}%"],
        ["CVC",f"{tc:,}",f"{tch:,}",f"{tcl:,}",f"+{int((tch/tc-1)*100)}%",f"+{int((tcl/tc-1)*100)}%"],
        ["DOMOTIQUE",f"{td:,}",f"{tdh:,}",f"{tdl:,}",f"+{int((tdh/td-1)*100)}%",f"+{int((tdl/td-1)*100)}%"],
        ["Imprevus & etudes (8%)",f"{impr_b:,}",f"{impr_h:,}",f"{impr_l:,}","",""],
        ["TOTAL GENERAL HT",f"{total_b:,}",f"{total_h:,}",f"{total_l:,}","",""],
        ["Equivalent EUR",f"{int(total_b/655.957):,} €",f"{int(total_h/655.957):,} €",f"{int(total_l/655.957):,} €","",""],
    ]
    t_rec = Table(recap, colWidths=[45*mm,35*mm,35*mm,35*mm,20*mm,20*mm])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),VERT),('TEXTCOLOR',(0,0),(-1,0),BLANC),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.5),
        ('GRID',(0,0),(-1,-1),0.3,GRIS_CLAIR),('ROWBACKGROUNDS',(0,1),(-1,-3),[BLANC,FOND]),
        ('BACKGROUND',(0,-2),(-1,-1),VERT_PALE),('FONTNAME',(0,-2),(-1,-1),'Helvetica-Bold'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t_rec)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph(
        f"BASIC : equipements conformes normes locales (SENELEC, ONAS, Senegal). Marques asiatiques et locales. | "
        f"HIGH-END : equipements europeens certifies. Efficacite energetique classe A+. Garantie 5 ans. | "
        f"LUXURY : equipements premium. Domotique KNX/BACnet integree. Finitions architecturales.",
        ParagraphStyle('note', fontSize=7, textColor=GRIS, spaceAfter=3)))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph("Prix marche Dakar — Mars 2025. Toutes fournitures + pose. Appel d'offres requis.", 
        ParagraphStyle('disc', fontSize=7, textColor=GRIS)))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)

"""
gen_boq_mep_detail_en.py — English MEP Detailed BOQ (7 lots × 3 tiers)
Complete translation of gen_boq_mep_detail.py with identical structure and calculations.
Uses tijan_theme.py for consistent PDF design.
Signature: generer_boq_mep_detail(rm, params_dict) → bytes
"""
import io, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer, PageBreak
from tijan_theme import *


def generer_boq_mep_detail(rm, params: dict, lang: str = "en") -> bytes:
    buf = io.BytesIO()
    hf = HeaderFooter(rm.params.nom, 'BOQ MEP — Detailed')
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=26*mm, bottomMargin=18*mm)
    doc.build(_build(rm), onFirstPage=hf, onLaterPages=hf)
    return buf.getvalue()


def _row(lot, desig, qte, unite, pu_b, pu_h, pu_l, note='', bold=False):
    st = 'td_b' if bold else 'td'
    return [
        p(lot, st), p(desig, st),
        p(str(qte) if qte != '' else '—', 'td_r'),
        p(unite, st),
        p(fmt_n(pu_b) if pu_b else '—', 'td_r'),
        p(fmt_n(pu_h) if pu_h else '—', 'td_r'),
        p(fmt_n(pu_l) if pu_l else '—', 'td_r'),
        p(note, 'small'),
    ]

def _sous_total(desig, c_b, c_h, c_l):
    return [p(''), p(desig, 'td_b'), p(''), p(''),
            p(fmt_fcfa(c_b), 'td_g_r'), p(fmt_fcfa(c_h), 'td_g_r'), p(fmt_fcfa(c_l), 'td_g_r'), p('')]

def _build(rm):
    story = []
    d = rm.params
    el = rm.electrique
    pl = rm.plomberie
    cv = rm.cvc
    cf = rm.courants_faibles
    si = rm.securite_incendie
    asc = rm.ascenseurs
    auto = rm.automatisation
    surf = rm.surf_batie_m2

    # Try to import pricing
    try:
        from prix_marche import get_prix_mep
        px = get_prix_mep(d.ville)
    except:
        class _PX:
            transfo_160kva=22_000_000; transfo_250kva=32_000_000; transfo_400kva=48_000_000
            groupe_electrogene_100kva=18_000_000; groupe_electrogene_200kva=32_000_000
            groupe_electrogene_400kva=58_000_000; compteur_monophase=180_000
            compteur_triphase=280_000; canalisation_cuivre_ml=12_000
            luminaire_led_standard=35_000; luminaire_led_premium=85_000
            colonne_montante_ml=22_000; tuyau_pvc_dn50_ml=8_500
            tuyau_pvc_dn100_ml=14_000; tuyau_pvc_dn150_ml=22_000
            robinet_standard=45_000; robinet_eco=75_000
            wc_standard=85_000; wc_double_chasse=130_000
            cuve_eau_5000l=850_000; cuve_eau_10000l=1_500_000
            pompe_surpresseur_1kw=450_000; pompe_surpresseur_3kw=850_000
            chauffe_eau_electrique_100l=180_000; chauffe_eau_solaire_200l=2_100_000
            split_1cv=450_000; split_2cv=750_000; split_cassette_4cv=1_800_000
            vmc_simple_flux=320_000; vmc_double_flux=850_000
            ascenseur_630kg_r4_r6=28_000_000; ascenseur_630kg_r7_r10=38_000_000
            ascenseur_1000kg_r6_r10=45_000_000; ascenseur_1000kg_r11_plus=58_000_000
            monte_charge_500kg=22_000_000; cablage_rj45_ml=3_500
            prise_rj45=18_000; baie_serveur_12u=850_000
            camera_ip_interieure=180_000; camera_ip_exterieure=280_000
            systeme_controle_acces=350_000; interphone_video=220_000
            detecteur_fumee=45_000; declencheur_manuel=35_000; sirene_flash=55_000
            centrale_incendie_16zones=1_800_000; centrale_incendie_32zones=3_200_000
            extincteur_6kg_co2=85_000; extincteur_9kg_poudre=65_000
            ria_dn25_ml=45_000; sprinkler_tete=85_000; sprinkler_centrale=4_500_000
            domotique_logement=850_000; bms_systeme=12_000_000
            eclairage_detecteur_presence=95_000
        px = _PX()

    # BOQ MEP columns
    CW_COLS = [CW*w for w in [0.05, 0.32, 0.06, 0.05, 0.12, 0.12, 0.12, 0.16]]
    HEADERS = [p(h,'th') for h in ['Lot','Description','Qty','Unit',f"Basic ({devise_label()})",'High-End','Luxury','Brand / Ref.']]

    def make_table(rows):
        t = Table([HEADERS] + rows, colWidths=CW_COLS, repeatRows=1)
        t.setStyle(table_style())
        return t

    # Header
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(d.nom, S['titre']))
    story.append(Paragraph(f'MEP Detailed BOQ — {d.ville} — R+{d.nb_niveaux-1} — {d.usage.value.capitalize()}', S['sous_titre']))
    story.append(Paragraph(
        f'Built area: {fmt_n(surf,0,"m²")} | {rm.nb_logements} units | {rm.nb_personnes} occupants | '
        f'3 tiers: Basic / High-End / Luxury',
        S['body']))
    story.append(Paragraph(
        'Unit prices local market 2026 — supply and install — margin ±15%. '
        'Document suitable for contractor tender.',
        S['note']))
    story.append(Spacer(1, 2*mm))

    totaux = {}

    # ══════════════════════════════════════════════════════════
    # LOT E — ELECTRICAL POWER
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT E', 'ELECTRICAL POWER (NF C 15-100)')
    story.append(Paragraph(el.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    # Transformer selection
    transfo_pu = {100: px.transfo_160kva, 160: px.transfo_160kva,
                   250: px.transfo_250kva, 400: px.transfo_400kva,
                   630: px.transfo_400kva, 1000: px.transfo_400kva*2}.get(el.transfo_kva, px.transfo_160kva)
    ge_pu = {60: px.groupe_electrogene_100kva, 100: px.groupe_electrogene_100kva,
              160: px.groupe_electrogene_200kva, 200: px.groupe_electrogene_200kva,
              250: px.groupe_electrogene_200kva, 400: px.groupe_electrogene_400kva}.get(el.groupe_electrogene_kva, px.groupe_electrogene_200kva)

    L_cable = int(surf * 2.5)  # estimated cabling ml
    nb_lum = int(surf / 12)    # 1 luminaire / 12m²

    rows_elec = [
        _row('E.1', f'MV/LV substation — transformer {el.transfo_kva} kVA', 1, 'ea',
             transfo_pu, int(transfo_pu*1.15), int(transfo_pu*1.40),
             'Schneider / ABB / Siemens'),
        _row('E.2', 'Main LV panel — general distribution', 1, 'ea',
             3_500_000, 5_500_000, 8_000_000,
             'Schneider Prisma / ABB MNS'),
        _row('E.3', f'Backup generator {el.groupe_electrogene_kva} kVA — soundproofed', 1, 'ea',
             ge_pu, int(ge_pu*1.20), int(ge_pu*1.45),
             'FG Wilson / Caterpillar / Cummins'),
        _row('E.4', f'Meters — {el.nb_compteurs} units',
             el.nb_compteurs, 'ea', px.compteur_monophase, px.compteur_triphase, int(px.compteur_triphase*1.3),
             'SENELEC compatible'),
        _row('E.5', 'Riser column + distribution boards',
             d.nb_niveaux, 'level', 1_200_000, 1_800_000, 2_500_000,
             f'Section {el.section_colonne_mm2} mm²'),
        _row('E.6', f'Copper cabling distribution — {L_cable} lm',
             L_cable, 'lm', px.canalisation_cuivre_ml, int(px.canalisation_cuivre_ml*1.3), int(px.canalisation_cuivre_ml*1.6),
             'Cables NYM / H07RN'),
        _row('E.7', f'LED luminaires — {nb_lum} units',
             nb_lum, 'ea', px.luminaire_led_standard, px.luminaire_led_premium, int(px.luminaire_led_premium*1.5),
             'Philips / Osram / Legrand'),
        _row('E.8', 'Power outlets + switches',
             int(surf/8), 'ea', 12_000, 22_000, 38_000,
             'Legrand Mosaic / Schneider Unica'),
        _row('E.9', 'Earthing + surge protection',
             1, 'lump sum', 850_000, 1_200_000, 1_800_000,
             'Required NF C 15-100'),
    ]

    c_elec_b = (transfo_pu + 3_500_000 + ge_pu + el.nb_compteurs*px.compteur_monophase +
                d.nb_niveaux*1_200_000 + L_cable*px.canalisation_cuivre_ml +
                nb_lum*px.luminaire_led_standard + int(surf/8)*12_000 + 850_000)
    c_elec_h = int(c_elec_b * 1.35)
    c_elec_l = int(c_elec_b * 1.75)
    rows_elec.append(_sous_total('SUBTOTAL LOT E', c_elec_b, c_elec_h, c_elec_l))
    totaux['E'] = (c_elec_b, c_elec_h, c_elec_l)
    story.append(make_table(rows_elec))

    # ══════════════════════════════════════════════════════════
    # LOT P — PLUMBING
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT P', 'PLUMBING AND SANITARY (DTU 60.11)')
    story.append(Paragraph(pl.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    # Water tank
    cuve_pu = px.cuve_eau_5000l if pl.volume_citerne_m3 <= 5 else px.cuve_eau_10000l
    nb_cuves = max(1, math.ceil(pl.volume_citerne_m3 / 10))
    # Booster pump
    surp_pu = px.pompe_surpresseur_1kw if pl.debit_surpresseur_m3h <= 4 else px.pompe_surpresseur_3kw

    rows_plomb = [
        _row('P.1', f'Polyethylene water tank {int(pl.volume_citerne_m3)} m³',
             nb_cuves, 'ea', cuve_pu, int(cuve_pu*1.20), int(cuve_pu*1.50),
             f'Total capacity {int(pl.volume_citerne_m3)} m³'),
        _row('P.2', f'Booster pump {pl.debit_surpresseur_m3h} m³/h — with variable speed drive',
             1, 'ea', surp_pu, int(surp_pu*1.30), int(surp_pu*1.70),
             'Grundfos / DAB / Ebara'),
        _row('P.3', f'Cold water risers DN{pl.diam_colonne_montante_mm}',
             int(d.nb_niveaux * d.hauteur_etage_m * 1.2), 'lm',
             px.colonne_montante_ml, int(px.colonne_montante_ml*1.2), int(px.colonne_montante_ml*1.5),
             'Galvanized steel / PPR'),
        _row('P.4', 'Wastewater/vent network — PVC DN100/DN150',
             int(surf*0.15), 'lm', px.tuyau_pvc_dn100_ml, int(px.tuyau_pvc_dn100_ml*1.2), int(px.tuyau_pvc_dn100_ml*1.5),
             'Wavin / Georg Fischer'),
        _row('P.5', f'WC + standard flush — {pl.nb_wc_double_chasse} u.',
             pl.nb_wc_double_chasse, 'ea', px.wc_standard, px.wc_double_chasse, int(px.wc_double_chasse*1.8),
             'Basic: Standard | HE: Dual flush | Lux: Geberit'),
        _row('P.6', f'Mixer taps — {pl.nb_robinets_eco} u.',
             pl.nb_robinets_eco, 'ea', px.robinet_standard, px.robinet_eco, int(px.robinet_eco*2.5),
             'Basic: Local | HE: Grohe | Lux: Hansgrohe'),
        _row('P.7', 'Wash basins + showers + bathtubs',
             pl.nb_logements, 'unit', 280_000, 520_000, 1_200_000,
             'Flat-rate sanitary fixtures per unit'),
        _row('P.8', 'Electric water heater 100L backup',
             pl.nb_logements, 'ea', px.chauffe_eau_electrique_100l, int(px.chauffe_eau_electrique_100l*1.3), int(px.chauffe_eau_electrique_100l*1.6),
             'Atlantic / Thermor'),
    ]
    if pl.nb_chauffe_eau_solaire > 0:
        rows_plomb.append(_row('P.9', f'Solar water heaters 200L — {pl.nb_chauffe_eau_solaire} u.',
             pl.nb_chauffe_eau_solaire, 'ea', px.chauffe_eau_solaire_200l, int(px.chauffe_eau_solaire_200l*1.2), int(px.chauffe_eau_solaire_200l*1.5),
             'CESI = +6% EDGE energy — ROI 5-7 years'))

    c_pl_b = (nb_cuves*cuve_pu + surp_pu +
              int(d.nb_niveaux*d.hauteur_etage_m*1.2*px.colonne_montante_ml) +
              int(surf*0.15*px.tuyau_pvc_dn100_ml) +
              pl.nb_wc_double_chasse*px.wc_standard +
              pl.nb_robinets_eco*px.robinet_standard +
              pl.nb_logements*280_000 +
              pl.nb_logements*px.chauffe_eau_electrique_100l)
    if pl.nb_chauffe_eau_solaire > 0:
        c_pl_b += pl.nb_chauffe_eau_solaire * px.chauffe_eau_solaire_200l
    c_pl_h = int(c_pl_b * 1.40)
    c_pl_l = int(c_pl_b * 1.90)
    rows_plomb.append(_sous_total('SUBTOTAL LOT P', c_pl_b, c_pl_h, c_pl_l))
    totaux['P'] = (c_pl_b, c_pl_h, c_pl_l)
    story.append(make_table(rows_plomb))

    # ══════════════════════════════════════════════════════════
    # LOT C — HVAC
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT C', 'HVAC — COOLING, VENTILATION AND HEATING (EN 12831)')
    story.append(Paragraph(cv.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    rows_cvc = []
    if cv.nb_splits_sejour > 0:
        rows_cvc += [
            _row('C.1', f'Wall mounted splits living area 1HP — {cv.nb_splits_sejour} u.',
                 cv.nb_splits_sejour, 'ea', px.split_1cv, int(px.split_1cv*1.35), int(px.split_1cv*1.80),
                 'Daikin / Mitsubishi / Carrier'),
            _row('C.2', f'Wall mounted splits bedroom 1HP — {cv.nb_splits_chambre} u.',
                 cv.nb_splits_chambre, 'ea', px.split_1cv, int(px.split_1cv*1.35), int(px.split_1cv*1.80),
                 'Basic: Standard | Lux: Inverter A+++'),
        ]
    if cv.nb_cassettes > 0:
        rows_cvc.append(_row('C.1', f'Ceiling mounted cassettes 4HP — {cv.nb_cassettes} u.',
             cv.nb_cassettes, 'ea', px.split_cassette_4cv, int(px.split_cassette_4cv*1.30), int(px.split_cassette_4cv*1.70),
             'Daikin VRV / Mitsubishi City Multi'))

    vmc_pu = px.vmc_double_flux if cv.type_vmc == 'double_flux' else px.vmc_simple_flux
    rows_cvc += [
        _row('C.3', f'Ventilation unit {cv.type_vmc} — {cv.nb_vmc} u.',
             cv.nb_vmc, 'ea', vmc_pu, int(vmc_pu*1.25), int(vmc_pu*1.60),
             'Atlantic / Aldes / Zehnder (double flux)'),
        _row('C.4', 'Ventilation ductwork network',
             int(surf*0.08), 'm²', 18_000, 25_000, 35_000,
             'Galvanized sheet metal + insulation'),
        _row('C.5', 'Grilles + diffusers',
             int(rm.nb_logements * 4), 'ea', 15_000, 25_000, 45_000,
             'Aldes / Price'),
        _row('C.6', 'Zone control + thermostat',
             int(surf/80), 'zone', 85_000, 150_000, 280_000,
             'Honeywell / Siemens / KNX'),
    ]

    nb_sp = cv.nb_splits_sejour + cv.nb_splits_chambre + cv.nb_cassettes
    c_cv_b = (nb_sp * px.split_1cv + cv.nb_vmc * vmc_pu +
              int(surf*0.08*18_000) + int(rm.nb_logements*4*15_000) + int(surf/80*85_000))
    c_cv_h = int(c_cv_b * 1.40)
    c_cv_l = int(c_cv_b * 1.90)
    rows_cvc.append(_sous_total('SUBTOTAL LOT C', c_cv_b, c_cv_h, c_cv_l))
    totaux['C'] = (c_cv_b, c_cv_h, c_cv_l)
    story.append(make_table(rows_cvc))

    # ══════════════════════════════════════════════════════════
    # LOT CF — LOW CURRENT SYSTEMS
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT CF', 'LOW CURRENT SYSTEMS — NETWORK, VIDEO, ACCESS, INTERCOM')
    story.append(Paragraph(cf.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    L_rj45 = int(cf.nb_prises_rj45 * 25)
    rows_cf = [
        _row('CF.1', f'Network cabling Cat6A — {L_rj45} lm',
             L_rj45, 'lm', px.cablage_rj45_ml, int(px.cablage_rj45_ml*1.3), int(px.cablage_rj45_ml*1.6),
             'Legrand / Nexans Cat6A'),
        _row('CF.2', f'RJ45 double outlets — {cf.nb_prises_rj45} u.',
             cf.nb_prises_rj45, 'ea', px.prise_rj45, int(px.prise_rj45*1.4), int(px.prise_rj45*2.0),
             'Basic: Cat6 | HE: Cat6A | Lux: Cat7'),
        _row('CF.3', f'Server racks 12U — {cf.baies_serveur} u.',
             cf.baies_serveur, 'ea', px.baie_serveur_12u, int(px.baie_serveur_12u*1.5), int(px.baie_serveur_12u*2.0),
             'APC / Legrand / Eaton'),
        _row('CF.4', f'Interior IP cameras — {cf.nb_cameras_int} u.',
             cf.nb_cameras_int, 'ea', px.camera_ip_interieure, int(px.camera_ip_interieure*1.8), int(px.camera_ip_interieure*2.5),
             'Axis / Hikvision / Dahua'),
        _row('CF.5', f'Exterior IP cameras — {cf.nb_cameras_ext} u.',
             cf.nb_cameras_ext, 'ea', px.camera_ip_exterieure, int(px.camera_ip_exterieure*1.6), int(px.camera_ip_exterieure*2.2),
             'Axis P-series / Bosch'),
        _row('CF.6', f'Access control — {cf.nb_portes_controle_acces} doors',
             cf.nb_portes_controle_acces, 'door', px.systeme_controle_acces, int(px.systeme_controle_acces*1.5), int(px.systeme_controle_acces*2.5),
             'HID / Nedap / Siemens'),
        _row('CF.7', f'Video intercoms — {cf.nb_interphones} u.',
             cf.nb_interphones, 'ea', px.interphone_video, int(px.interphone_video*1.5), int(px.interphone_video*2.5),
             'Legrand / BTicino / Aiphone'),
        _row('CF.8', 'Video recording NVR + storage',
             cf.baies_serveur, 'ea', 850_000, 1_500_000, 3_000_000,
             '30 days storage — NAS disks'),
    ]
    if cf.systeme_audio_video:
        rows_cf.append(_row('CF.9', 'Audio/video system for common areas',
             1, 'lump sum', 2_500_000, 5_000_000, 12_000_000,
             'Bose / Sonos / Crestron'))

    c_cf_b = (L_rj45*px.cablage_rj45_ml + cf.nb_prises_rj45*px.prise_rj45 +
              cf.baies_serveur*px.baie_serveur_12u +
              cf.nb_cameras_int*px.camera_ip_interieure +
              cf.nb_cameras_ext*px.camera_ip_exterieure +
              cf.nb_portes_controle_acces*px.systeme_controle_acces +
              cf.nb_interphones*px.interphone_video +
              cf.baies_serveur*850_000)
    c_cf_h = int(c_cf_b * 1.55)
    c_cf_l = int(c_cf_b * 2.20)
    rows_cf.append(_sous_total('SUBTOTAL LOT CF', c_cf_b, c_cf_h, c_cf_l))
    totaux['CF'] = (c_cf_b, c_cf_h, c_cf_l)
    story.append(make_table(rows_cf))

    # ══════════════════════════════════════════════════════════
    # LOT SI — FIRE SAFETY
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('LOT SI', 'FIRE SAFETY (IT 246 — France/Senegal)')
    story.append(Paragraph(si.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    centrale_pu = px.centrale_incendie_32zones if si.centrale_zones > 16 else px.centrale_incendie_16zones

    rows_si = [
        _row('SI.1', f'Addressable fire panel — {si.centrale_zones} zones',
             1, 'ea', centrale_pu, int(centrale_pu*1.30), int(centrale_pu*1.70),
             'Schneider Esser / Siemens Cerberus / Tyco'),
        _row('SI.2', f'Optical smoke detectors — {si.nb_detecteurs_fumee} u.',
             si.nb_detecteurs_fumee, 'ea', px.detecteur_fumee, int(px.detecteur_fumee*1.3), int(px.detecteur_fumee*1.6),
             'Apollo / Siemens / Hochiki'),
        _row('SI.3', f'Manual call points — {si.nb_declencheurs_manuels} u.',
             si.nb_declencheurs_manuels, 'ea', px.declencheur_manuel, int(px.declencheur_manuel*1.2), int(px.declencheur_manuel*1.5),
             '1 min per level'),
        _row('SI.4', f'Alarm bells + strobes — {si.nb_sirenes} u.',
             si.nb_sirenes, 'ea', px.sirene_flash, int(px.sirene_flash*1.2), int(px.sirene_flash*1.5),
             '1 per level min.'),
        _row('SI.5', f'CO2 extinguishers 6kg — {si.nb_extincteurs_co2} u.',
             si.nb_extincteurs_co2, 'ea', px.extincteur_6kg_co2, int(px.extincteur_6kg_co2*1.2), int(px.extincteur_6kg_co2*1.4),
             'Amerex / Firex / Sicli'),
        _row('SI.6', f'Powder extinguishers 9kg — {si.nb_extincteurs_poudre} u.',
             si.nb_extincteurs_poudre, 'ea', px.extincteur_9kg_poudre, int(px.extincteur_9kg_poudre*1.2), int(px.extincteur_9kg_poudre*1.4),
             'Technical areas + parking'),
        _row('SI.7', f'Fire riser DN25 — {int(si.longueur_ria_ml)} lm',
             int(si.longueur_ria_ml), 'lm', px.ria_dn25_ml, int(px.ria_dn25_ml*1.2), int(px.ria_dn25_ml*1.4),
             f'Required {si.categorie_erp}'),
    ]
    if si.sprinklers_requis and si.nb_tetes_sprinkler > 0:
        rows_si += [
            _row('SI.8', f'Sprinkler system + supply network',
                 1, 'ea', px.sprinkler_centrale, int(px.sprinkler_centrale*1.2), int(px.sprinkler_centrale*1.5),
                 '⚠ Required — significant cost'),
            _row('SI.9', f'Sprinkler heads — {si.nb_tetes_sprinkler} u.',
                 si.nb_tetes_sprinkler, 'ea', px.sprinkler_tete, int(px.sprinkler_tete*1.2), int(px.sprinkler_tete*1.4),
                 f'1 head / 9m² — {si.nb_tetes_sprinkler} heads'),
        ]
    if si.desenfumage_requis:
        c_desenfum = int(surf * 3500)
        rows_si.append(_row('SI.10', 'Smoke evacuation — motorized dampers + ducts',
             1, 'lump sum', c_desenfum, int(c_desenfum*1.3), int(c_desenfum*1.6),
             '⚠ Required — check IT 246'))

    c_si_b = (centrale_pu + si.nb_detecteurs_fumee*px.detecteur_fumee +
              si.nb_declencheurs_manuels*px.declencheur_manuel +
              si.nb_sirenes*px.sirene_flash +
              si.nb_extincteurs_co2*px.extincteur_6kg_co2 +
              si.nb_extincteurs_poudre*px.extincteur_9kg_poudre +
              int(si.longueur_ria_ml*px.ria_dn25_ml) +
              (si.nb_tetes_sprinkler*px.sprinkler_tete + px.sprinkler_centrale if si.sprinklers_requis else 0) +
              (int(surf*3500) if si.desenfumage_requis else 0))
    c_si_h = int(c_si_b * 1.30)
    c_si_l = int(c_si_b * 1.60)
    rows_si.append(_sous_total('SUBTOTAL LOT SI', c_si_b, c_si_h, c_si_l))
    totaux['SI'] = (c_si_b, c_si_h, c_si_l)
    story.append(make_table(rows_si))

    # ══════════════════════════════════════════════════════════
    # LOT ASC — ELEVATORS
    # ══════════════════════════════════════════════════════════
    if asc.nb_ascenseurs > 0:
        story.append(PageBreak())
        story += section_title('LOT ASC', 'ELEVATORS AND SERVICE LIFTS (EN 81-20/50)')
        story.append(Paragraph(f'{asc.note_dimensionnement} | {asc.note_impact_prix}', S['note']))
        story.append(Spacer(1, 2*mm))

        if asc.capacite_kg == 630 and d.nb_niveaux <= 6:
            asc_pu = px.ascenseur_630kg_r4_r6
        elif asc.capacite_kg == 630:
            asc_pu = px.ascenseur_630kg_r7_r10
        elif d.nb_niveaux <= 10:
            asc_pu = px.ascenseur_1000kg_r6_r10
        else:
            asc_pu = px.ascenseur_1000kg_r11_plus

        rows_asc = [
            _row('ASC.1', f'Elevator {asc.capacite_kg}kg {asc.vitesse_ms}m/s — {asc.nb_ascenseurs} u.',
                 asc.nb_ascenseurs, 'ea', asc_pu, int(asc_pu*1.15), int(asc_pu*1.40),
                 'Otis / Schindler / Kone / Thyssen'),
            _row('ASC.2', 'RC hoistway + pit',
                 asc.nb_ascenseurs, 'ea', 3_500_000, 4_200_000, 4_200_000,
                 'Included in gros oeuvre if planned'),
            _row('ASC.3', 'Dedicated electrical panel for elevators',
                 asc.nb_ascenseurs, 'ea', 850_000, 1_200_000, 1_500_000,
                 'Dedicated power supply NF C 15-100'),
        ]
        if asc.nb_monte_charges > 0:
            rows_asc.append(_row('ASC.4', f'Service lift 500kg — {asc.nb_monte_charges} u.',
                 asc.nb_monte_charges, 'ea', px.monte_charge_500kg, int(px.monte_charge_500kg*1.15), int(px.monte_charge_500kg*1.35),
                 'Service + hotel kitchen'))

        c_asc_b = (asc.nb_ascenseurs * asc_pu + asc.nb_ascenseurs*3_500_000 +
                   asc.nb_ascenseurs*850_000 + asc.nb_monte_charges*px.monte_charge_500kg)
        c_asc_h = int(c_asc_b * 1.15)
        c_asc_l = int(c_asc_b * 1.40)
        rows_asc.append(_sous_total('SUBTOTAL LOT ASC', c_asc_b, c_asc_h, c_asc_l))
        totaux['ASC'] = (c_asc_b, c_asc_h, c_asc_l)
        story.append(make_table(rows_asc))

    # ══════════════════════════════════════════════════════════
    # LOT AUTO — BUILDING AUTOMATION
    # ══════════════════════════════════════════════════════════
    story += section_title('LOT AUTO', f'BUILDING AUTOMATION BMS — {auto.niveau.upper()} ({auto.protocole})')
    story.append(Paragraph(auto.note_dimensionnement, S['note']))
    story.append(Spacer(1, 2*mm))

    rows_auto = [
        _row('AUTO.1', f'BMS/GTB system — {auto.protocole}',
             1, 'lump sum',
             5_000_000 if auto.niveau == 'basic' else 12_000_000 if auto.niveau == 'standard' else px.bms_systeme,
             8_000_000 if auto.niveau == 'basic' else 18_000_000 if auto.niveau == 'standard' else int(px.bms_systeme*1.4),
             12_000_000 if auto.niveau == 'basic' else 28_000_000 if auto.niveau == 'standard' else int(px.bms_systeme*1.8),
             'Schneider EcoStruxure / Siemens Desigo / KNX'),
        _row('AUTO.2', f'Lighting management — {auto.nb_points_controle} points',
             auto.nb_points_controle, 'point', px.eclairage_detecteur_presence, int(px.eclairage_detecteur_presence*1.4), int(px.eclairage_detecteur_presence*2.0),
             'Presence detectors + dimming'),
        _row('AUTO.3', 'Centralized HVAC management',
             1, 'lump sum', 2_500_000, 4_500_000, 8_000_000,
             'Integrated in BMS or standalone'),
    ]
    if auto.gestion_energie:
        rows_auto.append(_row('AUTO.4', 'Energy metering + dashboards',
             1, 'lump sum', 3_500_000, 6_000_000, 10_000_000,
             'Schneider PowerLogic / ABB Ability'))
    if not auto.bms_requis:
        rows_auto.append(_row('AUTO.5', f'Home automation per unit — {rm.nb_logements} u.',
             rm.nb_logements, 'ea', px.domotique_logement, int(px.domotique_logement*1.5), int(px.domotique_logement*2.5),
             'KNX / Legrand MyHome / Somfy'))

    c_auto_b_base = 5_000_000 if auto.niveau == 'basic' else (12_000_000 if auto.niveau == 'standard' else px.bms_systeme)
    c_auto_b = (c_auto_b_base + auto.nb_points_controle*px.eclairage_detecteur_presence +
                2_500_000 + (rm.nb_logements*px.domotique_logement if not auto.bms_requis else 0))
    c_auto_h = int(c_auto_b * 1.55)
    c_auto_l = int(c_auto_b * 2.20)
    rows_auto.append(_sous_total('SUBTOTAL LOT AUTO', c_auto_b, c_auto_h, c_auto_l))
    totaux['AUTO'] = (c_auto_b, c_auto_h, c_auto_l)
    story.append(make_table(rows_auto))

    # ══════════════════════════════════════════════════════════
    # GENERAL MEP SUMMARY
    # ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += section_title('RECAP', 'GENERAL MEP SUMMARY')

    total_b = sum(v[0] for v in totaux.values())
    total_h = sum(v[1] for v in totaux.values())
    total_l = sum(v[2] for v in totaux.values())
    ratio_b = int(total_b / surf) if surf > 0 else 0
    ratio_h = int(total_h / surf) if surf > 0 else 0

    lot_labels = {
        'E': 'Electrical power',
        'P': 'Plumbing and sanitary',
        'C': 'HVAC — Cooling + Ventilation',
        'CF': 'Low current systems',
        'SI': 'Fire safety',
        'ASC': 'Elevators and service lifts',
        'AUTO': 'Building Automation BMS',
    }

    CW_RECAP = [CW*w for w in [0.06, 0.38, 0.16, 0.16, 0.16, 0.08]]
    recap_rows = [[p(h,'th') for h in ['Lot','Description','BASIC','HIGH-END','LUXURY','% TOTAL']]]
    for k, (cb, ch, cl) in totaux.items():
        recap_rows.append([
            p(k,'td_b'), p(lot_labels.get(k,'—')),
            p(fmt_fcfa(cb),'td_r'), p(fmt_fcfa(ch),'td_r'), p(fmt_fcfa(cl),'td_r'),
            p(f'{cb/total_b*100:.0f}%','td_r'),
        ])
    recap_rows.append([
        p('','td_b'), p('TOTAL MEP','td_b'),
        p(fmt_fcfa(total_b),'td_g_r'), p(fmt_fcfa(total_h),'td_g_r'), p(fmt_fcfa(total_l),'td_g_r'),
        p('100%','td_b'),
    ])
    recap_rows.append([
        p('','td_b'), p(f'MEP cost / m² built ({fmt_n(surf,0)} m²)','td_b'),
        p(f'{ratio_b:,} {devise_label()}/m²'.replace(',', ' '),'td_r'),
        p(f'{ratio_h:,} {devise_label()}/m²'.replace(',', ' '),'td_r'),
        p('—','td_r'), p('','td_b'),
    ])

    tr = Table(recap_rows, colWidths=CW_RECAP, repeatRows=1)
    ts_r = table_style(zebra=False)
    ts_r.add('BACKGROUND', (0,-2), (-1,-1), VERT_LIGHT)
    ts_r.add('FONTNAME',   (0,-2), (-1,-1), 'Helvetica-Bold')
    ts_r.add('LINEABOVE',  (0,-2), (-1,-2), 1.5, VERT)
    tr.setStyle(ts_r)
    story.append(tr)

    # Recommendation note
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(rm.boq.recommandation, S['note']))
    story.append(Paragraph(rm.boq.note_choix, S['small']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '* This BOQ is a pre-project estimate (±15%). '
        'Quantities are calculated from MEP technical assessments. '
        'A detailed take-off from execution plans is required before tender.',
        S['disc']))

    return story

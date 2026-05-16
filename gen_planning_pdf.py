"""
gen_planning_pdf.py — Planning d'exécution (Gantt + Trésorerie)
Tijan AI — PDF professionnel avec diagramme de Gantt et plan de trésorerie
"""
import io
import logging
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, Spacer, PageBreak, KeepTogether, Flowable,
)
from reportlab.lib import colors
from tijan_theme import *

logger = logging.getLogger(__name__)

# ── Lot colors ───────────────────────────────────────────────────
LOT_COLORS = {
    "STRUCTURE": VERT,
    "MEP": BLEU,
    "FINITIONS": ORANGE,
}
LOT_COLORS_LIGHT = {
    "STRUCTURE": VERT_LIGHT,
    "MEP": BLEU_LT,
    "FINITIONS": ORANGE_LT,
}
LOT_COLORS_DARK = {
    "STRUCTURE": VERT_DARK,
    "MEP": colors.HexColor("#0D47A1"),
    "FINITIONS": colors.HexColor("#BF5F00"),
}

LOT_LABELS = {
    "fr": {"STRUCTURE": "Structure", "MEP": "MEP", "FINITIONS": "Finitions"},
    "en": {"STRUCTURE": "Structure", "MEP": "MEP", "FINITIONS": "Finishing"},
}


# ── i18n labels ──────────────────────────────────────────────────
_LABELS = {
    "fr": {
        "title_gantt": "Planning d'exécution",
        "subtitle": "R+{n} — {ville} — Durée totale : {mois} mois",
        "tache": "Tâche",
        "lot": "Lot",
        "duree": "Durée (j)",
        "title_cash": "Plan de Trésorerie",
        "mois": "Mois",
        "materiel": "Matériaux / Équipements",
        "pose": "Main d'œuvre / Pose",
        "total_mensuel": "Total mensuel",
        "cumul": "Cumul",
        "total": "TOTAL",
        "scurve_title": "Courbe en S — Dépenses cumulées",
        "title_cross": "Répartition par Lot × Phase",
        "phase": "Phase",
        "pct": "% du total",
        "cout_total": "Coût total",
    },
    "en": {
        "title_gantt": "Execution Schedule",
        "subtitle": "G+{n} — {ville} — Total duration: {mois} months",
        "tache": "Task",
        "lot": "Lot",
        "duree": "Duration (d)",
        "title_cash": "Cash Flow Plan",
        "mois": "Month",
        "materiel": "Materials / Equipment",
        "pose": "Labour / Installation",
        "total_mensuel": "Monthly total",
        "cumul": "Cumulative",
        "total": "TOTAL",
        "scurve_title": "S-Curve — Cumulative Expenditure",
        "title_cross": "Cost Breakdown by Lot × Phase",
        "phase": "Phase",
        "pct": "% of total",
        "cout_total": "Total cost",
    },
}


def _t(key: str, lang: str = "fr") -> str:
    return _LABELS.get(lang, _LABELS["fr"]).get(key, key)


# ── Gantt Flowable ───────────────────────────────────────────────
class GanttFlowable(Flowable):
    """Custom flowable that draws a horizontal Gantt chart using canvas primitives.
    Accepts a subset of groups (lot, tasks) to allow splitting across pages."""

    def __init__(self, planning, lang="fr", width=None, groups=None):
        super().__init__()
        self.planning = planning
        self.lang = lang
        self._width = width or CW
        self._groups_override = groups  # if provided, only draw these groups
        self._compute_layout()

    def _compute_layout(self):
        pl = self.planning
        self.nb_mois = max(pl.duree_totale_mois, 1)

        # Use override groups if provided, otherwise build from planning
        if self._groups_override is not None:
            self.groups = self._groups_override
        else:
            self.groups = []
            seen_lots = []
            for t in pl.taches:
                if t.lot not in seen_lots:
                    seen_lots.append(t.lot)
            for lot in seen_lots:
                taches = [t for t in pl.taches if t.lot == lot]
                self.groups.append((lot, taches))

        self.total_tasks = sum(len(tl) for _, tl in self.groups)
        self.total_rows = self.total_tasks + len(self.groups)  # tasks + lot headers

        # Layout dimensions
        self.label_w = 110 * mm
        self.chart_w = self._width - self.label_w
        self.header_h = 7 * mm
        self.row_h = 5.5 * mm
        self._height = self.header_h + self.total_rows * self.row_h + 4 * mm

    def wrap(self, availWidth, availHeight):
        return self._width, self._height

    def draw(self):
        c = self.canv
        pl = self.planning
        x0 = self.label_w
        y_top = self._height - 2 * mm

        # ── Month header ─────────────────────────────────────────
        month_w = self.chart_w / self.nb_mois
        y_header = y_top - self.header_h
        c.setFont("Helvetica-Bold", 6.5)
        for m in range(self.nb_mois):
            mx = x0 + m * month_w
            # Alternate background
            if m % 2 == 0:
                c.setFillColor(GRIS1)
                c.rect(mx, y_header, month_w, self.header_h, fill=1, stroke=0)
            # Vertical grid line
            c.setStrokeColor(GRIS2)
            c.setLineWidth(0.3)
            c.line(mx, y_header, mx, y_header - self.total_rows * self.row_h)
            # Month label
            c.setFillColor(NOIR)
            label = f"M{m + 1}"
            c.drawCentredString(mx + month_w / 2, y_header + 2 * mm, label)

        # Right border
        c.setStrokeColor(GRIS2)
        c.line(x0 + self.chart_w, y_header, x0 + self.chart_w,
               y_header - self.total_rows * self.row_h)

        # ── Task rows ────────────────────────────────────────────
        y = y_header
        row_idx = 0
        for lot, taches in self.groups:
            # Lot header row
            y -= self.row_h
            color = LOT_COLORS.get(lot, GRIS3)
            c.setFillColor(color)
            c.rect(0, y, self._width, self.row_h, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(BLANC)
            lot_label = LOT_LABELS.get(self.lang, LOT_LABELS["fr"]).get(lot, lot)
            c.drawString(3 * mm, y + 1.5 * mm, lot_label.upper())
            row_idx += 1

            for t in taches:
                y -= self.row_h
                # Zebra stripe
                if row_idx % 2 == 0:
                    c.setFillColor(GRIS1)
                    c.rect(0, y, x0, self.row_h, fill=1, stroke=0)
                # Horizontal grid line
                c.setStrokeColor(GRIS2)
                c.setLineWidth(0.2)
                c.line(0, y, self._width, y)

                # Task label (truncate if needed)
                c.setFont("Helvetica", 6)
                c.setFillColor(NOIR)
                label = t.designation
                if len(label) > 55:
                    label = label[:52] + "..."
                c.drawString(3 * mm, y + 1.5 * mm, label)

                # Duration text
                c.setFont("Helvetica", 5.5)
                c.setFillColor(GRIS3)
                dur_str = f"{t.duree_jours}j"
                c.drawRightString(x0 - 2 * mm, y + 1.5 * mm, dur_str)

                # Gantt bar
                bar_color = LOT_COLORS.get(t.lot, GRIS3)
                dark_color = LOT_COLORS_DARK.get(t.lot, NOIR)
                day_w = self.chart_w / (self.nb_mois * 30)
                bx = x0 + t.debut_jour * day_w
                bw = max(t.duree_jours * day_w, 1.5 * mm)
                bar_y = y + 1 * mm
                bar_h = self.row_h - 2 * mm

                # Check if critical path (no successors or longest chain)
                is_critical = _is_critical_task(t, pl.taches)
                if is_critical:
                    c.setFillColor(dark_color)
                else:
                    c.setFillColor(bar_color)
                c.roundRect(bx, bar_y, bw, bar_h, radius=1, fill=1, stroke=0)

                row_idx += 1

        # Bottom border
        c.setStrokeColor(GRIS2)
        c.setLineWidth(0.5)
        c.line(0, y, self._width, y)


# ── S-Curve Flowable ─────────────────────────────────────────────
class SCurveFlowable(Flowable):
    """Draws cumulative cost S-curve with ReportLab canvas."""

    def __init__(self, tresorerie, lang="fr", width=None, height=None):
        super().__init__()
        self.treso = tresorerie
        self.lang = lang
        self._width = width or CW
        self._height = height or 75 * mm

    def wrap(self, availWidth, availHeight):
        return self._width, self._height

    def draw(self):
        c = self.canv
        treso = self.treso
        if not treso:
            return

        # Chart area
        margin_l = 22 * mm
        margin_b = 10 * mm
        margin_r = 5 * mm
        margin_t = 8 * mm
        chart_w = self._width - margin_l - margin_r
        chart_h = self._height - margin_b - margin_t

        x0 = margin_l
        y0 = margin_b
        nb_mois = len(treso)

        # Title
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NOIR)
        c.drawString(x0, self._height - 5 * mm, _t("scurve_title", self.lang))

        # Max value for Y scale
        max_cumul = max((row.get("cumul_fcfa", 0) for row in treso), default=1)
        if max_cumul <= 0:
            max_cumul = 1

        # Y-axis grid lines and labels
        nb_ticks = 5
        c.setFont("Helvetica", 5.5)
        for i in range(nb_ticks + 1):
            yy = y0 + (i / nb_ticks) * chart_h
            val = (i / nb_ticks) * max_cumul
            c.setStrokeColor(GRIS2)
            c.setLineWidth(0.2)
            c.line(x0, yy, x0 + chart_w, yy)
            c.setFillColor(GRIS3)
            c.drawRightString(x0 - 2 * mm, yy - 1.5 * mm, _fmt_short(val))

        # X-axis labels
        step_w = chart_w / max(nb_mois, 1)
        for i, row in enumerate(treso):
            xx = x0 + (i + 0.5) * step_w
            c.setFillColor(GRIS3)
            c.setFont("Helvetica", 5.5)
            c.drawCentredString(xx, y0 - 6 * mm, f"M{row.get('mois', i+1)}")

        # Draw lines: materials cumul, labour cumul, total cumul
        mat_cumul = 0
        pose_cumul = 0
        points_mat = []
        points_pose = []
        points_total = []
        for i, row in enumerate(treso):
            xx = x0 + (i + 0.5) * step_w
            mat_cumul += row.get("depense_materiel_fcfa", 0)
            pose_cumul += row.get("depense_pose_fcfa", 0)
            cumul = row.get("cumul_fcfa", 0)
            points_mat.append((xx, y0 + (mat_cumul / max_cumul) * chart_h))
            points_pose.append((xx, y0 + (pose_cumul / max_cumul) * chart_h))
            points_total.append((xx, y0 + (cumul / max_cumul) * chart_h))

        # Draw lines
        _draw_curve(c, points_mat, VERT, 1.2)
        _draw_curve(c, points_pose, BLEU, 1.2)
        _draw_curve(c, points_total, NOIR, 1.8)

        # Legend
        legend_y = self._height - 5 * mm
        legend_x = x0 + chart_w - 60 * mm
        for color, label in [
            (VERT, _t("materiel", self.lang)),
            (BLEU, _t("pose", self.lang)),
            (NOIR, _t("cumul", self.lang)),
        ]:
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            c.line(legend_x, legend_y + 1.5 * mm, legend_x + 6 * mm, legend_y + 1.5 * mm)
            c.setFillColor(NOIR)
            c.setFont("Helvetica", 5.5)
            c.drawString(legend_x + 7 * mm, legend_y, label)
            legend_x += 22 * mm

        # Axes
        c.setStrokeColor(NOIR)
        c.setLineWidth(0.5)
        c.line(x0, y0, x0, y0 + chart_h)
        c.line(x0, y0, x0 + chart_w, y0)


# ── Helpers ──────────────────────────────────────────────────────
def _draw_curve(canvas, points, color, width):
    """Draw a polyline on the canvas."""
    if len(points) < 2:
        return
    canvas.setStrokeColor(color)
    canvas.setLineWidth(width)
    path = canvas.beginPath()
    path.moveTo(points[0][0], points[0][1])
    for px, py in points[1:]:
        path.lineTo(px, py)
    canvas.drawPath(path, fill=0, stroke=1)
    # Draw dots at data points
    canvas.setFillColor(color)
    for px, py in points:
        canvas.circle(px, py, 1, fill=1, stroke=0)


def _fmt_short(val):
    """Short format for axis labels."""
    if val >= 1e9:
        return f"{val/1e9:.1f}G"
    if val >= 1e6:
        return f"{val/1e6:.1f}M"
    if val >= 1e3:
        return f"{val/1e3:.0f}k"
    return f"{int(val)}"


def _split_groups_for_pages(planning, width, max_avail_h=150*mm):
    """Split planning tasks into page-sized chunks of groups.
    Returns a list of group-lists, each fitting within max_avail_h."""
    # Build full groups list
    seen_lots = []
    for t in planning.taches:
        if t.lot not in seen_lots:
            seen_lots.append(t.lot)
    all_groups = []
    for lot in seen_lots:
        taches = [t for t in planning.taches if t.lot == lot]
        all_groups.append((lot, taches))

    row_h = 5.5 * mm
    header_h = 7 * mm
    overhead = header_h + 4 * mm  # month header + padding
    max_rows = int((max_avail_h - overhead) / row_h)
    if max_rows < 5:
        max_rows = 5

    pages = []
    current_page = []
    current_rows = 0

    for lot, taches in all_groups:
        group_rows = 1 + len(taches)  # 1 lot header + N task rows
        if current_rows + group_rows <= max_rows:
            # Fits on current page
            current_page.append((lot, taches))
            current_rows += group_rows
        elif group_rows <= max_rows:
            # Doesn't fit current page but fits on a fresh page
            if current_page:
                pages.append(current_page)
            current_page = [(lot, taches)]
            current_rows = group_rows
        else:
            # Group itself is too large — split its tasks across pages
            if current_page:
                pages.append(current_page)
                current_page = []
                current_rows = 0
            # Split tasks into sub-chunks
            remaining = list(taches)
            while remaining:
                avail = max_rows - current_rows - 1  # -1 for lot header
                if avail < 1:
                    if current_page:
                        pages.append(current_page)
                    current_page = []
                    current_rows = 0
                    avail = max_rows - 1
                chunk = remaining[:avail]
                remaining = remaining[avail:]
                current_page.append((lot, chunk))
                current_rows += 1 + len(chunk)
                if remaining:
                    pages.append(current_page)
                    current_page = []
                    current_rows = 0

    if current_page:
        pages.append(current_page)

    return pages if pages else [all_groups]


def _is_critical_task(task, all_tasks):
    """Heuristic: a task is critical if it has no slack (fin_jour matches a successor's debut_jour)."""
    for other in all_tasks:
        if task.id in other.predecesseurs and other.debut_jour == task.fin_jour:
            return True
    # Last task in its lot is also critical
    lot_tasks = [t for t in all_tasks if t.lot == task.lot]
    if lot_tasks and lot_tasks[-1].id == task.id:
        return True
    return False


# ── Main generator ───────────────────────────────────────────────
def generer_planning_pdf(planning, lang: str = "fr") -> bytes:
    """Generate Gantt-only planning PDF (execution schedule) in LANDSCAPE mode."""
    set_pdf_lang(lang)
    buf = io.BytesIO()
    page = landscape(A4)
    hf = HeaderFooter(
        planning.projet_nom,
        _t("title_gantt", lang),
        lang=lang,
    )
    doc = SimpleDocTemplate(
        buf,
        pagesize=page,
        leftMargin=ML,
        rightMargin=MR,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
    )

    # Landscape content width
    cw_land = page[0] - ML - MR
    story = _build_gantt_story(planning, lang, content_width=cw_land)
    try:
        doc.build(story, onFirstPage=hf, onLaterPages=hf)
    except Exception:
        logger.exception("Failed to build planning PDF")
        raise
    return buf.getvalue()


def generer_tresorerie_pdf(planning, lang: str = "fr") -> bytes:
    """Generate cash flow / treasury PDF (expense schedule)."""
    set_pdf_lang(lang)
    buf = io.BytesIO()
    hf = HeaderFooter(
        planning.projet_nom,
        _t("title_cash", lang),
        lang=lang,
    )
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=ML,
        rightMargin=MR,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
    )

    story = _build_tresorerie_story(planning, lang)
    try:
        doc.build(story, onFirstPage=hf, onLaterPages=hf)
    except Exception:
        logger.exception("Failed to build tresorerie PDF")
        raise
    return buf.getvalue()


def _build_gantt_story(planning, lang, content_width=None):
    """Story for Gantt-only PDF."""
    story = []
    pl = planning
    w = content_width or CW

    story.append(Spacer(1, 3 * mm))
    story.append(p(pl.projet_nom, "titre"))
    subtitle = _t("subtitle", lang).format(
        n=pl.nb_niveaux - 1 if pl.nb_niveaux > 0 else 0,
        ville=pl.ville,
        mois=pl.duree_totale_mois,
    )
    story.append(p(subtitle, "sous_titre"))
    story.append(Spacer(1, 2 * mm))

    info = f"{fmt_n(pl.surface_batie_m2, 0)} m² — {pl.duree_totale_jours} "
    info += "jours" if lang == "fr" else "days"
    info += f" — {fmt_fcfa(pl.cout_total_fcfa)}"
    story.append(p(info, "body"))
    story.append(Spacer(1, 4 * mm))

    # Gantt chart — split across pages if too many tasks
    gantt_pages = _split_groups_for_pages(pl, w)
    for i, groups_chunk in enumerate(gantt_pages):
        if i > 0:
            story.append(PageBreak())
        gantt = GanttFlowable(pl, lang=lang, width=w, groups=groups_chunk)
        story.append(gantt)

    # Task summary table after Gantt
    story.append(PageBreak())
    story += section_title("2", "Récapitulatif des tâches" if lang == "fr" else "Task Summary")
    story.append(Spacer(1, 2 * mm))

    seen_lots = []
    for t in pl.taches:
        if t.lot not in seen_lots:
            seen_lots.append(t.lot)

    for lot in seen_lots:
        lot_label = LOT_LABELS.get(lang, LOT_LABELS["fr"]).get(lot, lot)
        lot_tasks = [t for t in pl.taches if t.lot == lot]
        lot_dur = max((t.fin_jour for t in lot_tasks), default=0) - min((t.debut_jour for t in lot_tasks), default=0)
        story.append(p(f"{lot_label} — {len(lot_tasks)} {'tâches' if lang == 'fr' else 'tasks'} — {lot_dur} {'jours' if lang == 'fr' else 'days'}", "h1"))
        story.append(Spacer(1, 1 * mm))

        header = [
            p("N°", "th"), p("Tâche" if lang == "fr" else "Task", "th"),
            p("Durée (j)" if lang == "fr" else "Duration (d)", "th"),
            p("Début (j)" if lang == "fr" else "Start (d)", "th"),
            p("Fin (j)" if lang == "fr" else "End (d)", "th"),
        ]
        rows = [header]
        col_w = [w * 0.06, w * 0.54, w * 0.12, w * 0.14, w * 0.14]
        for idx, t in enumerate(lot_tasks, 1):
            rows.append([
                p(str(idx), "td_r"),
                p(t.designation, "td"),
                p(str(t.duree_jours), "td_r"),
                p(f"J{t.debut_jour}", "td_r"),
                p(f"J{t.fin_jour}", "td_r"),
            ])
        ts = table_style(zebra=True)
        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(ts)
        story.append(tbl)
        story.append(Spacer(1, 4 * mm))

    return story


def _build_tresorerie_story(planning, lang):
    """Story for cash flow / treasury PDF."""
    story = []
    pl = planning

    story.append(Spacer(1, 3 * mm))
    story.append(p(pl.projet_nom, "titre"))
    subtitle = _t("subtitle", lang).format(
        n=pl.nb_niveaux - 1 if pl.nb_niveaux > 0 else 0,
        ville=pl.ville,
        mois=pl.duree_totale_mois,
    )
    story.append(p(subtitle, "sous_titre"))
    story.append(Spacer(1, 2 * mm))

    # ── PAGE 1: CASH FLOW TABLE ──────────────────────────────────
    story += section_title("1", _t("title_cash", lang))
    story.append(Spacer(1, 2 * mm))

    treso = pl.tresorerie_mensuelle or []
    if treso:
        header = [
            p(_t("mois", lang), "th"),
            p(_t("materiel", lang), "th"),
            p(_t("pose", lang), "th"),
            p(_t("total_mensuel", lang), "th"),
            p(_t("cumul", lang), "th"),
        ]
        rows = [header]
        col_w = [CW * 0.10, CW * 0.25, CW * 0.22, CW * 0.22, CW * 0.21]
        for row in treso:
            rows.append([
                p(f"Mois {row.get('mois', '—')}", "td"),
                p(fmt_fcfa(row.get("depense_materiel_fcfa", 0)), "td_r"),
                p(fmt_fcfa(row.get("depense_pose_fcfa", 0)), "td_r"),
                p(fmt_fcfa(row.get("depense_total_fcfa", 0)), "td_b_r"),
                p(fmt_fcfa(row.get("cumul_fcfa", 0)), "td_g_r"),
            ])
        total_mat = sum(r.get("depense_materiel_fcfa", 0) for r in treso)
        total_pose = sum(r.get("depense_pose_fcfa", 0) for r in treso)
        rows.append([
            p(_t("total", lang), "td_b"),
            p(fmt_fcfa(total_mat), "td_b_r"),
            p(fmt_fcfa(total_pose), "td_b_r"),
            p(fmt_fcfa(pl.cout_total_fcfa), "td_g_r"),
            p("", "td"),
        ])
        ts = table_style(zebra=True)
        total_row_style(ts)
        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(ts)
        story.append(tbl)

    # S-Curve
    story.append(Spacer(1, 6 * mm))
    scurve = SCurveFlowable(treso, lang=lang, width=CW, height=70 * mm)
    story.append(scurve)

    # ── PAGE 2: LOT × PHASE CROSS-TAB ───────────────────────────
    if pl.tresorerie_lot_phase:
        story.append(PageBreak())
        story += section_title("2", _t("title_cross", lang))
        story.append(Spacer(1, 2 * mm))

        cross = pl.tresorerie_lot_phase
        # Extract unique phases and lots
        phases = []
        lots = []
        data_map = {}
        for entry in cross:
            ph = entry.get("phase", "")
            lot = entry.get("lot", "")
            if ph and ph not in phases:
                phases.append(ph)
            if lot and lot not in lots:
                lots.append(lot)
            data_map[(lot, ph)] = entry.get("cout_total_fcfa", 0)

        if phases and lots:
            # Header row
            header = [p("Lot / " + _t("phase", lang), "th")]
            for ph in phases:
                header.append(p(ph, "th"))
            header.append(p(_t("total", lang), "th"))
            header.append(p(_t("pct", lang), "th"))

            nb_cols = len(phases) + 3
            col_w_cross = [CW * 0.18] + [CW * (0.64 / max(len(phases), 1))] * len(phases) + [CW * 0.12, CW * 0.06]

            rows_cross = [header]
            grand_total = max(pl.cout_total_fcfa, 1)

            for lot in lots:
                row = [p(LOT_LABELS.get(lang, LOT_LABELS["fr"]).get(lot, lot), "td_b")]
                lot_total = 0
                for ph in phases:
                    val = data_map.get((lot, ph), 0)
                    lot_total += val
                    row.append(p(fmt_fcfa(val), "td_r"))
                row.append(p(fmt_fcfa(lot_total), "td_b_r"))
                pct = (lot_total / grand_total) * 100 if grand_total else 0
                row.append(p(f"{pct:.0f}%", "td_r"))
                rows_cross.append(row)

            # Phase totals row
            total_row = [p(_t("total", lang), "td_b")]
            for ph in phases:
                ph_total = sum(data_map.get((lot, ph), 0) for lot in lots)
                total_row.append(p(fmt_fcfa(ph_total), "td_b_r"))
            total_row.append(p(fmt_fcfa(pl.cout_total_fcfa), "td_g_r"))
            total_row.append(p("100%", "td_b_r"))
            rows_cross.append(total_row)

            ts_cross = table_style(zebra=True)
            total_row_style(ts_cross)
            tbl_cross = Table(rows_cross, colWidths=col_w_cross, repeatRows=1)
            tbl_cross.setStyle(ts_cross)
            story.append(tbl_cross)

            # Cost summary
            story.append(Spacer(1, 4 * mm))
            story.append(p(
                f"{_t('cout_total', lang)} : {fmt_fcfa(pl.cout_total_fcfa)}",
                "h1",
            ))

    return story

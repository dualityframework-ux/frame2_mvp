"""
export_era_comparison_pdf.py
Generates a multi-page infographic PDF for the Red Sox Era Comparison dashboard.
Usage:  python export_era_comparison_pdf.py [output_path]
"""

import sys, os, math, textwrap
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.flowables import KeepTogether
import io

# ── project imports ──────────────────────────────────────────────────────────
from adapters.redsox_history_loader import load_redsox_history
from intelligence.redsox_history_engine import classify_process_vs_result

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
MACRO_ERAS = {
    "Yaz Era\n(1967–76)":              list(range(1967, 1977)),
    "Rice & Lynn\n(1977–86)":          list(range(1977, 1987)),
    "Boggs & Clemens\n(1987–96)":      list(range(1987, 1997)),
    "Pedro & Manny\n(1997–2006)":      list(range(1997, 2007)),
    "Francona Dynasty\n(2007–13)":     list(range(2007, 2014)),
    "Betts Emergence\n(2014–19)":      list(range(2014, 2020)),
    "Rebuild & Now\n(2020–24)":        list(range(2020, 2025)),
}

ERA_EMOJIS = {
    "Yaz Era\n(1967–76)":           "⚾",
    "Rice & Lynn\n(1977–86)":        "💪",
    "Boggs & Clemens\n(1987–96)":    "🎯",
    "Pedro & Manny\n(1997–2006)":    "🔥",
    "Francona Dynasty\n(2007–13)":   "🏆",
    "Betts Emergence\n(2014–19)":    "🌟",
    "Rebuild & Now\n(2020–24)":      "🔄",
}

ERA_COLORS_HEX = {
    "Yaz Era\n(1967–76)":           "#4a90d9",
    "Rice & Lynn\n(1977–86)":        "#e4b84d",
    "Boggs & Clemens\n(1987–96)":    "#7eb8f7",
    "Pedro & Manny\n(1997–2006)":    "#c8102e",
    "Francona Dynasty\n(2007–13)":   "#2da870",
    "Betts Emergence\n(2014–19)":    "#c8940a",
    "Rebuild & Now\n(2020–24)":      "#999999",
}

# Short names for chart labels
ERA_SHORT = {
    "Yaz Era\n(1967–76)":           "Yaz Era",
    "Rice & Lynn\n(1977–86)":        "Rice & Lynn",
    "Boggs & Clemens\n(1987–96)":    "Boggs & Clemens",
    "Pedro & Manny\n(1997–2006)":    "Pedro & Manny",
    "Francona Dynasty\n(2007–13)":   "Francona Dyn.",
    "Betts Emergence\n(2014–19)":    "Betts Era",
    "Rebuild & Now\n(2020–24)":      "Rebuild & Now",
}

RED_SOX_RED   = "#c8102e"
RED_SOX_NAVY  = "#0d1b2a"
LIGHT_GRAY    = "#f5f5f5"
MID_GRAY      = "#cccccc"
DARK_GRAY     = "#555555"
WHITE         = "#ffffff"
GOLD          = "#e4b84d"

# ══════════════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ══════════════════════════════════════════════════════════════════════════════
def build_era_stats(df):
    era_map = {}
    for era, yrs in MACRO_ERAS.items():
        for y in yrs:
            era_map[y] = era
    df = df.copy()
    df["macro_era"] = df["season"].map(era_map)
    df["tag"] = df.apply(classify_process_vs_result, axis=1)

    stats = []
    for era in MACRO_ERAS:
        sub = df[df["macro_era"] == era]
        ws = (sub["playoff_result"] == "world series").sum()
        playoff = sub["playoff_result"].isin(
            ["world series", "lost alcs", "lost alds", "al east tie-break loss"]
        ).sum()
        n = len(sub)
        tag_counts = sub["tag"].value_counts().to_dict()
        best = sub.loc[sub["wins"].idxmax(), "season"] if n else None
        worst = sub.loc[sub["wins"].idxmin(), "season"] if n else None
        stats.append({
            "era":          era,
            "short":        ERA_SHORT[era],
            "color":        ERA_COLORS_HEX[era],
            "n":            n,
            "avg_wins":     round(sub["wins"].mean(), 1),
            "avg_losses":   round(sub["losses"].mean(), 1),
            "avg_rd":       round(sub["run_diff"].mean(), 1),
            "avg_ops":      round(sub["team_ops"].mean(), 3),
            "avg_obp":      round(sub["team_obp"].mean(), 3),
            "avg_slg":      round(sub["team_slg"].mean(), 3),
            "avg_era":      round(sub["team_era"].mean(), 2),
            "avg_fip":      round(sub["team_fip"].mean(), 2),
            "ws_titles":    int(ws),
            "playoff_apps": int(playoff),
            "playoff_rate": round(playoff / n * 100, 0) if n else 0,
            "best_season":  int(best) if best else "-",
            "worst_season": int(worst) if worst else "-",
            "signal":       tag_counts.get("signal", 0),
            "balanced":     tag_counts.get("balanced", 0),
            "overperformed":tag_counts.get("overperformed process", 0),
            "underperformed":tag_counts.get("underperformed process", 0),
        })
    return pd.DataFrame(stats), df

# ══════════════════════════════════════════════════════════════════════════════
# MATPLOTLIB CHART HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))

def fig_to_image_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

def set_axis_style(ax, title="", xlabel="", ylabel="", grid=True):
    ax.set_facecolor(LIGHT_GRAY)
    ax.set_title(title, fontsize=10, fontweight="bold", color=RED_SOX_NAVY, pad=8)
    if xlabel: ax.set_xlabel(xlabel, fontsize=8, color=DARK_GRAY)
    if ylabel: ax.set_ylabel(ylabel, fontsize=8, color=DARK_GRAY)
    ax.tick_params(colors=DARK_GRAY, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(MID_GRAY)
    if grid:
        ax.grid(axis="y", color=MID_GRAY, linestyle="--", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

# ── CHART 1: Avg Wins per Era ──────────────────────────────────────────────
def chart_avg_wins(era_df):
    fig, ax = plt.subplots(figsize=(8, 3.5), facecolor=WHITE)
    names  = era_df["short"].tolist()
    vals   = era_df["avg_wins"].tolist()
    colors_list = [hex_to_rgb(c) for c in era_df["color"]]
    bars = ax.bar(names, vals, color=colors_list, width=0.6, zorder=3,
                  edgecolor="white", linewidth=0.8)
    ax.axhline(81, color=RED_SOX_RED, linestyle="--", linewidth=1.2,
               alpha=0.7, label=".500 (81 wins)")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.5, f"{v}",
                ha="center", va="bottom", fontsize=8, fontweight="bold",
                color=RED_SOX_NAVY)
    ax.set_ylim(60, 100)
    ax.legend(fontsize=7, loc="lower right", frameon=True)
    set_axis_style(ax, "Average Wins Per Season by Era", ylabel="Avg Wins")
    ax.set_xticklabels(names, fontsize=7, rotation=15, ha="right")
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 2: Avg Run Differential ─────────────────────────────────────────
def chart_avg_rd(era_df):
    fig, ax = plt.subplots(figsize=(8, 3.5), facecolor=WHITE)
    names = era_df["short"].tolist()
    vals  = era_df["avg_rd"].tolist()
    bar_colors = ["#2da870" if v >= 0 else "#c8102e" for v in vals]
    bars = ax.bar(names, vals, color=bar_colors, width=0.6, zorder=3,
                  edgecolor="white", linewidth=0.8)
    ax.axhline(0, color=RED_SOX_NAVY, linewidth=1.0, alpha=0.6)
    for bar, v in zip(bars, vals):
        offset = 1.5 if v >= 0 else -4
        va = "bottom" if v >= 0 else "top"
        ax.text(bar.get_x() + bar.get_width()/2, v + offset, f"{v:+.0f}",
                ha="center", va=va, fontsize=8, fontweight="bold", color=WHITE
                if abs(v) > 20 else RED_SOX_NAVY)
    set_axis_style(ax, "Average Run Differential Per Season by Era", ylabel="Avg Run Diff")
    ax.set_xticklabels(names, fontsize=7, rotation=15, ha="right")
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 3: OPS vs ERA side-by-side grouped ──────────────────────────────
def chart_offense_pitching(era_df):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), facecolor=WHITE)
    names  = era_df["short"].tolist()
    x      = np.arange(len(names))
    colors_list = [hex_to_rgb(c) for c in era_df["color"]]

    # OPS
    ax = axes[0]
    bars = ax.bar(x, era_df["avg_ops"], color=colors_list, width=0.6, zorder=3,
                  edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, era_df["avg_ops"]):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.002, f"{v:.3f}",
                ha="center", va="bottom", fontsize=7, fontweight="bold", color=RED_SOX_NAVY)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.5, rotation=20, ha="right")
    set_axis_style(ax, "Avg Team OPS by Era", ylabel="OPS")
    ax.set_ylim(0.68, 0.85)

    # ERA
    ax = axes[1]
    bars = ax.bar(x, era_df["avg_era"], color=colors_list, width=0.6, zorder=3,
                  edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, era_df["avg_era"]):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.03, f"{v:.2f}",
                ha="center", va="bottom", fontsize=7, fontweight="bold", color=RED_SOX_NAVY)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.5, rotation=20, ha="right")
    set_axis_style(ax, "Avg Team ERA by Era", ylabel="ERA")
    ax.set_ylim(3.0, 5.2)

    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 4: Radar / Spider Chart ─────────────────────────────────────────
def normalize_col(series, invert=False):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0]*len(series), index=series.index)
    norm = (series - mn) / (mx - mn) * 100
    return 100 - norm if invert else norm

def chart_radar(era_df):
    categories = ["Win %", "Run Diff", "OPS", "ERA (inv)", "FIP (inv)"]
    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    era_df = era_df.copy()
    era_df["win_pct_norm"] = normalize_col(era_df["avg_wins"])
    era_df["rd_norm"]      = normalize_col(era_df["avg_rd"])
    era_df["ops_norm"]     = normalize_col(era_df["avg_ops"])
    era_df["era_norm"]     = normalize_col(era_df["avg_era"], invert=True)
    era_df["fip_norm"]     = normalize_col(era_df["avg_fip"], invert=True)

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True), facecolor=WHITE)
    ax.set_facecolor(LIGHT_GRAY)

    for _, row in era_df.iterrows():
        vals = [row["win_pct_norm"], row["rd_norm"], row["ops_norm"],
                row["era_norm"], row["fip_norm"]]
        vals += vals[:1]
        c = hex_to_rgb(row["color"])
        ax.plot(angles, vals, color=c, linewidth=2, linestyle="solid")
        ax.fill(angles, vals, color=c, alpha=0.12)

    ax.set_thetagrids([a * 180/math.pi for a in angles[:-1]], categories,
                      fontsize=8, color=RED_SOX_NAVY)
    ax.set_ylim(0, 100)
    ax.set_yticklabels([])
    ax.grid(color=MID_GRAY, linewidth=0.5)
    ax.set_title("Era Profile Radar\n(normalised, higher = better)", fontsize=9,
                 fontweight="bold", color=RED_SOX_NAVY, pad=15)

    legend_patches = [
        mpatches.Patch(color=hex_to_rgb(row["color"]), label=row["short"])
        for _, row in era_df.iterrows()
    ]
    ax.legend(handles=legend_patches, loc="upper right",
              bbox_to_anchor=(1.35, 1.15), fontsize=7, frameon=True,
              fancybox=True, shadow=False)
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 5: Scatter – Wins vs Run Diff (all seasons) ────────────────────
def chart_scatter(full_df, era_df):
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=WHITE)
    ax.set_facecolor(LIGHT_GRAY)

    era_color_map = dict(zip(era_df["era"], era_df["color"]))
    for _, row in full_df.dropna(subset=["macro_era"]).iterrows():
        c = hex_to_rgb(era_color_map.get(row["macro_era"], "#999"))
        ax.scatter(row["run_diff"], row["wins"], color=c, s=50, alpha=0.8,
                   edgecolors="white", linewidth=0.5, zorder=3)
        if row["playoff_result"] == "world series":
            ax.scatter(row["run_diff"], row["wins"], s=120, facecolors="none",
                       edgecolors=GOLD, linewidth=2, zorder=4)
            ax.annotate(str(int(row["season"])),
                        (row["run_diff"], row["wins"]),
                        textcoords="offset points", xytext=(5, 3),
                        fontsize=6.5, color=GOLD, fontweight="bold")

    ax.axhline(81, color=RED_SOX_RED, linestyle="--", linewidth=1, alpha=0.6)
    ax.axvline(0,  color=RED_SOX_RED, linestyle="--", linewidth=1, alpha=0.6)
    set_axis_style(ax, "Wins vs Run Differential — All 58 Seasons",
                   xlabel="Run Differential", ylabel="Wins")
    ax.text(-280, 81.5, ".500", fontsize=7, color=RED_SOX_RED, alpha=0.8)
    ax.text(1, 62, "Zero RD", fontsize=7, color=RED_SOX_RED, alpha=0.8, rotation=90)

    legend_patches = [
        mpatches.Patch(color=hex_to_rgb(era_color_map[e["era"]]), label=e["short"])
        for _, e in era_df.iterrows()
    ]
    legend_patches.append(
        Line2D([0],[0], marker='o', color='w', markerfacecolor='none',
               markeredgecolor=GOLD, markeredgewidth=2, markersize=9,
               label="World Series Win")
    )
    ax.legend(handles=legend_patches, fontsize=6.5, loc="upper left",
              frameon=True, ncol=2)
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 6: Process Tag Breakdown ─────────────────────────────────────────
def chart_process_tags(era_df):
    fig, ax = plt.subplots(figsize=(9, 3.5), facecolor=WHITE)
    names   = era_df["short"].tolist()
    x       = np.arange(len(names))
    width   = 0.2

    tag_cols  = ["signal", "balanced", "overperformed", "underperformed"]
    tag_labels= ["Signal (process backed)", "Balanced", "Overperformed", "Underperformed"]
    tag_colors= ["#2da870", "#4a90d9", "#e4b84d", "#c8102e"]

    for i, (col, lbl, clr) in enumerate(zip(tag_cols, tag_labels, tag_colors)):
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, era_df[col], width, label=lbl,
                      color=clr, alpha=0.85, zorder=3, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=7, rotation=15, ha="right")
    ax.set_ylabel("Season Count", fontsize=8)
    set_axis_style(ax, "Process vs Result Tag Breakdown by Era")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 7: Wins timeline all seasons ────────────────────────────────────
def chart_wins_timeline(full_df, era_df):
    fig, ax = plt.subplots(figsize=(11, 3.5), facecolor=WHITE)
    ax.set_facecolor(LIGHT_GRAY)
    ax.plot(full_df["season"], full_df["wins"], color=MID_GRAY,
            linewidth=1.2, alpha=0.5, zorder=1)

    era_color_map = dict(zip(era_df["era"], era_df["color"]))
    for era_name, seasons in MACRO_ERAS.items():
        sub = full_df[full_df["season"].isin(seasons)]
        c = hex_to_rgb(era_color_map.get(era_name, "#999"))
        ax.plot(sub["season"], sub["wins"], color=c, linewidth=2.2,
                alpha=0.9, zorder=2)

    ws_seasons = full_df[full_df["playoff_result"] == "world series"]
    ax.scatter(ws_seasons["season"], ws_seasons["wins"],
               s=120, color=GOLD, zorder=5, marker="*", label="World Series Win")
    ax.axhline(81, color=RED_SOX_RED, linestyle="--", linewidth=1, alpha=0.6)

    # era boundary lines
    boundaries = [1967, 1977, 1987, 1997, 2007, 2014, 2020, 2025]
    for b in boundaries:
        ax.axvline(b, color=MID_GRAY, linestyle=":", linewidth=0.8, alpha=0.6)

    set_axis_style(ax, "Season Win Totals — 1967 to 2024",
                   xlabel="Season", ylabel="Wins")
    ax.set_xlim(1965, 2026)
    ax.set_ylim(50, 120)
    ax.legend(fontsize=7, loc="upper right")

    legend_patches = [
        mpatches.Patch(color=hex_to_rgb(era_color_map[e["era"]]), label=e["short"])
        for _, e in era_df.iterrows()
    ]
    ax.legend(handles=legend_patches + [
        Line2D([0],[0], marker='*', color='w', markerfacecolor=GOLD,
               markersize=10, label="World Series")
    ], fontsize=6.5, loc="upper right", ncol=2, frameon=True)
    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ── CHART 8: WS Titles & Playoff Rate ─────────────────────────────────────
def chart_titles_and_playoff(era_df):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), facecolor=WHITE)
    names  = era_df["short"].tolist()
    x      = np.arange(len(names))
    colors_list = [hex_to_rgb(c) for c in era_df["color"]]

    ax = axes[0]
    bars = ax.bar(x, era_df["ws_titles"], color=colors_list, width=0.6,
                  zorder=3, edgecolor="white")
    for bar, v in zip(bars, era_df["ws_titles"]):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.05, "[WS]"*v,
                    ha="center", va="bottom", fontsize=9, fontweight="bold",
                    color=GOLD)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.5, rotation=20, ha="right")
    ax.set_yticks([0,1,2])
    set_axis_style(ax, "World Series Titles by Era", ylabel="Titles")

    ax = axes[1]
    bars = ax.bar(x, era_df["playoff_rate"], color=colors_list, width=0.6,
                  zorder=3, edgecolor="white")
    for bar, v in zip(bars, era_df["playoff_rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{v:.0f}%",
                ha="center", va="bottom", fontsize=8, fontweight="bold",
                color=RED_SOX_NAVY)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.5, rotation=20, ha="right")
    set_axis_style(ax, "Playoff Appearance Rate by Era", ylabel="% of Seasons")
    ax.set_ylim(0, 80)

    fig.tight_layout(pad=1.5)
    return fig_to_image_bytes(fig)

# ══════════════════════════════════════════════════════════════════════════════
# REPORTLAB PDF ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════
def build_pdf(output_path):
    df = load_redsox_history()
    era_df, full_df = build_era_stats(df)

    # ── styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Normal"],
        fontSize=28, fontName="Helvetica-Bold",
        textColor=colors.HexColor(WHITE),
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica",
        textColor=colors.HexColor(GOLD),
        alignment=TA_CENTER, spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=colors.HexColor(RED_SOX_NAVY),
        spaceBefore=14, spaceAfter=6,
        borderPad=0,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=8.5, fontName="Helvetica",
        textColor=colors.HexColor(DARK_GRAY),
        leading=13, spaceAfter=4,
    )
    kpi_label_style = ParagraphStyle(
        "KPILabel", parent=styles["Normal"],
        fontSize=7.5, fontName="Helvetica",
        textColor=colors.HexColor(DARK_GRAY),
        alignment=TA_CENTER,
    )
    kpi_value_style = ParagraphStyle(
        "KPIValue", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica-Bold",
        textColor=colors.HexColor(RED_SOX_RED),
        alignment=TA_CENTER,
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica-Oblique",
        textColor=colors.HexColor(MID_GRAY),
        alignment=TA_CENTER, spaceBefore=2,
    )
    table_header_style = ParagraphStyle(
        "TblHdr", parent=styles["Normal"],
        fontSize=7.5, fontName="Helvetica-Bold",
        textColor=colors.HexColor(WHITE),
        alignment=TA_CENTER,
    )
    table_cell_style = ParagraphStyle(
        "TblCell", parent=styles["Normal"],
        fontSize=7.5, fontName="Helvetica",
        textColor=colors.HexColor(RED_SOX_NAVY),
        alignment=TA_CENTER,
    )

    # ── doc setup ────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.55*inch, leftMargin=0.55*inch,
        topMargin=0.55*inch, bottomMargin=0.6*inch,
        title="Red Sox Era Comparison Report",
        author="Red Sox Analytics",
    )
    story = []
    PW = letter[0] - 1.1*inch   # usable page width

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ════════════════════════════════════════════════════════════════════════
    def cover_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(RED_SOX_NAVY))
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        # Red accent strip
        canvas.setFillColor(colors.HexColor(RED_SOX_RED))
        canvas.rect(0, letter[1]*0.35, letter[0], 4, fill=1, stroke=0)
        canvas.rect(0, letter[1]*0.65, letter[0], 4, fill=1, stroke=0)
        canvas.restoreState()

    # We'll simulate cover with colored table
    cover_data = [
        [Paragraph("", title_style)],
        [Paragraph("⚾  RED SOX FRANCHISE", title_style)],
        [Paragraph("ERA COMPARISON REPORT", title_style)],
        [Paragraph("1967 – 2024  ·  Seven Eras  ·  58 Seasons  ·  6 World Series Titles", subtitle_style)],
        [Paragraph("", body_style)],
        [Paragraph("A statistical deep-dive into every major era of Red Sox baseball,", body_style)],
        [Paragraph("from the Impossible Dream of 1967 to the rebuilding present.", body_style)],
    ]
    cover_table = Table(cover_data, colWidths=[PW])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor(RED_SOX_NAVY)),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
        ("LINEBELOW", (0,1), (-1,1), 1.5, colors.HexColor(RED_SOX_RED)),
        ("LINEABOVE", (0,6), (-1,6), 1.5, colors.HexColor(RED_SOX_RED)),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(Spacer(1, 1.8*inch))
    story.append(cover_table)
    story.append(Spacer(1, 0.4*inch))

    # KPI row on cover
    total_ws = era_df["ws_titles"].sum()
    total_seasons = era_df["n"].sum()
    best_era = era_df.loc[era_df["avg_wins"].idxmax(), "short"]
    best_rd  = era_df.loc[era_df["avg_rd"].idxmax(), "short"]

    kpi_data = [[
        Paragraph(f'<font color="{GOLD}" size="22"><b>{total_seasons}</b></font><br/><font size="8" color="#cccccc">Total Seasons</font>', body_style),
        Paragraph(f'<font color="{GOLD}" size="22"><b>{total_ws}</b></font><br/><font size="8" color="#cccccc">World Series Titles</font>', body_style),
        Paragraph(f'<font color="{GOLD}" size="13"><b>{best_era}</b></font><br/><font size="8" color="#cccccc">Most Wins Era</font>', body_style),
        Paragraph(f'<font color="{GOLD}" size="13"><b>{best_rd}</b></font><br/><font size="8" color="#cccccc">Best Run Diff Era</font>', body_style),
    ]]
    kpi_table = Table(kpi_data, colWidths=[PW/4]*4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#152235")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),12),
        ("BOTTOMPADDING",(0,0),(-1,-1),12),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor(RED_SOX_RED)),
        ("ROUNDEDCORNERS",[4]),
    ]))
    story.append(kpi_table)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 2 — ERA OVERVIEW SUMMARY TABLE
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Era Overview", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))
    story.append(Paragraph(
        "Seven macro-eras spanning 58 seasons. Each era is defined by roster identity, "
        "organizational philosophy, and on-field performance. All metrics are per-season averages.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    # Table header
    hdr = ["Era", "Seasons", "Avg W", "Avg L", "Avg RD", "Avg OPS",
           "Avg ERA", "Avg FIP", "WS 🏆", "Playoff %"]
    tbl_data = [[Paragraph(h, table_header_style) for h in hdr]]
    for _, row in era_df.iterrows():
        tbl_data.append([
            Paragraph(row["short"], table_cell_style),
            Paragraph(f"{int(row['n'])} ({row['era'].split(chr(10))[-1].strip().split('–')[0]}–{row['era'].split(chr(10))[-1].strip().split('–')[-1].replace(')','')})", table_cell_style),
            Paragraph(str(row["avg_wins"]), table_cell_style),
            Paragraph(str(row["avg_losses"]), table_cell_style),
            Paragraph(f"{row['avg_rd']:+.1f}", table_cell_style),
            Paragraph(f"{row['avg_ops']:.3f}", table_cell_style),
            Paragraph(f"{row['avg_era']:.2f}", table_cell_style),
            Paragraph(f"{row['avg_fip']:.2f}", table_cell_style),
            Paragraph(str(int(row["ws_titles"])), table_cell_style),
            Paragraph(f"{row['playoff_rate']:.0f}%", table_cell_style),
        ])

    col_widths = [PW*0.18, PW*0.14, PW*0.08, PW*0.08,
                  PW*0.08, PW*0.09, PW*0.09, PW*0.09,
                  PW*0.07, PW*0.10]
    overview_table = Table(tbl_data, colWidths=col_widths, repeatRows=1)

    era_hex_list = [era_df.iloc[i]["color"] for i in range(len(era_df))]
    row_styles = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor(RED_SOX_NAVY)),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor(MID_GRAY)),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor(LIGHT_GRAY)]),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
    ]
    for i, hex_c in enumerate(era_hex_list):
        row_styles.append(("LEFTPADDING", (0, i+1), (0, i+1), 5))
        row_styles.append(("BACKGROUND", (0, i+1), (0, i+1),
                            colors.HexColor(hex_c + "30")))  # 30 = ~20% opacity
    overview_table.setStyle(TableStyle(row_styles))
    story.append(overview_table)
    story.append(Spacer(1, 0.15*inch))

    # Best/worst season note
    best_season_col = era_df[["short","best_season","worst_season"]]
    story.append(Paragraph(
        "  ·  ".join(
            f"<b>{r['short']}</b>: best {r['best_season']}, worst {r['worst_season']}"
            for _, r in best_season_col.iterrows()
        ), body_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 3 — WINS & RUN DIFFERENTIAL CHARTS
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Wins & Run Differential", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))

    wins_img = chart_avg_wins(era_df)
    story.append(RLImage(wins_img, width=PW, height=2.8*inch))
    story.append(Paragraph(
        "The Francona Dynasty (2007–13) edges out Pedro & Manny (1997–2006) in average wins. "
        "The dotted red line marks .500 (81 wins). All eras except the current rebuild period "
        "averaged above .500.",
        caption_style
    ))
    story.append(Spacer(1, 0.18*inch))

    rd_img = chart_avg_rd(era_df)
    story.append(RLImage(rd_img, width=PW, height=2.8*inch))
    story.append(Paragraph(
        "Run differential is a stronger predictor of true team quality than wins alone. "
        "The Francona Dynasty (+119 avg) is the clear process leader. "
        "The Rebuild & Now era is the only one with a negative average run differential.",
        caption_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 4 — OFFENSE & PITCHING
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Offense vs Pitching", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))
    story.append(Paragraph(
        "OPS (On-base Plus Slugging) measures overall offensive production. "
        "ERA (Earned Run Average) measures pitching effectiveness — lower is better. "
        "Note that ERA league baselines shifted across decades (Year of the Pitcher in 1968, "
        "steroids era in the late 1990s–2000s).",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    off_pitch_img = chart_offense_pitching(era_df)
    story.append(RLImage(off_pitch_img, width=PW, height=3.0*inch))
    story.append(Paragraph(
        "Pedro & Manny recorded the highest OPS (.803) in a high-scoring era. "
        "The Yaz Era had the best ERA (3.66) in a pitcher-dominated period. "
        "Rebuild & Now has the worst ERA (4.59) and below-average OPS.",
        caption_style
    ))
    story.append(Spacer(1, 0.18*inch))

    # OBP / SLG / FIP comparison table
    story.append(Paragraph("Detailed Offensive & Pitching Metrics", section_style))
    detail_hdr = ["Era", "Avg OBP", "Avg SLG", "Avg OPS", "Avg ERA", "Avg FIP"]
    detail_data = [[Paragraph(h, table_header_style) for h in detail_hdr]]
    for _, row in era_df.iterrows():
        detail_data.append([
            Paragraph(row["short"], table_cell_style),
            Paragraph(f"{row['avg_obp']:.3f}", table_cell_style),
            Paragraph(f"{row['avg_slg']:.3f}", table_cell_style),
            Paragraph(f"{row['avg_ops']:.3f}", table_cell_style),
            Paragraph(f"{row['avg_era']:.2f}", table_cell_style),
            Paragraph(f"{row['avg_fip']:.2f}", table_cell_style),
        ])
    detail_col_w = [PW*0.28] + [PW*0.144]*5
    detail_table = Table(detail_data, colWidths=detail_col_w, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor(RED_SOX_NAVY)),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor(MID_GRAY)),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor(LIGHT_GRAY)]),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("FONTSIZE",(0,0),(-1,-1),8),
    ]))
    story.append(detail_table)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 5 — RADAR CHART
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Era Profile Radar", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))
    story.append(Paragraph(
        "Each axis is normalised 0–100 relative to the best and worst era for that dimension. "
        "ERA and FIP are inverted so that a larger area always represents a better performance. "
        "A perfectly round web at 100 would be the ideal franchise era.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    radar_img = chart_radar(era_df)
    story.append(RLImage(radar_img, width=PW*0.7, height=4.0*inch))
    story.append(Paragraph(
        "The Francona Dynasty (green) and Pedro & Manny (red) eras dominate most axes. "
        "The Boggs & Clemens era (light blue) shows a distinctly narrow win-% footprint "
        "despite competitive pitching.",
        caption_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 6 — SCATTER + TIMELINE
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Wins vs Run Differential — All 58 Seasons", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))
    story.append(Paragraph(
        "Every season plotted by wins (y-axis) and run differential (x-axis). "
        "Gold stars mark World Series wins. Seasons in the top-right quadrant "
        "(high wins, high run diff) are genuine process-backed contenders. "
        "Top-left quadrant seasons won more games than their run diff warranted — "
        "potential overperformers.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    scatter_img = chart_scatter(full_df, era_df)
    story.append(RLImage(scatter_img, width=PW, height=3.0*inch))
    story.append(Spacer(1, 0.18*inch))

    story.append(Paragraph("Season Win Totals — 1967 to 2024", section_style))
    story.append(HRFlowable(width=PW, thickness=1, color=colors.HexColor(MID_GRAY), spaceAfter=6))
    timeline_img = chart_wins_timeline(full_df, era_df)
    story.append(RLImage(timeline_img, width=PW, height=2.6*inch))
    story.append(Paragraph(
        "Era boundaries marked with dotted vertical lines. Gold stars = World Series wins. "
        "Coloured lines represent each macro-era; grey background line shows all 58 seasons.",
        caption_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 7 — TITLES, PLAYOFF RATE, PROCESS TAGS
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Titles, Playoff Rate & Process Quality", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))

    titles_img = chart_titles_and_playoff(era_df)
    story.append(RLImage(titles_img, width=PW, height=2.8*inch))
    story.append(Paragraph(
        "The Yaz Era and Francona Dynasty share 2 titles each. "
        "Boggs & Clemens produced zero championships despite above-.500 winning percentages. "
        "The Francona Dynasty has the highest playoff appearance rate at 57%.",
        caption_style
    ))
    story.append(Spacer(1, 0.18*inch))

    story.append(Paragraph("Process vs Result Classification", section_style))
    story.append(HRFlowable(width=PW, thickness=1, color=colors.HexColor(MID_GRAY), spaceAfter=6))
    story.append(Paragraph(
        "Each season is classified using run differential vs win total relative to league norms. "
        "<b>Signal ✅</b> = won AND had the process to back it. "
        "<b>Balanced ➡️</b> = results matched underlying performance. "
        "<b>Overperformed 🍀</b> = won more than the process predicted. "
        "<b>Underperformed 📉</b> = won fewer than the process predicted.",
        body_style
    ))
    story.append(Spacer(1, 0.06*inch))
    tags_img = chart_process_tags(era_df)
    story.append(RLImage(tags_img, width=PW, height=2.8*inch))
    story.append(Paragraph(
        "The Francona Dynasty and Betts Emergence eras have the highest signal density, "
        "indicating that their wins were backed by genuine process quality. "
        "[WS] in the titles chart = World Series championship.",
        caption_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 8 — FULL SEASON-BY-SEASON TABLE
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Full Season Reference Table — All 58 Seasons", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=8))

    full_hdr = ["Year", "W", "L", "RD", "Result", "OPS", "ERA", "FIP", "Manager", "Players"]
    full_tbl = [[Paragraph(h, table_header_style) for h in full_hdr]]
    for _, row in full_df.sort_values("season").iterrows():
        players = str(row.get("key_players",""))
        if len(players) > 35:
            players = players[:34] + "…"
        result_str = str(row["playoff_result"]).replace("world series","🏆 WS").replace(
            "lost alcs","🔴 ALCS").replace("lost alds","🔵 ALDS").replace(
            "al east tie-break loss","⚡ TBL").replace("missed playoffs","—")
        full_tbl.append([
            Paragraph(str(int(row["season"])), table_cell_style),
            Paragraph(str(int(row["wins"])), table_cell_style),
            Paragraph(str(int(row["losses"])), table_cell_style),
            Paragraph(f"{row['run_diff']:+d}", table_cell_style),
            Paragraph(result_str, table_cell_style),
            Paragraph(f"{row['team_ops']:.3f}", table_cell_style),
            Paragraph(f"{row['team_era']:.2f}", table_cell_style),
            Paragraph(f"{row['team_fip']:.2f}", table_cell_style),
            Paragraph(str(row["manager"]), table_cell_style),
            Paragraph(players, table_cell_style),
        ])

    full_col_w = [PW*0.07, PW*0.05, PW*0.05, PW*0.07, PW*0.11,
                  PW*0.07, PW*0.07, PW*0.07, PW*0.12, PW*0.26]
    full_table = Table(full_tbl, colWidths=full_col_w, repeatRows=1)

    era_color_map = dict(zip(era_df["era"], era_df["color"]))
    full_styles = [
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor(RED_SOX_NAVY)),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor(MID_GRAY)),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("FONTSIZE",(0,0),(-1,-1),6.5),
    ]
    # Highlight WS rows
    for i, (_, row) in enumerate(full_df.sort_values("season").iterrows()):
        if row["playoff_result"] == "world series":
            full_styles.append(("BACKGROUND",(0,i+1),(-1,i+1),
                                 colors.HexColor(GOLD + "40")))
        elif i % 2 == 0:
            full_styles.append(("BACKGROUND",(0,i+1),(-1,i+1),
                                 colors.HexColor(LIGHT_GRAY)))

    full_table.setStyle(TableStyle(full_styles))
    story.append(full_table)
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "🏆 WS = World Series win  ·  🔴 ALCS = lost ALCS  ·  🔵 ALDS = lost ALDS  "
        "·  ⚡ TBL = AL East tie-break loss  ·  — = missed playoffs  ·  Gold rows = championships",
        caption_style
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # PAGE 9 — CLOSING / INSIGHTS
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Key Insights & Takeaways", section_style))
    story.append(HRFlowable(width=PW, thickness=2, color=colors.HexColor(RED_SOX_RED), spaceAfter=10))

    insights = [
        ("Process Leaders", "The Francona Dynasty (2007–13) leads all eras in run differential (+119 avg), "
         "making it the most process-backed era in franchise history — two titles backed by genuine dominance."),
        ("Offensive Peak", "The Pedro & Manny era (1997–2006) posted the highest team OPS (.803), "
         "fueled by Manny Ramirez, David Ortiz, and one of the deepest lineups in AL history."),
        ("Pitching Dominance", "The Yaz Era (1967–76) had the best team ERA (3.66) in a pitcher-friendly "
         "period, built around Dick Williams' pitching-first philosophy and Carl Yastrzemski's leadership."),
        ("Championship Efficiency", "The Yaz Era won 2 World Series in 10 seasons (20%) while averaging only "
         "87 wins — proof that playoff structure and timing matter as much as regular-season dominance."),
        ("The Drought Era", "Boggs & Clemens (1987–96) produced zero championships in a decade despite "
         "Roger Clemens' peak years. Playoff losses in 1986 (ALCS) and 1988, 1990 (ALCS) defined the era."),
        ("Current State", "Rebuild & Now (2020–24) is the weakest era by every metric — 70.6 avg wins, "
         "−6 run differential — but Devers, Duran, Bello, and Houck represent the foundation of what comes next."),
        ("Process vs Luck", "The Francona Dynasty and Betts Emergence eras have the highest signal density, "
         "meaning their wins were earned. The Yaz Era shows more 'overperformed' seasons, consistent with "
         "an era where clutch moments (1967, 1975 WS) outshone underlying metrics."),
    ]
    for title, body in insights:
        insight_data = [[
            Paragraph(f"<b>{title}</b>", ParagraphStyle(
                "InsightTitle", parent=styles["Normal"],
                fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor(RED_SOX_RED)
            )),
        ],[
            Paragraph(body, body_style),
        ]]
        insight_table = Table(insight_data, colWidths=[PW])
        insight_table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#fff0f3")),
            ("BACKGROUND",(0,1),(-1,1), colors.white),
            ("LEFTPADDING",(0,0),(-1,-1), 10),
            ("RIGHTPADDING",(0,0),(-1,-1), 10),
            ("TOPPADDING",(0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("BOX",(0,0),(-1,-1),0.8,colors.HexColor(MID_GRAY)),
            ("LINEBELOW",(0,0),(-1,0),0.5,colors.HexColor(RED_SOX_RED)),
        ]))
        story.append(insight_table)
        story.append(Spacer(1, 0.09*inch))

    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width=PW, thickness=1, color=colors.HexColor(MID_GRAY)))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        "Red Sox Franchise Timeline Report  ·  Generated by frame2-redsox-history analytics engine  "
        "·  1967–2024  ·  58 seasons  ·  All statistics from redsox_history.csv",
        caption_style
    ))

    # ── Build ────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"PDF saved → {output_path}")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "frame2_redsox_era_comparison.pdf"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_pdf(out)

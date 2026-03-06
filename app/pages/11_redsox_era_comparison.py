"""
11_redsox_era_comparison.py
Side-by-side statistical dashboard for comparing Red Sox macro-eras.

Sections:
  ① KPI cards  — avg wins, run diff, WS titles, playoff rate
  ② Wins & run diff bar charts (side by side)
  ③ Pitching vs Offense charts (side by side)
  ④ Radar chart  — 5-dimension normalised profile
  ⑤ Scatter overlay  — wins vs run diff, all seasons coloured by era
  ⑥ Process-tag breakdown  — signal / balanced / over / under per era
  ⑦ Season-by-season line chart  — wins over time, selected eras highlighted
  ⑧ Detailed stats table
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from intelligence.redsox_history_engine import (
    get_history_df, classify_process_vs_result,
)
from config.styles import APP_CSS, pill_class

st.set_page_config(page_title="era comparison", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════
MACRO_ERAS = {
    "⚾ yaz era (1967–76)":            list(range(1967, 1977)),
    "💪 rice & lynn (1977–86)":         list(range(1977, 1987)),
    "🎯 boggs & clemens (1987–96)":     list(range(1987, 1997)),
    "🔥 pedro & manny (1997–2006)":     list(range(1997, 2007)),
    "🏆 francona dynasty (2007–13)":    list(range(2007, 2014)),
    "🌟 betts emergence (2014–19)":     list(range(2014, 2020)),
    "🔄 rebuild & now (2020–24)":       list(range(2020, 2025)),
}

ERA_COLORS = {
    "⚾ yaz era (1967–76)":            "#4a90d9",
    "💪 rice & lynn (1977–86)":         "#e4b84d",
    "🎯 boggs & clemens (1987–96)":     "#7eb8f7",
    "🔥 pedro & manny (1997–2006)":     "#c8102e",
    "🏆 francona dynasty (2007–13)":    "#2da870",
    "🌟 betts emergence (2014–19)":     "#c8940a",
    "🔄 rebuild & now (2020–24)":       "#999999",
}

PRESETS = {
    "all eras":              list(MACRO_ERAS.keys()),
    "championship eras":     ["🔥 pedro & manny (1997–2006)", "🏆 francona dynasty (2007–13)", "🌟 betts emergence (2014–19)"],
    "classic vs modern":     ["⚾ yaz era (1967–76)", "💪 rice & lynn (1977–86)", "🏆 francona dynasty (2007–13)", "🌟 betts emergence (2014–19)"],
    "heartbreak eras":       ["💪 rice & lynn (1977–86)", "🎯 boggs & clemens (1987–96)", "🔥 pedro & manny (1997–2006)"],
    "post-curse only":       ["🏆 francona dynasty (2007–13)", "🌟 betts emergence (2014–19)", "🔄 rebuild & now (2020–24)"],
}

CHART_BG    = "#ffffff"
PANEL_BG    = "#f7f8fa"
NAVY        = "#0d1b2a"
BORDER      = "#e8e9eb"

# ══════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load():
    df = get_history_df()
    df["season"] = df["season"].astype(int)
    # add macro-era column
    era_map = {}
    for era, yrs in MACRO_ERAS.items():
        for y in yrs:
            era_map[y] = era
    df["macro_era"] = df["season"].map(era_map)
    # add process tag
    df["process_tag"] = df.apply(lambda r: classify_process_vs_result(r)[0], axis=1)
    return df

df = load()

# ══════════════════════════════════════════════════════════════════════════
# HELPERS — aggregate one era
# ══════════════════════════════════════════════════════════════════════════
def era_stats(era_name: str, edf: pd.DataFrame) -> dict:
    ws = edf["playoff_result"].str.lower().str.contains("world series") & \
         ~edf["playoff_result"].str.lower().str.contains("lost")
    playoff = edf["playoff_result"] != "missed playoffs"
    best_row = edf.loc[edf["wins"].idxmax()]
    worst_row = edf.loc[edf["wins"].idxmin()]
    return {
        "era":         era_name,
        "seasons":     len(edf),
        "avg_wins":    edf["wins"].mean(),
        "avg_losses":  edf["losses"].mean(),
        "avg_rd":      edf["run_diff"].mean(),
        "ws_titles":   int(ws.sum()),
        "playoff_app": int(playoff.sum()),
        "playoff_pct": playoff.mean() * 100,
        "avg_ops":     edf["team_ops"].mean(),
        "avg_obp":     edf["team_obp"].mean(),
        "avg_slg":     edf["team_slg"].mean(),
        "avg_era":     edf["team_era"].mean(),
        "avg_fip":     edf["team_fip"].mean(),
        "best_wins":   int(best_row["wins"]),
        "best_year":   int(best_row["season"]),
        "worst_wins":  int(worst_row["wins"]),
        "worst_year":  int(worst_row["season"]),
        "color":       ERA_COLORS.get(era_name, "#888888"),
    }

# ══════════════════════════════════════════════════════════════════════════
# RADAR NORMALISATION (across ALL 7 eras for stable scale)
# ══════════════════════════════════════════════════════════════════════════
ALL_STATS = {
    era: era_stats(era, df[df["macro_era"] == era])
    for era in MACRO_ERAS
    if not df[df["macro_era"] == era].empty
}

def _minmax(key, invert=False):
    vals = [ALL_STATS[e][key] for e in ALL_STATS]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {e: 50 for e in ALL_STATS}
    if invert:
        return {e: (1 - (ALL_STATS[e][key] - lo) / (hi - lo)) * 100 for e in ALL_STATS}
    return {e: ((ALL_STATS[e][key] - lo) / (hi - lo)) * 100 for e in ALL_STATS}

RADAR_DIMS = {
    "winning %":       _minmax("avg_wins"),
    "run diff":        _minmax("avg_rd"),
    "offense (OPS)":   _minmax("avg_ops"),
    "pitching (ERA)":  _minmax("avg_era", invert=True),
    "process (FIP)":   _minmax("avg_fip", invert=True),
}

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 era comparison")
    st.caption("select two or more eras to compare")

    st.markdown("**quick presets**")
    preset_choice = st.radio(
        "preset",
        list(PRESETS.keys()),
        index=0,
        key="cmp_preset",
        label_visibility="collapsed",
    )

    # initialise / sync with preset
    if "cmp_eras_prev_preset" not in st.session_state:
        st.session_state["cmp_eras_prev_preset"] = preset_choice
        st.session_state["cmp_eras"] = PRESETS[preset_choice]

    if st.session_state["cmp_eras_prev_preset"] != preset_choice:
        st.session_state["cmp_eras"] = PRESETS[preset_choice]
        st.session_state["cmp_eras_prev_preset"] = preset_choice

    st.divider()
    st.markdown("**or pick manually**")

    selected_eras = st.multiselect(
        "eras",
        options=list(MACRO_ERAS.keys()),
        default=st.session_state["cmp_eras"],
        key="cmp_eras",
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**display options**")
    show_radar    = st.checkbox("radar chart",           value=True,  key="cmp_radar")
    show_scatter  = st.checkbox("scatter overlay",       value=True,  key="cmp_scatter")
    show_process  = st.checkbox("process tag breakdown", value=True,  key="cmp_process")
    show_timeline = st.checkbox("wins timeline",         value=True,  key="cmp_timeline")
    show_table    = st.checkbox("detailed stats table",  value=True,  key="cmp_table")

# guard
if len(selected_eras) < 1:
    st.warning("select at least one era in the sidebar to begin.")
    st.stop()

# build per-era stats for selected eras only
sel_stats   = {e: ALL_STATS[e] for e in selected_eras if e in ALL_STATS}
sel_dfs     = {e: df[df["macro_era"] == e] for e in selected_eras}
era_names   = list(sel_stats.keys())
era_colors  = [ERA_COLORS.get(e, "#888") for e in era_names]
short_names = [e.split("(")[0].strip() for e in era_names]

# ══════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="background:{NAVY};border-radius:14px;padding:22px 28px 18px;">'
    f'<div style="font-size:28px;font-weight:800;color:white;letter-spacing:-1px;">era comparison</div>'
    f'<div style="font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;">'
    f'comparing {len(selected_eras)} era{"s" if len(selected_eras)!=1 else ""} · '
    f'{sum(len(v) for e,v in sel_dfs.items())} seasons · '
    f'red sox franchise 1967–2024</div></div>',
    unsafe_allow_html=True,
)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ① KPI CARDS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("### at a glance")
kpi_cols = st.columns(len(era_names))

for col, era in zip(kpi_cols, era_names):
    s = sel_stats[era]
    c = s["color"]
    ws_stars = "★" * s["ws_titles"] if s["ws_titles"] > 0 else "—"
    playoff_bar_pct = int(s["playoff_pct"])

    col.markdown(f"""
<div style="
    background:white;border-radius:12px;padding:18px 20px 14px;
    border-top:4px solid {c};border:1px solid {BORDER};
    border-top:4px solid {c};
    box-shadow:0 1px 6px rgba(0,0,0,0.05);height:100%;
">
  <div style="font-size:11px;font-weight:700;text-transform:uppercase;
              letter-spacing:1px;color:{c};margin-bottom:8px;">
    {era.split('(')[0].strip()}
  </div>
  <div style="font-size:10px;color:#aaa;font-weight:600;
              text-transform:uppercase;letter-spacing:0.5px;">
    {era.split('(')[1].replace(')','') if '(' in era else ''}
  </div>

  <div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;">
    <div>
      <div style="font-size:32px;font-weight:800;color:#111;
                  letter-spacing:-1px;line-height:1;">{s['avg_wins']:.1f}</div>
      <div style="font-size:10px;color:#aaa;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">avg wins</div>
    </div>
    <div>
      <div style="font-size:32px;font-weight:800;
                  color:{'#2da870' if s['avg_rd']>=0 else '#c8102e'};
                  letter-spacing:-1px;line-height:1;">
        {s['avg_rd']:+.0f}</div>
      <div style="font-size:10px;color:#aaa;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">avg run diff</div>
    </div>
  </div>

  <div style="margin-top:12px;display:flex;gap:20px;flex-wrap:wrap;">
    <div>
      <div style="font-size:20px;font-weight:700;color:#c8940a;">{ws_stars}</div>
      <div style="font-size:10px;color:#aaa;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">
        ws title{"s" if s['ws_titles']!=1 else ""}</div>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;color:#111;">
        {s['playoff_app']}/{s['seasons']}</div>
      <div style="font-size:10px;color:#aaa;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">playoff apps</div>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;color:#111;">{s['seasons']}</div>
      <div style="font-size:10px;color:#aaa;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">seasons</div>
    </div>
  </div>

  <div style="margin-top:12px;">
    <div style="font-size:10px;color:#aaa;margin-bottom:3px;">playoff rate</div>
    <div style="background:#f0f0f0;border-radius:4px;height:6px;overflow:hidden;">
      <div style="background:{c};width:{playoff_bar_pct}%;height:6px;border-radius:4px;"></div>
    </div>
    <div style="font-size:10px;color:#666;margin-top:2px;">{playoff_bar_pct}%</div>
  </div>

  <div style="margin-top:10px;display:flex;gap:16px;flex-wrap:wrap;">
    <div style="font-size:11px;color:#666;">
      best: <strong>{s['best_year']} ({s['best_wins']}W)</strong>
    </div>
    <div style="font-size:11px;color:#666;">
      worst: <strong>{s['worst_year']} ({s['worst_wins']}W)</strong>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ② WINS & RUN DIFF (side by side)
# ══════════════════════════════════════════════════════════════════════════
st.markdown("### wins & run differential")
ch1, ch2 = st.columns(2)

with ch1:
    fig_wins = go.Figure()
    fig_wins.add_trace(go.Bar(
        x=short_names,
        y=[sel_stats[e]["avg_wins"] for e in era_names],
        marker_color=era_colors,
        text=[f"{sel_stats[e]['avg_wins']:.1f}" for e in era_names],
        textposition="outside",
        textfont=dict(size=11, color="#333"),
        hovertemplate="<b>%{x}</b><br>avg wins: %{y:.1f}<extra></extra>",
    ))
    fig_wins.add_hline(y=81, line=dict(color="#cccccc", width=1, dash="dot"),
                       annotation_text=".500", annotation_font=dict(color="#aaa", size=9))
    fig_wins.update_layout(
        title=dict(text="average wins per season", font=dict(size=13, color="#111"), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=320, margin=dict(l=0, r=0, t=36, b=8),
        yaxis=dict(range=[0, 115], gridcolor="#eeeeee", tickfont=dict(color="#888", size=9)),
        xaxis=dict(tickfont=dict(color="#555", size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig_wins, use_container_width=True, key="cmp_wins")

with ch2:
    rd_vals  = [sel_stats[e]["avg_rd"] for e in era_names]
    rd_clrs  = ["#2da870" if v >= 0 else "#c8102e" for v in rd_vals]
    fig_rd   = go.Figure()
    fig_rd.add_trace(go.Bar(
        x=short_names,
        y=rd_vals,
        marker_color=rd_clrs,
        text=[f"{v:+.0f}" for v in rd_vals],
        textposition="outside",
        textfont=dict(size=11, color="#333"),
        hovertemplate="<b>%{x}</b><br>avg run diff: %{y:+.1f}<extra></extra>",
    ))
    fig_rd.add_hline(y=0, line=dict(color="#cccccc", width=1, dash="dot"))
    fig_rd.update_layout(
        title=dict(text="average run differential", font=dict(size=13, color="#111"), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=320, margin=dict(l=0, r=0, t=36, b=8),
        yaxis=dict(gridcolor="#eeeeee", tickfont=dict(color="#888", size=9)),
        xaxis=dict(tickfont=dict(color="#555", size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig_rd, use_container_width=True, key="cmp_rd")

# ══════════════════════════════════════════════════════════════════════════
# ③ PITCHING vs OFFENSE (side by side)
# ══════════════════════════════════════════════════════════════════════════
st.markdown("### pitching vs offense")
ch3, ch4 = st.columns(2)

with ch3:
    fig_pitch = go.Figure()
    # ERA bars
    fig_pitch.add_trace(go.Bar(
        name="ERA",
        x=short_names,
        y=[sel_stats[e]["avg_era"] for e in era_names],
        marker_color=era_colors,
        opacity=0.85,
        text=[f"{sel_stats[e]['avg_era']:.2f}" for e in era_names],
        textposition="outside",
        textfont=dict(size=10, color="#333"),
        hovertemplate="<b>%{x}</b><br>avg ERA: %{y:.2f}<extra></extra>",
    ))
    # FIP line
    fig_pitch.add_trace(go.Scatter(
        name="FIP",
        x=short_names,
        y=[sel_stats[e]["avg_fip"] for e in era_names],
        mode="lines+markers+text",
        line=dict(color="#c8102e", width=2, dash="dot"),
        marker=dict(size=7, color="#c8102e"),
        text=[f"{sel_stats[e]['avg_fip']:.2f}" for e in era_names],
        textposition="top center",
        textfont=dict(size=9, color="#c8102e"),
        hovertemplate="<b>%{x}</b><br>avg FIP: %{y:.2f}<extra></extra>",
    ))
    fig_pitch.update_layout(
        title=dict(text="avg ERA (bars) vs avg FIP (line) — lower is better",
                   font=dict(size=12, color="#111"), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=320, margin=dict(l=0, r=0, t=36, b=8),
        yaxis=dict(gridcolor="#eeeeee", tickfont=dict(color="#888", size=9), autorange="reversed"),
        xaxis=dict(tickfont=dict(color="#555", size=10)),
        legend=dict(orientation="h", y=1.05, x=0, font=dict(size=9)),
        barmode="group",
    )
    st.plotly_chart(fig_pitch, use_container_width=True, key="cmp_pitch")

with ch4:
    fig_off = go.Figure()
    # OPS bars
    fig_off.add_trace(go.Bar(
        name="OPS",
        x=short_names,
        y=[sel_stats[e]["avg_ops"] for e in era_names],
        marker_color=era_colors,
        opacity=0.85,
        text=[f"{sel_stats[e]['avg_ops']:.3f}" for e in era_names],
        textposition="outside",
        textfont=dict(size=10, color="#333"),
        hovertemplate="<b>%{x}</b><br>avg OPS: %{y:.3f}<extra></extra>",
    ))
    # OBP line
    fig_off.add_trace(go.Scatter(
        name="OBP",
        x=short_names,
        y=[sel_stats[e]["avg_obp"] for e in era_names],
        mode="lines+markers+text",
        line=dict(color="#4a90d9", width=2, dash="dot"),
        marker=dict(size=7, color="#4a90d9"),
        text=[f"{sel_stats[e]['avg_obp']:.3f}" for e in era_names],
        textposition="top center",
        textfont=dict(size=9, color="#4a90d9"),
        hovertemplate="<b>%{x}</b><br>avg OBP: %{y:.3f}<extra></extra>",
    ))
    fig_off.update_layout(
        title=dict(text="avg OPS (bars) vs avg OBP (line) — higher is better",
                   font=dict(size=12, color="#111"), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=320, margin=dict(l=0, r=0, t=36, b=8),
        yaxis=dict(gridcolor="#eeeeee", tickfont=dict(color="#888", size=9)),
        xaxis=dict(tickfont=dict(color="#555", size=10)),
        legend=dict(orientation="h", y=1.05, x=0, font=dict(size=9)),
    )
    st.plotly_chart(fig_off, use_container_width=True, key="cmp_off")

# ══════════════════════════════════════════════════════════════════════════
# ④ RADAR CHART
# ══════════════════════════════════════════════════════════════════════════
if show_radar:
    st.markdown("### five-dimension profile")
    st.caption(
        "each axis is normalised 0–100 across all 7 eras. "
        "winning % = avg wins  ·  pitching ERA inverted (lower ERA → higher score)  ·  "
        "process FIP inverted"
    )

    radar_dims = list(RADAR_DIMS.keys())
    fig_radar = go.Figure()

    for era in era_names:
        vals = [RADAR_DIMS[dim].get(era, 0) for dim in radar_dims]
        vals_closed = vals + [vals[0]]
        dims_closed = radar_dims + [radar_dims[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=dims_closed,
            fill="toself",
            fillcolor=ERA_COLORS.get(era, "#888") + "33",
            line=dict(color=ERA_COLORS.get(era, "#888"), width=2),
            name=era.split("(")[0].strip(),
            hovertemplate=(
                "<b>" + era.split("(")[0].strip() + "</b><br>"
                "%{theta}: %{r:.0f}/100<extra></extra>"
            ),
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor=PANEL_BG,
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=8, color="#aaa"),
                            gridcolor="#dddddd", linecolor="#dddddd"),
            angularaxis=dict(tickfont=dict(size=11, color="#333"),
                             gridcolor="#dddddd", linecolor="#dddddd"),
        ),
        paper_bgcolor=CHART_BG,
        showlegend=True,
        legend=dict(
            orientation="v", x=1.05, y=0.5,
            font=dict(size=10, color="#333"),
            bgcolor="white", bordercolor=BORDER, borderwidth=1,
        ),
        height=440,
        margin=dict(l=60, r=180, t=20, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="cmp_radar_fig")

# ══════════════════════════════════════════════════════════════════════════
# ⑤ SCATTER OVERLAY — wins vs run diff, coloured by era
# ══════════════════════════════════════════════════════════════════════════
if show_scatter:
    st.markdown("### wins vs run differential — every season")
    st.caption("each dot = one season. colour = era. hover for details.")

    fig_sc = go.Figure()
    for era in era_names:
        edf = sel_dfs[era]
        if edf.empty:
            continue
        hover_texts = [
            f"<b>{int(r['season'])}</b><br>"
            f"{int(r['wins'])}-{int(r['losses'])}<br>"
            f"run diff: {int(r['run_diff']):+d}<br>"
            f"{r['playoff_result']}"
            for _, r in edf.iterrows()
        ]
        fig_sc.add_trace(go.Scatter(
            x=edf["run_diff"],
            y=edf["wins"],
            mode="markers+text",
            name=era.split("(")[0].strip(),
            marker=dict(size=10, color=ERA_COLORS.get(era, "#888"),
                        line=dict(width=1, color="white"), opacity=0.85),
            text=edf["season"].astype(str),
            textposition="top center",
            textfont=dict(size=8, color=ERA_COLORS.get(era, "#888")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
        ))

    fig_sc.add_hline(y=81, line=dict(color="#dddddd", width=1, dash="dot"),
                     annotation_text=".500 line", annotation_font=dict(color="#aaa", size=9))
    fig_sc.add_vline(x=0, line=dict(color="#dddddd", width=1, dash="dot"))

    fig_sc.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=400,
        margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(title="run differential", gridcolor="#eeeeee",
                   tickfont=dict(color="#888", size=9),
                   title_font=dict(color="#555", size=10)),
        yaxis=dict(title="wins", gridcolor="#eeeeee",
                   tickfont=dict(color="#888", size=9),
                   title_font=dict(color="#555", size=10)),
        legend=dict(orientation="h", y=-0.12, x=0, font=dict(size=10)),
        hovermode="closest",
    )
    st.plotly_chart(fig_sc, use_container_width=True, key="cmp_scatter_fig")

# ══════════════════════════════════════════════════════════════════════════
# ⑥ PROCESS-TAG BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════
if show_process:
    st.markdown("### process tag breakdown")
    st.caption(
        "how many seasons in each era were 'as good as they looked' vs lucky vs unlucky"
    )

    TAG_ORDER  = ["signal", "balanced", "overperformed process", "underperformed process"]
    TAG_LABELS = {
        "signal":                 "✅ signal",
        "balanced":               "➡️ balanced",
        "overperformed process":  "🍀 got lucky",
        "underperformed process": "📉 underperformed",
    }
    TAG_COLORS = {
        "signal":                 "#2da870",
        "balanced":               "#aaaaaa",
        "overperformed process":  "#c8940a",
        "underperformed process": "#4a90d9",
    }

    fig_proc = go.Figure()
    for tag in TAG_ORDER:
        counts = []
        for era in era_names:
            edf = sel_dfs[era]
            counts.append(int((edf["process_tag"] == tag).sum()))
        fig_proc.add_trace(go.Bar(
            name=TAG_LABELS[tag],
            x=short_names,
            y=counts,
            marker_color=TAG_COLORS[tag],
            text=counts,
            textposition="inside",
            textfont=dict(size=10, color="white"),
            hovertemplate=f"<b>%{{x}}</b><br>{TAG_LABELS[tag]}: %{{y}} season(s)<extra></extra>",
        ))

    fig_proc.update_layout(
        barmode="stack",
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=320, margin=dict(l=0, r=0, t=10, b=8),
        yaxis=dict(title="seasons", gridcolor="#eeeeee",
                   tickfont=dict(color="#888", size=9)),
        xaxis=dict(tickfont=dict(color="#555", size=10)),
        legend=dict(orientation="h", y=-0.15, x=0, font=dict(size=10)),
    )
    st.plotly_chart(fig_proc, use_container_width=True, key="cmp_process_fig")

# ══════════════════════════════════════════════════════════════════════════
# ⑦ SEASON-BY-SEASON WINS TIMELINE
# ══════════════════════════════════════════════════════════════════════════
if show_timeline:
    st.markdown("### wins over time")
    st.caption("selected eras highlighted — all other seasons shown faintly for context")

    fig_tl = go.Figure()

    # faint context line for all seasons
    fig_tl.add_trace(go.Scatter(
        x=df["season"], y=df["wins"],
        mode="lines",
        line=dict(color="#dddddd", width=1),
        showlegend=False,
        hoverinfo="skip",
    ))

    # one line per selected era
    for era in era_names:
        edf = sel_dfs[era].sort_values("season")
        if edf.empty:
            continue
        hover_texts = [
            f"<b>{int(r['season'])}</b> — {int(r['wins'])}W<br>{r['playoff_result']}"
            for _, r in edf.iterrows()
        ]
        # WS win markers
        ws_mask = edf["playoff_result"].str.lower().str.contains("world series") & \
                  ~edf["playoff_result"].str.lower().str.contains("lost")

        fig_tl.add_trace(go.Scatter(
            x=edf["season"], y=edf["wins"],
            mode="lines+markers",
            name=era.split("(")[0].strip(),
            line=dict(color=ERA_COLORS.get(era, "#888"), width=2.5),
            marker=dict(size=6, color=ERA_COLORS.get(era, "#888"),
                        line=dict(width=1, color="white")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
        ))

        # ★ markers on WS wins
        ws_rows = edf[ws_mask]
        if not ws_rows.empty:
            fig_tl.add_trace(go.Scatter(
                x=ws_rows["season"], y=ws_rows["wins"] + 2,
                mode="text",
                text=["★"] * len(ws_rows),
                textfont=dict(size=14, color="#c8940a"),
                showlegend=False,
                hoverinfo="skip",
            ))

    fig_tl.add_hline(y=81, line=dict(color="#dddddd", width=1, dash="dot"),
                     annotation_text=".500", annotation_font=dict(color="#aaa", size=9))
    fig_tl.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=PANEL_BG,
        height=350, margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(title="season", gridcolor="#eeeeee",
                   tickfont=dict(color="#888", size=9)),
        yaxis=dict(title="wins", gridcolor="#eeeeee", range=[40, 120],
                   tickfont=dict(color="#888", size=9)),
        legend=dict(orientation="h", y=-0.12, x=0, font=dict(size=10)),
        hovermode="x unified",
    )
    st.plotly_chart(fig_tl, use_container_width=True, key="cmp_tl_fig")

# ══════════════════════════════════════════════════════════════════════════
# ⑧ DETAILED STATS TABLE
# ══════════════════════════════════════════════════════════════════════════
if show_table:
    st.markdown("### detailed stats table")

    table_rows = []
    for era in era_names:
        s = sel_stats[era]
        table_rows.append({
            "era":           era.split("(")[0].strip(),
            "years":         era.split("(")[1].replace(")", "") if "(" in era else "",
            "seasons":       s["seasons"],
            "avg W":         f"{s['avg_wins']:.1f}",
            "avg L":         f"{s['avg_losses']:.1f}",
            "avg RD":        f"{s['avg_rd']:+.1f}",
            "WS":            s["ws_titles"],
            "playoff %":     f"{s['playoff_pct']:.0f}%",
            "avg OPS":       f"{s['avg_ops']:.3f}",
            "avg OBP":       f"{s['avg_obp']:.3f}",
            "avg SLG":       f"{s['avg_slg']:.3f}",
            "avg ERA":       f"{s['avg_era']:.2f}",
            "avg FIP":       f"{s['avg_fip']:.2f}",
            "best season":   f"{s['best_year']} ({s['best_wins']}W)",
            "worst season":  f"{s['worst_year']} ({s['worst_wins']}W)",
        })

    tbl_df = pd.DataFrame(table_rows)
    st.dataframe(
        tbl_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "avg W":     st.column_config.NumberColumn(format="%.1f"),
            "WS":        st.column_config.NumberColumn("🏆 WS titles"),
            "avg RD":    st.column_config.TextColumn("avg RD"),
            "playoff %": st.column_config.TextColumn("playoff %"),
        },
    )

    # downloadable CSV
    csv_bytes = tbl_df.to_csv(index=False).encode()
    st.download_button(
        "⬇ download comparison table (.csv)",
        data=csv_bytes,
        file_name="redsox_era_comparison.csv",
        mime="text/csv",
        key="cmp_dl",
    )

# ══════════════════════════════════════════════════════════════════════════
# ⑨ PDF EXPORT
# ══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📄 export infographic PDF")
st.markdown(
    "Generates a full 10-page era comparison PDF including all charts, "
    "the detailed stats table, and key insights. "
    "Uses all 58 seasons regardless of current sidebar filters."
)

if st.button("generate & download PDF report", key="pdf_export_btn"):
    import sys, os, tempfile
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    with st.spinner("building charts and assembling PDF… (may take 10–15 seconds)"):
        try:
            from export_era_comparison_pdf import build_pdf
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            build_pdf(tmp.name)
            with open(tmp.name, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(tmp.name)
            st.success(f"PDF ready — {len(pdf_bytes)//1024} KB · 10 pages")
            st.download_button(
                "⬇ download era comparison report (.pdf)",
                data=pdf_bytes,
                file_name="redsox_era_comparison_report.pdf",
                mime="application/pdf",
                key="pdf_dl_btn",
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
            raise

"""
app/pages/06_redsox_process_vs_result.py
────────────────────────────────────────
Process vs Result scatter dashboard.

Four quadrants:
  Signal          — high wins + high run diff  (top-right)
  Overperformed   — high wins + low run diff   (top-left)
  Underperformed  — low wins  + high run diff  (bottom-right)
  Balanced        — low wins  + low run diff   (bottom-left)
"""

import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from intelligence.redsox_history_engine import (
    get_history_df,
    build_process_vs_result_table,
    classify_process_vs_result,
)
from config.styles import APP_CSS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Process vs Result · frame²", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown("## ⚙️ process vs result")
st.caption("58 seasons mapped to four quadrants — does the record tell the truth?")

# ── Load data ─────────────────────────────────────────────────────────────────
df = get_history_df()

# Build tag + explanation column
tags, explanations = zip(*[classify_process_vs_result(row) for _, row in df.iterrows()])
df = df.copy()
df["tag"] = list(tags)
df["explanation"] = list(explanations)

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("### filters")
eras = ["all eras"] + sorted(df["era_label"].unique().tolist())
sel_era = st.sidebar.selectbox("era", eras, key="pvr_era")
sel_tags = st.sidebar.multiselect(
    "process tags",
    ["signal", "underperformed process", "overperformed process", "balanced"],
    default=["signal", "underperformed process", "overperformed process", "balanced"],
    key="pvr_tags",
)

# Apply filters
fdf = df.copy()
if sel_era != "all eras":
    fdf = fdf[fdf["era_label"] == sel_era]
if sel_tags:
    fdf = fdf[fdf["tag"].isin(sel_tags)]

# ── Color map ─────────────────────────────────────────────────────────────────
TAG_COLOR = {
    "signal":                  "#bd3039",   # Red Sox red
    "underperformed process":  "#f0ad4e",   # amber
    "overperformed process":   "#5bc0de",   # blue
    "balanced":                "#8e9ba8",   # grey
}
TAG_SYMBOL = {
    "signal": "star",
    "underperformed process": "triangle-up",
    "overperformed process": "triangle-down",
    "balanced": "circle",
}

# ── Scatter plot ──────────────────────────────────────────────────────────────
fig = go.Figure()

# Quadrant shading
for x0, x1, y0, y1, color, label in [
    (-250, 0, 92, 130, "rgba(93,188,210,0.06)",  "overperformed"),
    (0,    400, 92, 130, "rgba(189,48,57,0.06)",  "signal"),
    (-250, 0, 55,  92, "rgba(142,155,168,0.06)", "balanced"),
    (0,    400, 55,  92, "rgba(240,173,78,0.06)", "underperformed"),
]:
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                  fillcolor=color, line_width=0, layer="below")
    fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, text=label,
                       font=dict(size=10, color="rgba(200,200,200,0.25)"),
                       showarrow=False)

# Quadrant dividers
fig.add_hline(y=92, line_dash="dot", line_color="rgba(255,255,255,0.15)")
fig.add_vline(x=0,  line_dash="dot", line_color="rgba(255,255,255,0.15)")

# Season traces by tag
for tag in ["signal", "underperformed process", "overperformed process", "balanced"]:
    sub = fdf[fdf["tag"] == tag]
    if sub.empty:
        continue
    hover = (
        sub["season"].astype(str) + " · " +
        sub["wins"].astype(str) + "-" + sub["losses"].astype(str) +
        " · RD " + sub["run_diff"].astype(str) +
        "<br>" + sub["playoff_result"] +
        "<br><i>" + sub["explanation"] + "</i>"
    )
    fig.add_trace(go.Scatter(
        x=sub["run_diff"], y=sub["wins"],
        mode="markers+text",
        name=tag,
        marker=dict(
            color=TAG_COLOR[tag],
            symbol=TAG_SYMBOL[tag],
            size=10,
            line=dict(color="white", width=0.5),
        ),
        text=sub["season"].astype(str).str[-2:],
        textposition="top center",
        textfont=dict(size=8, color="rgba(220,220,220,0.6)"),
        hovertext=hover,
        hoverinfo="text",
    ))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    height=520,
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(title="run differential", gridcolor="#1e2530", zeroline=False),
    yaxis=dict(title="wins", gridcolor="#1e2530", zeroline=False),
    legend=dict(orientation="h", y=-0.15, x=0),
    font=dict(color="#e8eaed"),
)

st.plotly_chart(fig, use_container_width=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
st.markdown("---")
cols = st.columns(4)
for col, tag in zip(cols, ["signal", "underperformed process", "overperformed process", "balanced"]):
    count = int((df["tag"] == tag).sum())
    pct = count / len(df) * 100
    col.metric(tag, f"{count} seasons", f"{pct:.0f}% of history")

# ── Tag breakdown table ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### breakdown by process tag")

table = build_process_vs_result_table(fdf if len(fdf) < len(df) else df)

# Enhance with avg stats per tag
tag_stats = (
    df.groupby("tag")
    .agg(
        seasons=("season", "count"),
        avg_wins=("wins", "mean"),
        avg_run_diff=("run_diff", "mean"),
        playoff_pct=("playoff_result", lambda x: (x.str.lower() != "missed playoffs").mean() * 100),
    )
    .round(1)
    .reset_index()
)
tag_stats.columns = ["tag", "seasons", "avg wins", "avg run diff", "playoff %"]
st.dataframe(tag_stats, use_container_width=True, hide_index=True)

# ── Season list for selected tag ──────────────────────────────────────────────
st.markdown("---")
sel_detail_tag = st.selectbox(
    "drill into tag",
    ["signal", "underperformed process", "overperformed process", "balanced"],
    key="pvr_detail_tag",
)
detail = df[df["tag"] == sel_detail_tag][
    ["season", "wins", "losses", "run_diff", "playoff_result", "manager", "explanation"]
].sort_values("season")
st.dataframe(detail, use_container_width=True, hide_index=True)

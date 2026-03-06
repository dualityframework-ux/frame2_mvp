"""
app/pages/10_redsox_core_pipeline_explorer.py
──────────────────────────────────────────────
Core & Pipeline Explorer — visual breakdown of the Red Sox
organizational pipeline across macro-eras, with player timeline,
pipeline-read cards, and era-level comparison charts.
"""

import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters.redsox_core_pipeline_loader import load_redsox_core_pipeline
from intelligence.redsox_history_engine import get_history_df, build_era_summary
from config.styles import APP_CSS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Core Pipeline · frame²", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown("## 🔩 core + pipeline explorer")
st.caption("who carried each era — and how deep was the organizational well?")

# ── Load ──────────────────────────────────────────────────────────────────────
pipeline_df = load_redsox_core_pipeline()
history_df = get_history_df()
era_summary = build_era_summary(history_df)

# Era colour palette
ERA_COLORS = ["#bd3039","#c0392b","#e74c3c","#3498db","#2980b9","#1abc9c","#16a085"]
era_list = pipeline_df["era_label"].tolist()
color_map = {era: ERA_COLORS[i % len(ERA_COLORS)] for i, era in enumerate(era_list)}

PIPELINE_DEPTH_COLOR = {"light": "#8e9ba8", "medium": "#f0ad4e", "deep": "#2ecc71"}

# ── Era selector ──────────────────────────────────────────────────────────────
st.markdown("### select era")
sel_era = st.selectbox("era", era_list, key="pipeline_era_sel")
row = pipeline_df.loc[pipeline_df["era_label"] == sel_era].iloc[0]

# ── Era detail card ───────────────────────────────────────────────────────────
depth = str(row.get("prospect_wave", "light")).lower().strip()
depth_color = PIPELINE_DEPTH_COLOR.get(depth, "#8e9ba8")
bg_color = color_map.get(sel_era, "#bd3039")

col_card, col_stats = st.columns([3, 2])

with col_card:
    st.markdown(
        f"""
        <div style="background:{bg_color}18;border-left:5px solid {bg_color};
                    border-radius:8px;padding:18px 20px;margin-bottom:12px;">
          <div style="font-size:12px;color:#aaa;margin-bottom:4px;text-transform:uppercase;
                      letter-spacing:1px;">{sel_era}</div>
          <div style="font-size:13px;color:#e8eaed;margin-bottom:10px;">
            <b>window:</b> {int(row['start_season'])}–{int(row['end_season'])}
          </div>
          <div style="font-size:13px;color:#e8eaed;margin-bottom:8px;">
            <b>core players:</b><br>
            <span style="color:#ccc">{row['core_players']}</span>
          </div>
          <div style="font-size:13px;color:#e8eaed;margin-bottom:8px;">
            <b>prospect wave:</b>
            <span style="background:{depth_color}30;color:{depth_color};
                         padding:2px 8px;border-radius:10px;font-size:11px;margin-left:6px;">
              {depth}
            </span>
          </div>
          <div style="font-size:13px;color:#e8eaed;margin-bottom:8px;">
            <b>pipeline read:</b><br>
            <span style="color:#ccc">{row['pipeline_read']}</span>
          </div>
          <div style="font-size:13px;color:#e8eaed;">
            <b>org implication:</b><br>
            <span style="color:#ccc">{row['organizational_implication']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_stats:
    # Merge era-level stats from history summary
    era_row = era_summary[era_summary["era_label"] == sel_era] if "era_label" in era_summary.columns else pd.DataFrame()
    if not era_row.empty:
        r = era_row.iloc[0]
        wins_col = next((c for c in ["avg_wins","wins_mean"] if c in r.index), None)
        po_col   = next((c for c in ["playoff_pct","playoff_rate"] if c in r.index), None)
        rd_col   = next((c for c in ["avg_run_diff","run_diff_mean"] if c in r.index), None)

        m1, m2, m3 = st.columns(3)
        if wins_col: m1.metric("avg wins", f"{r[wins_col]:.1f}")
        if po_col:
            pv = r[po_col] * 100 if r[po_col] <= 1 else r[po_col]
            m2.metric("playoff %", f"{pv:.0f}%")
        if rd_col: m3.metric("avg run diff", f"{r[rd_col]:+.0f}")

    # Seasons in this era
    era_seasons = history_df[history_df["era_label"] == sel_era].sort_values("season")
    st.dataframe(
        era_seasons[["season","wins","losses","run_diff","playoff_result"]],
        use_container_width=True,
        hide_index=True,
        height=200,
    )

# ── Pipeline depth comparison ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("### pipeline depth across all eras")

depth_order = {"deep": 3, "medium": 2, "light": 1}
pipeline_df["depth_score"] = pipeline_df["prospect_wave"].str.lower().str.strip().map(depth_order).fillna(1)

fig_depth = go.Figure()
for era, grp in pipeline_df.groupby("era_label"):
    d = str(grp["prospect_wave"].iloc[0]).lower().strip()
    clr = PIPELINE_DEPTH_COLOR.get(d, "#8e9ba8")
    fig_depth.add_trace(go.Bar(
        name=era,
        x=[era],
        y=[grp["depth_score"].iloc[0]],
        marker_color=clr,
        text=[d],
        textposition="outside",
        hovertemplate=f"<b>{era}</b><br>pipeline: {d}<extra></extra>",
    ))

fig_depth.update_layout(
    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    height=280, margin=dict(l=40, r=20, t=30, b=60),
    xaxis=dict(tickangle=-15, gridcolor="#1e2530"),
    yaxis=dict(
        title="pipeline depth", gridcolor="#1e2530",
        tickvals=[1, 2, 3], ticktext=["light", "medium", "deep"], range=[0, 3.8]
    ),
    font=dict(color="#e8eaed"),
    showlegend=False,
)
st.plotly_chart(fig_depth, use_container_width=True)

# ── Core player timeline ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### core player eras — timeline")

timeline_rows = []
for _, r in pipeline_df.iterrows():
    for player in str(r["core_players"]).split(","):
        player = player.strip()
        if player:
            timeline_rows.append({
                "player": player,
                "era": r["era_label"],
                "start": int(r["start_season"]),
                "end": int(r["end_season"]),
                "color": color_map.get(r["era_label"], "#bd3039"),
            })

if timeline_rows:
    tdf = pd.DataFrame(timeline_rows)
    fig_tl = go.Figure()
    for i, row_t in tdf.iterrows():
        fig_tl.add_trace(go.Scatter(
            x=[row_t["start"], row_t["end"]],
            y=[row_t["player"], row_t["player"]],
            mode="lines+markers",
            line=dict(color=row_t["color"], width=6),
            marker=dict(size=8, color=row_t["color"]),
            name=row_t["era"],
            showlegend=False,
            hovertemplate=f"<b>{row_t['player']}</b><br>{row_t['era']}: "
                          f"{row_t['start']}–{row_t['end']}<extra></extra>",
        ))
    fig_tl.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=max(300, len(tdf["player"].unique()) * 22),
        margin=dict(l=140, r=20, t=20, b=40),
        xaxis=dict(title="season", range=[1965, 2026], gridcolor="#1e2530"),
        yaxis=dict(gridcolor="#1e2530"),
        font=dict(color="#e8eaed"),
    )
    st.plotly_chart(fig_tl, use_container_width=True)

# ── Full pipeline table ───────────────────────────────────────────────────────
st.markdown("---")
with st.expander("full pipeline table", expanded=False):
    st.dataframe(pipeline_df.drop(columns=["depth_score"], errors="ignore"),
                 use_container_width=True, hide_index=True)

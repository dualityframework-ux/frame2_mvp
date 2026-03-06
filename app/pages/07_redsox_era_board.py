"""
app/pages/07_redsox_era_board.py
────────────────────────────────
Era Board — visual summary of each macro-era with bar charts,
stat heatmap, and era comparison cards.
"""

import os
import sys
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from intelligence.redsox_history_engine import get_history_df, build_era_summary
from config.styles import APP_CSS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Era Board · frame²", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown("## 🗂️ era board")
st.caption("seven macro-eras · avg wins · playoff rate · process signature")

# ── Load ──────────────────────────────────────────────────────────────────────
df = get_history_df()
era_df = build_era_summary(df)

# ── Era colour palette ────────────────────────────────────────────────────────
ERA_COLORS = [
    "#bd3039", "#c0392b", "#e74c3c",
    "#3498db", "#2980b9", "#1abc9c", "#16a085",
]
era_list = era_df["era_label"].tolist() if "era_label" in era_df.columns else era_df.index.tolist()
color_map = {era: ERA_COLORS[i % len(ERA_COLORS)] for i, era in enumerate(era_list)}

# ── Era cards ─────────────────────────────────────────────────────────────────
st.markdown("### era overview")

era_col_count = min(3, len(era_df))
card_rows = [era_df.iloc[i:i+era_col_count] for i in range(0, len(era_df), era_col_count)]

for chunk in card_rows:
    cols = st.columns(len(chunk))
    for col, (_, row) in zip(cols, chunk.iterrows()):
        era_name = row.get("era_label", row.name)
        avg_w = row.get("avg_wins", row.get("wins_mean", "—"))
        playoff = row.get("playoff_pct", row.get("playoff_rate", "—"))
        seasons = row.get("seasons", row.get("n_seasons", "—"))
        avg_rd = row.get("avg_run_diff", row.get("run_diff_mean", "—"))

        # Format values
        avg_w_str = f"{avg_w:.1f}" if isinstance(avg_w, float) else str(avg_w)
        playoff_str = f"{float(playoff):.0f}%" if playoff != "—" else "—"
        avg_rd_str = f"{avg_rd:+.0f}" if isinstance(avg_rd, float) else str(avg_rd)
        seasons_str = str(int(seasons)) if seasons != "—" else "—"

        bg = color_map.get(era_name, "#bd3039")
        col.markdown(
            f"""
            <div style="background:{bg}18;border-left:4px solid {bg};
                        border-radius:6px;padding:14px 16px;margin-bottom:8px;">
              <div style="font-size:13px;color:#aaa;margin-bottom:6px;">{era_name}</div>
              <div style="display:flex;gap:20px;flex-wrap:wrap;">
                <div><span style="font-size:22px;font-weight:700;color:#e8eaed">{avg_w_str}</span>
                     <div style="font-size:10px;color:#8e9ba8">avg wins</div></div>
                <div><span style="font-size:22px;font-weight:700;color:{bg}">{playoff_str}</span>
                     <div style="font-size:10px;color:#8e9ba8">playoff %</div></div>
                <div><span style="font-size:22px;font-weight:700;color:#e8eaed">{avg_rd_str}</span>
                     <div style="font-size:10px;color:#8e9ba8">avg run diff</div></div>
                <div><span style="font-size:22px;font-weight:700;color:#8e9ba8">{seasons_str}</span>
                     <div style="font-size:10px;color:#8e9ba8">seasons</div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Avg Wins bar chart ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### avg wins by era")

wins_col = next((c for c in ["avg_wins", "wins_mean"] if c in era_df.columns), None)
if wins_col:
    fig_wins = go.Figure(go.Bar(
        x=era_df["era_label"] if "era_label" in era_df.columns else era_df.index,
        y=era_df[wins_col],
        marker_color=[color_map.get(e, "#bd3039") for e in
                      (era_df["era_label"] if "era_label" in era_df.columns else era_df.index)],
        text=era_df[wins_col].round(1),
        textposition="outside",
    ))
    fig_wins.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=320, margin=dict(l=40, r=20, t=20, b=60),
        xaxis=dict(tickangle=-20, gridcolor="#1e2530"),
        yaxis=dict(title="avg wins", gridcolor="#1e2530", range=[60, 100]),
        font=dict(color="#e8eaed"),
        showlegend=False,
    )
    st.plotly_chart(fig_wins, use_container_width=True)

# ── Playoff % bar chart ───────────────────────────────────────────────────────
st.markdown("### playoff rate by era")

playoff_col = next((c for c in ["playoff_pct", "playoff_rate"] if c in era_df.columns), None)
if playoff_col:
    playoff_vals = era_df[playoff_col]
    if playoff_vals.max() <= 1.0:
        playoff_vals = playoff_vals * 100  # convert 0-1 → percent

    fig_po = go.Figure(go.Bar(
        x=era_df["era_label"] if "era_label" in era_df.columns else era_df.index,
        y=playoff_vals,
        marker_color=[color_map.get(e, "#bd3039") for e in
                      (era_df["era_label"] if "era_label" in era_df.columns else era_df.index)],
        text=[f"{v:.0f}%" for v in playoff_vals],
        textposition="outside",
    ))
    fig_po.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=320, margin=dict(l=40, r=20, t=20, b=60),
        xaxis=dict(tickangle=-20, gridcolor="#1e2530"),
        yaxis=dict(title="playoff %", gridcolor="#1e2530", range=[0, 105]),
        font=dict(color="#e8eaed"),
        showlegend=False,
    )
    st.plotly_chart(fig_po, use_container_width=True)

# ── Stat heatmap ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### stat heatmap across eras")

num_cols = [c for c in era_df.columns
            if era_df[c].dtype in ["float64", "int64"]
            and c not in ["start_season", "end_season"]]

if num_cols and len(era_df) > 0:
    era_labels = era_df["era_label"].tolist() if "era_label" in era_df.columns else era_df.index.tolist()
    heat_data = era_df[num_cols].copy()
    # Normalize each column 0-1
    for c in num_cols:
        rng = heat_data[c].max() - heat_data[c].min()
        heat_data[c] = (heat_data[c] - heat_data[c].min()) / rng if rng > 0 else 0

    fig_heat = go.Figure(go.Heatmap(
        z=heat_data.values.T,
        x=era_labels,
        y=[c.replace("_", " ") for c in num_cols],
        colorscale=[[0, "#0d1117"], [0.5, "#bd303960"], [1.0, "#bd3039"]],
        showscale=False,
        text=era_df[num_cols].round(1).values.T,
        texttemplate="%{text}",
        textfont=dict(size=10),
    ))
    fig_heat.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=max(200, len(num_cols) * 40),
        margin=dict(l=120, r=20, t=20, b=60),
        xaxis=dict(tickangle=-20),
        font=dict(color="#e8eaed"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Full era table ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### full era summary table")
st.dataframe(era_df, use_container_width=True, hide_index=True)

# ── Season drill-down ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### seasons in era")
sel_era = st.selectbox("select era", era_list, key="era_board_drill")
era_seasons = df[df["era_label"] == sel_era][
    ["season", "wins", "losses", "run_diff", "playoff_result", "manager", "team_ops", "team_era"]
].sort_values("season")
st.dataframe(era_seasons, use_container_width=True, hide_index=True)

import streamlit as st
from intelligence.redsox_history_engine import (
    get_history_df, get_season_row, build_ian_insight,
    classify_process_vs_result, build_plain_summary,
    get_top_seasons_by_wins, get_top_seasons_by_run_diff, build_era_summary,
)
from config.styles import APP_CSS, pill_class, tag_class

st.set_page_config(page_title="red sox history", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)

df = get_history_df()

st.markdown('<div class="section-label">red sox history intelligence</div>', unsafe_allow_html=True)

# ── top row: best seasons at a glance ─────────────────
col_w, col_r = st.columns(2)

with col_w:
    st.markdown('<div class="omi-label">top seasons by wins</div>', unsafe_allow_html=True)
    st.dataframe(
        get_top_seasons_by_wins(df)[["season", "wins", "losses", "run_diff", "playoff_result"]],
        use_container_width=True, hide_index=True,
    )

with col_r:
    st.markdown('<div class="omi-label">top seasons by run differential</div>', unsafe_allow_html=True)
    st.dataframe(
        get_top_seasons_by_run_diff(df)[["season", "wins", "losses", "run_diff", "playoff_result"]],
        use_container_width=True, hide_index=True,
    )

st.divider()

# ── era summary ───────────────────────────────────────
st.markdown('<div class="omi-label">era summary</div>', unsafe_allow_html=True)
st.dataframe(build_era_summary(df), use_container_width=True, hide_index=True)

st.divider()

# ── quick season card ─────────────────────────────────
st.markdown('<div class="section-label">quick look</div>', unsafe_allow_html=True)
season_options = sorted(df["season"].dropna().astype(int).unique().tolist(), reverse=True)
season = st.selectbox("season", season_options, key="home_season", label_visibility="collapsed")

row = get_season_row(df, int(season))
insight = build_ian_insight(row)
tag, _ = classify_process_vs_result(row)
summary = build_plain_summary(row, tag)
tc = tag_class(tag)
pc = pill_class(str(row["playoff_result"]))

st.markdown(f"""
<div class="top-card">
  <div class="big-year">{int(row['season'])}</div>
  <div class="record">{int(row['wins'])} &ndash; {int(row['losses'])}</div>
  <span class="pill {pc}">{row['playoff_result']}</span>
  <div class="meta-line">manager: <strong>{row['manager']}</strong></div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="narrative-card {tc}">
  <div class="process-tag {tc}">● {tag}</div>
  <div class="sentence">{summary}</div>
</div>
""", unsafe_allow_html=True)

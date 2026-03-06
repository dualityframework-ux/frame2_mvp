import streamlit as st
from intelligence.redsox_history_engine import (
    get_history_df, get_season_row, build_ian_insight,
    classify_process_vs_result, build_plain_summary,
)
from content_engine.post_generator import build_post_variants
from config.styles import APP_CSS, pill_class, tag_class

st.set_page_config(page_title="post generator", layout="centered")
st.markdown(APP_CSS, unsafe_allow_html=True)

df = get_history_df()
season_options = sorted(df["season"].dropna().astype(int).unique().tolist(), reverse=True)
season = st.selectbox("season", season_options, key="postgen_season", label_visibility="collapsed")

row = get_season_row(df, int(season))
insight = build_ian_insight(row)
tag, _ = classify_process_vs_result(row)
summary = build_plain_summary(row, tag)
tc = tag_class(tag)
pc = pill_class(str(row["playoff_result"]))

# ── season card (compact) ──────────────────────────────
st.markdown(f"""
<div class="top-card">
  <div class="big-year">{int(row['season'])}</div>
  <div class="record">{int(row['wins'])} &ndash; {int(row['losses'])}</div>
  <span class="pill {pc}">{row['playoff_result']}</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="narrative-card {tc}">
  <div class="process-tag {tc}">● {tag}</div>
  <div class="sentence">{summary}</div>
</div>
""", unsafe_allow_html=True)

# ── editable fields ────────────────────────────────────
st.markdown('<div class="section-label">edit before building</div>', unsafe_allow_html=True)

observation = st.text_area("what happened", value=insight["observation"], height=70, key="pg_obs")
mechanism   = st.text_area("why it happened", value=insight["mechanism"], height=90, key="pg_mech")
implication = st.text_area("what it means", value=insight["implication"], height=70, key="pg_impl")

# ── tone + output ──────────────────────────────────────
st.markdown('<div class="section-label">tone</div>', unsafe_allow_html=True)

tone = st.radio(
    "tone", ["simple", "analytical", "one-liner"],
    horizontal=True, label_visibility="collapsed",
    key="pg_tone",
)

edited_insight = {
    "observation": observation,
    "mechanism": mechanism,
    "implication": implication,
    "tag": tag,
}

post_text = build_post_variants(edited_insight, tone)

st.markdown('<div class="section-label">post</div>', unsafe_allow_html=True)
st.markdown(f'<div class="post-box">{post_text}</div>', unsafe_allow_html=True)
st.code(post_text, language=None)

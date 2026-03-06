import streamlit as st
from intelligence.redsox_history_engine import (
    get_history_df, get_season_row, build_ian_insight,
    classify_process_vs_result, build_plain_summary,
)
from content_engine.post_generator import build_post_variants
from config.styles import APP_CSS, pill_class, tag_class

st.set_page_config(page_title="season explorer", layout="centered")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ── load full dataset ──────────────────────────────────
df = get_history_df()
all_seasons = sorted(df["season"].dropna().astype(int).unique().tolist(), reverse=True)

# ── filters ───────────────────────────────────────────
with st.expander("🔍 filter seasons", expanded=False):
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        min_wins = st.slider(
            "min wins", min_value=20, max_value=115,
            value=20, step=1, key="filt_wins",
        )

    with fc2:
        max_losses = st.slider(
            "max losses", min_value=40, max_value=120,
            value=120, step=1, key="filt_losses",
        )

    with fc3:
        playoff_filter = st.radio(
            "postseason",
            ["all", "playoff seasons only", "missed playoffs only"],
            key="filt_playoff",
        )

# ── apply filters ──────────────────────────────────────
filtered = df.copy()
filtered = filtered[filtered["wins"] >= min_wins]
filtered = filtered[filtered["losses"] <= max_losses]

if playoff_filter == "playoff seasons only":
    filtered = filtered[filtered["playoff_result"] != "missed playoffs"]
elif playoff_filter == "missed playoffs only":
    filtered = filtered[filtered["playoff_result"] == "missed playoffs"]

season_options = sorted(
    filtered["season"].dropna().astype(int).unique().tolist(), reverse=True
)

# ── guard: no results ──────────────────────────────────
if not season_options:
    st.warning("no seasons match those filters. try relaxing the criteria.")
    st.stop()

# ── filter summary badge ───────────────────────────────
total = len(all_seasons)
showing = len(season_options)
if showing < total:
    st.markdown(
        f'<div class="filter-badge">showing {showing} of {total} seasons</div>',
        unsafe_allow_html=True,
    )

# ── season selector ────────────────────────────────────
season = st.selectbox(
    "season", season_options,
    key="explorer_season", label_visibility="collapsed",
)

# ── build season data ──────────────────────────────────
row     = get_season_row(df, int(season))
insight = build_ian_insight(row)
tag, _  = classify_process_vs_result(row)
summary = build_plain_summary(row, tag)
tc      = tag_class(tag)
pc      = pill_class(str(row["playoff_result"]))
rd      = int(row["run_diff"])
rd_display = f"+{rd}" if rd > 0 else str(rd)

# ── layer 1: result card ───────────────────────────────
st.markdown(f"""
<div class="top-card">
  <div class="big-year">{int(row['season'])}</div>
  <div class="record">{int(row['wins'])} &ndash; {int(row['losses'])}</div>
  <span class="pill {pc}">{row['playoff_result']}</span>
  <div class="meta-line">manager: <strong>{row['manager']}</strong> &nbsp;·&nbsp; {row['era_label']}</div>
</div>
""", unsafe_allow_html=True)

# ── layer 2: one sentence ──────────────────────────────
st.markdown(f"""
<div class="narrative-card {tc}">
  <div class="process-tag {tc}">● {tag}</div>
  <div class="sentence">{summary}</div>
</div>
""", unsafe_allow_html=True)

# ── layer 3: dig deeper ────────────────────────────────
with st.expander("dig deeper"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="omi-label">what happened</div>', unsafe_allow_html=True)
        st.write(insight["observation"])
    with col2:
        st.markdown('<div class="omi-label">why it happened</div>', unsafe_allow_html=True)
        st.write(insight["mechanism"])
    with col3:
        st.markdown('<div class="omi-label">what it means</div>', unsafe_allow_html=True)
        st.write(insight["implication"])

    st.divider()

    s1, s2, s3 = st.columns(3)
    s1.metric("run diff", rd_display)
    s2.metric("team ops",  row["team_ops"])
    s3.metric("team era",  row["team_era"])

    s4, s5, s6 = st.columns(3)
    s4.metric("team obp", row["team_obp"])
    s5.metric("team slg", row["team_slg"])
    s6.metric("team fip", row["team_fip"])

# ── post builder ───────────────────────────────────────
st.markdown('<div class="section-label">build a post</div>', unsafe_allow_html=True)

tone = st.radio(
    "tone", ["simple", "analytical", "one-liner"],
    horizontal=True, label_visibility="collapsed",
    key="explorer_tone",
)

post_text = build_post_variants(insight, tone)
st.markdown(f'<div class="post-box">{post_text}</div>', unsafe_allow_html=True)
st.code(post_text, language=None)

"""
09_redsox_franchise_timeline.py
Interactive franchise timeline — era filter, playoff filter, player search.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from intelligence.redsox_history_engine import (
    get_history_df, get_season_row, build_ian_insight,
    classify_process_vs_result, build_plain_summary,
)
from content_engine.post_generator import build_post_variants
from config.styles import APP_CSS, TIMELINE_CSS, pill_class, tag_class

st.set_page_config(page_title="franchise timeline", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown(TIMELINE_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════
df = get_history_df()
df = df.sort_values("season").reset_index(drop=True)
df["season"] = df["season"].astype(int)

# ── macro-era definitions  (casual-friendly groupings) ───────────────────
MACRO_ERAS = {
    "⚾ yaz era  (1967–1976)": list(range(1967, 1977)),
    "💪 rice & lynn  (1977–1986)": list(range(1977, 1987)),
    "🎯 boggs & clemens  (1987–1996)": list(range(1987, 1997)),
    "🔥 pedro & manny  (1997–2006)": list(range(1997, 2007)),
    "🏆 francona dynasty  (2007–2013)": list(range(2007, 2014)),
    "🌟 betts emergence  (2014–2019)": list(range(2014, 2020)),
    "🔄 rebuild & now  (2020–2024)": list(range(2020, 2025)),
}

# band colours for chart vrects (alternating, subtle)
MACRO_ERA_COLORS = [
    "rgba(200,16,46,0.06)",
    "rgba(126,184,247,0.06)",
    "rgba(228,184,77,0.06)",
    "rgba(200,16,46,0.06)",
    "rgba(126,184,247,0.06)",
    "rgba(228,184,77,0.06)",
    "rgba(200,16,46,0.06)",
]

# ── playoff result display names ─────────────────────────────────────────
RESULT_DISPLAY = {
    "world series":           "🏆 world series win",
    "lost alcs":              "🔴 lost alcs",
    "lost alds":              "🔵 lost alds",
    "al east tie-break loss": "⚪ al east tiebreak loss",
    "missed playoffs":        "✖️ missed playoffs",
}
ALL_RESULTS_RAW  = sorted(df["playoff_result"].unique().tolist())
ALL_RESULTS_DISP = [RESULT_DISPLAY.get(r, r) for r in ALL_RESULTS_RAW]

# reverse map: display → raw
DISP_TO_RAW = {v: k for k, v in RESULT_DISPLAY.items()}

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── player search ────────────────────────────────────────────────────
    st.markdown("## 🔎 player search")
    player_query = st.text_input(
        "search by player",
        placeholder="e.g. Pedro, Ortiz, Betts…",
        key="tl_player",
    ).strip().lower()

    st.divider()

    # ── era filter ───────────────────────────────────────────────────────
    st.markdown("## 📅 era")
    st.caption("select one or more eras to focus on")

    era_col1, era_col2 = st.columns(2)
    if era_col1.button("all", key="era_all", use_container_width=True):
        st.session_state["tl_eras"] = list(MACRO_ERAS.keys())
    if era_col2.button("clear", key="era_clear", use_container_width=True):
        st.session_state["tl_eras"] = []

    if "tl_eras" not in st.session_state:
        st.session_state["tl_eras"] = list(MACRO_ERAS.keys())

    selected_macro_eras = st.multiselect(
        "eras",
        options=list(MACRO_ERAS.keys()),
        default=st.session_state["tl_eras"],
        key="tl_eras",
        label_visibility="collapsed",
    )

    st.divider()

    # ── playoff filter ───────────────────────────────────────────────────
    st.markdown("## 🏆 playoff result")
    st.caption("pick which outcomes to include")

    pl_col1, pl_col2 = st.columns(2)
    if pl_col1.button("all", key="pl_all", use_container_width=True):
        st.session_state["tl_results"] = ALL_RESULTS_DISP
    if pl_col2.button("ws only", key="pl_ws", use_container_width=True):
        st.session_state["tl_results"] = ["🏆 world series win"]

    if "tl_results" not in st.session_state:
        st.session_state["tl_results"] = ALL_RESULTS_DISP

    selected_result_disp = st.multiselect(
        "results",
        options=ALL_RESULTS_DISP,
        default=st.session_state["tl_results"],
        key="tl_results",
        label_visibility="collapsed",
    )

    st.divider()

    # ── wins / losses sliders ────────────────────────────────────────────
    st.markdown("## 📊 record")
    min_wins   = st.slider("min wins",   20,  115, 20,  1, key="tl_wins")
    max_losses = st.slider("max losses", 40,  120, 120, 1, key="tl_losses")

    st.divider()

    # ── keyword search ───────────────────────────────────────────────────
    st.markdown("## 🔍 keyword")
    keyword = st.text_input(
        "keyword",
        placeholder="e.g. Francona, collapse, 2011…",
        key="tl_keyword",
        label_visibility="collapsed",
    ).strip().lower()

    st.divider()
    st.markdown(
        "<small style='color:#aaa;'>click any bar to explore that season</small>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════
# FILTER LOGIC
# ══════════════════════════════════════════════════════════════════════════
mask = pd.Series([True] * len(df), index=df.index)

# era filter — expand macro-eras to season years
if selected_macro_eras:
    era_seasons = set()
    for macro in selected_macro_eras:
        era_seasons.update(MACRO_ERAS[macro])
    mask &= df["season"].isin(era_seasons)
else:
    # nothing selected → show nothing (all dim)
    mask &= pd.Series([False] * len(df), index=df.index)

# playoff result filter
if selected_result_disp:
    selected_results_raw = {DISP_TO_RAW.get(d, d) for d in selected_result_disp}
    mask &= df["playoff_result"].isin(selected_results_raw)
else:
    mask &= pd.Series([False] * len(df), index=df.index)

# record sliders
mask &= df["wins"]   >= min_wins
mask &= df["losses"] <= max_losses

# player search
if player_query:
    pm  = df["key_players"].str.lower().str.contains(player_query, na=False)
    pm |= df["mechanism_summary"].str.lower().str.contains(player_query, na=False)
    mask &= pm

# keyword search
if keyword:
    kw_cols = ["manager", "era_label", "playoff_result", "mechanism_summary", "key_players"]
    km = df[kw_cols].apply(
        lambda col: col.astype(str).str.lower().str.contains(keyword, na=False)
    ).any(axis=1)
    try:
        km |= (df["season"] == int(keyword))
    except ValueError:
        pass
    mask &= km

active_seasons = set(df.loc[mask, "season"].tolist())
total_seasons  = len(df)
active_count   = len(active_seasons)

# ══════════════════════════════════════════════════════════════════════════
# ACTIVE FILTER CHIPS  (compact summary bar above the chart)
# ══════════════════════════════════════════════════════════════════════════
chip_parts = []

if len(selected_macro_eras) < len(MACRO_ERAS):
    for m in selected_macro_eras:
        chip_parts.append(f'<span class="chip chip-era">{m}</span>')
    if not selected_macro_eras:
        chip_parts.append('<span class="chip chip-warn">no era selected</span>')

if len(selected_result_disp) < len(ALL_RESULTS_DISP):
    for r in selected_result_disp:
        chip_parts.append(f'<span class="chip chip-result">{r}</span>')
    if not selected_result_disp:
        chip_parts.append('<span class="chip chip-warn">no result selected</span>')

if min_wins > 20:
    chip_parts.append(f'<span class="chip chip-record">wins ≥ {min_wins}</span>')
if max_losses < 120:
    chip_parts.append(f'<span class="chip chip-record">losses ≤ {max_losses}</span>')
if player_query:
    chip_parts.append(f'<span class="chip chip-player">👤 {player_query}</span>')
if keyword:
    chip_parts.append(f'<span class="chip chip-keyword">🔍 {keyword}</span>')

count_chip = (
    f'<span class="chip chip-count">{active_count} of {total_seasons} seasons</span>'
    if active_count < total_seasons
    else f'<span class="chip chip-count-all">all {total_seasons} seasons</span>'
)
chip_parts.insert(0, count_chip)

chips_html = '<div class="chip-bar">' + "".join(chip_parts) + "</div>"
st.markdown(chips_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# CHART — colour / opacity / hover
# ══════════════════════════════════════════════════════════════════════════
def bar_color(row):
    pr = str(row["playoff_result"]).lower()
    if "world series" in pr and "lost" not in pr: return "#c8102e"
    if "alcs" in pr:                              return "#e4b84d"
    if "alds" in pr or "tiebreak" in pr or "tie-break" in pr: return "#7eb8f7"
    return "#4a4a5a"

df["_color"]   = df.apply(bar_color, axis=1)
df["_opacity"] = df["season"].apply(lambda s: 1.0 if int(s) in active_seasons else 0.10)

def make_hover(row):
    pr  = str(row["playoff_result"])
    rd  = int(row["run_diff"])
    rds = f"+{rd}" if rd > 0 else str(rd)
    pl  = str(row.get("key_players", "")).strip()
    pl_line = f"<br><i>{pl}</i>" if pl else ""
    return (
        f"<b>{int(row['season'])}</b><br>"
        f"{int(row['wins'])}-{int(row['losses'])}<br>"
        f"run diff: {rds}<br>"
        f"{pr}{pl_line}"
    )

df["_hover"] = df.apply(make_hover, axis=1)

# ── selected season state ─────────────────────────────────────────────────
if "tl_selected_season" not in st.session_state:
    playoff_df = df.loc[df["playoff_result"] != "missed playoffs", "season"]
    st.session_state["tl_selected_season"] = (
        int(playoff_df.max()) if not playoff_df.empty else int(df["season"].max())
    )

# ══════════════════════════════════════════════════════════════════════════
# BUILD PLOTLY FIGURE
# ══════════════════════════════════════════════════════════════════════════
fig = go.Figure()

# ── era band shading (vrects) ─────────────────────────────────────────────
for i, (macro_name, yrs) in enumerate(MACRO_ERAS.items()):
    yrs_in_df = [y for y in yrs if y in df["season"].values]
    if not yrs_in_df:
        continue
    x0 = min(yrs_in_df) - 0.5
    x1 = max(yrs_in_df) + 0.5
    is_active = macro_name in selected_macro_eras
    fill_color = MACRO_ERA_COLORS[i] if is_active else "rgba(0,0,0,0)"
    fig.add_vrect(
        x0=x0, x1=x1,
        fillcolor=fill_color,
        layer="below",
        line_width=0,
    )
    # era label tick at top of band
    mid_year = (min(yrs_in_df) + max(yrs_in_df)) / 2
    short_name = macro_name.split("(")[0].strip().lstrip("⚾💪🎯🔥🏆🌟🔄 ")
    fig.add_annotation(
        x=mid_year, y=115,
        text=short_name,
        showarrow=False,
        font=dict(
            color="rgba(255,255,255,0.55)" if is_active else "rgba(255,255,255,0.12)",
            size=8,
        ),
        xanchor="center",
    )

# ── bars ──────────────────────────────────────────────────────────────────
fig.add_trace(go.Bar(
    x=df["season"].tolist(),
    y=df["wins"].tolist(),
    marker=dict(
        color=df["_color"].tolist(),
        opacity=df["_opacity"].tolist(),
        line=dict(width=0),
    ),
    hovertemplate="%{customdata}<extra></extra>",
    customdata=df["_hover"].tolist(),
))

# ── .500 line ─────────────────────────────────────────────────────────────
fig.add_hline(
    y=81,
    line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dot"),
    annotation_text=".500",
    annotation_font=dict(color="rgba(255,255,255,0.3)", size=10),
    annotation_position="left",
)

fig.update_layout(
    paper_bgcolor="#0d1b2a",
    plot_bgcolor="#0d1b2a",
    height=320,
    margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(
        tickmode="linear", dtick=5,
        tickfont=dict(color="rgba(255,255,255,0.4)", size=10),
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.1)",
    ),
    yaxis=dict(
        title=dict(text="wins", font=dict(color="rgba(255,255,255,0.3)", size=10)),
        tickfont=dict(color="rgba(255,255,255,0.3)", size=10),
        gridcolor="rgba(255,255,255,0.06)",
        range=[0, 120],
    ),
    showlegend=False,
    bargap=0.15,
    clickmode="event+select",
)

# ── colour legend ─────────────────────────────────────────────────────────
legend_html = """
<div class="tl-legend">
  <span class="tl-dot" style="background:#c8102e;"></span> world series win &nbsp;
  <span class="tl-dot" style="background:#e4b84d;"></span> alcs &nbsp;
  <span class="tl-dot" style="background:#7eb8f7;"></span> alds / tiebreak &nbsp;
  <span class="tl-dot" style="background:#4a4a5a;"></span> missed playoffs
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)

# ── render + capture click ────────────────────────────────────────────────
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    key="timeline_chart",
)

if event and event.get("selection") and event["selection"].get("points"):
    pts = event["selection"]["points"]
    if pts:
        cx = pts[0].get("x")
        if cx is not None:
            st.session_state["tl_selected_season"] = int(cx)

selected_season = st.session_state["tl_selected_season"]

# ── season jump dropdown ──────────────────────────────────────────────────
active_list = sorted(list(active_seasons), reverse=True)

if not active_list:
    st.warning("no seasons match the current filters — try selecting more eras or results.")
    st.stop()

if selected_season not in active_list:
    selected_season = active_list[0]
    st.session_state["tl_selected_season"] = selected_season

jump = st.selectbox(
    "jump to season",
    active_list,
    index=active_list.index(selected_season),
    key="tl_jump",
    label_visibility="collapsed",
)
if jump != selected_season:
    st.session_state["tl_selected_season"] = jump
    selected_season = jump

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# SEASON CARD
# ══════════════════════════════════════════════════════════════════════════
row     = get_season_row(df, int(selected_season))
insight = build_ian_insight(row)
tag, _  = classify_process_vs_result(row)
summary = build_plain_summary(row, tag)
tc      = tag_class(tag)
pc      = pill_class(str(row["playoff_result"]))
rd      = int(row["run_diff"])
rd_disp = f"+{rd}" if rd > 0 else str(rd)

FRIENDLY_TAGS = {
    "signal":                 "✅ as good as they looked",
    "underperformed process": "📉 better than the record shows",
    "overperformed process":  "🍀 got a little lucky",
    "balanced":               "➡️ exactly what they were",
}
friendly_label = FRIENDLY_TAGS.get(tag, tag)

raw_players = str(row.get("key_players", "")).strip()
player_list = [p.strip() for p in raw_players.split(",") if p.strip()]

def player_chip_html(name, query):
    highlighted = query and query in name.lower()
    cls = "player-chip player-chip-highlight" if highlighted else "player-chip"
    return f'<span class="{cls}">{name}</span>'

player_chips_html = (
    '<div class="player-chips">'
    + "".join(player_chip_html(p, player_query) for p in player_list)
    + "</div>"
) if player_list else ""

# which macro-era does this season belong to?
season_macro = next(
    (k for k, v in MACRO_ERAS.items() if int(row["season"]) in v), ""
)

col_card, col_meta = st.columns([2, 1])

with col_card:
    era_line = (
        f'<div class="era-badge">{season_macro}</div>'
        if season_macro else ""
    )
    st.markdown(f"""
<div class="top-card">
  <div class="big-year">{int(row['season'])}</div>
  <div class="record">{int(row['wins'])} &ndash; {int(row['losses'])}</div>
  <span class="pill {pc}">{row['playoff_result']}</span>
  {era_line}
  <div class="meta-line">manager: <strong>{row['manager']}</strong> &nbsp;·&nbsp; {row['era_label']}</div>
  {player_chips_html}
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="narrative-card {tc}">
  <div class="process-tag {tc}">● {friendly_label}</div>
  <div class="sentence">{summary}</div>
</div>
""", unsafe_allow_html=True)

with col_meta:
    st.markdown(f"""
<div class="stat-panel">
  <div class="stat-item"><span class="stat-label">run diff</span><span class="stat-val">{rd_disp}</span></div>
  <div class="stat-item"><span class="stat-label">team ops</span><span class="stat-val">{row['team_ops']}</span></div>
  <div class="stat-item"><span class="stat-label">team era</span><span class="stat-val">{row['team_era']}</span></div>
  <div class="stat-item"><span class="stat-label">team fip</span><span class="stat-val">{row['team_fip']}</span></div>
</div>
""", unsafe_allow_html=True)

# ── dig deeper ────────────────────────────────────────────────────────────
with st.expander("dig deeper →  observation / mechanism / implication"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="omi-label">what happened</div>', unsafe_allow_html=True)
        st.write(insight["observation"])
    with c2:
        st.markdown('<div class="omi-label">why it happened</div>', unsafe_allow_html=True)
        st.write(insight["mechanism"])
    with c3:
        st.markdown('<div class="omi-label">what it means</div>', unsafe_allow_html=True)
        st.write(insight["implication"])
    st.divider()
    s1, s2, s3 = st.columns(3)
    s1.metric("obp",    row["team_obp"])
    s2.metric("slg",    row["team_slg"])
    s3.metric("losses", int(row["losses"]))

# ── post builder ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">build a post</div>', unsafe_allow_html=True)
tone = st.radio(
    "tone", ["simple", "analytical", "one-liner"],
    horizontal=True, label_visibility="collapsed", key="tl_tone",
)
post_text = build_post_variants(insight, tone)
st.markdown(f'<div class="post-box">{post_text}</div>', unsafe_allow_html=True)
st.code(post_text, language=None)

# ── "all seasons with this player" panel ─────────────────────────────────
if player_query and active_count > 1:
    st.divider()
    st.markdown(
        f'<div class="section-label">all seasons with "{player_query}"</div>',
        unsafe_allow_html=True,
    )
    related = df.loc[df["season"].isin(active_seasons)].sort_values("season", ascending=False)
    rows_html = ""
    for _, r in related.iterrows():
        yr  = int(r["season"])
        w   = int(r["wins"])
        l   = int(r["losses"])
        pr  = str(r["playoff_result"])
        pc2 = pill_class(pr)
        bold = " style='font-weight:700;'" if yr == selected_season else ""
        rows_html += (
            f'<div class="related-row"{bold}>'
            f'<span class="related-year">{yr}</span>'
            f'<span class="related-record">{w}-{l}</span>'
            f'<span class="pill {pc2}" style="font-size:10px;padding:3px 10px;">{pr}</span>'
            f"</div>"
        )
    st.markdown(f'<div class="related-list">{rows_html}</div>', unsafe_allow_html=True)

# ── era comparison mini-table  (shows when exactly one macro-era active) ──
if len(selected_macro_eras) == 1:
    st.divider()
    chosen_era = selected_macro_eras[0]
    era_seasons_df = df[df["season"].isin(MACRO_ERAS[chosen_era])].copy()
    if not era_seasons_df.empty:
        st.markdown(
            f'<div class="section-label">{chosen_era} — all seasons</div>',
            unsafe_allow_html=True,
        )
        era_tags = era_seasons_df.apply(
            lambda r: classify_process_vs_result(r)[0], axis=1
        )
        display_df = era_seasons_df[
            ["season", "wins", "losses", "run_diff", "playoff_result", "manager"]
        ].copy()
        display_df.insert(len(display_df.columns), "process tag", era_tags.values)
        display_df = display_df.rename(columns={
            "season": "year", "run_diff": "run diff",
            "playoff_result": "result", "process tag": "tag",
        })
        st.dataframe(
            display_df.sort_values("year", ascending=False).reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
        avg_wins = era_seasons_df["wins"].mean()
        avg_rd   = era_seasons_df["run_diff"].mean()
        ws_count = era_seasons_df["playoff_result"].str.lower().str.contains(
            "world series"
        ).sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("avg wins",    f"{avg_wins:.1f}")
        m2.metric("avg run diff", f"{avg_rd:+.1f}")
        m3.metric("ws titles",   int(ws_count))

# ══════════════════════════════════════════════════════════════════════════
# SLIDESHOW EXPORT
# ══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎞️ export as slideshow")
st.markdown(
    "Generates a fully-designed 17-slide PPTX presentation covering every era, "
    "all 58 seasons, 6 championship cards, radar comparison, and the current rebuild. "
    "Opens in PowerPoint, Keynote, or Google Slides."
)

if st.button("generate & download PPTX slideshow", key="pptx_export_btn"):
    import sys, os, tempfile
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    with st.spinner("building 17 slides… (~10 seconds)"):
        try:
            from build_timeline_slideshow import build_slideshow
            tmp = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
            tmp.close()
            build_slideshow(tmp.name)
            with open(tmp.name, "rb") as f:
                pptx_bytes = f.read()
            os.unlink(tmp.name)
            st.success(f"PPTX ready — {len(pptx_bytes)//1024} KB · 17 slides")
            st.download_button(
                "⬇ download franchise timeline slideshow (.pptx)",
                data=pptx_bytes,
                file_name="redsox_franchise_timeline.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="pptx_dl_btn",
            )
        except Exception as e:
            st.error(f"Slideshow generation failed: {e}")
            raise

# ══════════════════════════════════════════════════════════════════════════
# WEB EXPORT
# ══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🌐 export as interactive web page")
st.markdown(
    "Generates a fully self-contained **HTML file** you can open in any browser — "
    "no server, no Python, no dependencies. "
    "Includes all 4 charts, season detail cards, era table, player search, and keyboard navigation."
)

if st.button("generate & download HTML web timeline", key="html_export_btn"):
    import sys, os, tempfile
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    with st.spinner("building interactive web timeline… (~5 seconds)"):
        try:
            from generate_web_timeline import build_html
            tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            tmp.close()
            build_html(tmp.name)
            with open(tmp.name, "r", encoding="utf-8") as f:
                html_str = f.read()
            os.unlink(tmp.name)
            st.success(f"HTML ready — {len(html_str)//1024} KB · standalone, open in any browser")
            st.download_button(
                "⬇ download interactive timeline (.html)",
                data=html_str.encode("utf-8"),
                file_name="redsox_franchise_timeline.html",
                mime="text/html",
                key="html_dl_btn",
            )
        except Exception as e:
            st.error(f"HTML generation failed: {e}")
            raise


# ── Mobile Web Export ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📱 Mobile-Responsive Web Export")
st.markdown(
    "Generate a **mobile-first standalone HTML** timeline — works on phone, tablet, or desktop. "
    "No Python or server required; open by double-clicking the file."
)
if st.button("Generate Mobile Timeline HTML", key="gen_mobile_html"):
    import time, tempfile, os
    t0 = time.time()
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        import generate_mobile_timeline as _gmt
        html_bytes = _gmt.HTML.encode("utf-8")
        elapsed = time.time() - t0
        st.success(f"Mobile HTML ready — {len(html_bytes)//1024:.0f} KB in {elapsed:.1f}s")
        st.download_button(
            label="Download redsox_mobile_timeline.html",
            data=html_bytes,
            file_name="redsox_mobile_timeline.html",
            mime="text/html",
            key="dl_mobile_html"
        )
    except Exception as e:
        st.error(f"Generation failed: {e}")

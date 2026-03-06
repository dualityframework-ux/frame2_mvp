APP_CSS = """
<style>
/* ── hide default streamlit chrome ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* ── global ── */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
}

/* ── top card ── */
.top-card {
    background: #0d1b2a;
    border-radius: 14px;
    padding: 28px 32px 24px;
    color: white;
    margin-bottom: 12px;
}
.top-card .big-year {
    font-size: 52px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1;
    color: white;
}
.top-card .record {
    font-size: 26px;
    font-weight: 300;
    color: rgba(255,255,255,0.65);
    margin-top: 4px;
    margin-bottom: 14px;
}
.pill {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.pill-ws   { background: #c8102e; color: white; }
.pill-alcs { background: rgba(228,184,77,0.25); color: #e4b84d; }
.pill-alds { background: rgba(126,184,247,0.2); color: #7eb8f7; }
.pill-miss { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.45); }

/* ── era badge inside top-card ── */
.era-badge {
    display: inline-block;
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.5);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 10px;
    margin-left: 6px;
    letter-spacing: 0.3px;
}

/* ── player chips inside top-card ── */
.player-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 14px;
}
.player-chip {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.65);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 12px;
    font-weight: 500;
}
.player-chip-highlight {
    background: rgba(200,16,46,0.35) !important;
    color: #ff8fa3 !important;
    border-color: rgba(200,16,46,0.5) !important;
    font-weight: 700;
}

/* ── narrative card ── */
.narrative-card {
    background: white;
    border-radius: 12px;
    border-left: 4px solid #ccc;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}
.narrative-card.signal      { border-left-color: #2da870; }
.narrative-card.over        { border-left-color: #c8940a; }
.narrative-card.under       { border-left-color: #4a90d9; }
.narrative-card.balanced    { border-left-color: #999; }

.process-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
}
.process-tag.signal   { color: #2da870; }
.process-tag.over     { color: #c8940a; }
.process-tag.under    { color: #4a90d9; }
.process-tag.balanced { color: #999; }

.sentence {
    font-size: 18px;
    font-weight: 600;
    color: #111;
    line-height: 1.5;
}

/* ── omi labels ── */
.omi-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #aaa;
    margin-bottom: 6px;
}

/* ── post box ── */
.post-box {
    background: #f7f8fa;
    border-radius: 10px;
    padding: 16px;
    font-size: 13px;
    color: #333;
    line-height: 1.8;
    font-family: Georgia, serif;
    margin-bottom: 10px;
    white-space: pre-wrap;
    border: 1px solid #e8e9eb;
}

/* ── section label ── */
.section-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #aaa;
    margin: 20px 0 10px;
}

/* ── manager / meta line ── */
.meta-line {
    font-size: 13px;
    color: rgba(255,255,255,0.45);
    margin-top: 10px;
}
.meta-line strong { color: rgba(255,255,255,0.75); }

/* ── active filter chip bar ── */
.chip-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
    align-items: center;
}
.chip {
    display: inline-block;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
    white-space: nowrap;
}
.chip-count     { background: rgba(200,16,46,0.10); color: #c8102e; }
.chip-count-all { background: rgba(45,168,112,0.10); color: #2da870; }
.chip-era       { background: rgba(126,184,247,0.15); color: #4a90d9; border: 1px solid rgba(126,184,247,0.3); }
.chip-result    { background: rgba(228,184,77,0.15); color: #a07820; border: 1px solid rgba(228,184,77,0.3); }
.chip-record    { background: rgba(150,150,150,0.12); color: #666; }
.chip-player    { background: rgba(200,16,46,0.10); color: #c8102e; }
.chip-keyword   { background: rgba(100,100,100,0.08); color: #555; }
.chip-warn      { background: rgba(200,100,0,0.12); color: #b06000; }

/* ── filter badge (legacy) ── */
.filter-badge {
    display: inline-block;
    background: rgba(200,16,46,0.10);
    color: #c8102e;
    font-size: 12px;
    font-weight: 600;
    border-radius: 20px;
    padding: 4px 12px;
    margin-bottom: 10px;
    margin-right: 6px;
}
.player-search-badge {
    display: inline-block;
    background: rgba(74,144,217,0.12);
    color: #4a90d9;
    font-size: 12px;
    font-weight: 600;
    border-radius: 20px;
    padding: 4px 12px;
    margin-bottom: 10px;
}

/* ── related seasons list ── */
.related-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
}
.related-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 8px 14px;
    background: #f7f8fa;
    border-radius: 8px;
    border: 1px solid #eee;
    font-size: 13px;
}
.related-year   { font-weight: 700; color: #111; min-width: 38px; }
.related-record { color: #555; min-width: 52px; }
</style>
"""

# ── timeline-specific CSS ──────────────────────────────────────────────────
TIMELINE_CSS = """
<style>
.tl-legend {
    font-size: 12px;
    color: rgba(255,255,255,0.45);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
}
.tl-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 3px;
}
.stat-panel {
    background: #f7f8fa;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #e8e9eb;
    height: 100%;
}
.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}
.stat-item:last-child { border-bottom: none; }
.stat-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #aaa;
}
.stat-val {
    font-size: 16px;
    font-weight: 700;
    color: #111;
}
</style>
"""


def pill_class(playoff_result: str) -> str:
    r = (playoff_result or "").lower()
    if "world series" in r and "lost" not in r: return "pill-ws"
    if "alcs" in r:                             return "pill-alcs"
    if "alds" in r or "tiebreak" in r or "tie-break" in r: return "pill-alds"
    return "pill-miss"


def tag_class(tag: str) -> str:
    t = (tag or "").lower()
    if t == "signal":            return "signal"
    if "underperform" in t:      return "under"
    if "overperform" in t:       return "over"
    return "balanced"

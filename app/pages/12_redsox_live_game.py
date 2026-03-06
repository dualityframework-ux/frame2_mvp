"""
app/pages/12_redsox_live_game.py
────────────────────────────────
Live Game Monitor — today's Red Sox game status, score,
and linescore pulled from the MLB Stats API.
Gracefully falls back to a "no game today" message.
"""

import os
import sys
import streamlit as st
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from adapters.mlb_statsapi import get_schedule, summarize_live, resolve_team_id
from config.styles import APP_CSS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Live Game · frame²", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown("## 📡 live game monitor")
st.caption("today's Red Sox game · data via MLB Stats API (statsapi.mlb.com)")

# ── Date picker ───────────────────────────────────────────────────────────────
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
sel_date = st.date_input("game date", value=datetime.now(timezone.utc).date(), key="live_date")
date_str = sel_date.strftime("%Y-%m-%d")

auto_refresh = st.checkbox("auto-refresh every 30 s", value=False, key="live_refresh")
if auto_refresh:
    import time
    st.empty()  # placeholder — in production use st_autorefresh

st.markdown("---")

# ── Fetch schedule ────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_schedule(date: str):
    try:
        team_id = resolve_team_id("red sox")
        games = get_schedule(team_id, day=date)
        return games, None
    except Exception as exc:
        return [], str(exc)


with st.spinner("checking schedule…"):
    games, err = fetch_schedule(date_str)

if err:
    st.warning(f"⚠️ Could not reach MLB Stats API: `{err}`")
    st.info("The live game monitor requires an internet connection to statsapi.mlb.com.")
    st.stop()

if not games:
    st.info(f"⚾ No Red Sox game scheduled on **{date_str}**.")
    st.markdown("Browse history instead using the **Season Explorer** or **Franchise Timeline** pages.")
    st.stop()

# ── Game selector (doubleheaders) ─────────────────────────────────────────────
game = games[0]
if len(games) > 1:
    labels = [f"Game {i+1}: {g['away']} @ {g['home']} ({g['status']})" for i, g in enumerate(games)]
    sel_idx = st.selectbox("select game", range(len(games)), format_func=lambda i: labels[i])
    game = games[sel_idx]

game_pk = game["gamePk"]
status  = game.get("status", "Unknown")

st.markdown(f"### {game['away']} @ {game['home']}")
st.caption(f"Game PK: {game_pk} · Status: **{status}**")

# ── Live scoreboard ───────────────────────────────────────────────────────────
LIVE_STATUSES = {"In Progress", "Warmup", "Pre-Game", "Delayed"}

if any(s in (status or "") for s in LIVE_STATUSES):
    @st.cache_data(ttl=10)
    def fetch_live(pk: int):
        try:
            return summarize_live(pk), None
        except Exception as exc:
            return {}, str(exc)

    live, live_err = fetch_live(game_pk)

    if live_err:
        st.warning(f"Live feed error: `{live_err}`")
    elif live:
        # Score row
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 2])
        c1.markdown(f"**{live.get('away','—')}**")
        c2.metric("score", str(live.get("away_runs", "—")))
        c3.markdown(
            f"<div style='text-align:center;font-size:28px;padding-top:8px'>–</div>",
            unsafe_allow_html=True
        )
        c4.metric("score", str(live.get("home_runs", "—")))
        c5.markdown(f"**{live.get('home','—')}**")

        st.markdown("---")

        # Count / outs / bases
        inning = live.get("inning", "—")
        half   = live.get("half", "")
        count  = live.get("count", "—")
        outs   = live.get("outs", "—")
        bases  = live.get("bases", "___")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("inning", f"{half} {inning}" if inning != "—" else "—")
        d2.metric("count (B-S)", count)
        d3.metric("outs", outs)

        # Base display
        b1 = "🟥" if bases[0] == "1" else "⬜"
        b2 = "🟥" if len(bases) > 1 and bases[1] == "2" else "⬜"
        b3 = "🟥" if len(bases) > 2 and bases[2] == "3" else "⬜"
        d4.markdown(
            f"""<div style='text-align:center;font-size:11px;color:#aaa;margin-top:4px'>bases</div>
            <div style='text-align:center;font-size:22px;letter-spacing:4px'>{b2}<br>{b1}{b3}</div>""",
            unsafe_allow_html=True
        )

        st.caption(f"_Data cached for 10 s · {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC_")

elif "Final" in (status or "") or "Completed" in (status or ""):
    @st.cache_data(ttl=3600)
    def fetch_final(pk: int):
        try:
            return summarize_live(pk), None
        except Exception as exc:
            return {}, str(exc)

    final, fin_err = fetch_final(game_pk)
    if fin_err:
        st.warning(f"Could not load final score: `{fin_err}`")
    elif final:
        st.markdown(f"### final score")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        c1.markdown(f"**{final.get('away','—')}**")
        c2.metric("", str(final.get("away_runs", "—")))
        c3.metric("", str(final.get("home_runs", "—")))
        c4.markdown(f"**{final.get('home','—')}**")
        st.success(f"Game complete · status: {status}")
else:
    # Scheduled / postponed
    game_time_utc = game.get("gameDate", "—")
    st.info(f"⏰ Game status: **{status}**")
    if game_time_utc and game_time_utc != "—":
        st.markdown(f"Scheduled start: `{game_time_utc[:16]} UTC`")
    st.markdown("Come back closer to game time for live score updates.")

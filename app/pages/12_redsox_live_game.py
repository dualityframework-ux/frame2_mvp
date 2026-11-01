from datetime import datetime
import streamlit as st


# -----------------------------
# helpers
# -----------------------------
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def classify_signal(score: float) -> str:
    if score >= 75:
        return "strong signal"
    if score >= 55:
        return "lean signal"
    if score >= 40:
        return "mixed"
    return "variance / weak edge"


def tilt_summary(contact_tilt: float, discipline_tilt: float, pressure_tilt: float) -> str:
    values = {
        "contact quality": contact_tilt,
        "plate discipline": discipline_tilt,
        "pressure / leverage": pressure_tilt,
    }
    best = max(values, key=values.get)
    worst = min(values, key=values.get)

    if values[best] - values[worst] < 5:
        return "the game is relatively balanced right now. no single mechanism is fully controlling the environment."
    return f"the clearest live tilt is {best}. the weakest area is {worst}."


def build_live_post(team_name: str, signal_tag: str, summary: str) -> str:
    team_name = (team_name or "red sox").strip().lower()
    return "\n".join([
        f"{team_name} live read:",
        summary,
        f"right now this looks like {signal_tag.lower()}.",
    ])


def build_mechanism_post(
    team_name: str,
    contact_tilt: float,
    discipline_tilt: float,
    pressure_tilt: float,
) -> str:
    team_name = (team_name or "red sox").strip().lower()

    values = [
        ("contact quality", contact_tilt),
        ("plate discipline", discipline_tilt),
        ("pressure", pressure_tilt),
    ]
    values.sort(key=lambda x: x[1], reverse=True)
    top_name, top_value = values[0]
    second_name, second_value = values[1]

    return (
        f"{team_name} aren’t just winning moments right now.\n"
        f"they’re tilting the environment through {top_name} ({top_value:.1f}) "
        f"with {second_name} ({second_value:.1f}) right behind it.\n"
        f"scoreboard usually follows when the mechanism keeps repeating."
    )


def compute_live_model(
    hard_hit_rate: float,
    barrel_proxy: float,
    chase_rate: float,
    whiff_rate: float,
    re24_swing: float,
    runners_on: str,
    leverage: str,
    redsox_score: int,
    opponent_score: int,
    inning: int,
) -> dict:
    traffic_map = {
        "bases empty": 20,
        "runner on": 45,
        "runners in scoring position": 70,
        "bases loaded": 90,
    }

    leverage_map = {
        "low": 30,
        "medium": 60,
        "high": 90,
    }

    contact_tilt = clamp((hard_hit_rate * 65) + (barrel_proxy * 35), 0, 100)
    discipline_tilt = clamp((chase_rate * 55) + (whiff_rate * 45), 0, 100)
    pressure_tilt = clamp(
        (((re24_swing + 3) / 6) * 55)
        + (traffic_map[runners_on] * 0.20)
        + (leverage_map[leverage] * 0.25),
        0,
        100,
    )

    live_edge_score = clamp(
        (contact_tilt * 0.40) + (discipline_tilt * 0.35) + (pressure_tilt * 0.25),
        0,
        100,
    )

    score_diff = redsox_score - opponent_score
    win_pressure = clamp(
        50
        + (score_diff * 8)
        + ((inning - 5) * 2.5)
        + ((live_edge_score - 50) * 0.45),
        1,
        99,
    )

    signal_tag = classify_signal(live_edge_score)
    summary_text = tilt_summary(contact_tilt, discipline_tilt, pressure_tilt)

    return {
        "contact_tilt": contact_tilt,
        "discipline_tilt": discipline_tilt,
        "pressure_tilt": pressure_tilt,
        "live_edge_score": live_edge_score,
        "win_pressure": win_pressure,
        "signal_tag": signal_tag,
        "summary_text": summary_text,
    }


# -----------------------------
# page
# -----------------------------
st.title("red sox game simulator")
st.caption("Explore manually entered game scenarios. This page does not fetch live game data.")

with st.sidebar:
    st.header("game input")

    team_name = st.text_input("team", value="red sox")
    opponent_name = st.text_input("opponent", value="yankees")

    inning = st.slider("inning", min_value=1, max_value=12, value=6)
    redsox_score = st.number_input("red sox runs", min_value=0, max_value=30, value=4)
    opponent_score = st.number_input("opponent runs", min_value=0, max_value=30, value=3)

    st.divider()
    st.subheader("process inputs")

    hard_hit_rate = st.slider("hard-hit rate", 0.0, 1.0, 0.42, 0.01)
    barrel_proxy = st.slider("barrel proxy", 0.0, 1.0, 0.10, 0.01)
    chase_rate = st.slider("opponent chase rate forced", 0.0, 1.0, 0.31, 0.01)
    whiff_rate = st.slider("swing-and-miss rate", 0.0, 1.0, 0.27, 0.01)
    re24_swing = st.slider("run expectancy swing", -3.0, 3.0, 0.8, 0.1)

    st.divider()
    st.subheader("context")

    runners_on = st.selectbox(
        "traffic",
        ["bases empty", "runner on", "runners in scoring position", "bases loaded"],
    )
    leverage = st.select_slider("leverage", options=["low", "medium", "high"], value="medium")

try:
    model = compute_live_model(
        hard_hit_rate=hard_hit_rate,
        barrel_proxy=barrel_proxy,
        chase_rate=chase_rate,
        whiff_rate=whiff_rate,
        re24_swing=re24_swing,
        runners_on=runners_on,
        leverage=leverage,
        redsox_score=redsox_score,
        opponent_score=opponent_score,
        inning=inning,
    )

    post_text = build_live_post(team_name, model["signal_tag"], model["summary_text"])
    mechanism_post = build_mechanism_post(
        team_name,
        model["contact_tilt"],
        model["discipline_tilt"],
        model["pressure_tilt"],
    )

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("score", f"{redsox_score} - {opponent_score}")
    top2.metric("inning", inning)
    top3.metric("live edge", f'{model["live_edge_score"]:.1f}')
    top4.metric("win pressure", f'{model["win_pressure"]:.1f}%')

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("one-glance game card")

        c1, c2, c3 = st.columns(3)
        c1.metric("contact quality tilt", f'{model["contact_tilt"]:.1f}')
        c2.metric("plate discipline tilt", f'{model["discipline_tilt"]:.1f}')
        c3.metric("pressure tilt", f'{model["pressure_tilt"]:.1f}')

        st.info(model["summary_text"])
        st.success(f'signal tag: {model["signal_tag"]}')

        st.markdown("### observation")
        st.write(
            f"{team_name} are in inning {inning} with a {redsox_score}-{opponent_score} game state against the {opponent_name}."
        )

        st.markdown("### mechanism")
        st.write(
            "contact quality, plate discipline, and run expectancy pressure are combined into one live edge score."
        )

        st.markdown("### implication")
        st.write(
            "if the strongest tilt keeps repeating, the scoreboard usually catches up to the process."
        )

    with right:
        st.subheader("tilt breakdown")

        st.progress(int(model["contact_tilt"]))
        st.caption(f'contact quality tilt: {model["contact_tilt"]:.1f}')

        st.progress(int(model["discipline_tilt"]))
        st.caption(f'plate discipline tilt: {model["discipline_tilt"]:.1f}')

        st.progress(int(model["pressure_tilt"]))
        st.caption(f'pressure tilt: {model["pressure_tilt"]:.1f}')

        st.progress(int(model["live_edge_score"]))
        st.caption(f'overall live edge: {model["live_edge_score"]:.1f}')

    st.divider()

    post_col1, post_col2 = st.columns(2)

    with post_col1:
        st.subheader("ready-to-post live take")
        st.code(post_text, language="text")

    with post_col2:
        st.subheader("mechanism post")
        st.code(mechanism_post, language="text")

    with st.expander("model notes"):
        st.write(
            """
- contact quality tilt = hard-hit rate + barrel proxy
- discipline tilt = chase rate forced + whiff rate
- pressure tilt = run expectancy swing + traffic + leverage
- overall live edge is weighted toward repeatable process, not just score
            """
        )

    st.caption(f"last refreshed: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")

except Exception as e:
    st.error("live game page failed to render.")
    st.exception(e)
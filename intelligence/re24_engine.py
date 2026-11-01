from __future__ import annotations

import pandas as pd

RUN_EXPECTANCY = {
    (0, 0): 0.54, (1, 0): 0.95, (2, 0): 1.19, (3, 0): 1.48,
    (0, 1): 0.29, (1, 1): 0.57, (2, 1): 0.73, (3, 1): 0.98,
    (0, 2): 0.11, (1, 2): 0.24, (2, 2): 0.35, (3, 2): 0.39,
}


def estimate_re24_delta(runners_on: int, outs: int, next_runners_on: int, next_outs: int) -> float:
    start = RUN_EXPECTANCY.get((runners_on, outs), 0.0)
    end = RUN_EXPECTANCY.get((next_runners_on, next_outs), 0.0)
    return round(end - start, 3)


def summarize_re24_proxy(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    if "events" not in df.columns:
        return 0.0

    positive_events = {"single", "double", "triple", "home_run", "walk", "hit_by_pitch"}
    negative_events = {"strikeout", "grounded_into_double_play"}

    score = 0.0
    for event in df["events"].dropna().astype(str):
        if event in positive_events:
            score += 0.35
        elif event in negative_events:
            score -= 0.25

    return round(score, 3)

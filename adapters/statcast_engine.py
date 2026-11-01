from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import pandas as pd

try:
    from pybaseball import statcast
except Exception:
    statcast = None


@dataclass(frozen=True)
class StatcastWindow:
    start_date: str
    end_date: str


def default_window(days: int = 7) -> StatcastWindow:
    end = date.today()
    start = end - timedelta(days=days)
    return StatcastWindow(start.isoformat(), end.isoformat())


def load_statcast_window(start_date: str, end_date: str, team: Optional[str] = None) -> pd.DataFrame:
    if statcast is None:
        return pd.DataFrame()

    try:
        df = statcast(start_dt=start_date, end_dt=end_date)
    except Exception:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    keep_cols = [
        "game_date", "home_team", "away_team", "inning_topbot",
        "player_name", "pitcher", "batter", "events", "description",
        "launch_speed", "launch_angle", "estimated_woba_using_speedangle",
        "woba_value", "bb_type", "zone", "plate_x", "plate_z",
    ]
    existing = [c for c in keep_cols if c in df.columns]
    df = df[existing]

    if team:
        if not {"home_team", "away_team", "inning_topbot"}.issubset(df.columns):
            return pd.DataFrame()
        team = team.upper()
        batting = ((df["away_team"] == team) & (df["inning_topbot"] == "Top")) | (
            (df["home_team"] == team) & (df["inning_topbot"] == "Bot"))
        df = df.loc[batting]

    return df.reset_index(drop=True)


def enrich_statcast_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if "launch_speed" in out.columns:
        out["is_hard_hit"] = out["launch_speed"].fillna(0).ge(95)
        out["is_barrel_proxy"] = (
            out["launch_speed"].fillna(0).ge(98) &
            out["launch_angle"].fillna(-999).between(26, 30)
        ) if "launch_angle" in out.columns else False
    else:
        out["is_hard_hit"] = False
        out["is_barrel_proxy"] = False

    if "description" in out.columns:
        whiffs = {
            "swinging_strike",
            "swinging_strike_blocked",
            "foul_tip",
        }
        swings = whiffs | {
            "foul",
            "foul_bunt",
            "hit_into_play",
            "hit_into_play_no_out",
            "hit_into_play_score",
        }
        out["is_whiff"] = out["description"].isin(whiffs)
        out["is_swing"] = out["description"].isin(swings)
    else:
        out["is_whiff"] = False
        out["is_swing"] = False

    if "zone" in out.columns and "description" in out.columns:
        chase_descriptions = {
            "swinging_strike",
            "swinging_strike_blocked",
            "foul",
            "foul_tip",
            "hit_into_play",
            "hit_into_play_no_out",
            "hit_into_play_score",
        }
        out["is_outside_zone"] = ~out["zone"].fillna(0).between(1, 9)
        out["is_chase"] = out["is_outside_zone"] & out["description"].isin(chase_descriptions)
    else:
        out["is_outside_zone"] = False
        out["is_chase"] = False

    return out


def summarize_team_process(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "barrel_rate": 0.0,
            "hard_hit_rate": 0.0,
            "whiff_rate": 0.0,
            "chase_rate": 0.0,
            "xwoba": 0.0,
            "sample_size": 0,
        }

    swings = max(int(df["is_swing"].sum()), 1) if "is_swing" in df.columns else 1
    outside_pitches = max(int(df["is_outside_zone"].sum()), 1) if "is_outside_zone" in df.columns else 1

    xwoba = 0.0
    if "estimated_woba_using_speedangle" in df.columns:
        xw = pd.to_numeric(df["estimated_woba_using_speedangle"], errors="coerce").dropna()
        xwoba = float(xw.mean()) if not xw.empty else 0.0

    return {
        "barrel_rate": float(df["is_barrel_proxy"].mean()) if "is_barrel_proxy" in df.columns else 0.0,
        "hard_hit_rate": float(df["is_hard_hit"].mean()) if "is_hard_hit" in df.columns else 0.0,
        "whiff_rate": float(df["is_whiff"].sum() / swings) if "is_whiff" in df.columns else 0.0,
        "chase_rate": float(df["is_chase"].sum() / outside_pitches) if "is_chase" in df.columns else 0.0,
        "xwoba": xwoba,
        "sample_size": int(len(df)),
    }

from __future__ import annotations
from typing import Dict, Tuple
import pandas as pd
from adapters.redsox_history_loader import load_redsox_history
from config.settings import LUCK_BAND, WS_TITLE_SEASONS


def get_history_df(csv_path: str = "storage/parquet/redsox_history.csv") -> pd.DataFrame:
    return load_redsox_history(csv_path)


def get_season_row(df: pd.DataFrame, season: int) -> pd.Series:
    season_df = df.loc[df["season"] == season]
    if season_df.empty:
        raise ValueError(f"season not found: {season}")
    return season_df.iloc[0]


def classify_process_vs_result(row: pd.Series) -> Tuple[str, str]:
    """Tag a season by how its record compares with the wins its run differential was worth.

    Both are scaled to 162 games, so shortened seasons are judged fairly:
      overperformed  - win pace at least LUCK_BAND wins above expected
      underperformed - win pace at least LUCK_BAND wins below expected
      signal         - a 95+ win pace that matches its run differential
      balanced       - everything else
    """
    luck = luck_wins_162(row)
    if luck >= LUCK_BAND:
        return ("overperformed process", f"the record outran the run differential by {luck:.1f} wins per 162")
    if luck <= -LUCK_BAND:
        return ("underperformed process", f"the run differential was worth {-luck:.1f} more wins per 162 than the record")
    if win_pace_162(row) >= 95:
        return ("signal", "elite underlying quality matched elite results")
    return ("balanced", "the result and process were relatively aligned")


RUNS_PER_WIN = 10.0  # rule of thumb: about 10 runs of differential are worth one win


def win_pace_162(row: pd.Series) -> float:
    """Actual wins scaled to a 162-game season, so shortened seasons compare fairly."""
    games = float(row["wins"]) + float(row["losses"])
    return float(row["wins"]) * 162.0 / games if games else 0.0


def expected_wins_162(row: pd.Series) -> float:
    """Wins the run differential is worth over 162 games: 81 + scaled run diff / 10.

    The dataset has run differential but not runs scored and allowed separately, so this uses
    the linear runs-per-win rule instead of the full Pythagorean formula.
    """
    games = float(row["wins"]) + float(row["losses"])
    if not games:
        return 81.0
    return 81.0 + float(row["run_diff"]) * (162.0 / games) / RUNS_PER_WIN


def luck_wins_162(row: pd.Series) -> float:
    """Win pace minus expected wins. Positive means the record outran the process."""
    return win_pace_162(row) - expected_wins_162(row)


def add_expected_wins(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with win_pace_162, expected_wins_162 and luck_wins_162 columns."""
    out = df.copy()
    out["win_pace_162"] = out.apply(win_pace_162, axis=1)
    out["expected_wins_162"] = out.apply(expected_wins_162, axis=1)
    out["luck_wins_162"] = out["win_pace_162"] - out["expected_wins_162"]
    return out


def build_plain_summary(row: pd.Series, tag: str) -> str:
    """One plain-English sentence that any fan can read."""
    wins = int(row["wins"])
    run_diff = int(row["run_diff"])
    result = str(row.get("playoff_result", "")).lower()

    if tag == "signal":
        if int(row.get("season", 0)) in WS_TITLE_SEASONS:
            return "This team was as good as it looked — the process earned the title."
        if run_diff >= 180:
            return "One of the most dominant Red Sox teams in history, top to bottom."
        if run_diff >= 120:
            return "The process and the result were telling the same story."
        return "A legitimately strong team — the record matched what was underneath it."

    if tag == "underperformed process":
        if "missed" in result:
            return "Better than the record shows — this team had no business missing the playoffs."
        return "Stronger underneath than the final result suggests — the process pointed higher."

    if tag == "overperformed process":
        return "The result outran the process — variance went their way more than the numbers said it should."

    # balanced
    if wins < 75:
        return "A genuinely tough year — the process metrics agreed with the bad record."
    if wins < 85:
        return "An average team in an average year — nothing the numbers didn't already know."
    return "What you saw is what you got — the record and the process were aligned."


def build_ian_insight(row: pd.Series) -> Dict[str, str]:
    tag, explanation = classify_process_vs_result(row)
    observation = f"{int(row['season'])} finished {int(row['wins'])}-{int(row['losses'])}."
    mechanism = str(row["mechanism_summary"]).strip()

    if tag == "signal":
        implication = "the result matched the process."
    elif tag == "underperformed process":
        implication = "the team was probably stronger than the record suggests."
    elif tag == "overperformed process":
        implication = "the result likely had more variance than fans remember."
    else:
        implication = explanation

    return {
        "observation": observation,
        "mechanism": mechanism,
        "implication": implication,
        "tag": tag,
    }


def get_top_seasons_by_wins(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return df.sort_values(["wins", "run_diff"], ascending=[False, False]).head(n)


def get_top_seasons_by_run_diff(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return df.sort_values("run_diff", ascending=False).head(n)


def build_process_vs_result_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        tag, why = classify_process_vs_result(row)
        rows.append({
            "season": int(row["season"]),
            "wins": int(row["wins"]),
            "losses": int(row["losses"]),
            "run_diff": int(row["run_diff"]),
            "playoff_result": row["playoff_result"],
            "era_label": row["era_label"],
            "tag": tag,
            "why": why,
        })
    return pd.DataFrame(rows).sort_values("season", ascending=False)


def build_era_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("era_label", dropna=False).agg(
        seasons=("season", "count"),
        avg_wins=("wins", "mean"),
        avg_run_diff=("run_diff", "mean"),
        avg_ops=("team_ops", "mean"),
        avg_era=("team_era", "mean"),
        avg_fip=("team_fip", "mean"),
    ).reset_index()
    grouped["avg_wins"] = grouped["avg_wins"].round(1)
    grouped["avg_run_diff"] = grouped["avg_run_diff"].round(1)
    grouped["avg_ops"] = grouped["avg_ops"].round(3)
    grouped["avg_era"] = grouped["avg_era"].round(2)
    grouped["avg_fip"] = grouped["avg_fip"].round(2)
    return grouped.sort_values("avg_wins", ascending=False)

from __future__ import annotations
from typing import Dict, Tuple
import pandas as pd
from adapters.redsox_history_loader import load_redsox_history


def get_history_df(csv_path: str = "storage/parquet/redsox_history.csv") -> pd.DataFrame:
    return load_redsox_history(csv_path)


def get_season_row(df: pd.DataFrame, season: int) -> pd.Series:
    season_df = df.loc[df["season"] == season]
    if season_df.empty:
        raise ValueError(f"season not found: {season}")
    return season_df.iloc[0]


def classify_process_vs_result(row: pd.Series) -> Tuple[str, str]:
    wins = float(row["wins"])
    run_diff = float(row["run_diff"])
    if run_diff >= 150 and wins >= 95:
        return ("signal", "elite underlying quality matched elite results")
    if run_diff >= 75 and wins < 90:
        return ("underperformed process", "the process looked stronger than the record")
    if run_diff < 25 and wins >= 92:
        return ("overperformed process", "the record outran the underlying profile")
    return ("balanced", "the result and process were relatively aligned")


def build_plain_summary(row: pd.Series, tag: str) -> str:
    """One plain-English sentence that any fan can read."""
    wins = int(row["wins"])
    run_diff = int(row["run_diff"])
    result = str(row.get("playoff_result", "")).lower()

    if tag == "signal":
        if "world series" in result and "lost" not in result:
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

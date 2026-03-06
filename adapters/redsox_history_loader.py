from __future__ import annotations
import os
import pandas as pd

DEFAULT_HISTORY_PATH = "storage/parquet/redsox_history.csv"

def load_redsox_history(csv_path: str = DEFAULT_HISTORY_PATH) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"history file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required_cols = [
        "season", "wins", "losses", "run_diff", "playoff_result",
        "team_ops", "team_obp", "team_slg", "team_era", "team_fip",
        "manager", "era_label", "mechanism_summary",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    # key_players is optional — fill with empty string if absent
    if "key_players" not in df.columns:
        df["key_players"] = ""
    else:
        df["key_players"] = df["key_players"].fillna("")

    numeric_cols = [
        "season", "wins", "losses", "run_diff",
        "team_ops", "team_obp", "team_slg", "team_era", "team_fip",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("season").reset_index(drop=True)

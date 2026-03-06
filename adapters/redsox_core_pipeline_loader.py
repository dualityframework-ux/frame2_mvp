from __future__ import annotations
import os
import pandas as pd

DEFAULT_CORE_PATH = "storage/parquet/redsox_core_pipeline.csv"

def load_redsox_core_pipeline(csv_path: str = DEFAULT_CORE_PATH) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"missing file: {csv_path}")
    df = pd.read_csv(csv_path)
    return df.sort_values("start_season").reset_index(drop=True)

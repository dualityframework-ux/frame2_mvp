"""
tests/test_adapters.py
Tests for adapters/redsox_history_loader.py:
load_redsox_history — happy path, error handling, data coercion.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.redsox_history_loader import load_redsox_history

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "parquet", "redsox_history.csv")

MINIMAL_COLS = [
    "season", "wins", "losses", "run_diff", "playoff_result",
    "team_ops", "team_obp", "team_slg", "team_era", "team_fip",
    "manager", "era_label", "mechanism_summary",
]


def make_minimal_csv(tmp_path, extra_cols=None, rows=3):
    """Write a minimal valid CSV to a temp file and return the path."""
    data = {
        "season": list(range(2000, 2000 + rows)),
        "wins": [85] * rows,
        "losses": [77] * rows,
        "run_diff": [50] * rows,
        "playoff_result": ["missed playoffs"] * rows,
        "team_ops": [0.750] * rows,
        "team_obp": [0.330] * rows,
        "team_slg": [0.420] * rows,
        "team_era": [4.20] * rows,
        "team_fip": [4.10] * rows,
        "manager": ["Test Manager"] * rows,
        "era_label": ["test era"] * rows,
        "mechanism_summary": ["a balanced team without a clear identifiable edge"] * rows,
    }
    if extra_cols:
        data.update(extra_cols)
    df = pd.DataFrame(data)
    path = os.path.join(tmp_path, "test.csv")
    df.to_csv(path, index=False)
    return path


# ── Happy path ────────────────────────────────────────────────────────────────

class TestLoadHappyPath:
    def test_loads_real_csv(self):
        df = load_redsox_history(CSV_PATH)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 58

    def test_sorted_by_season(self):
        df = load_redsox_history(CSV_PATH)
        assert df["season"].is_monotonic_increasing

    def test_index_is_reset(self):
        df = load_redsox_history(CSV_PATH)
        assert list(df.index) == list(range(len(df)))

    def test_numeric_columns_are_numeric(self):
        df = load_redsox_history(CSV_PATH)
        numeric = ["season", "wins", "losses", "run_diff",
                   "team_ops", "team_obp", "team_slg", "team_era", "team_fip"]
        for col in numeric:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"

    def test_key_players_column_present(self):
        df = load_redsox_history(CSV_PATH)
        assert "key_players" in df.columns

    def test_key_players_no_nulls(self):
        df = load_redsox_history(CSV_PATH)
        assert df["key_players"].isna().sum() == 0


# ── Error handling ────────────────────────────────────────────────────────────

class TestLoadErrors:
    def test_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_redsox_history("/nonexistent/path/file.csv")

    def test_raises_value_error_on_missing_column(self, tmp_path):
        # Write CSV missing 'wins'
        data = {c: [1] for c in MINIMAL_COLS if c != "wins"}
        df = pd.DataFrame(data)
        path = os.path.join(str(tmp_path), "bad.csv")
        df.to_csv(path, index=False)
        with pytest.raises(ValueError, match="missing required columns"):
            load_redsox_history(path)

    def test_error_message_names_missing_col(self, tmp_path):
        data = {c: [1] for c in MINIMAL_COLS if c not in ("wins", "losses")}
        df = pd.DataFrame(data)
        path = os.path.join(str(tmp_path), "bad2.csv")
        df.to_csv(path, index=False)
        with pytest.raises(ValueError) as exc_info:
            load_redsox_history(path)
        assert "wins" in str(exc_info.value) or "losses" in str(exc_info.value)


# ── key_players optional handling ─────────────────────────────────────────────

class TestKeyPlayersOptional:
    def test_adds_key_players_column_if_absent(self, tmp_path):
        path = make_minimal_csv(str(tmp_path))
        df = load_redsox_history(path)
        assert "key_players" in df.columns

    def test_key_players_filled_empty_string_when_absent(self, tmp_path):
        path = make_minimal_csv(str(tmp_path))
        df = load_redsox_history(path)
        assert (df["key_players"] == "").all()

    def test_key_players_null_filled_with_empty_string(self, tmp_path):
        path = make_minimal_csv(str(tmp_path), extra_cols={"key_players": [None, "Player A", None]})
        df = load_redsox_history(path)
        assert df["key_players"].isna().sum() == 0
        assert df["key_players"].iloc[0] == ""


# ── Numeric coercion ──────────────────────────────────────────────────────────

class TestNumericCoercion:
    def test_string_numbers_coerced(self, tmp_path):
        path = make_minimal_csv(str(tmp_path), extra_cols={"wins": ["85", "90", "78"]})
        df = load_redsox_history(path)
        assert pd.api.types.is_numeric_dtype(df["wins"])

    def test_non_numeric_coerced_to_nan(self, tmp_path):
        path = make_minimal_csv(str(tmp_path), extra_cols={"wins": ["85", "N/A", "78"]})
        df = load_redsox_history(path)
        assert pd.isna(df["wins"].iloc[1])


# ── redsox_core_pipeline_loader ───────────────────────────────────────────────

import os as _os
_PIPELINE_CSV = _os.path.join(_os.path.dirname(__file__), "..", "storage", "parquet", "redsox_core_pipeline.csv")

from adapters.redsox_core_pipeline_loader import load_redsox_core_pipeline

class TestCorePipelineLoader:
    def test_loads_dataframe(self):
        df = load_redsox_core_pipeline(_PIPELINE_CSV)
        assert len(df) > 0

    def test_required_columns(self):
        df = load_redsox_core_pipeline(_PIPELINE_CSV)
        for col in ["era_label", "start_season", "end_season", "core_players", "pipeline_read"]:
            assert col in df.columns, f"missing column: {col}"

    def test_sorted_by_start_season(self):
        df = load_redsox_core_pipeline(_PIPELINE_CSV)
        assert list(df["start_season"]) == sorted(df["start_season"].tolist())

    def test_missing_file_raises(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_redsox_core_pipeline(str(tmp_path / "nonexistent.csv"))

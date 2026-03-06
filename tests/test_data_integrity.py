"""
tests/test_data_integrity.py
Validates that the redsox_history.csv dataset is complete,
well-typed, and internally consistent for all 58 seasons.
"""
import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.redsox_history_loader import load_redsox_history

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "parquet", "redsox_history.csv")


@pytest.fixture(scope="module")
def df():
    return load_redsox_history(CSV_PATH)


# ── Schema ────────────────────────────────────────────────────────────────────

class TestSchema:
    REQUIRED_COLS = [
        "season", "wins", "losses", "run_diff", "playoff_result",
        "team_ops", "team_obp", "team_slg", "team_era", "team_fip",
        "manager", "era_label", "mechanism_summary", "key_players",
    ]

    def test_all_required_columns_present(self, df):
        missing = [c for c in self.REQUIRED_COLS if c not in df.columns]
        assert not missing, f"Missing columns: {missing}"

    def test_row_count_is_58(self, df):
        assert len(df) == 58, f"Expected 58 rows, got {len(df)}"

    def test_season_range(self, df):
        assert df["season"].min() == 1967
        assert df["season"].max() == 2024

    def test_no_duplicate_seasons(self, df):
        dupes = df[df["season"].duplicated()]["season"].tolist()
        assert not dupes, f"Duplicate seasons: {dupes}"

    def test_seasons_are_consecutive(self, df):
        seasons = sorted(df["season"].tolist())
        expected = list(range(1967, 2025))
        assert seasons == expected, f"Gaps in seasons: {set(expected) - set(seasons)}"


# ── Numeric ranges ─────────────────────────────────────────────────────────────

class TestNumericRanges:
    def test_wins_between_20_and_120(self, df):
        assert df["wins"].between(20, 120).all(), \
            f"Wins out of range:\n{df[~df['wins'].between(20,120)][['season','wins']]}"

    def test_losses_between_20_and_120(self, df):
        assert df["losses"].between(20, 120).all(), \
            f"Losses out of range:\n{df[~df['losses'].between(20,120)][['season','losses']]}"

    def test_wins_plus_losses_reasonable(self, df):
        """Full season: 162 games; shortened seasons (1972, 1981, 1994, 1995, 2020) have fewer."""
        total = df["wins"] + df["losses"]
        SHORT_SEASONS = {1972, 1981, 1994, 1995, 2020}
        full = df[~df["season"].isin(SHORT_SEASONS)]
        assert full.apply(lambda r: 155 <= r["wins"] + r["losses"] <= 165, axis=1).all(), \
            f"W+L out of full-season range:\n{full[~full.apply(lambda r: 155<=r['wins']+r['losses']<=165, axis=1)][['season','wins','losses']]}"

    def test_run_diff_reasonable(self, df):
        assert df["run_diff"].between(-300, 350).all(), \
            f"Run diff out of range:\n{df[~df['run_diff'].between(-300,350)][['season','run_diff']]}"

    def test_team_ops_range(self, df):
        assert df["team_ops"].between(0.60, 1.00).all(), \
            f"OPS out of range:\n{df[~df['team_ops'].between(0.60,1.00)][['season','team_ops']]}"

    def test_team_obp_range(self, df):
        assert df["team_obp"].between(0.28, 0.42).all(), \
            f"OBP out of range:\n{df[~df['team_obp'].between(0.28,0.42)][['season','team_obp']]}"

    def test_team_slg_range(self, df):
        assert df["team_slg"].between(0.30, 0.55).all(), \
            f"SLG out of range:\n{df[~df['team_slg'].between(0.30,0.55)][['season','team_slg']]}"

    def test_team_era_range(self, df):
        assert df["team_era"].between(2.50, 6.50).all(), \
            f"ERA out of range:\n{df[~df['team_era'].between(2.50,6.50)][['season','team_era']]}"

    def test_team_fip_range(self, df):
        assert df["team_fip"].between(2.40, 6.40).all(), \
            f"FIP out of range:\n{df[~df['team_fip'].between(2.40,6.40)][['season','team_fip']]}"

    def test_obp_le_ops(self, df):
        """OBP must always be <= OPS (OPS = OBP + SLG)."""
        bad = df[df["team_obp"] > df["team_ops"]]
        assert bad.empty, f"OBP > OPS in seasons: {bad['season'].tolist()}"

    def test_no_nulls_in_numeric_cols(self, df):
        numeric = ["wins", "losses", "run_diff", "team_ops", "team_obp",
                   "team_slg", "team_era", "team_fip"]
        nulls = {c: df[c].isna().sum() for c in numeric if df[c].isna().any()}
        assert not nulls, f"Null values found: {nulls}"


# ── String columns ─────────────────────────────────────────────────────────────

class TestStringColumns:
    PLAYOFF_VALID = {
        "world series", "lost alcs", "lost alds", "missed playoffs",
        "al east tie-break loss",
    }

    def test_playoff_result_values(self, df):
        vals = set(df["playoff_result"].str.lower().str.strip().unique())
        unknown = vals - self.PLAYOFF_VALID
        assert not unknown, f"Unknown playoff_result values: {unknown}"

    def test_manager_not_empty(self, df):
        empty = df[df["manager"].isna() | (df["manager"].str.strip() == "")]
        assert empty.empty, f"Empty manager in seasons: {empty['season'].tolist()}"

    def test_era_label_not_empty(self, df):
        empty = df[df["era_label"].isna() | (df["era_label"].str.strip() == "")]
        assert empty.empty, f"Empty era_label in seasons: {empty['season'].tolist()}"

    def test_mechanism_summary_min_length(self, df):
        short = df[df["mechanism_summary"].str.len() < 20]
        assert short.empty, f"Too-short mechanism_summary in seasons: {short['season'].tolist()}"

    def test_key_players_not_empty(self, df):
        empty = df[df["key_players"].str.strip() == ""]
        assert empty.empty, f"Empty key_players in seasons: {empty['season'].tolist()}"


# ── World Series seasons ───────────────────────────────────────────────────────

class TestWorldSeriesSeasons:
    # 7 WS appearances: 1967/1975/1986 (losses), 2004/2007/2013/2018 (wins)
    WS_YEARS = {1967, 1975, 1986, 2004, 2007, 2013, 2018}

    def test_ws_seasons_have_correct_result(self, df):
        ws_df = df[df["season"].isin(self.WS_YEARS)]
        for _, row in ws_df.iterrows():
            assert "world series" in row["playoff_result"].lower(), \
                f"{row['season']} expected World Series, got '{row['playoff_result']}'"

    def test_2018_best_win_total(self, df):
        row_2018 = df[df["season"] == 2018].iloc[0]
        assert row_2018["wins"] == df["wins"].max(), \
            f"2018 should have most wins; got {row_2018['wins']} vs max {df['wins'].max()}"

    def test_2018_best_run_differential(self, df):
        row_2018 = df[df["season"] == 2018].iloc[0]
        assert row_2018["run_diff"] == df["run_diff"].max(), \
            f"2018 should have best run diff; got {row_2018['run_diff']} vs max {df['run_diff'].max()}"

    def test_total_world_series_count(self, df):
        """7 WS appearances total: 4 wins (2004/2007/2013/2018) + 3 losses (1967/1975/1986)."""
        ws_count = df["playoff_result"].str.lower().str.strip().eq("world series").sum()
        assert ws_count == 7, f"Expected 7 WS appearances, found {ws_count}"

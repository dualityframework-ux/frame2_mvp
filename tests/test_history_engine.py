"""
tests/test_history_engine.py
Unit tests for intelligence/redsox_history_engine.py:
classify_process_vs_result, build_plain_summary, build_ian_insight,
get_top_seasons_*, build_process_vs_result_table, build_era_summary.
"""
import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from intelligence.redsox_history_engine import (
    classify_process_vs_result,
    build_plain_summary,
    build_ian_insight,
    get_season_row,
    get_top_seasons_by_wins,
    get_top_seasons_by_run_diff,
    build_process_vs_result_table,
    build_era_summary,
    get_history_df,
)

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "parquet", "redsox_history.csv")


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_row(**kwargs):
    defaults = dict(
        season=2000, wins=85, losses=77, run_diff=40,
        playoff_result="missed playoffs", team_ops=0.750,
        team_obp=0.330, team_slg=0.420, team_era=4.20, team_fip=4.10,
        manager="Test Manager", era_label="test era",
        mechanism_summary="a balanced team without a clear edge",
        key_players="Player A, Player B",
    )
    defaults.update(kwargs)
    return pd.Series(defaults)


@pytest.fixture(scope="module")
def full_df():
    return get_history_df(CSV_PATH)


# ── classify_process_vs_result ─────────────────────────────────────────────────

class TestClassifyProcessVsResult:
    def test_signal_high_rd_high_wins(self):
        tag, _ = classify_process_vs_result(make_row(wins=98, run_diff=181))
        assert tag == "signal"

    def test_underperformed_high_rd_low_wins(self):
        tag, _ = classify_process_vs_result(make_row(wins=85, run_diff=100))
        assert tag == "underperformed process"

    def test_overperformed_low_rd_high_wins(self):
        tag, _ = classify_process_vs_result(make_row(wins=93, run_diff=10))
        assert tag == "overperformed process"

    def test_balanced_default(self):
        tag, _ = classify_process_vs_result(make_row(wins=85, run_diff=40))
        assert tag == "balanced"

    def test_returns_explanation_string(self):
        _, explanation = classify_process_vs_result(make_row(wins=85, run_diff=40))
        assert isinstance(explanation, str) and len(explanation) > 5

    def test_boundary_signal_rd_150_wins_95(self):
        tag, _ = classify_process_vs_result(make_row(wins=95, run_diff=150))
        assert tag == "signal"

    def test_boundary_underperformed_rd_75_wins_89(self):
        tag, _ = classify_process_vs_result(make_row(wins=89, run_diff=75))
        assert tag == "underperformed process"

    def test_boundary_overperformed_rd_24_wins_92(self):
        tag, _ = classify_process_vs_result(make_row(wins=92, run_diff=24))
        assert tag == "overperformed process"

    @pytest.mark.parametrize("wins,rd,expected_tag", [
        (108, 229, "signal"),
        (97, 197, "signal"),
        (70, 20, "balanced"),
        (69, -72, "balanced"),
        (86, 93, "underperformed process"),
        (93, 15, "overperformed process"),
    ])
    def test_parametrized_known_seasons(self, wins, rd, expected_tag):
        tag, _ = classify_process_vs_result(make_row(wins=wins, run_diff=rd))
        assert tag == expected_tag


# ── build_plain_summary ────────────────────────────────────────────────────────

class TestBuildPlainSummary:
    def test_signal_ws_title(self):
        row = make_row(wins=98, run_diff=181, playoff_result="world series")
        summary = build_plain_summary(row, "signal")
        assert isinstance(summary, str) and len(summary) > 10

    def test_signal_dominant(self):
        summary = build_plain_summary(make_row(wins=108, run_diff=229), "signal")
        assert "dominant" in summary.lower() or "history" in summary.lower()

    def test_underperformed_missed(self):
        row = make_row(wins=80, run_diff=90, playoff_result="missed playoffs")
        summary = build_plain_summary(row, "underperformed process")
        assert "record" in summary.lower() or "missed" in summary.lower() or "stronger" in summary.lower()

    def test_overperformed(self):
        summary = build_plain_summary(make_row(wins=93, run_diff=10), "overperformed process")
        assert "variance" in summary.lower() or "outran" in summary.lower()

    def test_balanced_bad_year(self):
        summary = build_plain_summary(make_row(wins=69, run_diff=-72), "balanced")
        assert "tough" in summary.lower() or "bad" in summary.lower() or "agreed" in summary.lower()

    def test_balanced_average_year(self):
        summary = build_plain_summary(make_row(wins=80, run_diff=20), "balanced")
        assert isinstance(summary, str) and len(summary) > 10

    def test_balanced_good_year(self):
        summary = build_plain_summary(make_row(wins=88, run_diff=50), "balanced")
        assert "aligned" in summary.lower() or "saw" in summary.lower()

    def test_always_returns_string(self):
        for tag in ["signal", "underperformed process", "overperformed process", "balanced"]:
            result = build_plain_summary(make_row(), tag)
            assert isinstance(result, str) and len(result) > 0


# ── build_ian_insight ─────────────────────────────────────────────────────────

class TestBuildIanInsight:
    def test_returns_dict_with_required_keys(self):
        insight = build_ian_insight(make_row())
        assert set(insight.keys()) == {"observation", "mechanism", "implication", "tag"}

    def test_observation_contains_season_and_record(self):
        insight = build_ian_insight(make_row(season=2004, wins=98, losses=64))
        assert "2004" in insight["observation"]
        assert "98" in insight["observation"]
        assert "64" in insight["observation"]

    def test_mechanism_matches_row(self):
        row = make_row(mechanism_summary="elite run prevention drove everything")
        insight = build_ian_insight(row)
        assert insight["mechanism"] == "elite run prevention drove everything"

    def test_tag_is_valid(self):
        insight = build_ian_insight(make_row())
        assert insight["tag"] in {"signal", "balanced", "underperformed process", "overperformed process"}

    def test_all_values_are_strings(self):
        insight = build_ian_insight(make_row())
        for k, v in insight.items():
            assert isinstance(v, str), f"Key '{k}' is not a string: {type(v)}"


# ── get_season_row ─────────────────────────────────────────────────────────────

class TestGetSeasonRow:
    def test_returns_correct_season(self, full_df):
        row = get_season_row(full_df, 2004)
        assert row["season"] == 2004
        assert row["wins"] == 98

    def test_raises_for_missing_season(self, full_df):
        with pytest.raises(ValueError, match="season not found"):
            get_season_row(full_df, 1900)

    def test_2018_record(self, full_df):
        row = get_season_row(full_df, 2018)
        assert row["wins"] == 108


# ── get_top_seasons ────────────────────────────────────────────────────────────

class TestGetTopSeasons:
    def test_top5_wins_returns_5_rows(self, full_df):
        result = get_top_seasons_by_wins(full_df, n=5)
        assert len(result) == 5

    def test_top_wins_is_2018(self, full_df):
        result = get_top_seasons_by_wins(full_df, n=1)
        assert result.iloc[0]["season"] == 2018

    def test_top_run_diff_returns_n_rows(self, full_df):
        result = get_top_seasons_by_run_diff(full_df, n=3)
        assert len(result) == 3

    def test_top_run_diff_is_2018(self, full_df):
        result = get_top_seasons_by_run_diff(full_df, n=1)
        assert result.iloc[0]["season"] == 2018

    def test_top_wins_sorted_descending(self, full_df):
        result = get_top_seasons_by_wins(full_df, n=10)
        wins = result["wins"].tolist()
        assert wins == sorted(wins, reverse=True)

    def test_top_rd_sorted_descending(self, full_df):
        result = get_top_seasons_by_run_diff(full_df, n=10)
        rds = result["run_diff"].tolist()
        assert rds == sorted(rds, reverse=True)


# ── build_process_vs_result_table ─────────────────────────────────────────────

class TestBuildProcessVsResultTable:
    def test_returns_dataframe(self, full_df):
        result = build_process_vs_result_table(full_df)
        assert isinstance(result, pd.DataFrame)

    def test_same_row_count_as_input(self, full_df):
        result = build_process_vs_result_table(full_df)
        assert len(result) == len(full_df)

    def test_has_tag_and_why_columns(self, full_df):
        result = build_process_vs_result_table(full_df)
        assert "tag" in result.columns
        assert "why" in result.columns

    def test_all_tags_are_valid(self, full_df):
        result = build_process_vs_result_table(full_df)
        valid = {"signal", "balanced", "underperformed process", "overperformed process"}
        invalid = set(result["tag"].unique()) - valid
        assert not invalid, f"Invalid tags found: {invalid}"

    def test_sorted_descending_by_season(self, full_df):
        result = build_process_vs_result_table(full_df)
        seasons = result["season"].tolist()
        assert seasons == sorted(seasons, reverse=True)


# ── build_era_summary ─────────────────────────────────────────────────────────

class TestBuildEraSummary:
    def test_returns_dataframe(self, full_df):
        result = build_era_summary(full_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, full_df):
        result = build_era_summary(full_df)
        for col in ["era_label", "seasons", "avg_wins", "avg_run_diff", "avg_ops", "avg_era"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_avg_wins_positive(self, full_df):
        result = build_era_summary(full_df)
        assert (result["avg_wins"] > 0).all()

    def test_seasons_sum_to_58(self, full_df):
        result = build_era_summary(full_df)
        assert result["seasons"].sum() == 58


# ── Extra coverage: build_plain_summary signal branches ───────────────────────

class TestBuildPlainSummarySignalBranches:
    """Target lines 42, 48 — signal with run_diff 120-179, and underperform non-missed."""

    def test_signal_run_diff_120_to_179(self):
        row = make_row(wins=95, run_diff=150)
        summary = build_plain_summary(row, "signal")
        assert "process and the result" in summary.lower() or "telling the same story" in summary.lower()

    def test_signal_run_diff_below_120(self):
        row = make_row(wins=93, run_diff=90)
        summary = build_plain_summary(row, "signal")
        assert isinstance(summary, str) and len(summary) > 0

    def test_underperformed_non_missed(self):
        row = make_row(wins=85, run_diff=100, playoff_result="lost alds")
        summary = build_plain_summary(row, "underperformed process")
        assert "stronger underneath" in summary.lower() or "process pointed higher" in summary.lower()


class TestBuildIanInsightImplicationBranches:
    """Target lines 67, 69, 71 — implication strings for each tag in build_ian_insight."""

    def test_signal_implication(self):
        row = make_row(wins=98, run_diff=181)
        insight = build_ian_insight(row)
        assert "matched the process" in insight.get("implication", "")

    def test_underperformed_implication(self):
        row = make_row(wins=85, run_diff=100)
        insight = build_ian_insight(row)
        assert "stronger than the record" in insight.get("implication", "")

    def test_overperformed_implication(self):
        row = make_row(wins=95, run_diff=10)
        insight = build_ian_insight(row)
        assert "more variance" in insight.get("implication", "")

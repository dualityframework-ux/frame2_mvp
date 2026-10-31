"""Expected wins from run differential, scaled to 162 games."""
import pandas as pd
import pytest

from intelligence.redsox_history_engine import (
    add_expected_wins, expected_wins_162, luck_wins_162, win_pace_162,
)


def row(w, l, rd):
    return pd.Series({"wins": w, "losses": l, "run_diff": rd})


def test_even_run_diff_is_81_wins():
    assert expected_wins_162(row(81, 81, 0)) == pytest.approx(81.0)


def test_ten_runs_per_win():
    assert expected_wins_162(row(90, 72, 100)) == pytest.approx(91.0)


def test_short_season_is_scaled():
    # 1995: 86-58 over 144 games is a 96.75-win pace
    r = row(86, 58, 93)
    assert win_pace_162(r) == pytest.approx(96.75)
    assert expected_wins_162(r) == pytest.approx(81 + 93 * 162 / 144 / 10)
    assert luck_wins_162(r) > 0


def test_2020_sixty_games():
    r = row(24, 36, -59)
    assert win_pace_162(r) == pytest.approx(64.8)
    assert abs(luck_wins_162(r)) < 1


def test_columns_on_real_data():
    df = add_expected_wins(pd.read_csv("storage/parquet/redsox_history.csv"))
    assert {"win_pace_162", "expected_wins_162", "luck_wins_162"} <= set(df.columns)
    assert df["win_pace_162"].corr(df["expected_wins_162"]) > 0.85
    unluckiest = df.loc[df["luck_wins_162"].idxmin(), "season"]
    assert unluckiest == 1985

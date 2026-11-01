"""Offline coverage for the adapter that was previously outside the test suite."""
from unittest.mock import patch
import pandas as pd
from adapters import statcast_engine as engine


def test_team_filter_keeps_only_team_batting_pitches():
    raw = pd.DataFrame({
        'home_team': ['BOS', 'BOS', 'NYY', 'NYY'],
        'away_team': ['NYY', 'NYY', 'BOS', 'BOS'],
        'inning_topbot': ['Top', 'Bot', 'Top', 'Bot'], 'batter': [1, 2, 3, 4],
    })
    with patch.object(engine, 'statcast', return_value=raw):
        result = engine.load_statcast_window('2026-01-01', '2026-01-02', team='bos')
    assert result.batter.tolist() == [2, 3]
    assert raw.batter.tolist() == [1, 2, 3, 4]


def test_missing_inning_half_does_not_mix_opponent_data():
    raw = pd.DataFrame({'home_team': ['BOS'], 'away_team': ['NYY']})
    with patch.object(engine, 'statcast', return_value=raw):
        assert engine.load_statcast_window('2026-01-01', '2026-01-02', team='BOS').empty


def test_network_failure_is_empty_data():
    with patch.object(engine, 'statcast', side_effect=RuntimeError('offline')):
        assert engine.load_statcast_window('2026-01-01', '2026-01-02').empty


def test_missing_launch_angle_does_not_crash_or_mutate_input():
    raw = pd.DataFrame({'launch_speed': [100.0]})
    result = engine.enrich_statcast_metrics(raw)
    assert bool(result.is_hard_hit.iloc[0])
    assert not bool(result.is_barrel_proxy.iloc[0])
    assert raw.columns.tolist() == ['launch_speed']

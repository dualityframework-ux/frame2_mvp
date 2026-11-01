"""FIP is computed from MLB counts with the standard formula; these tests pin the formula and the data."""
import csv
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compute_fip as cf  # noqa: E402

# Red Sox and all-MLB regular-season pitching counts for 1967, as returned by the MLB Stats API.
BOS_1967 = {'homeRuns': 142, 'baseOnBalls': 477, 'hitByPitch': 47, 'strikeOuts': 1010, 'outs': 4378, 'earnedRuns': 546}
MLB_1967 = {'homeRuns': 2299, 'baseOnBalls': 9665, 'hitByPitch': 751, 'strikeOuts': 19413, 'outs': 87553, 'earnedRuns': 10723}


def team_snapshot(year, stat):
    return {'source_url': f'https://statsapi.mlb.com/api/v1/teams/111/stats?season={year}&stats=season&group=hitting%2Cpitching',
            'retrieved_at': 'test', 'data': {'stats': [{'group': {'displayName': 'pitching'}, 'splits': [{'season': str(year), 'stat': stat}]}]}}


def league_snapshot(year, team_stats, url=None):
    splits = [{'season': str(year), 'team': {'id': tid}, 'stat': st} for tid, st in team_stats]
    return {'source_url': url or cf.league_url(year), 'retrieved_at': 'test', 'data': {'stats': [{'splits': splits}]}}


def test_1967_worked_by_hand():
    # lgIP = 87553/3 = 29184.33; lgERA = 9*10723/lgIP = 3.30681; C = 3.30681 - 22309/lgIP = 2.54239
    # BOS: (13*142 + 3*(477+47) - 2*1010) / (4378/3) = 1398/1459.33 = 0.9580; FIP = 3.50
    constant, _ = cf.league_constant([MLB_1967])
    assert constant == pytest.approx(2.54239, abs=1e-5)
    assert cf.fip(BOS_1967, constant) == pytest.approx(3.50, abs=0.005)


def test_a_team_that_is_the_whole_league_has_fip_equal_to_league_era():
    constant, totals = cf.league_constant([MLB_1967])
    assert cf.fip(MLB_1967, constant) == pytest.approx(9 * totals['earnedRuns'] / (totals['outs'] / 3))


def test_innings_come_from_outs_not_the_decimal_display():
    two_thirds = dict(BOS_1967, outs=3 * 1459 + 2)          # 1459 2/3 innings, displayed "1459.2"
    assert cf._core(two_thirds) == pytest.approx(1398 / (1459 + 2 / 3))


def test_league_constant_sums_every_team():
    half = {k: v / 2 for k, v in MLB_1967.items()}
    assert cf.league_constant([half, half])[0] == pytest.approx(cf.league_constant([MLB_1967])[0])


def test_compute_season_records_sources_and_inputs():
    other = {k: v - BOS_1967[k] for k, v in MLB_1967.items()}
    row = cf.compute_season(1967, '3.26', team_snapshot(1967, BOS_1967), league_snapshot(1967, [(111, BOS_1967), (999, other)]))
    assert row['status'] == 'computed' and row['computed_fip'] == 3.50
    assert row['league_teams'] == 2 and len(row['sources']['league']['sha256']) == 64


@pytest.mark.parametrize('bad', [
    lambda: (team_snapshot(1968, BOS_1967), league_snapshot(1967, [(111, MLB_1967)])),                 # wrong season
    lambda: (team_snapshot(1967, BOS_1967), league_snapshot(1967, [(111, MLB_1967)], url='https://example.com/x')),
    lambda: (team_snapshot(1967, BOS_1967), league_snapshot(1967, [(147, MLB_1967)])),                  # Red Sox missing
    lambda: (team_snapshot(1967, {'homeRuns': 1}), league_snapshot(1967, [(111, MLB_1967)])),         # counts missing
])
def test_unusable_sources_are_unavailable_not_guessed(bad):
    team, league = bad()
    assert cf.compute_season(1967, '3.26', team, league)['status'] == 'unavailable'


def test_apply_only_changes_computed_seasons(tmp_path):
    path = tmp_path / 'h.csv'
    path.write_text('season,team_fip,manager\n1967,3.26,A\n1968,3.23,B\n')
    report = {'seasons': [{'season': 1967, 'status': 'computed', 'computed_fip': 3.5},
                          {'season': 1968, 'status': 'unavailable', 'computed_fip': None}]}
    assert cf.apply(path, report) == 1
    assert list(csv.DictReader(path.open())) == [{'season': '1967', 'team_fip': '3.50', 'manager': 'A'},
                                                 {'season': '1968', 'team_fip': '3.23', 'manager': 'B'}]


def test_dataset_matches_the_committed_fip_report():
    report = json.loads((ROOT / 'docs/fip-computed.json').read_text())
    with (ROOT / 'storage/parquet/redsox_history.csv').open(newline='', encoding='utf-8-sig') as handle:
        data = {int(r['season']): r['team_fip'] for r in csv.DictReader(handle)}
    assert report['summary']['computed'] == len(data) == 58
    for season in report['seasons']:
        assert data[season['season']] == f"{season['computed_fip']:.2f}"

"""Compute Red Sox team FIP for every season from MLB's own counts.

FIP (fielding independent pitching) uses only home runs, walks, hit batters and
strikeouts, scaled to look like ERA:

    FIP = (13*HR + 3*(BB + HBP) - 2*K) / IP + C
    C   = league ERA - (13*lgHR + 3*(lgBB + lgHBP) - 2*lgK) / lgIP

The league constant C is computed per season from every MLB team's pitching
totals. Innings come from outs / 3, so 1443.2 innings is 1443 2/3, not 1443.2.
BB includes intentional walks.

Sources: the cached team snapshot used by audit_history_sources.py
({year}-stats.json) and a league snapshot of all teams ({year}-league.json).
Network reads are opt-in with --fetch. The CSV is only changed with --apply.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_history_sources import _stats, _valid_snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LEAGUE_API = 'https://statsapi.mlb.com/api/v1/teams/stats'
TEAM_ID = 111
COUNTS = ('homeRuns', 'baseOnBalls', 'hitByPitch', 'strikeOuts', 'outs', 'earnedRuns')


def league_url(year):
    return LEAGUE_API + '?' + urlencode({'season': year, 'group': 'pitching', 'stats': 'season',
                                         'sportIds': 1, 'gameType': 'R'})


def fetch_league(year, cache):
    import requests
    response = requests.get(league_url(year), timeout=30)
    response.raise_for_status()
    snapshot = {'source_url': response.url, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'data': response.json()}
    path = Path(cache) / f'{year}-league.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2) + '\n')
    return path


def _valid_league(snapshot, year):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('data'), dict):
        return False
    url = urlsplit(snapshot.get('source_url', ''))
    q = parse_qs(url.query)
    return (url.scheme == 'https' and url.netloc == 'statsapi.mlb.com' and url.path == '/api/v1/teams/stats'
            and q.get('season') == [str(year)] and q.get('group') == ['pitching'] and q.get('stats') == ['season']
            and q.get('sportIds') == ['1'] and q.get('gameType', ['R']) == ['R'])


def _counts(stat):
    """The counts FIP needs, as numbers. Raises KeyError if any is missing."""
    return {k: float(stat[k]) for k in COUNTS}


def _core(c):
    """13*HR + 3*(BB + HBP) - 2*K, per inning."""
    return (13 * c['homeRuns'] + 3 * (c['baseOnBalls'] + c['hitByPitch']) - 2 * c['strikeOuts']) / (c['outs'] / 3)


def league_constant(team_stats):
    """C for one season, from a list of every team's pitching stat dicts."""
    total = {k: sum(_counts(s)[k] for s in team_stats) for k in COUNTS}
    league_era = 9 * total['earnedRuns'] / (total['outs'] / 3)
    return league_era - _core(total), total


def fip(team_stat, constant):
    return _core(_counts(team_stat)) + constant


def _hash(snapshot):
    return hashlib.sha256(json.dumps(snapshot.get('data', {}), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def compute_season(year, dataset_fip, team_snapshot, league_snapshot):
    row = {'season': year, 'dataset_fip': dataset_fip, 'computed_fip': None, 'status': 'unavailable'}
    if not _valid_snapshot(team_snapshot, year, 'stats') or not _valid_league(league_snapshot, year):
        return row
    team = _stats(team_snapshot, year).get('pitching')
    splits = (league_snapshot['data'].get('stats') or [{}])[0].get('splits', [])
    league = [s['stat'] for s in splits if str(s.get('season')) == str(year)]
    if not team or not league or not any(s.get('team', {}).get('id') == TEAM_ID for s in splits):
        return row
    try:
        constant, totals = league_constant(league)
        value = fip(team, constant)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return row
    row.update({
        'computed_fip': round(value, 2), 'computed_fip_unrounded': value, 'league_constant': constant,
        'team_counts': _counts(team), 'league_counts': totals, 'league_teams': len(league),
        'status': 'computed',
        'sources': {'team': {'url': team_snapshot['source_url'], 'retrieved_at': team_snapshot['retrieved_at'], 'sha256': _hash(team_snapshot)},
                    'league': {'url': league_snapshot['source_url'], 'retrieved_at': league_snapshot['retrieved_at'], 'sha256': _hash(league_snapshot)}},
    })
    return row


def compute_all(csv_path, cache):
    with Path(csv_path).open(newline='', encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    seasons = []
    for r in rows:
        year = int(r['season'])
        load = lambda name: json.loads((Path(cache) / name).read_text()) if (Path(cache) / name).exists() else None
        seasons.append(compute_season(year, r.get('team_fip'), load(f'{year}-stats.json'), load(f'{year}-league.json')))
    done = [s for s in seasons if s['status'] == 'computed']
    diffs = [abs(float(s['dataset_fip']) - s['computed_fip']) for s in done if s['dataset_fip'] not in (None, '')]
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'method': 'FIP = (13*HR + 3*(BB+HBP) - 2*K)/IP + C; C = lgERA - (13*lgHR + 3*(lgBB+lgHBP) - 2*lgK)/lgIP, '
                  'all from MLB Stats API regular-season pitching counts; IP = outs/3; BB includes intentional walks.',
        'summary': {'seasons': len(seasons), 'computed': len(done), 'unavailable': len(seasons) - len(done),
                    'previous_values_within_0.05': sum(d <= 0.05 + 1e-9 for d in diffs),
                    'largest_difference': round(max(diffs), 2) if diffs else None},
        'seasons': seasons,
    }


def apply(csv_path, report):
    """Write computed FIP into the CSV. Seasons that could not be computed are left unchanged."""
    path = Path(csv_path)
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    computed = {s['season']: s['computed_fip'] for s in report['seasons'] if s['status'] == 'computed'}
    changed = 0
    for r in rows:
        value = computed.get(int(r['season']))
        if value is not None and r['team_fip'] != f'{value:.2f}':
            r['team_fip'] = f'{value:.2f}'
            changed += 1
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--csv', type=Path, default=ROOT / 'storage/parquet/redsox_history.csv')
    parser.add_argument('--cache', type=Path, default=ROOT / 'storage/source_cache')
    parser.add_argument('--fetch', action='store_true', help='Opt in to retrieving league snapshots from MLB.')
    parser.add_argument('--apply', action='store_true', help='Write computed FIP into the CSV.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.fetch:
        with args.csv.open(newline='', encoding='utf-8-sig') as handle:
            years = [int(r['season']) for r in csv.DictReader(handle)]
        for year in years:  # sequential and small: one request per season
            fetch_league(year, args.cache)
    report = compute_all(args.csv, args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))
    if args.apply:
        print(f'{apply(args.csv, report)} team_fip values updated in {args.csv.name}')


if __name__ == '__main__':
    main()

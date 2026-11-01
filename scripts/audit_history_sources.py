"""Compare the bundled season data with MLB's public season statistics and roster.

No dataset is modified. Network reads are opt-in with --fetch; ordinary runs use
saved source snapshots. Missing source fields remain explicitly unverified.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
API = 'https://statsapi.mlb.com/api/v1/teams/111'
FIELDS = {'wins':('pitching','wins'), 'losses':('pitching','losses'),
          'team_ops':('hitting','ops'), 'team_obp':('hitting','obp'),
          'team_slg':('hitting','slg'), 'team_era':('pitching','era')}


def source_url(year, kind):
    from urllib.parse import urlencode
    parameters = {'season':year, **({'rosterType':'fullSeason'} if kind == 'roster'
                                    else {'stats':'season','group':'hitting,pitching'})}
    return API + '/' + kind + '?' + urlencode(parameters)


def fetch_source(year, kind, cache):
    import requests
    url = source_url(year, kind)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    snapshot = {'source_url':response.url, 'retrieved_at':datetime.now(timezone.utc).isoformat(), 'data':response.json()}
    path = cache / f'{year}-{kind}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2) + '\n')
    return path


def _name(value):
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r'\b(jr|sr|ii|iii|iv)\.?$', '', value.lower()).strip()
    return re.sub('[^a-z]', '', value)


def _valid_snapshot(snapshot, year, kind):
    from urllib.parse import parse_qs, urlsplit
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('data'), dict):
        return False
    url = urlsplit(snapshot.get('source_url', ''))
    query = parse_qs(url.query)
    correct_kind = (query.get('rosterType') == ['fullSeason'] if kind == 'roster'
                    else query.get('stats') == ['season'] and query.get('gameType', ['R']) == ['R'])
    return (url.scheme == 'https' and url.netloc == 'statsapi.mlb.com'
            and url.path == f'/api/v1/teams/111/{kind}'
            and query.get('season') == [str(year)] and correct_kind)


def _stats(snapshot, year):
    groups = {}
    for group in snapshot.get('data', {}).get('stats', []):
        name = group.get('group', {}).get('displayName')
        for split in group.get('splits', []):
            if str(split.get('season')) == str(year):
                groups[name] = split.get('stat', {})
    return groups


def _check(dataset, source):
    if source is None:
        return {'dataset':dataset, 'source':None, 'status':'unavailable'}
    try:
        actual, expected = float(dataset), float(source)
        matches = math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual, expected, abs_tol=1e-9, rel_tol=0)
    except (TypeError, ValueError):
        matches = False
    return {'dataset':dataset, 'source':source, 'status':'match' if matches else 'mismatch'}


def audit_row(row, stats_snapshot=None, roster_snapshot=None):
    year = int(row['season'])
    stats_snapshot = stats_snapshot if _valid_snapshot(stats_snapshot, year, 'stats') else None
    roster_snapshot = roster_snapshot if _valid_snapshot(roster_snapshot, year, 'roster') else None
    groups = _stats(stats_snapshot or {}, year)
    checks = {field:_check(row.get(field), groups.get(group, {}).get(key)) for field, (group,key) in FIELDS.items()}
    scored = groups.get('hitting', {}).get('runs')
    allowed = groups.get('pitching', {}).get('runs')
    checks['run_diff'] = _check(row.get('run_diff'), float(scored)-float(allowed) if scored is not None and allowed is not None else None)
    # MLB's season response has no FIP field; scripts/compute_fip.py computes it from MLB counts.
    checks['team_fip'] = _check(row.get('team_fip'), groups.get('pitching', {}).get('fip'))
    roster = (roster_snapshot or {}).get('data', {}).get('roster')
    if not isinstance(roster, list) or not roster:
        roster = None
    names = [_name(item.get('person', {}).get('fullName','')) for item in roster or []]
    players = [part.strip() for part in row.get('key_players','').split(',') if part.strip()]
    absent = [player for player in players if not any(name.endswith(_name(player)) for name in names)] if roster is not None else []
    return {
        'season':year,
        'sources':{kind:{'url':snapshot.get('source_url'), 'retrieved_at':snapshot.get('retrieved_at'),
                        'sha256':hashlib.sha256(json.dumps(snapshot.get('data', {}), sort_keys=True, separators=(',',':')).encode()).hexdigest() if snapshot else None}
                   for kind,snapshot in [('stats',stats_snapshot or {}),('roster',roster_snapshot or {})]},
        'numeric_checks':checks,
        'contributor_roster_check':{'status':'unavailable' if roster is None else 'needs_review' if absent else 'names_present',
                                    'names_not_found':absent,
                                    'limitation':'Surname presence checks roster membership only, not relative contribution.'},
        'narratives':'not audited: manager, era labels and causal interpretations require separate citations',
    }


def audit_history(csv_path, cache, years=None):
    with Path(csv_path).open(newline='', encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    if years is not None:
        rows = [row for row in rows if int(row['season']) in set(years)]
    results = []
    for row in rows:
        year = int(row['season'])
        snapshots = {}
        for kind in ['stats','roster']:
            path = Path(cache) / f'{year}-{kind}.json'
            if path.exists():
                snapshots[kind] = json.loads(path.read_text())
        results.append(audit_row(row, snapshots.get('stats'), snapshots.get('roster')))
    checks = [check for result in results for check in result['numeric_checks'].values()]
    return {'generated_at':datetime.now(timezone.utc).isoformat(),
            'dataset':str(Path(csv_path).relative_to(ROOT)) if Path(csv_path).is_relative_to(ROOT) else Path(csv_path).name,
            'method':'Exact numeric comparison at the precision stored in the CSV; no inferred FIP and no automatic edits.',
            'summary':{'seasons':len(results), **{status:sum(check['status']==status for check in checks) for status in ['match','mismatch','unavailable']},
                       'contributor_seasons_needing_review':sum(result['contributor_roster_check']['status']=='needs_review' for result in results)},
            'seasons':results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT/'storage/parquet/redsox_history.csv')
    parser.add_argument('--cache', type=Path, default=ROOT/'storage/source_cache')
    parser.add_argument('--years', nargs='+', type=int)
    parser.add_argument('--fetch', action='store_true', help='Opt in to retrieving public MLB sources; never edits the dataset.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.fetch:
        with args.csv.open(newline='', encoding='utf-8-sig') as handle:
            years = args.years or [int(row['season']) for row in csv.DictReader(handle)]
        tasks = [(year,kind) for year in years for kind in ['stats','roster']]
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda query:fetch_source(*query,args.cache), tasks))
    report = audit_history(args.csv, args.cache, args.years)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()

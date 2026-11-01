"""Source-audit behavior is tested offline, without treating synthetic fixtures as evidence."""
import csv
import json
from pathlib import Path

from scripts.audit_history_sources import audit_history, audit_row, source_url

ROW = {'season':'2024','wins':'81','losses':'81','run_diff':'4','team_ops':'0.742',
       'team_obp':'0.319','team_slg':'0.423','team_era':'4.04','team_fip':'3.94',
       'key_players':'Devers, Bregman'}


def snapshots(year=2024):
    stats = {'source_url':source_url(year,'stats'), 'retrieved_at':'2026-11-01T00:00:00Z', 'data':{'stats':[
        {'group':{'displayName':'hitting'},'splits':[{'season':str(year),'stat':{'runs':751,'ops':'.742','obp':'.319','slg':'.423'}}]},
        {'group':{'displayName':'pitching'},'splits':[{'season':str(year),'stat':{'runs':747,'wins':81,'losses':81,'era':'4.04'}}]},
    ]}}
    roster = {'source_url':source_url(year,'roster'), 'retrieved_at':'2026-11-01T00:00:00Z',
              'data':{'roster':[{'person':{'fullName':'Rafael Devers'}}]}}
    return stats, roster


def test_compares_values_without_inventing_a_fip_source():
    stats, roster = snapshots()
    result = audit_row(ROW, stats, roster)
    assert sum(check['status']=='match' for check in result['numeric_checks'].values()) == 7
    assert result['numeric_checks']['team_fip']['status'] == 'unavailable'
    assert result['contributor_roster_check']['names_not_found'] == ['Bregman']
    assert len(result['sources']['stats']['sha256']) == 64


def test_precision_difference_is_reported_not_silently_rounded_away():
    stats, roster = snapshots()
    result = audit_row({**ROW,'team_era':'4.03'}, stats, roster)
    assert result['numeric_checks']['team_era']['status'] == 'mismatch'


def test_missing_snapshots_do_not_produce_verified_claims():
    result = audit_row(ROW)
    assert all(check['status']=='unavailable' for check in result['numeric_checks'].values())
    assert result['contributor_roster_check']['status'] == 'unavailable'


def test_wrong_season_snapshot_is_not_compared():
    stats, roster = snapshots(2022)
    result = audit_row(ROW, stats, roster)
    assert all(check['status']=='unavailable' for check in result['numeric_checks'].values())
    assert result['contributor_roster_check']['status'] == 'unavailable'


def test_wrong_provider_is_not_treated_as_mlb_evidence():
    stats, roster = snapshots()
    stats['source_url'] = stats['source_url'].replace('statsapi.mlb.com','example.com')
    assert audit_row(ROW, stats, roster)['numeric_checks']['wins']['status'] == 'unavailable'


def test_surname_matching_handles_accents_but_does_not_claim_player_importance():
    stats, roster = snapshots()
    roster['data']['roster'] = [{'person':{'fullName':'Enrique Hernández Jr.'}}]
    result = audit_row({**ROW,'key_players':'Hernandez'}, stats, roster)
    assert result['contributor_roster_check']['status'] == 'names_present'
    assert 'not relative contribution' in result['contributor_roster_check']['limitation']


def test_offline_audit_never_modifies_the_dataset(tmp_path):
    csv_path = tmp_path / 'history.csv'
    with csv_path.open('w', newline='') as handle:
        writer=csv.DictWriter(handle, fieldnames=list(ROW));writer.writeheader();writer.writerow(ROW)
    original=csv_path.read_bytes()
    for kind, snapshot in zip(['stats','roster'], snapshots()):
        (tmp_path/f'2024-{kind}.json').write_text(json.dumps(snapshot))
    report=audit_history(csv_path,tmp_path)
    assert report['summary'] == {'seasons':1,'match':7,'mismatch':0,'unavailable':1,'contributor_seasons_needing_review':1}
    assert csv_path.read_bytes() == original


def test_empty_or_partial_roster_is_not_evidence_of_absent_players():
    stats, roster = snapshots()
    roster['data']['roster'] = []
    assert audit_row(ROW, stats, roster)['contributor_roster_check']['status'] == 'unavailable'
    roster['source_url'] = roster['source_url'].replace('fullSeason','active')
    assert audit_row(ROW, stats, roster)['contributor_roster_check']['status'] == 'unavailable'

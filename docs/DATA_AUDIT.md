# Historical data source audit

The audit command compares the CSV with MLB Stats API responses without editing it.
The separately reviewed corrections are documented below; this is not a certificate that every field is correct. The reviewed machine-readable report
is [data-source-audit.json](data-source-audit.json). It records source URLs,
retrieval times and response hashes for each season.

## Reviewed snapshot

All 58 seasons (1967–2024) were checked using team 111's regular-season hitting
and pitching totals and full-season rosters. Of 406 compared values (wins,
losses, run differential, OPS, OBP, SLG and ERA), 406 now match numerically at the CSV's
precision. The following seven ERA differences of 0.01 were resolved using the MLB response:

| Season | Previous ERA | MLB response ERA |
| --- | --- | --- |
| 1967 | 3.36 | 3.37 |
| 1971 | 3.80 | 3.81 |
| 1975 | 3.98 | 3.99 |
| 1977 | 4.11 | 4.12 |
| 1979 | 4.03 | 4.02 |
| 1982 | 4.03 | 4.04 |
| 1993 | 3.77 | 3.78 |

These are source discrepancies. Their origin could include historical corrections
or rounding; the comparison alone does not establish why they differ. The CSV now follows the selected MLB response. Every before/after value and source is preserved in [history-corrections.json](history-corrections.json). For example, the
[1967 MLB season response](https://statsapi.mlb.com/api/v1/teams/111/stats?season=1967&stats=season&group=hitting,pitching)
is recorded alongside the bundled value in the report.

The following names were removed from contributor lists after reviewing full-season rosters:

| Season | Name needing review | Source |
| --- | --- | --- |
| 1993 | Boggs | [MLB roster](https://statsapi.mlb.com/api/v1/teams/111/roster?season=1993&rosterType=fullSeason) |
| 2012 | Valentine | [MLB roster](https://statsapi.mlb.com/api/v1/teams/111/roster?season=2012&rosterType=fullSeason) |
| 2022 | Schwarber | [MLB roster](https://statsapi.mlb.com/api/v1/teams/111/roster?season=2022&rosterType=fullSeason) |
| 2024 | Bregman | [MLB roster](https://statsapi.mlb.com/api/v1/teams/111/roster?season=2024&rosterType=fullSeason) |

Roster matching uses accent-insensitive surnames. A name's presence does not prove
relative contribution, and an absent name is a review finding, not an automatic
edit. The 2012 row also lists Valentine in its manager field; manager context
should not be confused with player-roster membership.

## FIP

MLB's season responses have no FIP field, so [`scripts/compute_fip.py`](../scripts/compute_fip.py)
computes it from MLB's own counts with the standard formula:

- FIP = (13×HR + 3×(BB + HBP) − 2×K) ÷ IP + C
- C = league ERA − (13×lgHR + 3×(lgBB + lgHBP) − 2×lgK) ÷ lgIP, from every MLB team's
  regular-season pitching totals for that season

Innings come from outs ÷ 3, and walks include intentional walks. All 58 seasons were computed.
The earlier `team_fip` values had no recorded source: only 10 of 58 were within 0.05 of the
computed value, and the largest difference was 0.42. The CSV now holds the computed values.
Every input count, league constant, source URL, retrieval time and response hash is in
[fip-computed.json](fip-computed.json). Published FIP on other sites may differ slightly
in the constant or in how intentional walks are handled; these values were not compared
with them. Outputs label FIP as computed, and comparative radar charts still leave it out.

## Not audited

Managers,
postseason results, era labels, contributor importance and narrative/causal
interpretations require separate sources. The World Series title list was not
a new finding of this audit.

## Reproduce

Run from the repository root. Network retrieval is explicit:

```bash
python scripts/audit_history_sources.py --fetch --output /tmp/redsox-audit.json
```

To audit a subset or rerun from downloaded snapshots:

```bash
python scripts/audit_history_sources.py --years 2022 2024 --fetch --output /tmp/recent-audit.json
python scripts/audit_history_sources.py --output /tmp/cached-audit.json
```

To recompute FIP (needs the team snapshots above; `--fetch` adds one league request per season, `--apply` writes the CSV):

```bash
python scripts/compute_fip.py --fetch --output docs/fip-computed.json
python scripts/compute_fip.py --apply --output docs/fip-computed.json
```

Raw snapshots are cached under git-ignored `storage/source_cache/`. Without
snapshots, fields are reported unavailable, never counted as verified. Offline
unit tests use explicitly synthetic responses and do not make network calls.
The report's successful generation does not mean all comparisons passed; inspect
its match, mismatch, unavailable and contributor-review counts.

For future corrections, select and document the authoritative metric source,
review the roster findings, preserve the change provenance, and regenerate all
consuming artifacts from the same data. Do not bulk-copy an older local tree over
the maintained repository.

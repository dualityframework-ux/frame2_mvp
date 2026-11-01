# Historical data source audit

This is a read-only comparison with the MLB Stats API, not a data replacement or
a certificate that every field is correct. The reviewed machine-readable report
is [data-source-audit.json](data-source-audit.json). It records source URLs,
retrieval times and response hashes for each season.

## Reviewed snapshot

All 58 seasons (1967–2024) were checked using team 111's regular-season hitting
and pitching totals and full-season rosters. Of 406 compared values (wins,
losses, run differential, OPS, OBP, SLG and ERA), 399 match numerically at the CSV's
precision. Seven ERA values differ by 0.01:

| Season | Bundled ERA | MLB response ERA |
| --- | --- | --- |
| 1967 | 3.36 | 3.37 |
| 1971 | 3.80 | 3.81 |
| 1975 | 3.98 | 3.99 |
| 1977 | 4.11 | 4.12 |
| 1979 | 4.03 | 4.02 |
| 1982 | 4.03 | 4.04 |
| 1993 | 3.77 | 3.78 |

These are source discrepancies. Their origin could include historical corrections
or rounding; the comparison alone does not establish why they differ. The CSV
has not been rewritten. For example, the
[1967 MLB season response](https://statsapi.mlb.com/api/v1/teams/111/stats?season=1967&stats=season&group=hitting,pitching)
is recorded alongside the bundled value in the report.

Contributor names not found by the full-season roster check:

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

The fetched basic pitching responses do not supply FIP. All 58 `team_fip` values
remain unverified; no FIP estimate was invented to fill that gap. Managers,
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

Raw snapshots are cached under git-ignored `storage/source_cache/`. Without
snapshots, fields are reported unavailable, never counted as verified. Offline
unit tests use explicitly synthetic responses and do not make network calls.
The report's successful generation does not mean all comparisons passed; inspect
its match, mismatch, unavailable and contributor-review counts.

Before editing the dataset, select and document the authoritative metric source,
review the roster findings, preserve the change provenance, and regenerate all
consuming artifacts from the same data. Do not bulk-copy an older local tree over
the maintained repository.

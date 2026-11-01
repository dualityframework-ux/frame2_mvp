# Red Sox history: data, method, exports and hosting

`frame2_mvp` is the canonical development repository. This guide preserves and
updates the useful deployment and dataset documentation from
`frame2-redsox-history`. The secondary repository is being retained as a legacy
snapshot; its retirement does not require deleting its history.

## Dataset

`storage/parquet/redsox_history.csv` is a CSV despite the directory name. It
contains 58 seasons, 1967–2024, with these 14 fields:

| Field | Meaning |
| --- | --- |
| season | Season year |
| wins, losses | Regular-season record; their sum is the games used for scaling |
| run_diff | Team run differential |
| playoff_result | Postseason appearance/result label |
| team_ops, team_obp, team_slg | Offensive metrics |
| team_era, team_fip | Pitching metrics |
| manager | Primary season manager |
| era_label | Curated era label |
| mechanism_summary | Curated interpretation, not a measured causal finding |
| key_players | Curated contributor list |

The `world series` result means an **appearance**, including losses. There are
seven such rows. `config.settings.WS_TITLE_SEASONS` separately identifies the four
winning seasons in this dataset: 2004, 2007, 2013 and 2018. Exports distinguish the
two measures; the dataset does not cover all championships in franchise history.
The narrative fields do not yet have row-level source citations and need source
verification before being presented as a research dataset.

## Process tags

The engine computes `games = wins + losses`, `win_pace = wins × 162 / games`,
`expected_wins = 81 + (run_diff × 162 / games) / 10`, then the difference between
win pace and expected wins. The default band is four wins:

| Tag | Rule, evaluated in this order |
| --- | --- |
| Overperformed | Difference ≥ +4 |
| Underperformed | Difference ≤ −4 |
| Signal | Inside that band with win pace ≥ 95 |
| Balanced | Everything else |

This linear runs-per-win approximation is a descriptive heuristic. It is not the
full Pythagorean formula, a causal estimate or a calibrated prediction. Shortened
seasons are scaled before comparison. See `intelligence/redsox_history_engine.py`
and `config/settings.py` for the implementation and threshold.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHONPATH=. python -m streamlit run app/app.py
```

The history dashboard and exports are implemented. The game page is a manually
entered simulator; automatic ingestion agents are placeholders. The Statcast
adapter is experimental and its network fetch is mocked in tests.

## Exports

Run these from the repository root; replace each path with your chosen output:

```bash
python export_era_comparison_pdf.py /tmp/era-comparison.pdf
python build_timeline_slideshow.py /tmp/franchise.pptx
python generate_web_timeline.py /tmp/timeline.html
python generate_mobile_timeline.py /tmp/mobile.html
```

## Hosting configuration

The application entry point is `app/app.py`. Install `requirements.txt` from the
repository root. The existing `Procfile` starts Streamlit on the platform-provided
port. For a host requiring an explicit command, use:

```bash
PYTHONPATH=. python -m streamlit run app/app.py --server.port=$PORT --server.address=0.0.0.0
```

`packages.txt` lists system fonts. Platforms differ in how they install system
packages; check the provider configuration before deploying. No assumption about
free plans or deployment time is required. The checked-in runtime declaration
uses Python 3.11; the local review tests also run on Python 3.12.

## Consolidation provenance

`repository-comparison.json` records both baseline commit IDs and the file-tree
comparison. At those revisions, 70 shared files were identical and README.md was
the only differing shared file. The canonical repository also held seven image
files; the secondary repository had no unique source or data files. Preserve the
secondary Git history and publish the canonical fixes before its legacy notice.

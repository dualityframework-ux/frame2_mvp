# frame² — Red Sox Franchise History  ⚾  v10
[![CI](https://github.com/YOUR-USERNAME/frame2-redsox-history/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/frame2-redsox-history/actions/workflows/ci.yml)
[![Nightly Audit](https://github.com/YOUR-USERNAME/frame2-redsox-history/actions/workflows/nightly.yml/badge.svg)](https://github.com/YOUR-USERNAME/frame2-redsox-history/actions/workflows/nightly.yml)
[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org)
[![Coverage ≥70%](https://img.shields.io/badge/coverage-%E2%89%A570%25-brightgreen.svg)](https://codecov.io)
[![Tests 214 passed](https://img.shields.io/badge/tests-168%20passed-brightgreen.svg)](#)



> A self-contained analytics platform covering 58 seasons of Boston Red Sox history (1967–2024).  
> 7 macro-eras · 7 World Series appearances (4 wins) · wins, run-differential, OPS, ERA, and process tags for every season.

---

## Deploy in 2 minutes — Streamlit Community Cloud (free)

1. **Fork or push this repo to GitHub** (public or private)
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → "New app"
3. Set the fields:

   | Field | Value |
   |---|---|
   | Repository | `your-github-username/frame2-redsox-history` |
   | Branch | `main` |
   | Main file path | `app/app.py` |

4. Click **Deploy** — Streamlit Cloud auto-installs `requirements.txt` and `packages.txt`
5. Your app is live at `https://your-app-name.streamlit.app`

---

## Deploy on Railway (free tier available)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Railway reads the `Procfile` automatically:
```
web: streamlit run app/app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## Deploy on Render

1. Create a new **Web Service** at [render.com](https://render.com)
2. Connect your GitHub repo
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `streamlit run app/app.py --server.port=$PORT --server.address=0.0.0.0`

---

## Run Locally

```bash
git clone https://github.com/your-username/frame2-redsox-history.git
cd frame2-redsox-history

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app/app.py
# Opens at http://localhost:8501
```

---

## Project Structure

```
frame2-redsox-history/
│
├── app/
│   ├── app.py                              # Streamlit entry point
│   └── pages/
│       ├── 04_redsox_history_home.py       # Landing dashboard
│       ├── 05_redsox_season_explorer.py    # Season-by-season explorer
│       ├── 06_redsox_process_vs_result.py  # Process vs result analysis
│       ├── 07_redsox_era_board.py          # Era leaderboard
│       ├── 08_redsox_history_post_generator.py  # Social post generator
│       ├── 09_redsox_franchise_timeline.py # ★ Main timeline + all exports
│       ├── 10_redsox_core_pipeline_explorer.py  # Pipeline explorer
│       └── 11_redsox_era_comparison.py     # ★ Era comparison dashboard
│
├── storage/parquet/
│   ├── redsox_history.csv                  # 58 rows, 14 columns incl. key_players
│   └── redsox_core_pipeline.csv
│
├── adapters/                               # Data loaders
├── intelligence/                           # Signal/noise engine
├── content_engine/                         # Post generator
├── config/                                 # Settings, styles, utils
├── tests/
│   └── test_signal_noise.py
│
├── export_era_comparison_pdf.py            # Era comparison PDF (10 pages)
├── build_timeline_slideshow.py             # 17-slide PPTX
├── generate_web_timeline.py                # Desktop HTML timeline
├── generate_mobile_timeline.py             # Mobile-responsive HTML
│
├── .streamlit/config.toml                  # Dark Red Sox theme + server config
├── requirements.txt                        # Python dependencies
├── packages.txt                            # System packages (Streamlit Cloud)
├── Procfile                                # Railway / Render start command
└── .gitignore
```

---

## Data Schema

`storage/parquet/redsox_history.csv` — 58 rows × 14 columns

| Column | Type | Description |
|---|---|---|
| season | int | 1967–2024 |
| wins / losses | int | Regular season record |
| run_diff | int | Team run differential |
| playoff_result | str | "world series", "lost alcs", "missed playoffs", etc. |
| team_ops / obp / slg | float | Offensive triple-slash |
| team_era / fip | float | Pitching metrics |
| manager | str | Primary season manager |
| era_label | str | Short contextual label |
| mechanism_summary | str | 1-sentence process narrative |
| key_players | str | Comma-separated key contributors |

---

## Macro-Eras

| Era | Years | Avg W | Avg RD | WS | Playoff% |
|---|---|---|---|---|---|
| Yaz Era | 1967–1976 | 87.3 | +50 | 2 | 20% |
| Rice & Lynn | 1977–1986 | 85.8 | +66 | 1 | 20% |
| Boggs & Clemens | 1987–1996 | 80.0 | +18 | 0 | 30% |
| Pedro & Manny | 1997–2006 | 89.8 | +96 | 1 | 50% |
| Francona Dynasty | 2007–2013 | 90.1 | +119 | 2 | 57% |
| Betts Emergence | 2014–2019 | 87.8 | +86 | 1 | 50% |
| Rebuild & Now | 2020–2024 | 70.6 | −6 | 0 | 20% |

---

## Export Tools (CLI)

```bash
# Era comparison PDF (10 pages)
python export_era_comparison_pdf.py [output.pdf]

# Franchise timeline PPTX (17 slides)
python build_timeline_slideshow.py [output.pptx]

# Desktop interactive HTML
python generate_web_timeline.py [output.html]

# Mobile-responsive HTML
python generate_mobile_timeline.py [output.html]
```

All four are also accessible as **in-app download buttons** on pages 09 and 11 — no CLI needed.

---

## Process Tags

| Tag | Definition |
|---|---|
| **Signal** | ≥95 W + ≥80 RD — elite process matched elite result |
| **Balanced** | Wins and run-differential roughly aligned |
| **Overperformed** | Wins outran the run-differential expectation |
| **Underperformed** | Run-differential was stronger than the win total |

---

## Requirements

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
matplotlib>=3.8.0
reportlab>=4.1.0
python-pptx>=0.6.23
numpy>=1.26.0
```

System packages (auto-installed by Streamlit Cloud via `packages.txt`):
```
fonts-liberation
fontconfig
```


---

## CI/CD Pipeline

The project ships with **two GitHub Actions workflows** in `.github/workflows/`.

### `ci.yml` — Push & PR Pipeline

Triggered on every push or pull request to `main` (also `develop`), plus manual **workflow_dispatch**.

| Job | Python | What it does |
|---|---|---|
| **Tests (3×)** | 3.10 · 3.11 · 3.12 | 214 pytest tests in parallel; coverage XML; uploads to Codecov on 3.11 |
| **Lint** | 3.11 | flake8 + bugbear, max-line 110, excludes `app/pages` |
| **Syntax** | 3.11 | `py_compile` on every `.py` file in the repo |
| **Data Integrity** | 3.11 | Schema, 58-row count, season range 1967–2024, 7 WS appearances, no-null check |
| **HTML Smoke** | 3.11 | Generates both timeline HTMLs and validates 10 structural tokens each |
| **Deploy Notify** | — | Confirms Streamlit Cloud auto-deploy on green `main` push |

**Coverage gate:** ≥ 65% (currently **99.65%**).
All 5 jobs must be green before `deploy-notify` fires.

### `nightly.yml` — Daily Audit

Scheduled at **06:00 UTC** every day; also manually triggerable via `workflow_dispatch`.

- Full test suite at **≥ 70%** coverage  
- Data completeness audit: 58 rows, 7 WS appearances, no nulls in core stat columns  
- HTML size regression: both mobile + web timelines must be **> 50 KB**

### Activating on GitHub

After your first `git push`, go to your repo → **Actions** tab.
Both workflows appear and run automatically — no extra configuration needed.

**Optional secrets** (Settings → Secrets and variables → Actions → New repository secret):

| Secret name | Purpose |
|---|---|
| `CODECOV_TOKEN` | Upload coverage to [codecov.io](https://codecov.io) (free for public repos) |

### Update Badge URLs

Replace `YOUR-USERNAME` in the five badge lines at the top of this README:

```
[![CI](https://github.com/YOUR-USERNAME/frame2-redsox-history/...
                ^^^^^^^^^^^^^ ← your GitHub username
```

Badges will then show live ✅ / ❌ status on every commit.


---

## Version History

| Version | Key Addition |
|---|---|
| v1–v4 | Core app, data pipeline, home/explorer pages |
| v5 | Timeline era filters, multiselect, shaded bands |
| v6 | Era comparison page — 7 Plotly charts |
| v7 | PDF export (`export_era_comparison_pdf.py`) |
| v8 | PPTX slideshow (`build_timeline_slideshow.py`, 17 slides) |
| v9 | Desktop interactive HTML (`generate_web_timeline.py`) |
| v10 | Mobile-responsive HTML · `.streamlit/config.toml` · `packages.txt` · `Procfile` · `.gitignore` · Production-ready |

---

*frame² analytics · Red Sox Franchise History · 1967–2024*

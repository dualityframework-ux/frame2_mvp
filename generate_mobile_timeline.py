#!/usr/bin/env python3
"""Generate mobile-responsive Red Sox franchise timeline HTML."""
import json, sys

# The CSV is the only season-data source; generation fails if it is unavailable.
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters.redsox_history_loader import load_redsox_history
from intelligence.redsox_history_engine import classify_process_vs_result

SEASONS = load_redsox_history(Path(__file__).resolve().parent / "storage/parquet/redsox_history.csv").to_dict(orient="records")
MACRO_ERAS = [{'name': 'Yaz Era', 'start': 1967, 'end': 1976, 'color': '#c8a951', 'emoji': 'Y'},
 {'name': 'Rice & Lynn', 'start': 1977, 'end': 1986, 'color': '#e07b39', 'emoji': 'R'},
 {'name': 'Boggs & Clemens', 'start': 1987, 'end': 1996, 'color': '#7d8da1', 'emoji': 'B'},
 {'name': 'Pedro & Manny', 'start': 1997, 'end': 2006, 'color': '#c0392b', 'emoji': 'P'},
 {'name': 'Francona Dynasty', 'start': 2007, 'end': 2013, 'color': '#2980b9', 'emoji': 'F'},
 {'name': 'Betts Emergence', 'start': 2014, 'end': 2019, 'color': '#27ae60', 'emoji': 'B'},
 {'name': 'Rebuild & Now', 'start': 2020, 'end': 2024, 'color': '#8e44ad', 'emoji': 'N'}]
_SHORT = {"signal":"signal", "balanced":"balanced", "overperformed process":"overperformed", "underperformed process":"underperformed"}
for season in SEASONS:
    season["tag"] = _SHORT[classify_process_vs_result(season)[0]]
for era in MACRO_ERAS:
    seasons = [row for row in SEASONS if era["start"] <= row["season"] <= era["end"]]
    era["avg_w"] = round(sum(row["wins"] for row in seasons) / len(seasons), 1)
    era["avg_rd"] = round(sum(row["run_diff"] for row in seasons) / len(seasons))
    era["ws"] = sum(row["playoff_result"] == "world series" for row in seasons)
    era["pct"] = round(100 * sum(row["playoff_result"] != "missed playoffs" for row in seasons) / len(seasons))

DATA_JSON = json.dumps(SEASONS)
ERAS_JSON = json.dumps(MACRO_ERAS)

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<meta name="theme-color" content="#0d1117">
<title>Red Sox Franchise Timeline</title>
<meta name="description" content="Every Red Sox season from 1967 to 2024: wins, run differential and whether the record matched the process. Built with frame².">
<meta property="og:type" content="website">
<meta property="og:title" content="Red Sox Franchise Timeline · frame²">
<meta property="og:description" content="Every Red Sox season from 1967 to 2024: wins, run differential and whether the record matched the process.">
<meta property="og:image" content="https://dualityframework-ux.github.io/duality-framework/frame2/preview.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:url" content="https://dualityframework-ux.github.io/duality-framework/frame2/">
<meta name="twitter:card" content="summary_large_image">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
/* ── reset & tokens ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#0d2240;--red:#bd3039;--gold:#c8a951;--cream:#f5f0e8;--dark:#0d1117;
  --text:#e8eaed;--muted:#8b949e;--border:#30363d;--card:#161b22;--glass:#1c2333;
  --radius:10px;--gap:16px;
  --era1:#c8a951;--era2:#e07b39;--era3:#7d8da1;--era4:#c0392b;
  --era5:#2980b9;--era6:#27ae60;--era7:#8e44ad;
  --signal:#27ae60;--balanced:#3498db;--over:#f39c12;--under:#e74c3c;
}
html{scroll-behavior:smooth;overflow-x:hidden}
body{background:var(--dark);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;min-height:100vh;overflow-x:hidden}
img{display:block;max-width:100%}
button{cursor:pointer;border:none;font-family:inherit}
a{color:inherit;text-decoration:none}
/* ── layout ── */
.container{max-width:1200px;margin:0 auto;padding:0 var(--gap)}
/* ── NAV ── */
nav{position:sticky;top:0;z-index:200;background:rgba(13,17,23,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:52px;gap:12px}
.nav-brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:1rem;color:var(--red);white-space:nowrap}
.nav-brand span{color:var(--cream)}
.nav-links{display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;flex:1;justify-content:center}
.nav-links::-webkit-scrollbar{display:none}
.nav-link{padding:6px 10px;border-radius:6px;font-size:.78rem;color:var(--muted);white-space:nowrap;transition:color .2s,background .2s}
.nav-link:hover,.nav-link.active{color:var(--text);background:var(--glass)}
.search-wrap{position:relative;flex-shrink:0}
#playerSearch{background:var(--glass);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:6px 10px 6px 30px;font-size:.8rem;width:150px;outline:none;transition:border-color .2s,width .3s}
#playerSearch:focus{border-color:var(--red);width:200px}
.search-icon{position:absolute;left:9px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:.8rem;pointer-events:none}
/* ── HERO ── */
.hero{padding:28px var(--gap) 20px;text-align:center;background:linear-gradient(180deg,rgba(189,48,57,.08) 0%,transparent 100%)}
.hero-title{font-size:clamp(1.5rem,5vw,2.6rem);font-weight:800;letter-spacing:-.02em;line-height:1.1}
.hero-title .sox{color:var(--red)}
.hero-sub{color:var(--muted);margin:6px 0 20px;font-size:.9rem}
.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:700px;margin:0 auto}
@media(max-width:540px){.kpi-row{grid-template-columns:repeat(3,1fr)}}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:10px 6px;text-align:center}
.kpi-val{font-size:1.5rem;font-weight:800;color:var(--gold)}
.kpi-lbl{font-size:.65rem;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.04em}
/* ── ERA CHIPS ── */
.era-bar{position:sticky;top:52px;z-index:190;background:rgba(13,17,23,.97);border-bottom:1px solid var(--border);padding:8px var(--gap);overflow-x:auto;-webkit-overflow-scrolling:touch;display:flex;gap:8px;scrollbar-width:none}
.era-bar::-webkit-scrollbar{display:none}
.era-chip{flex-shrink:0;padding:5px 12px;border-radius:20px;font-size:.75rem;font-weight:600;border:2px solid transparent;background:var(--glass);color:var(--muted);transition:all .2s;white-space:nowrap}
.era-chip.active,.era-chip:hover{color:#fff;border-color:currentColor}
.era-chip[data-era="all"]{color:var(--gold)}
.era-chip[data-era="all"].active{background:rgba(200,169,81,.15)}
/* ── FILTER BAR ── */
.filter-section{padding:12px var(--gap);background:var(--card);border-bottom:1px solid var(--border)}
.filter-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.filter-group{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.filter-label{font-size:.72rem;color:var(--muted);white-space:nowrap}
select.filter-sel{background:var(--glass);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:4px 8px;font-size:.75rem;outline:none}
.range-wrap{display:flex;align-items:center;gap:6px}
input[type=range]{accent-color:var(--red);width:90px}
#minWinsVal{font-size:.75rem;color:var(--gold);min-width:24px}
.tag-filters{display:flex;gap:5px;flex-wrap:wrap}
.tag-btn{padding:4px 9px;border-radius:14px;font-size:.72rem;border:1px solid var(--border);background:var(--glass);color:var(--muted);transition:all .2s}
.tag-btn.active{color:#0d1117;font-weight:600}  /* dark text: white on these bright fills fell below 4.5:1 */
.tag-btn[data-tag="signal"].active{background:var(--signal);border-color:var(--signal)}
.tag-btn[data-tag="balanced"].active{background:var(--balanced);border-color:var(--balanced)}
.tag-btn[data-tag="overperformed"].active{background:var(--over);border-color:var(--over)}
.tag-btn[data-tag="underperformed"].active{background:var(--under);border-color:var(--under)}
.filter-meta{margin-left:auto;font-size:.72rem;color:var(--muted)}
.reset-btn{padding:4px 10px;border-radius:6px;font-size:.72rem;background:var(--glass);color:var(--muted);border:1px solid var(--border);transition:all .2s}
.reset-btn:hover{color:var(--text);border-color:var(--muted)}
/* ── SECTION HEADERS ── */
.section-head{padding:24px var(--gap) 8px;display:flex;align-items:center;gap:10px}
.section-title{font-size:1.1rem;font-weight:700}
.section-pill{font-size:.7rem;padding:2px 8px;border-radius:10px;background:var(--glass);color:var(--muted);border:1px solid var(--border)}
/* ── CHARTS ── */
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);padding:0 var(--gap) var(--gap)}
@media(max-width:700px){.charts-grid{grid-template-columns:1fr}}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:14px}
.chart-title{font-size:.8rem;font-weight:600;color:var(--muted);margin-bottom:10px;text-transform:uppercase;letter-spacing:.06em}
.chart-canvas-wrap{position:relative;height:220px}
@media(max-width:480px){.chart-canvas-wrap{height:180px}}
/* wide charts */
.chart-card.wide{grid-column:1/-1}
/* ── SEASON DETAIL CARD ── */
#seasonCard{display:none;margin:0 var(--gap) var(--gap);background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.sc-header{padding:16px 18px 12px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}
.sc-year{font-size:2.2rem;font-weight:900;color:var(--gold);line-height:1}
.sc-era{font-size:.75rem;color:var(--muted);margin-top:4px}
.sc-record{font-size:1.4rem;font-weight:700}
.sc-result{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:600;margin-top:4px}
.sc-result.ws{background:rgba(200,169,81,.2);color:var(--gold);border:1px solid var(--gold)}
.sc-result.playoff{background:rgba(41,128,185,.2);color:#5dade2;border:1px solid #5dade2}
.sc-result.miss{background:var(--glass);color:var(--muted);border:1px solid var(--border)}
.sc-body{padding:14px 18px}
.sc-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(80px,1fr));gap:8px;margin-bottom:14px}
.sc-stat{text-align:center;background:var(--glass);border-radius:8px;padding:8px 4px}
.sc-stat-val{font-size:1rem;font-weight:700;color:var(--cream)}
.sc-stat-lbl{font-size:.6rem;color:var(--muted);text-transform:uppercase;margin-top:2px}
.sc-tag{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:10px;font-size:.75rem;font-weight:600;margin-bottom:10px}
.sc-tag.signal{background:rgba(39,174,96,.15);color:var(--signal);border:1px solid var(--signal)}
.sc-tag.balanced{background:rgba(52,152,219,.15);color:var(--balanced);border:1px solid var(--balanced)}
.sc-tag.overperformed{background:rgba(243,156,18,.15);color:var(--over);border:1px solid var(--over)}
.sc-tag.underperformed{background:rgba(231,76,60,.15);color:var(--under);border:1px solid var(--under)}
.sc-quote{font-size:.82rem;color:var(--muted);line-height:1.5;font-style:italic;border-left:3px solid var(--red);padding-left:10px;margin-bottom:12px}
.sc-players{display:flex;flex-wrap:wrap;gap:5px}
.player-chip{padding:3px 9px;border-radius:10px;font-size:.72rem;background:var(--glass);border:1px solid var(--border);color:var(--text)}
.sc-nav{display:flex;gap:8px;margin-top:14px;justify-content:flex-end}
.sc-nav-btn{padding:6px 14px;border-radius:7px;font-size:.8rem;background:var(--glass);color:var(--muted);border:1px solid var(--border);transition:all .2s}
.sc-nav-btn:hover{color:var(--text);border-color:var(--muted)}
.close-btn{background:none;border:none;color:var(--muted);font-size:1.2rem;padding:4px;line-height:1;align-self:flex-start}
.close-btn:hover{color:var(--text)}
/* ── SEASON GRID ── */
.season-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;padding:0 var(--gap) var(--gap)}
@media(max-width:400px){.season-grid{grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:6px}}
.sg-tile{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 8px 8px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.sg-tile:hover{border-color:var(--red);transform:translateY(-2px)}
.sg-tile.active{border-color:var(--gold);box-shadow:0 0 0 2px rgba(200,169,81,.3)}
.sg-tile.dimmed{opacity:.25}
.sg-era-rail{height:3px;border-radius:2px;margin-bottom:7px}
.sg-season{font-size:.7rem;color:var(--muted)}
.sg-wl{font-size:1rem;font-weight:700}
.sg-rd{font-size:.7rem;color:var(--muted);margin-top:2px}
.sg-ws{position:absolute;top:5px;right:6px;font-size:.75rem;color:var(--gold)}
.sg-tag-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-top:4px}
/* ── ERA TABLE ── */
.era-table-wrap{padding:0 var(--gap) var(--gap);overflow-x:auto}
table.era-table{width:100%;border-collapse:collapse;font-size:.78rem;min-width:520px}
table.era-table th{padding:8px 10px;text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
table.era-table td{padding:8px 10px;border-bottom:1px solid rgba(48,54,61,.6);vertical-align:middle}
table.era-table tr:hover td{background:var(--glass)}
table.era-table tr.selected td{background:rgba(189,48,57,.08)}
.era-swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:middle}
.ws-badge{display:inline-flex;gap:2px}
.ws-star{color:var(--gold);font-size:.85rem}
/* ── PROCESS SECTION ── */
.scatter-info{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;padding:0 var(--gap) 8px}
@media(max-width:480px){.scatter-info{grid-template-columns:1fr}}
.scatter-legend-item{display:flex;align-items:center;gap:7px;font-size:.75rem;color:var(--muted)}
.legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
/* ── FOOTER ── */
footer{padding:28px var(--gap);text-align:center;color:var(--muted);font-size:.78rem;border-top:1px solid var(--border);margin-top:20px}
/* ── MOBILE TWEAKS ── */
@media(max-width:700px){
  .nav-inner{padding:0 12px}
  #playerSearch{width:120px}
  #playerSearch:focus{width:150px}
  .hero{padding:18px var(--gap) 14px}
  .section-head{padding:18px var(--gap) 6px}
  .charts-grid{padding:0 var(--gap) 12px}
}
@media(max-width:480px){
  .filter-row{gap:7px}
  .nav-brand .full{display:none}
  .kpi-val{font-size:1.2rem}
}
/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--dark)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--muted)}
/* ── TRANSITIONS ── */
.fade-in{animation:fadeIn .25s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>

<!-- NAV -->
<nav>
<div class="nav-inner container">
  <div class="nav-brand">
    <span style="font-size:1.3rem">&#9918;</span>
    <span class="sox">RED SOX</span><span class="full">&nbsp;TIMELINE</span>
  </div>
  <div class="nav-links">
    <a class="nav-link active" href="#charts" onclick="setActive(this)">Charts</a>
    <a class="nav-link" href="#process" onclick="setActive(this)">Process</a>
    <a class="nav-link" href="#seasons" onclick="setActive(this)">Seasons</a>
    <a class="nav-link" href="#eras" onclick="setActive(this)">Eras</a>
  </div>
  <div class="search-wrap">
    <span class="search-icon">&#128269;</span>
    <input id="playerSearch" type="search" placeholder="Search player..." autocomplete="off" aria-label="Search players">
  </div>
</div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="container">
    <div class="hero-title">Boston <span class="sox">Red Sox</span></div>
    <div class="hero-title">Franchise Timeline &nbsp;<span style="color:var(--gold)">1967&ndash;2024</span></div>
    <p class="hero-sub">ERA follows MLB source snapshots, and FIP is computed from MLB counts. Narrative interpretations remain unverified.</p>
    <div class="hero-sub">58 seasons &bull; 7 macro-eras &bull; 7 World Series trips, 4 titles</div>
    <div class="kpi-row" id="heroKpis">
      <div class="kpi"><div class="kpi-val">58</div><div class="kpi-lbl">Seasons</div></div>
      <div class="kpi"><div class="kpi-val">4</div><div class="kpi-lbl">WS Titles</div></div>
      <div class="kpi"><div class="kpi-val">108</div><div class="kpi-lbl">Best Wins</div></div>
      <div class="kpi"><div class="kpi-val">+229</div><div class="kpi-lbl">Best RD</div></div>
      <div class="kpi"><div class="kpi-val">20</div><div class="kpi-lbl">Playoffs</div></div>
    </div>
  </div>
</section>

<!-- ERA CHIPS -->
<div class="era-bar" id="eraBar">
  <button class="era-chip active" data-era="all" style="border-color:var(--gold);color:var(--gold)">All Eras</button>
</div>

<!-- FILTER BAR -->
<div class="filter-section">
<div class="container">
  <div class="filter-row">
    <div class="filter-group">
      <span class="filter-label">Result:</span>
      <select class="filter-sel" id="resultFilter">
        <option value="all">All</option>
        <option value="world series">World Series</option>
        <option value="playoff">Made Playoffs</option>
        <option value="missed playoffs">Missed Playoffs</option>
      </select>
    </div>
    <div class="filter-group">
      <span class="filter-label">Min W:</span>
      <div class="range-wrap">
        <input type="range" id="minWins" min="24" max="108" value="24">
        <span id="minWinsVal">24</span>
      </div>
    </div>
    <div class="filter-group">
      <span class="filter-label">Tag:</span>
      <div class="tag-filters">
        <button class="tag-btn active" data-tag="signal">Signal</button>
        <button class="tag-btn active" data-tag="balanced">Balanced</button>
        <button class="tag-btn active" data-tag="overperformed">Over</button>
        <button class="tag-btn active" data-tag="underperformed">Under</button>
      </div>
    </div>
    <span class="filter-meta" id="filterMeta">58 seasons</span>
    <button class="reset-btn" onclick="resetFilters()">Reset</button>
  </div>
</div>
</div>

<!-- SEASON CARD -->
<div id="seasonCard" class="fade-in"></div>

<!-- CHARTS -->
<section id="charts">
  <div class="section-head container">
    <div class="section-title">Win Totals &amp; Run Differential</div>
    <div class="section-pill" id="chartPill">58 seasons</div>
  </div>
  <div class="charts-grid container">
    <div class="chart-card">
      <div class="chart-title">Wins Per Season</div>
      <div class="chart-canvas-wrap"><canvas id="winsChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Run Differential</div>
      <div class="chart-canvas-wrap"><canvas id="rdChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">OPS vs ERA Over Time</div>
      <div class="chart-canvas-wrap"><canvas id="opsEraChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Wins Distribution by Era</div>
      <div class="chart-canvas-wrap"><canvas id="eraWinsChart"></canvas></div>
    </div>
  </div>
</section>

<!-- PROCESS SCATTER -->
<section id="process">
  <div class="section-head container">
    <div class="section-title">Process vs Result — 58 Seasons</div>
    <div class="section-pill">Wins vs Run Differential</div>
  </div>
  <div class="charts-grid container">
    <div class="chart-card wide">
      <div class="chart-title">All 58 Seasons &mdash; Wins vs Run Differential (colored by era)</div>
      <div class="chart-canvas-wrap" style="height:280px"><canvas id="scatterChart"></canvas></div>
    </div>
  </div>
  <div class="scatter-info container">
    <div class="scatter-legend-item"><div class="legend-dot" style="background:var(--signal)"></div>Signal — Elite process AND elite result</div>
    <div class="scatter-legend-item"><div class="legend-dot" style="background:var(--balanced)"></div>Balanced — Process matched result</div>
    <div class="scatter-legend-item"><div class="legend-dot" style="background:var(--over)"></div>Overperformed — Wins exceeded process</div>
    <div class="scatter-legend-item"><div class="legend-dot" style="background:var(--under)"></div>Underperformed — Process exceeded wins</div>
  </div>
</section>

<!-- SEASON GRID -->
<section id="seasons">
  <div class="section-head container">
    <div class="section-title">All Seasons</div>
    <div class="section-pill" id="gridPill">58 seasons</div>
  </div>
  <div class="season-grid container" id="seasonGrid"></div>
</section>

<!-- ERA TABLE -->
<section id="eras">
  <div class="section-head container">
    <div class="section-title">Era Comparison</div>
    <div class="section-pill">7 macro-eras</div>
  </div>
  <div class="era-table-wrap container">
    <table class="era-table" id="eraTable">
      <thead>
        <tr>
          <th>Era</th><th>Years</th><th>Avg W</th><th>Avg RD</th>
          <th>WS trips</th><th>Playoff%</th><th>Avg OPS</th><th>Avg ERA</th>
        </tr>
      </thead>
      <tbody id="eraTableBody"></tbody>
    </table>
  </div>
</section>

<footer>
  <div class="container">
    Red Sox Franchise Timeline &bull; 1967&ndash;2024 &bull; frame2 analytics &bull;
    Data: Baseball Reference &bull; Keyboard: &larr; &rarr; to navigate seasons
  </div>
</footer>

<script>
// ── DATA ──────────────────────────────────────────────────────────────────────
const SEASONS = """ + DATA_JSON + r""";
const MACRO_ERAS = """ + ERAS_JSON + r""";

// ── STATE ─────────────────────────────────────────────────────────────────────
let state = {
  era: 'all',
  result: 'all',
  minWins: 24,
  tags: new Set(['signal','balanced','overperformed','underperformed']),
  playerQuery: '',
  selectedSeason: null,
};

// ── HELPERS ───────────────────────────────────────────────────────────────────
function getEraForSeason(s){
  for(const e of MACRO_ERAS){
    if(s.season >= e.start && s.season <= e.end) return e;
  }
  return MACRO_ERAS[MACRO_ERAS.length-1];
}
function eraColor(s){ return getEraForSeason(s).color; }
function isWS(s){ return s.playoff_result.toLowerCase().includes('world series'); }
function isPlayoff(s){ return !s.playoff_result.toLowerCase().includes('missed'); }
function resultClass(s){
  if(isWS(s)) return 'ws';
  if(isPlayoff(s)) return 'playoff';
  return 'miss';
}
function tagColor(t){
  return {signal:'var(--signal)',balanced:'var(--balanced)',overperformed:'var(--over)',underperformed:'var(--under)'}[t]||'#888';
}
function filtered(){
  return SEASONS.filter(s=>{
    if(state.era!=='all'){
      const e=MACRO_ERAS.find(e=>e.name===state.era);
      if(!e||s.season<e.start||s.season>e.end) return false;
    }
    if(state.result==='world series' && !isWS(s)) return false;
    if(state.result==='playoff' && !isPlayoff(s)) return false;
    if(state.result==='missed playoffs' && isPlayoff(s)) return false;
    if(s.wins < state.minWins) return false;
    if(!state.tags.has(s.tag)) return false;
    if(state.playerQuery){
      const q=state.playerQuery.toLowerCase();
      if(!s.key_players.toLowerCase().includes(q) && !s.manager.toLowerCase().includes(q)) return false;
    }
    return true;
  });
}

// ── CHARTS ────────────────────────────────────────────────────────────────────
let charts = {};
const CHART_DEFAULTS = {
  responsive:true,maintainAspectRatio:false,
  plugins:{legend:{display:false},tooltip:{callbacks:{}}},
  scales:{x:{ticks:{color:'#8b949e',font:{size:10},maxRotation:45},grid:{color:'rgba(48,54,61,.5)'}},
          y:{ticks:{color:'#8b949e',font:{size:10}},grid:{color:'rgba(48,54,61,.4)'}}}
};

function makeTooltip(extraLines){
  return {
    backgroundColor:'rgba(13,17,23,.95)',
    borderColor:'#30363d',borderWidth:1,
    titleColor:'#c8a951',bodyColor:'#e8eaed',
    padding:10,cornerRadius:8,
    callbacks:{
      title:(ctx)=>{
        const s=SEASONS.find(s=>s.season===parseInt(ctx[0].label||ctx[0].raw?.x||ctx[0].raw));
        return s?`${s.season} — ${s.era_label}`:'';
      },
      afterBody:(ctx)=>{
        const raw=ctx[0].label||ctx[0].raw?.x||ctx[0].raw;
        const s=SEASONS.find(s=>s.season===parseInt(raw));
        if(!s) return [];
        return [
          `W-L: ${s.wins}-${s.losses}`,
          `Result: ${s.playoff_result}`,
          `RD: ${s.run_diff>0?'+':''}${s.run_diff}`,
          ...extraLines(s)
        ];
      }
    }
  };
}

function buildWinsChart(data){
  const ctx=document.getElementById('winsChart');
  if(charts.wins) charts.wins.destroy();
  charts.wins=new Chart(ctx,{
    type:'bar',
    data:{
      labels:data.map(s=>s.season),
      datasets:[{
        data:data.map(s=>s.wins),
        backgroundColor:data.map(s=>isWS(s)?'rgba(200,169,81,.85)':eraColor(s)+'88'),
        borderColor:data.map(s=>isWS(s)?'#c8a951':eraColor(s)),
        borderWidth:data.map(s=>isWS(s)?2:1),
        borderRadius:3
      }]
    },
    options:{
      ...CHART_DEFAULTS,
      onClick:(_,els)=>{if(els.length){showSeason(data[els[0].index])}},
      plugins:{
        ...CHART_DEFAULTS.plugins,
        tooltip:makeTooltip(s=>[`OPS: ${s.team_ops}`,`ERA: ${s.team_era}`]),
        annotation:{annotations:{line1:{type:'line',yMin:81,yMax:81,borderColor:'rgba(255,255,255,.2)',borderWidth:1,borderDash:[5,5]}}}
      },
      scales:{...CHART_DEFAULTS.scales,y:{...CHART_DEFAULTS.scales.y,min:20}}
    }
  });
}
function buildRdChart(data){
  const ctx=document.getElementById('rdChart');
  if(charts.rd) charts.rd.destroy();
  charts.rd=new Chart(ctx,{
    type:'bar',
    data:{
      labels:data.map(s=>s.season),
      datasets:[{
        data:data.map(s=>s.run_diff),
        backgroundColor:data.map(s=>s.run_diff>=0?'rgba(39,174,96,.6)':'rgba(231,76,60,.6)'),
        borderColor:data.map(s=>s.run_diff>=0?'#27ae60':'#e74c3c'),
        borderWidth:1,borderRadius:3
      }]
    },
    options:{
      ...CHART_DEFAULTS,
      onClick:(_,els)=>{if(els.length){showSeason(data[els[0].index])}},
      plugins:{...CHART_DEFAULTS.plugins,tooltip:makeTooltip(s=>[`Wins: ${s.wins}`,`Result: ${s.playoff_result}`])}
    }
  });
}
function buildOpsEraChart(data){
  const ctx=document.getElementById('opsEraChart');
  if(charts.opsEra) charts.opsEra.destroy();
  charts.opsEra=new Chart(ctx,{
    type:'line',
    data:{
      labels:data.map(s=>s.season),
      datasets:[
        {label:'OPS',data:data.map(s=>s.team_ops),borderColor:'#e07b39',backgroundColor:'rgba(224,123,57,.1)',fill:true,tension:.35,pointRadius:2,borderWidth:2},
        {label:'ERA/10',data:data.map(s=>+(s.team_era/10).toFixed(3)),borderColor:'#c0392b',backgroundColor:'rgba(192,57,43,.1)',fill:false,tension:.35,pointRadius:2,borderWidth:2,borderDash:[4,3]}
      ]
    },
    options:{
      ...CHART_DEFAULTS,
      plugins:{legend:{display:true,labels:{color:'#8b949e',font:{size:10},boxWidth:14}},tooltip:makeTooltip(s=>[`OBP: ${s.team_obp}`,`SLG: ${s.team_slg}`])},
      scales:{...CHART_DEFAULTS.scales,y:{...CHART_DEFAULTS.scales.y}}
    }
  });
}
function buildEraWinsChart(){
  const ctx=document.getElementById('eraWinsChart');
  if(charts.eraW) charts.eraW.destroy();
  const avgs=MACRO_ERAS.map(e=>{
    const ss=SEASONS.filter(s=>s.season>=e.start&&s.season<=e.end);
    return ss.length?+(ss.reduce((a,s)=>a+s.wins,0)/ss.length).toFixed(1):0;
  });
  charts.eraW=new Chart(ctx,{
    type:'bar',
    data:{
      labels:MACRO_ERAS.map(e=>e.name),
      datasets:[{
        data:avgs,
        backgroundColor:MACRO_ERAS.map(e=>e.color+'99'),
        borderColor:MACRO_ERAS.map(e=>e.color),
        borderWidth:2,borderRadius:5
      }]
    },
    options:{
      ...CHART_DEFAULTS,
      plugins:{...CHART_DEFAULTS.plugins,tooltip:{callbacks:{title:ctx=>[ctx[0].label],label:ctx=>`Avg Wins: ${ctx.raw}`}}},
      scales:{x:{ticks:{color:'#8b949e',font:{size:9},maxRotation:35},grid:{color:'rgba(48,54,61,.4)'}},y:{...CHART_DEFAULTS.scales.y,min:60}}
    }
  });
}
function buildScatterChart(data){
  const ctx=document.getElementById('scatterChart');
  if(charts.scatter) charts.scatter.destroy();
  const datasets=MACRO_ERAS.map(e=>({
    label:e.name,
    data:data.filter(s=>s.season>=e.start&&s.season<=e.end).map(s=>({x:s.run_diff,y:s.wins,season:s.season,ws:isWS(s)})),
    backgroundColor:e.color+'bb',
    borderColor:e.color,
    borderWidth:1,
    pointRadius:ctx=>ctx.raw?.ws?8:5,
    pointStyle:ctx=>ctx.raw?.ws?'star':'circle'
  }));
  charts.scatter=new Chart(ctx,{
    type:'scatter',
    data:{datasets},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:true,labels:{color:'#8b949e',font:{size:10},boxWidth:10,padding:8}},
        tooltip:{
          backgroundColor:'rgba(13,17,23,.95)',borderColor:'#30363d',borderWidth:1,
          titleColor:'#c8a951',bodyColor:'#e8eaed',padding:10,cornerRadius:8,
          callbacks:{
            title:ctx=>{const s=SEASONS.find(s=>s.run_diff===ctx[0].raw.x&&s.wins===ctx[0].raw.y);return s?`${s.season} — ${s.era_label}`:''},
            label:ctx=>{const s=SEASONS.find(s=>s.run_diff===ctx.raw.x&&s.wins===ctx.raw.y);return s?`W:${s.wins} RD:${s.run_diff>0?'+':''}${s.run_diff} ${s.playoff_result}`:``}
          }
        }
      },
      scales:{
        x:{title:{display:true,text:'Run Differential',color:'#8b949e',font:{size:10}},ticks:{color:'#8b949e',font:{size:9}},grid:{color:'rgba(48,54,61,.4)'}},
        y:{title:{display:true,text:'Wins',color:'#8b949e',font:{size:10}},ticks:{color:'#8b949e',font:{size:9}},grid:{color:'rgba(48,54,61,.4)'}}
      },
      onClick:(_,els)=>{
        if(els.length){
          const pt=datasets[els[0].datasetIndex].data[els[0].index];
          const s=SEASONS.find(s=>s.run_diff===pt.x&&s.wins===pt.y);
          if(s) showSeason(s);
        }
      }
    }
  });
}

// ── SEASON CARD ───────────────────────────────────────────────────────────────
function showSeason(s){
  state.selectedSeason=s.season;
  const card=document.getElementById('seasonCard');
  const rc=resultClass(s);
  const rcLabel=isWS(s)?'World Series':isPlayoff(s)?s.playoff_result:'Missed Playoffs';
  const wsIcon=isWS(s)?'<span style="color:var(--gold)">&#9733;</span> ':'';
  const players=s.key_players.split(',').map(p=>`<span class="player-chip">${p.trim()}</span>`).join('');
  const rdFmt=(s.run_diff>0?'+':'')+s.run_diff;
  card.innerHTML=`
  <div class="sc-header">
    <div>
      <div class="sc-year">${wsIcon}${s.season}</div>
      <div class="sc-era">${s.era_label}</div>
    </div>
    <div style="text-align:right">
      <div class="sc-record">${s.wins}&#8209;${s.losses}</div>
      <div class="sc-result ${rc}">${rcLabel}</div>
    </div>
    <button class="close-btn" onclick="closeCard()" aria-label="Close">&#215;</button>
  </div>
  <div class="sc-body">
    <div class="sc-stats">
      <div class="sc-stat"><div class="sc-stat-val">${rdFmt}</div><div class="sc-stat-lbl">Run Diff</div></div>
      <div class="sc-stat"><div class="sc-stat-val">${s.team_ops}</div><div class="sc-stat-lbl">OPS</div></div>
      <div class="sc-stat"><div class="sc-stat-val">${s.team_obp}</div><div class="sc-stat-lbl">OBP</div></div>
      <div class="sc-stat"><div class="sc-stat-val">${s.team_slg}</div><div class="sc-stat-lbl">SLG</div></div>
      <div class="sc-stat"><div class="sc-stat-val">${s.team_era}</div><div class="sc-stat-lbl">ERA</div></div>
      <div class="sc-stat"><div class="sc-stat-val">${s.team_fip}</div><div class="sc-stat-lbl">FIP (computed)</div></div>
    </div>
    <div class="sc-tag ${s.tag}">${s.tag.charAt(0).toUpperCase()+s.tag.slice(1)}</div>
    <div class="sc-quote">${s.mechanism_summary}</div>
    <div style="font-size:.7rem;color:var(--muted);margin-bottom:5px">Manager: ${s.manager}</div>
    <div class="sc-players">${players}</div>
    <div class="sc-nav">
      <button class="sc-nav-btn" onclick="navSeason(-1)">&#8592; Prev</button>
      <button class="sc-nav-btn" onclick="navSeason(1)">Next &#8594;</button>
    </div>
  </div>`;
  card.style.display='block';
  card.classList.remove('fade-in');
  void card.offsetWidth;
  card.classList.add('fade-in');
  card.scrollIntoView({behavior:'smooth',block:'nearest'});
  // highlight grid tile
  document.querySelectorAll('.sg-tile').forEach(t=>{
    t.classList.toggle('active', parseInt(t.dataset.season)===s.season);
  });
}
function closeCard(){
  document.getElementById('seasonCard').style.display='none';
  state.selectedSeason=null;
  document.querySelectorAll('.sg-tile').forEach(t=>t.classList.remove('active'));
}
function navSeason(dir){
  if(!state.selectedSeason) return;
  const vis=filtered();
  const idx=vis.findIndex(s=>s.season===state.selectedSeason);
  if(idx===-1) return;
  const nxt=vis[idx+dir];
  if(nxt) showSeason(nxt);
}

// ── SEASON GRID ───────────────────────────────────────────────────────────────
function buildGrid(){
  const vis=filtered();
  const visSet=new Set(vis.map(s=>s.season));
  const grid=document.getElementById('seasonGrid');
  grid.innerHTML='';
  SEASONS.forEach(s=>{
    const e=getEraForSeason(s);
    const dim=!visSet.has(s.season);
    const ws=isWS(s);
    const tile=document.createElement('div');
    tile.className='sg-tile'+(dim?' dimmed':'');
    tile.dataset.season=s.season;
    tile.innerHTML=`
      <div class="sg-era-rail" style="background:${e.color}"></div>
      <div class="sg-season">${s.season}${ws?'<span class="sg-ws">&#9733;</span>':''}</div>
      <div class="sg-wl">${s.wins}-${s.losses}</div>
      <div class="sg-rd" style="color:${s.run_diff>=0?'#27ae60':'#e74c3c'}">${s.run_diff>0?'+':''}${s.run_diff}</div>
      <div class="sg-tag-dot" style="background:${tagColor(s.tag)}"></div>`;
    if(!dim) tile.onclick=()=>showSeason(s);
    grid.appendChild(tile);
  });
  document.getElementById('gridPill').textContent=`${vis.length} of 58`;
}

// ── ERA TABLE ─────────────────────────────────────────────────────────────────
function buildEraTable(){
  const tbody=document.getElementById('eraTableBody');
  tbody.innerHTML='';
  MACRO_ERAS.forEach(e=>{
    const ss=SEASONS.filter(s=>s.season>=e.start&&s.season<=e.end);
    if(!ss.length) return;
    const avgOps=(ss.reduce((a,s)=>a+s.team_ops,0)/ss.length).toFixed(3);
    const avgEra=(ss.reduce((a,s)=>a+s.team_era,0)/ss.length).toFixed(2);
    const stars='&#9733;'.repeat(e.ws);
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td><span class="era-swatch" style="background:${e.color}"></span>${e.name}</td>
      <td>${e.start}&ndash;${e.end}</td>
      <td><strong>${e.avg_w}</strong></td>
      <td style="color:${e.avg_rd>=0?'#27ae60':'#e74c3c'}">${e.avg_rd>=0?'+':''}${e.avg_rd}</td>
      <td><span class="ws-badge" style="color:var(--gold)">${stars||'&mdash;'}</span></td>
      <td>${e.pct}%</td>
      <td>${avgOps}</td>
      <td>${avgEra}</td>`;
    tr.onclick=()=>{
      document.querySelectorAll('#eraTableBody tr').forEach(r=>r.classList.remove('selected'));
      tr.classList.add('selected');
      setEra(e.name);
    };
    tbody.appendChild(tr);
  });
}

// ── ERA BAR ───────────────────────────────────────────────────────────────────
// Era colors are tuned for chart bars; mixed toward white they stay readable as text on the dark background.
function chipText(hex, amt=0.45){
  const n=parseInt(hex.slice(1),16), mix=c=>Math.round(c+(255-c)*amt);
  return `rgb(${mix(n>>16&255)},${mix(n>>8&255)},${mix(n&255)})`;
}
function buildEraBar(){
  const bar=document.getElementById('eraBar');
  MACRO_ERAS.forEach(e=>{
    const btn=document.createElement('button');
    btn.className='era-chip';
    btn.dataset.era=e.name;
    btn.textContent=e.name;
    btn.style.cssText=`border-color:${e.color};color:${chipText(e.color)}`;
    btn.onclick=()=>setEra(e.name);
    bar.appendChild(btn);
  });
}
function setEra(name){
  state.era=name;
  document.querySelectorAll('.era-chip').forEach(c=>{
    c.classList.toggle('active', c.dataset.era===name||(name==='all'&&c.dataset.era==='all'));
    if(c.classList.contains('active')){
      const e=MACRO_ERAS.find(e=>e.name===name);
      c.style.background=e?`${e.color}22`:'rgba(200,169,81,.15)';
    } else {
      c.style.background='var(--glass)';
    }
  });
  applyFilters();
}

// ── FILTER LOGIC ──────────────────────────────────────────────────────────────
function applyFilters(){
  const vis=filtered();
  document.getElementById('filterMeta').textContent=`${vis.length} season${vis.length!==1?'s':''}`;
  document.getElementById('chartPill').textContent=`${vis.length} seasons`;
  buildWinsChart(vis);
  buildRdChart(vis);
  buildOpsEraChart(vis);
  buildScatterChart(vis);
  buildGrid();
  if(state.selectedSeason){
    const s=vis.find(s=>s.season===state.selectedSeason);
    if(!s) closeCard();
    else showSeason(s);
  }
}
function resetFilters(){
  state={...state,era:'all',result:'all',minWins:24,tags:new Set(['signal','balanced','overperformed','underperformed']),playerQuery:''};
  document.getElementById('resultFilter').value='all';
  document.getElementById('minWins').value=24;
  document.getElementById('minWinsVal').textContent='24';
  document.querySelectorAll('.tag-btn').forEach(b=>b.classList.add('active'));
  document.getElementById('playerSearch').value='';
  document.querySelectorAll('.era-chip').forEach(c=>{c.classList.remove('active');c.style.background='var(--glass)'});
  document.querySelector('.era-chip[data-era="all"]').classList.add('active');
  document.querySelector('.era-chip[data-era="all"]').style.background='rgba(200,169,81,.15)';
  applyFilters();
}

// ── EVENT WIRING ──────────────────────────────────────────────────────────────
document.getElementById('resultFilter').addEventListener('change',e=>{state.result=e.target.value;applyFilters()});
document.getElementById('minWins').addEventListener('input',e=>{
  state.minWins=+e.target.value;
  document.getElementById('minWinsVal').textContent=e.target.value;
  applyFilters();
});
document.querySelectorAll('.tag-btn').forEach(b=>{
  b.addEventListener('click',()=>{
    const t=b.dataset.tag;
    if(state.tags.has(t)){state.tags.delete(t);b.classList.remove('active');}
    else{state.tags.add(t);b.classList.add('active');}
    applyFilters();
  });
});
document.getElementById('playerSearch').addEventListener('input',e=>{
  state.playerQuery=e.target.value.trim();
  applyFilters();
});
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft') navSeason(-1);
  if(e.key==='ArrowRight') navSeason(1);
  if(e.key==='Escape') closeCard();
});

// ── NAV ACTIVE ────────────────────────────────────────────────────────────────
function setActive(el){
  document.querySelectorAll('.nav-link').forEach(l=>l.classList.remove('active'));
  el.classList.add('active');
}
// ── INIT ──────────────────────────────────────────────────────────────────────
function init(){
  buildEraBar();
  buildEraTable();
  buildEraWinsChart();
  applyFilters();
}
init();
</script>
<div style="text-align:center;padding:28px 16px 40px;font:13px/1.5 system-ui,sans-serif;color:#8a94a6">Generated by <a href="https://github.com/dualityframework-ux/frame2_mvp" style="color:#e4b84d">frame²</a> · a project by <a href="../" style="color:#e4b84d">Ian Kachadorian · Duality</a> · <a href="case-study.html" style="color:#e4b84d">Read the case study</a></div>
</body>
</html>"""

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else 'redsox_mobile_timeline.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(HTML)
    print(f"Written: {len(HTML):,} bytes to {out}")

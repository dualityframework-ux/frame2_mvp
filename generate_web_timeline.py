#!/usr/bin/env python3
"""
generate_web_timeline.py
Generates a fully self-contained interactive HTML file for the Red Sox Franchise Timeline.
No server required — pure HTML + CSS + vanilla JS + Chart.js (CDN).
Usage: python generate_web_timeline.py [output_path.html]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from adapters.redsox_history_loader import load_redsox_history
from intelligence.redsox_history_engine import classify_process_vs_result


def build_html(output_path):
    df = load_redsox_history()
    df["season"] = df["season"].astype(int)
    df["tag"] = df.apply(classify_process_vs_result, axis=1)
    df["tag_label"] = df["tag"].apply(lambda t: t[0] if isinstance(t, tuple) else str(t))
    cols = ["season", "wins", "losses", "run_diff", "playoff_result",
            "team_ops", "team_obp", "team_slg", "team_era", "team_fip",
            "manager", "era_label", "mechanism_summary", "key_players", "tag_label"]
    seasons_json = json.dumps(df[cols].to_dict(orient="records"), ensure_ascii=True)

    # CSS ─────────────────────────────────────────────────────────────────
    css = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --red:#c8102e;--navy:#0d1b2a;--gold:#e4b84d;--white:#ffffff;
  --lgray:#f5f6f8;--mgray:#cccccc;--dgray:#555;--green:#2da870;
  --font:'Inter',system-ui,sans-serif;
}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--lgray);color:var(--navy);overflow-x:hidden}
/* NAV */
#topnav{
  position:sticky;top:0;z-index:100;
  background:var(--navy);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 1.4rem;height:52px;
  box-shadow:0 2px 12px rgba(0,0,0,.4);
}
#topnav .brand span{color:var(--gold);font-weight:800;font-size:1rem;letter-spacing:.03em}
#topnav .brand sub{color:var(--mgray);font-size:.72rem;margin-left:.3rem}
#topnav nav{display:flex;gap:.2rem}
#topnav nav a{
  color:var(--mgray);text-decoration:none;font-size:.79rem;font-weight:500;
  padding:.35rem .65rem;border-radius:4px;transition:all .15s;
}
#topnav nav a:hover,#topnav nav a.active{color:var(--white);background:rgba(255,255,255,.12)}
#search-nav input{
  background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
  color:var(--white);border-radius:6px;padding:.3rem .7rem;font-size:.8rem;
  outline:none;width:155px;transition:all .2s;
}
#search-nav input::placeholder{color:rgba(255,255,255,.38)}
#search-nav input:focus{background:rgba(255,255,255,.18);width:205px;border-color:var(--gold)}
/* HERO */
#hero{
  background:linear-gradient(135deg,#0d1b2a 0%,#182d42 60%,#0d1b2a 100%);
  padding:2.8rem 2rem 2.2rem;text-align:center;position:relative;overflow:hidden;
}
#hero::before{
  content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(
    45deg,transparent,transparent 40px,rgba(200,16,46,.04) 40px,rgba(200,16,46,.04) 41px
  );
}
#hero h1{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:900;color:var(--white);letter-spacing:.04em;position:relative;z-index:1}
#hero h1 em{color:var(--gold);font-style:normal}
#hero p{color:rgba(255,255,255,.55);font-size:.9rem;margin:.5rem 0 1.4rem;position:relative;z-index:1}
.hero-kpis{display:flex;justify-content:center;gap:.85rem;flex-wrap:wrap;position:relative;z-index:1}
.hero-kpi{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.65rem 1.1rem;min-width:90px}
.hero-kpi .val{font-size:1.5rem;font-weight:800;color:var(--gold)}
.hero-kpi .lbl{font-size:.68rem;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.06em}
/* ERA CHIPS BAR */
#era-nav{
  background:var(--navy);border-bottom:2px solid var(--red);
  padding:.45rem 1.4rem;display:flex;gap:.35rem;flex-wrap:wrap;align-items:center;
  position:sticky;top:52px;z-index:99;
}
#era-nav .lbl{color:var(--mgray);font-size:.73rem;margin-right:.1rem}
.era-btn{
  border:none;border-radius:20px;padding:.26rem .7rem;cursor:pointer;
  font-size:.76rem;font-weight:600;transition:all .14s;opacity:.6;
}
.era-btn.active{opacity:1;transform:scale(1.04)}
.era-btn:hover{opacity:1}
/* FILTER BAR */
#filter-bar{
  background:var(--white);border-bottom:1px solid #e5e7eb;
  padding:.55rem 1.4rem;display:flex;gap:.85rem;align-items:center;flex-wrap:wrap;
  font-size:.79rem;
}
#filter-bar label{color:var(--dgray);font-weight:500}
#filter-bar select{
  border:1px solid #d1d5db;border-radius:6px;padding:.22rem .45rem;
  font-size:.79rem;background:var(--white);cursor:pointer;
}
#filter-bar input[type=range]{width:90px;cursor:pointer}
.filter-chips{display:flex;gap:.35rem;flex-wrap:wrap;margin-left:auto}
.chip{padding:.2rem .52rem;border-radius:12px;font-size:.71rem;font-weight:600;cursor:pointer;border:none;transition:all .12s}
.chip-active{background:var(--red);color:var(--white)}
.chip-balanced-active{background:#3b82f6;color:#fff}
.chip-over-active{background:#e4b84d;color:#0d1b2a}
.chip-under-active{background:#8b5cf6;color:#fff}
.chip-clear{background:var(--lgray);color:var(--dgray)}
#filter-count{font-size:.73rem;color:var(--dgray);background:var(--lgray);border-radius:12px;padding:.18rem .55rem}
/* MAIN */
#main{max-width:1400px;margin:0 auto;padding:1.25rem 1.5rem}
.section-title{font-size:.92rem;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:.08em;border-left:4px solid var(--red);padding-left:.65rem;margin-bottom:.9rem}
/* CHART CARD */
.chart-card{background:var(--white);border-radius:12px;padding:1.15rem 1.4rem;box-shadow:0 1px 4px rgba(0,0,0,.07);margin-bottom:1.15rem}
.dual-charts{display:grid;grid-template-columns:1fr 1fr;gap:1.15rem;margin-bottom:1.15rem}
@media(max-width:700px){.dual-charts{grid-template-columns:1fr}}
/* SEASON CARD */
#season-card{background:var(--white);border-radius:14px;box-shadow:0 2px 16px rgba(0,0,0,.09);margin-bottom:1.15rem;overflow:hidden;transition:all .25s;border:2px solid transparent}
#season-card.ws{border-color:var(--gold)}
.card-header{background:var(--navy);padding:1rem 1.4rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.55rem}
.year-badge{font-size:2.2rem;font-weight:900;color:var(--gold);line-height:1}
.record-badge{font-size:1.4rem;font-weight:700;color:var(--white)}
.result-pill{padding:.3rem .85rem;border-radius:20px;font-size:.79rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em}
.pill-ws{background:var(--gold);color:var(--navy)}
.pill-alcs{background:#ef4444;color:#fff}
.pill-alds{background:#3b82f6;color:#fff}
.pill-tbl{background:#8b5cf6;color:#fff}
.pill-miss{background:#6b7280;color:#fff}
.card-body{padding:1.15rem 1.4rem;display:grid;grid-template-columns:1fr 1fr;gap:1.4rem}
@media(max-width:580px){.card-body{grid-template-columns:1fr}}
.meta-section h3{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;color:var(--mgray);margin-bottom:.55rem}
.meta-row{display:flex;justify-content:space-between;align-items:center;padding:.2rem 0;border-bottom:1px solid #f3f4f6}
.meta-row:last-child{border-bottom:none}
.meta-lbl{font-size:.8rem;color:var(--dgray)}
.meta-val{font-size:.83rem;font-weight:600;color:var(--navy)}
.meta-val.positive{color:var(--green)}
.meta-val.negative{color:var(--red)}
.tag-badge{display:inline-block;border-radius:20px;padding:.25rem .75rem;font-size:.76rem;font-weight:700;margin-bottom:.55rem}
.tag-signal{background:#d1fae5;color:#065f46}
.tag-balanced{background:#dbeafe;color:#1e40af}
.tag-over{background:#fef9c3;color:#854d0e}
.tag-under{background:#fee2e2;color:#991b1b}
.mech-text{font-size:.83rem;color:var(--dgray);line-height:1.55;font-style:italic;margin-top:.45rem}
.players-list{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.45rem}
.player-chip{background:var(--lgray);border-radius:12px;padding:.22rem .55rem;font-size:.73rem;font-weight:500;color:var(--navy)}
.player-chip.highlight{background:var(--red);color:#fff}
#no-selection{text-align:center;padding:2rem;color:var(--mgray);font-size:.88rem}
/* SEASON GRID */
#season-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:.5rem;margin-bottom:1.15rem}
.season-tile{
  background:var(--white);border-radius:8px;padding:.65rem .55rem;
  cursor:pointer;transition:all .17s;border:2px solid transparent;
  text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06);
  position:relative;overflow:hidden;
}
.season-tile::after{content:'';position:absolute;left:0;top:0;bottom:0;width:4px}
.season-tile.era-yaz::after{background:#4a90d9}
.season-tile.era-rice::after{background:#e4b84d}
.season-tile.era-boggs::after{background:#7eb8f7}
.season-tile.era-pedro::after{background:#c8102e}
.season-tile.era-francona::after{background:#2da870}
.season-tile.era-betts::after{background:#c8940a}
.season-tile.era-rebuild::after{background:#999}
.season-tile:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.12)}
.season-tile.selected{border-color:var(--red);background:#fff5f7}
.season-tile.dimmed{opacity:.27}
.tile-year{font-size:.84rem;font-weight:800;color:var(--navy)}
.tile-record{font-size:.7rem;color:var(--dgray);margin:.08rem 0}
.tile-star{font-size:.73rem;color:var(--gold)}
.tile-tag{font-size:.59rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-top:.18rem}
.tag-s{color:#065f46}.tag-b{color:#1e40af}.tag-o{color:#854d0e}.tag-u{color:#991b1b}
/* ERA TABLE */
#era-table-wrap{overflow-x:auto;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.07);margin-bottom:1.15rem}
#era-table{width:100%;border-collapse:collapse;font-size:.8rem}
#era-table th{background:var(--navy);color:var(--white);padding:.5rem .65rem;text-align:left;font-weight:600;font-size:.73rem;letter-spacing:.04em}
#era-table th:not(:first-child){text-align:center}
#era-table td{padding:.45rem .65rem;border-bottom:1px solid #f0f0f0;vertical-align:middle}
#era-table td:not(:first-child){text-align:center}
#era-table tr:nth-child(even){background:#f9fafb}
#era-table tr:hover{background:#fff5f7;cursor:pointer}
.era-cell{display:flex;align-items:center;gap:.45rem}
.era-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.td-green{color:var(--green);font-weight:600}
.td-red{color:var(--red);font-weight:600}
.ws-star{color:var(--gold)}
/* KEYBOARD HINT */
.key-hint{font-size:.74rem;color:var(--mgray);text-align:center;padding:.4rem;background:var(--lgray);border-radius:6px;margin-bottom:1rem}
/* SCROLLBAR */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--lgray)}
::-webkit-scrollbar-thumb{background:var(--mgray);border-radius:3px}
/* ANIMATIONS */
.fade-in{animation:fadeIn .28s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
/* FOOTER */
footer{text-align:center;padding:1.4rem;color:var(--dgray);font-size:.76rem;background:var(--white);border-top:1px solid #e5e7eb;margin-top:.5rem}
@media(max-width:580px){#topnav nav{display:none}}
"""

    # JS ──────────────────────────────────────────────────────────────────
    js = r"""
// ─── DATA ──────────────────────────────────────────────────────────────
const SEASONS = __SEASONS_JSON__;

const MACRO_ERAS = {
  yaz:      { years: range(1967,1977), color:'#4a90d9', label:'Yaz Era (1967-76)' },
  rice:     { years: range(1977,1987), color:'#e4b84d', label:'Rice & Lynn (1977-86)' },
  boggs:    { years: range(1987,1997), color:'#7eb8f7', label:'Boggs & Clemens (1987-96)' },
  pedro:    { years: range(1997,2007), color:'#c8102e', label:'Pedro & Manny (1997-2006)' },
  francona: { years: range(2007,2014), color:'#2da870', label:'Francona Dynasty (2007-13)' },
  betts:    { years: range(2014,2020), color:'#c8940a', label:'Betts Emergence (2014-19)' },
  rebuild:  { years: range(2020,2025), color:'#999999', label:'Rebuild & Now (2020-24)' },
};

function range(a,b){ return Array.from({length:b-a},(_,i)=>a+i); }
function getEra(season){ for(const [k,v] of Object.entries(MACRO_ERAS)) if(v.years.includes(+season)) return k; return 'rebuild'; }
function eraColor(season){ return MACRO_ERAS[getEra(season)]?.color||'#aaa'; }

const TAG_INFO = {
  'signal':                { label:'Signal', cls:'tag-signal', badge:'tag-s', text:'Process backed the result' },
  'balanced':              { label:'Balanced', cls:'tag-balanced', badge:'tag-b', text:'Result matched the process' },
  'overperformed process': { label:'Overperformed', cls:'tag-over', badge:'tag-o', text:'Won more than process predicted' },
  'underperformed process':{ label:'Underperformed', cls:'tag-under', badge:'tag-u', text:'Won less than process predicted' },
};

const RES_LABEL = {
  'world series':'World Series','lost alcs':'Lost ALCS','lost alds':'Lost ALDS',
  'al east tie-break loss':'AL East TBL','missed playoffs':'Missed Playoffs',
};
const RES_PILL = {
  'world series':'pill-ws','lost alcs':'pill-alcs','lost alds':'pill-alds',
  'al east tie-break loss':'pill-tbl','missed playoffs':'pill-miss',
};

// ─── STATE ─────────────────────────────────────────────────────────────
const S = {
  sel: null, era:'all', playoff:'all', minWins:24,
  tags: new Set(['signal','balanced','overperformed process','underperformed process']),
  player:'',
};

function matchFilter(s){
  if(S.era!=='all' && getEra(s.season)!==S.era) return false;
  if(S.playoff==='playoff'){
    if(!['world series','lost alcs','lost alds','al east tie-break loss'].includes(s.playoff_result)) return false;
  } else if(S.playoff!=='all' && s.playoff_result!==S.playoff) return false;
  if(s.wins < S.minWins) return false;
  if(!S.tags.has(s.tag_label)) return false;
  if(S.player){
    const q=S.player.toLowerCase();
    if(!s.key_players.toLowerCase().includes(q) && !String(s.season).includes(q) && !s.manager.toLowerCase().includes(q)) return false;
  }
  return true;
}
function filtered(){ return SEASONS.filter(matchFilter); }

// ─── CHARTS ────────────────────────────────────────────────────────────
let tlChart, rdChart, opsEraChart, scChart;

function refLinesPlugin(xVal, yVal){
  return {
    id:'refLines'+Math.random(),
    afterDraw(chart){
      const {ctx,chartArea,scales} = chart;
      if(!scales.x||!scales.y) return;
      ctx.save();
      ctx.setLineDash([5,4]);
      ctx.lineWidth=1;
      ctx.strokeStyle='rgba(200,16,46,.3)';
      if(yVal!==undefined){
        const y=scales.y.getPixelForValue(yVal);
        ctx.beginPath(); ctx.moveTo(chartArea.left,y); ctx.lineTo(chartArea.right,y); ctx.stroke();
        ctx.fillStyle='rgba(200,16,46,.45)'; ctx.font='bold 9px Inter,sans-serif';
        ctx.fillText('.500',chartArea.left+4,y-3);
      }
      if(xVal!==undefined){
        const x=scales.x.getPixelForValue(xVal);
        ctx.beginPath(); ctx.moveTo(x,chartArea.top); ctx.lineTo(x,chartArea.bottom); ctx.stroke();
        ctx.fillStyle='rgba(200,16,46,.45)'; ctx.font='bold 9px Inter,sans-serif';
        ctx.fillText('RD=0',x+3,chartArea.top+12);
      }
      ctx.restore();
    }
  };
}

const tooltipDefaults = {
  backgroundColor:'#0d1b2a',borderColor:'#c8102e',borderWidth:1,
  titleColor:'#e4b84d',bodyColor:'#ccc',padding:8,
};

function initTimeline(){
  const ctx=document.getElementById('tlChart').getContext('2d');
  tlChart = new Chart(ctx,{
    type:'bar',
    plugins:[refLinesPlugin(undefined,81)],
    data:{
      labels: SEASONS.map(s=>s.season),
      datasets:[{
        data: SEASONS.map(s=>s.wins),
        backgroundColor: SEASONS.map(s=>eraColor(s.season)),
        borderColor: SEASONS.map(s=>s.playoff_result==='world series'?'#e4b84d':'transparent'),
        borderWidth: SEASONS.map(s=>s.playoff_result==='world series'?3:0),
        borderRadius:3,
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{...tooltipDefaults,callbacks:{
          title:i=>''+i[0].label,
          label:i=>{
            const s=SEASONS.find(x=>x.season===+i.label);
            return [`${s.wins}-${s.losses}  ${RES_LABEL[s.playoff_result]||s.playoff_result}`,
                    `RD: ${s.run_diff>=0?'+':''}${s.run_diff}  OPS: ${s.team_ops.toFixed(3)}`,
                    `Manager: ${s.manager}`];
          }
        }}
      },
      scales:{
        x:{grid:{display:false},ticks:{color:'#888',font:{size:8.5},maxRotation:45}},
        y:{min:40,max:120,grid:{color:'#eee'},ticks:{color:'#888',font:{size:8.5}}},
      },
      onClick:(_,items)=>{ if(items.length) selectSeason(SEASONS[items[0].index].season); },
      animation:{duration:250},
    }
  });
}

function initRd(){
  const ctx=document.getElementById('rdChart').getContext('2d');
  rdChart = new Chart(ctx,{
    type:'bar',
    plugins:[refLinesPlugin(undefined,0)],
    data:{
      labels: SEASONS.map(s=>s.season),
      datasets:[{
        data: SEASONS.map(s=>s.run_diff),
        backgroundColor: SEASONS.map(s=>s.run_diff>=0?'#2da870bb':'#c8102ebb'),
        borderRadius:2,
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{...tooltipDefaults,callbacks:{
        title:i=>''+i[0].label,
        label:i=>{
          const s=SEASONS.find(x=>x.season===+i.label);
          return `RD: ${s.run_diff>=0?'+':''}${s.run_diff}  (${s.wins}-${s.losses})`;
        }
      }}},
      scales:{
        x:{grid:{display:false},ticks:{color:'#888',font:{size:8},maxRotation:45}},
        y:{grid:{color:'#eee'},ticks:{color:'#888',font:{size:8}}},
      },
      onClick:(_,items)=>{ if(items.length) selectSeason(SEASONS[items[0].index].season); },
      animation:{duration:250},
    }
  });
}

function initOpsEra(){
  const ctx=document.getElementById('opsEraChart').getContext('2d');
  opsEraChart = new Chart(ctx,{
    type:'line',
    data:{
      labels: SEASONS.map(s=>s.season),
      datasets:[
        {label:'OPS',data:SEASONS.map(s=>s.team_ops),borderColor:'#4a90d9',
         backgroundColor:'rgba(74,144,217,.07)',fill:true,tension:.35,
         pointRadius:2,pointHoverRadius:5,yAxisID:'yL'},
        {label:'ERA',data:SEASONS.map(s=>s.team_era),borderColor:'#c8102e',
         backgroundColor:'transparent',fill:false,tension:.35,
         pointRadius:2,pointHoverRadius:5,yAxisID:'yR',borderDash:[4,3]},
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:true,labels:{color:'#555',font:{size:8.5},boxWidth:12}},
        tooltip:{...tooltipDefaults,callbacks:{
          title:i=>''+i[0].label,
          label:i=>{
            const s=SEASONS.find(x=>x.season===+i.label);
            return [`OPS: ${s.team_ops.toFixed(3)}`,`ERA: ${s.team_era.toFixed(2)}`];
          }
        }}
      },
      scales:{
        x:{grid:{display:false},ticks:{color:'#888',font:{size:8},maxRotation:45}},
        yL:{position:'left',min:.62,max:.88,grid:{color:'#eee'},ticks:{color:'#4a90d9',font:{size:8}}},
        yR:{position:'right',min:3.0,max:5.6,grid:{display:false},ticks:{color:'#c8102e',font:{size:8}}},
      },
      onClick:(_,items)=>{ if(items.length) selectSeason(SEASONS[items[0].index].season); },
      animation:{duration:250},
    }
  });
}

function initScatter(){
  const ctx=document.getElementById('scChart').getContext('2d');
  const pts = SEASONS.map(s=>({x:s.run_diff,y:s.wins,season:s.season,isWS:s.playoff_result==='world series'}));
  scChart = new Chart(ctx,{
    type:'scatter',
    plugins:[refLinesPlugin(0,81)],
    data:{datasets:[{
      data:pts,
      backgroundColor: pts.map(p=>eraColor(p.season)+'cc'),
      borderColor: pts.map(p=>p.isWS?'#e4b84d':eraColor(p.season)+'55'),
      borderWidth: pts.map(p=>p.isWS?3:1),
      pointRadius: pts.map(p=>p.isWS?9:5.5),
      pointHoverRadius:10,
      pointStyle: pts.map(p=>p.isWS?'star':'circle'),
    }]},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{...tooltipDefaults,callbacks:{
        title:i=>String(i[0].raw.season),
        label:i=>{
          const s=SEASONS.find(x=>x.season===i[0].raw.season);
          return [`${s.wins}-${s.losses}  ${RES_LABEL[s.playoff_result]||s.playoff_result}`,
                  `RD: ${s.run_diff>=0?'+':''}${s.run_diff}`,
                  `OPS ${s.team_ops.toFixed(3)}  ERA ${s.team_era.toFixed(2)}`,
                  `Manager: ${s.manager}`];
        }
      }}},
      scales:{
        x:{title:{display:true,text:'Run Differential (process proxy)',color:'#888',font:{size:8.5}},
           grid:{color:'#eee'},ticks:{color:'#888',font:{size:8.5}}},
        y:{min:40,max:120,title:{display:true,text:'Wins',color:'#888',font:{size:8.5}},
           grid:{color:'#eee'},ticks:{color:'#888',font:{size:8.5}}},
      },
      onClick:(_,items)=>{ if(items.length) selectSeason(items[0].raw.season); },
      animation:{duration:250},
    }
  });
}

// ─── UPDATE CHARTS ON FILTER ───────────────────────────────────────────
function updateCharts(){
  const vis = new Set(filtered().map(s=>s.season));
  tlChart.data.datasets[0].backgroundColor  = SEASONS.map(s=>{ const c=eraColor(s.season); return vis.has(s.season)?c:c+'28'; });
  tlChart.data.datasets[0].borderColor       = SEASONS.map(s=>s.playoff_result==='world series'?'#e4b84d':'transparent');
  tlChart.data.datasets[0].borderWidth       = SEASONS.map(s=>s.playoff_result==='world series'?3:0);
  tlChart.update('none');

  rdChart.data.datasets[0].backgroundColor = SEASONS.map(s=>{ const c=s.run_diff>=0?'#2da870':'#c8102e'; return vis.has(s.season)?c+'bb':c+'22'; });
  rdChart.update('none');

  // OpsEra: fade non-matching points (borderWidth trick)
  opsEraChart.data.datasets[0].pointRadius = SEASONS.map(s=>vis.has(s.season)?2:1);
  opsEraChart.data.datasets[1].pointRadius = SEASONS.map(s=>vis.has(s.season)?2:1);
  opsEraChart.update('none');

  scChart.data.datasets[0].backgroundColor = scChart.data.datasets[0].data.map(p=>{ const c=eraColor(p.season); return vis.has(p.season)?c+'cc':c+'14'; });
  scChart.data.datasets[0].borderColor      = scChart.data.datasets[0].data.map(p=>vis.has(p.season)?(p.isWS?'#e4b84d':eraColor(p.season)+'55'):'transparent');
  scChart.update('none');
}

// ─── SEASON CARD ───────────────────────────────────────────────────────
function selectSeason(yr){
  S.sel=+yr;
  renderCard();
  updateGrid();
  // Highlight timeline bar (scale selected bar via backgroundColor brightness)
  document.getElementById('season-card').scrollIntoView({behavior:'smooth',block:'nearest'});
}

function renderCard(){
  const s=SEASONS.find(x=>x.season===S.sel); if(!s) return;
  const card=document.getElementById('season-card');
  card.className='fade-in'+(s.playoff_result==='world series'?' ws':'');
  const ti=TAG_INFO[s.tag_label]||TAG_INFO['balanced'];
  const pill=RES_PILL[s.playoff_result]||'pill-miss';
  const resLbl=RES_LABEL[s.playoff_result]||s.playoff_result;
  const rd=s.run_diff; const sign=rd>=0?'+':''; const rdcls=rd>=0?'positive':'negative';
  const q=S.player.toLowerCase();
  const players=s.key_players.split(',').map(p=>{
    const t=p.trim();
    const hl=q&&t.toLowerCase().includes(q);
    return `<span class="player-chip${hl?' highlight':''}">${t}</span>`;
  }).join('');
  card.innerHTML=`
    <div class="card-header">
      <div><div class="year-badge">${s.season}</div><div style="color:#888;font-size:.73rem;margin-top:.1rem">${s.era_label}</div></div>
      <div class="record-badge">${s.wins}-${s.losses}</div>
      <span class="result-pill ${pill}">${resLbl}</span>
      <div style="color:#888;font-size:.78rem">Manager: <b style="color:#fff">${s.manager}</b></div>
    </div>
    <div class="card-body">
      <div class="meta-section">
        <h3>Season Stats</h3>
        <div class="meta-row"><span class="meta-lbl">Run Differential</span><span class="meta-val ${rdcls}">${sign}${rd}</span></div>
        <div class="meta-row"><span class="meta-lbl">Team OPS</span><span class="meta-val">${s.team_ops.toFixed(3)}</span></div>
        <div class="meta-row"><span class="meta-lbl">Team OBP</span><span class="meta-val">${s.team_obp.toFixed(3)}</span></div>
        <div class="meta-row"><span class="meta-lbl">Team SLG</span><span class="meta-val">${s.team_slg.toFixed(3)}</span></div>
        <div class="meta-row"><span class="meta-lbl">Team ERA</span><span class="meta-val">${s.team_era.toFixed(2)}</span></div>
        <div class="meta-row"><span class="meta-lbl">Team FIP</span><span class="meta-val">${s.team_fip.toFixed(2)}</span></div>
      </div>
      <div class="meta-section">
        <h3>Process Analysis</h3>
        <span class="tag-badge ${ti.cls}">${ti.text}</span>
        <p class="mech-text">"${s.mechanism_summary}"</p>
        <h3 style="margin-top:.8rem">Key Players</h3>
        <div class="players-list">${players}</div>
      </div>
    </div>`;
}

// ─── SEASON GRID ───────────────────────────────────────────────────────
function buildGrid(){
  const g=document.getElementById('season-grid');
  g.innerHTML='';
  SEASONS.forEach(s=>{
    const ek=getEra(s.season);
    const ti=TAG_INFO[s.tag_label]||TAG_INFO['balanced'];
    const tile=document.createElement('div');
    tile.className=`season-tile era-${ek}`;
    tile.dataset.season=s.season;
    tile.innerHTML=`
      <div class="tile-year">${s.season}</div>
      <div class="tile-record">${s.wins}-${s.losses}</div>
      ${s.playoff_result==='world series'?'<div class="tile-star">★ WS</div>':''}
      <div class="tile-tag ${ti.badge}">${ti.label}</div>`;
    tile.addEventListener('click',()=>selectSeason(s.season));
    g.appendChild(tile);
  });
}

function updateGrid(){
  const vis=new Set(filtered().map(s=>s.season));
  document.querySelectorAll('.season-tile').forEach(tile=>{
    const yr=+tile.dataset.season;
    tile.classList.toggle('dimmed',!vis.has(yr));
    tile.classList.toggle('selected',yr===S.sel);
  });
}

// ─── ERA TABLE ─────────────────────────────────────────────────────────
function buildEraTable(){
  const tb=document.getElementById('era-table');
  const hdrs=['Era','Years','Avg W','Avg RD','Avg OPS','Avg ERA','WS','Playoff%'];
  let h=`<thead><tr>${hdrs.map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>`;
  for(const [k,v] of Object.entries(MACRO_ERAS)){
    const sub=SEASONS.filter(s=>v.years.includes(s.season));
    if(!sub.length) continue;
    const avgW=(sub.reduce((a,s)=>a+s.wins,0)/sub.length).toFixed(1);
    const avgRD=(sub.reduce((a,s)=>a+s.run_diff,0)/sub.length).toFixed(1);
    const avgOPS=(sub.reduce((a,s)=>a+s.team_ops,0)/sub.length).toFixed(3);
    const avgERA=(sub.reduce((a,s)=>a+s.team_era,0)/sub.length).toFixed(2);
    const ws=sub.filter(s=>s.playoff_result==='world series').length;
    const pl=Math.round(sub.filter(s=>['world series','lost alcs','lost alds','al east tie-break loss'].includes(s.playoff_result)).length/sub.length*100);
    const rdc=+avgRD>=0?'td-green':'td-red'; const rds=+avgRD>=0?'+':'';
    h+=`<tr onclick="filterEra('${k}')">
      <td><div class="era-cell"><div class="era-dot" style="background:${v.color}"></div>${v.label}</div></td>
      <td>${v.years[0]}&ndash;${v.years[v.years.length-1]}</td>
      <td>${avgW}</td>
      <td class="${rdc}">${rds}${avgRD}</td>
      <td>${avgOPS}</td>
      <td>${avgERA}</td>
      <td class="ws-star">${'&#9733;'.repeat(ws)||'&mdash;'}</td>
      <td>${pl}%</td>
    </tr>`;
  }
  tb.innerHTML=h+'</tbody>';
}

// ─── FILTER CONTROLS ───────────────────────────────────────────────────
function applyFilters(){
  const n=filtered().length;
  document.getElementById('filter-count').textContent=n+' season'+(n!==1?'s':'');
  updateCharts();
  updateGrid();
}

function filterEra(era){
  S.era=era;
  document.querySelectorAll('.era-btn').forEach(b=>b.classList.toggle('active',b.dataset.era===era));
  applyFilters();
  document.getElementById('chart-section').scrollIntoView({behavior:'smooth'});
}

function toggleTag(tag,btn){
  if(S.tags.has(tag)){ S.tags.delete(tag); btn.classList.remove('chip-active','chip-balanced-active','chip-over-active','chip-under-active'); btn.classList.add('chip-clear'); }
  else { S.tags.add(tag); btn.classList.remove('chip-clear');
    if(tag==='signal') btn.classList.add('chip-active');
    else if(tag==='balanced') btn.classList.add('chip-balanced-active');
    else if(tag==='overperformed process') btn.classList.add('chip-over-active');
    else btn.classList.add('chip-under-active');
  }
  applyFilters();
}

function clearFilters(){
  S.era='all'; S.playoff='all'; S.minWins=24; S.player='';
  S.tags=new Set(['signal','balanced','overperformed process','underperformed process']);
  document.getElementById('playoff-filter').value='all';
  document.getElementById('min-wins').value=24;
  document.getElementById('min-wins-val').textContent='24';
  document.getElementById('player-search').value='';
  document.querySelectorAll('.era-btn').forEach(b=>b.classList.toggle('active',b.dataset.era==='all'));
  document.getElementById('btn-signal').className='chip chip-active';
  document.getElementById('btn-balanced').className='chip chip-balanced-active';
  document.getElementById('btn-over').className='chip chip-over-active';
  document.getElementById('btn-under').className='chip chip-under-active';
  applyFilters();
}

// ─── EVENT WIRING ──────────────────────────────────────────────────────
document.querySelectorAll('.era-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    S.era=btn.dataset.era;
    document.querySelectorAll('.era-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    applyFilters();
  });
});

document.getElementById('playoff-filter').addEventListener('change',e=>{
  S.playoff=e.target.value; applyFilters();
});

document.getElementById('min-wins').addEventListener('input',e=>{
  S.minWins=+e.target.value;
  document.getElementById('min-wins-val').textContent=e.target.value;
  applyFilters();
});

document.getElementById('player-search').addEventListener('input',e=>{
  S.player=e.target.value.trim();
  applyFilters();
  if(S.player){
    const m=filtered().sort((a,b)=>b.season-a.season);
    if(m.length) selectSeason(m[0].season);
  }
});

// Keyboard navigation ←→
document.addEventListener('keydown',e=>{
  if(!S.sel) return;
  if(document.activeElement.tagName==='INPUT') return;
  const idx=SEASONS.findIndex(s=>s.season===S.sel);
  if(e.key==='ArrowRight'&&idx<SEASONS.length-1) selectSeason(SEASONS[idx+1].season);
  if(e.key==='ArrowLeft'&&idx>0) selectSeason(SEASONS[idx-1].season);
});

// Nav scroll active
const sectionIds=['chart-section','scatter-section','seasons-section','era-table-section'];
const io=new IntersectionObserver(entries=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      document.querySelectorAll('#topnav nav a').forEach(a=>{
        a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id);
      });
    }
  });
},{threshold:.3});
sectionIds.forEach(id=>{ const el=document.getElementById(id); if(el) io.observe(el); });

// ─── INIT ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  initTimeline();
  initRd();
  initOpsEra();
  initScatter();
  buildGrid();
  buildEraTable();
  applyFilters();
  setTimeout(()=>selectSeason(2018),350);
});
"""
    js = js.replace('__SEASONS_JSON__', seasons_json)

    # HTML ────────────────────────────────────────────────────────────────
    html = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8"/>\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>\n'
        '<title>Red Sox Franchise Timeline 1967\u20132024</title>\n'
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>\n'
        '<style>\n' + css + '\n</style>\n'
        '</head>\n'
        '<body>\n\n'

        '<!-- TOP NAV -->\n'
        '<header id="topnav">\n'
        '  <div class="brand"><span>\u26be RED SOX FRANCHISE TIMELINE</span><sub>1967\u20132024</sub></div>\n'
        '  <nav>\n'
        '    <a href="#chart-section" class="active">Timeline</a>\n'
        '    <a href="#scatter-section">Process</a>\n'
        '    <a href="#seasons-section">Seasons</a>\n'
        '    <a href="#era-table-section">Era Stats</a>\n'
        '  </nav>\n'
        '  <div id="search-nav"><input id="player-search" type="text" placeholder="Search player or year\u2026" autocomplete="off"/></div>\n'
        '</header>\n\n'

        '<!-- HERO -->\n'
        '<section id="hero">\n'
        '  <h1>Red Sox Franchise <em>Timeline</em></h1>\n'
        '  <p>58 seasons \u00b7 7 eras \u00b7 6 World Series championships \u00b7 1967\u20132024</p>\n'
        '  <div class="hero-kpis">\n'
        '    <div class="hero-kpi"><div class="val">58</div><div class="lbl">Seasons</div></div>\n'
        '    <div class="hero-kpi"><div class="val">6</div><div class="lbl">WS Titles</div></div>\n'
        '    <div class="hero-kpi"><div class="val">108</div><div class="lbl">Best Win Total</div></div>\n'
        '    <div class="hero-kpi"><div class="val">+229</div><div class="lbl">Best Run Diff</div></div>\n'
        '    <div class="hero-kpi"><div class="val">20</div><div class="lbl">Playoff Apps</div></div>\n'
        '    <div class="hero-kpi"><div class="val">86.2</div><div class="lbl">Avg Wins</div></div>\n'
        '  </div>\n'
        '</section>\n\n'

        '<!-- ERA CHIP BAR -->\n'
        '<div id="era-nav">\n'
        '  <span class="lbl">Era:</span>\n'
        '  <button class="era-btn active" data-era="all" style="background:#4a4a6a;color:#fff">All Eras</button>\n'
        '  <button class="era-btn" data-era="yaz" style="background:#4a90d9;color:#fff">\u26be Yaz Era</button>\n'
        '  <button class="era-btn" data-era="rice" style="background:#e4b84d;color:#0d1b2a">\ud83d\udcaa Rice &amp; Lynn</button>\n'
        '  <button class="era-btn" data-era="boggs" style="background:#7eb8f7;color:#0d1b2a">\ud83c\udfaf Boggs &amp; Clemens</button>\n'
        '  <button class="era-btn" data-era="pedro" style="background:#c8102e;color:#fff">\ud83d\udd25 Pedro &amp; Manny</button>\n'
        '  <button class="era-btn" data-era="francona" style="background:#2da870;color:#fff">\ud83c\udfc6 Francona Dynasty</button>\n'
        '  <button class="era-btn" data-era="betts" style="background:#c8940a;color:#fff">\ud83c\udf1f Betts Emergence</button>\n'
        '  <button class="era-btn" data-era="rebuild" style="background:#999;color:#fff">\ud83d\udd04 Rebuild &amp; Now</button>\n'
        '</div>\n\n'

        '<!-- FILTER BAR -->\n'
        '<div id="filter-bar">\n'
        '  <label>Playoff:</label>\n'
        '  <select id="playoff-filter">\n'
        '    <option value="all">All Results</option>\n'
        '    <option value="world series">World Series Only</option>\n'
        '    <option value="playoff">Any Playoff Appearance</option>\n'
        '    <option value="missed playoffs">Missed Playoffs</option>\n'
        '    <option value="lost alcs">Lost ALCS</option>\n'
        '    <option value="lost alds">Lost ALDS</option>\n'
        '  </select>\n'
        '  <label>Min Wins:</label>\n'
        '  <input type="range" id="min-wins" min="24" max="108" value="24" step="1"/>\n'
        '  <span id="min-wins-val" style="min-width:2rem;font-weight:600">24</span>\n'
        '  <div class="filter-chips">\n'
        '    <button class="chip chip-active" id="btn-signal" onclick="toggleTag(\'signal\',this)">Signal</button>\n'
        '    <button class="chip chip-balanced-active" id="btn-balanced" onclick="toggleTag(\'balanced\',this)">Balanced</button>\n'
        '    <button class="chip chip-over-active" id="btn-over" onclick="toggleTag(\'overperformed process\',this)">Overperformed</button>\n'
        '    <button class="chip chip-under-active" id="btn-under" onclick="toggleTag(\'underperformed process\',this)">Underperformed</button>\n'
        '    <button class="chip chip-clear" onclick="clearFilters()">\u21ba Reset</button>\n'
        '  </div>\n'
        '  <span id="filter-count">58 seasons</span>\n'
        '</div>\n\n'

        '<!-- MAIN -->\n'
        '<div id="main">\n\n'

        '  <!-- WINS TIMELINE -->\n'
        '  <div id="chart-section" class="chart-card">\n'
        '    <div class="section-title">Season Win Totals \u2014 All 58 Seasons</div>\n'
        '    <p style="font-size:.79rem;color:var(--dgray);margin-bottom:.75rem">Click any bar to explore that season \u00b7 Gold border = World Series win \u00b7 \u2190\u2192 keys to step through seasons</p>\n'
        '    <div style="position:relative;height:255px"><canvas id="tlChart"></canvas></div>\n'
        '  </div>\n\n'

        '  <!-- SEASON DETAIL CARD -->\n'
        '  <div id="season-card"><div id="no-selection"><div style="font-size:2rem;margin-bottom:.5rem">\u26be</div>Click any bar or tile to explore a season</div></div>\n\n'

        '  <!-- DUAL CHARTS -->\n'
        '  <div class="dual-charts">\n'
        '    <div class="chart-card">\n'
        '      <div class="section-title">Run Differential</div>\n'
        '      <p style="font-size:.77rem;color:var(--dgray);margin-bottom:.65rem">Process proxy \u2014 green = positive RD, red = negative</p>\n'
        '      <div style="position:relative;height:205px"><canvas id="rdChart"></canvas></div>\n'
        '    </div>\n'
        '    <div class="chart-card">\n'
        '      <div class="section-title">Team OPS &amp; ERA by Season</div>\n'
        '      <p style="font-size:.77rem;color:var(--dgray);margin-bottom:.65rem">Offense (left, blue) and pitching (right, red dashed)</p>\n'
        '      <div style="position:relative;height:205px"><canvas id="opsEraChart"></canvas></div>\n'
        '    </div>\n'
        '  </div>\n\n'

        '  <!-- SCATTER -->\n'
        '  <div id="scatter-section" class="chart-card">\n'
        '    <div class="section-title">Process vs Result \u2014 Wins \u00d7 Run Differential</div>\n'
        '    <p style="font-size:.79rem;color:var(--dgray);margin-bottom:.75rem">Top-right = elite process. Gold star = World Series win. Click any dot to open that season.</p>\n'
        '    <div style="position:relative;height:330px"><canvas id="scChart"></canvas></div>\n'
        '  </div>\n\n'

        '  <!-- SEASON GRID -->\n'
        '  <div id="seasons-section">\n'
        '    <div class="section-title">All Seasons at a Glance</div>\n'
        '    <p style="font-size:.79rem;color:var(--dgray);margin-bottom:.75rem">Era colour on left edge \u00b7 Click any tile to open season card \u00b7 Dimmed = filtered out</p>\n'
        '    <div class="key-hint">\u2190\u2192 keyboard arrows step through seasons when a season is selected</div>\n'
        '    <div id="season-grid"></div>\n'
        '  </div>\n\n'

        '  <!-- ERA TABLE -->\n'
        '  <div id="era-table-section">\n'
        '    <div class="section-title">Era Comparison Statistics</div>\n'
        '    <p style="font-size:.79rem;color:var(--dgray);margin-bottom:.75rem">Per-season averages \u00b7 Click a row to filter the timeline to that era</p>\n'
        '    <div id="era-table-wrap"><table id="era-table"></table></div>\n'
        '  </div>\n\n'

        '</div><!-- /main -->\n\n'

        '<footer>Red Sox Franchise Timeline \u00b7 frame2-redsox-history analytics engine \u00b7 data: 1967\u20132024 \u00b7 58 seasons \u00b7 all stats from redsox_history.csv</footer>\n\n'

        '<script>\n' + js + '\n</script>\n'
        '</body>\n'
        '</html>\n'
    )

    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
        f.write(html)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"\u2713 Web timeline saved \u2192 {output_path}  ({size_kb} KB)")
    return output_path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'redsox_franchise_timeline.html'
    build_html(out)

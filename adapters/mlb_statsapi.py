import requests
from datetime import date
from typing import Any, Dict, List, Optional
from config.settings import SETTINGS
from config.utils import cache_get, cache_set, ensure_dir

BASE = "https://statsapi.mlb.com/api/v1"
TEAM_ID = {"red sox": 111, "bos": 111, "boston": 111}

def _get(url: str, params: Optional[Dict[str, Any]] = None, ttl_s: int = 20) -> Dict[str, Any]:
    ensure_dir(SETTINGS.cache_dir)
    key = url.replace("https://", "").replace("/", "_")
    if params:
        key += "_" + "_".join([f"{k}-{params[k]}" for k in sorted(params.keys())])
    cache_path = f"{SETTINGS.cache_dir}/{key}.json"
    cached = cache_get(cache_path, ttl_s=ttl_s)
    if cached is not None:
        return cached
    r = requests.get(url, params=params, timeout=SETTINGS.request_timeout_s)
    r.raise_for_status()
    data = r.json()
    cache_set(cache_path, data)
    return data

def resolve_team_id(team: str) -> int:
    t = (team or "").strip().lower()
    if t in TEAM_ID:
        return TEAM_ID[t]
    data = _get(f"{BASE}/teams", params={"sportId": 1}, ttl_s=3600)
    for item in data.get("teams", []):
        name = (item.get("name") or "").lower()
        abbr = (item.get("abbreviation") or "").lower()
        if t in name or t == abbr:
            return int(item["id"])
    raise ValueError(f"could not resolve team: {team}")

def get_schedule(team_id: int, day: Optional[str] = None) -> List[Dict[str, Any]]:
    day = day or str(date.today())
    data = _get(f"{BASE}/schedule", params={"sportId": 1, "teamId": team_id, "date": day}, ttl_s=30)
    dates = data.get("dates", [])
    if not dates:
        return []
    out = []
    for g in dates[0].get("games", []):
        out.append({"gamePk": g.get("gamePk"), "gameDate": g.get("gameDate"), "status": (g.get("status") or {}).get("detailedState"), "home": ((g.get("teams") or {}).get("home") or {}).get("team", {}).get("name"), "away": ((g.get("teams") or {}).get("away") or {}).get("team", {}).get("name")})
    return out

def get_live_feed(game_pk: int) -> Dict[str, Any]:
    return _get(f"{BASE}/game/{game_pk}/feed/live", ttl_s=8)

def summarize_live(game_pk: int) -> Dict[str, Any]:
    feed = get_live_feed(game_pk)
    live = feed.get("liveData", {}) or {}
    linescore = live.get("linescore", {}) or {}
    teams = (feed.get("gameData", {}) or {}).get("teams", {}) or {}
    home = (teams.get("home") or {}).get("name")
    away = (teams.get("away") or {}).get("name")
    home_runs = ((linescore.get("teams") or {}).get("home") or {}).get("runs")
    away_runs = ((linescore.get("teams") or {}).get("away") or {}).get("runs")
    inning = linescore.get("currentInning")
    half = linescore.get("inningHalf")
    outs = linescore.get("outs")
    balls = linescore.get("balls")
    strikes = linescore.get("strikes")
    offense = linescore.get("offense") or {}
    bases = ("1" if offense.get("first") else "_") + ("2" if offense.get("second") else "_") + ("3" if offense.get("third") else "_")
    status = ((feed.get("gameData") or {}).get("status") or {}).get("detailedState")
    return {"home": home, "away": away, "home_runs": home_runs, "away_runs": away_runs, "inning": inning, "half": half, "count": f"{balls}-{strikes}", "outs": outs, "bases": bases, "status": status}

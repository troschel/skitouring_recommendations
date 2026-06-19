import json
import os

_DIR = os.path.dirname(__file__)
_SKI_FIXTURE    = os.path.join(_DIR, "fixtures", "skitouren_by_region.json")
_SNOW_FIXTURE   = os.path.join(_DIR, "fixtures", "schneeschuh_by_region.json")

SKI_DIFFICULTY_ORDER  = {"L": 1, "WS": 2, "ZS": 3, "S": 4, "SS": 5, "AS": 6, "EX": 7}
# Snowshoe colour codes mapped to WT rank: blau→WT2, rot→WT3, schwarz→WT5
SNOW_WT_RANK = {"WT1": 1, "WT2": 2, "WT3": 3, "WT4": 4, "WT5": 5}

_cache: dict = {}

def _load(path: str) -> dict:
    if path not in _cache:
        with open(path, encoding="utf-8") as f:
            _cache[path] = json.load(f)
    return _cache[path]

def _ski_rank(diff_str: str) -> int:
    base = diff_str.rstrip("+-") if diff_str else ""
    return SKI_DIFFICULTY_ORDER.get(base, 99)

def get_ski_routes(region: str, max_difficulty: str, limit: int = 20) -> list[dict]:
    """Ski touring routes up to and including max_difficulty."""
    data = _load(_SKI_FIXTURE)
    max_rank = _ski_rank(max_difficulty)
    routes = [r for r in data.get(region, []) if r["diff_rank"] <= max_rank]
    return routes[:limit]

def get_snowshoe_routes(region: str, max_wt: str, limit: int = 20) -> list[dict]:
    """Snowshoe routes up to and including the selected WT grade."""
    data = _load(_SNOW_FIXTURE)
    max_rank = SNOW_WT_RANK.get(max_wt, 3)
    routes = [r for r in data.get(region, []) if r["diff_rank"] <= max_rank]
    return routes[:limit]

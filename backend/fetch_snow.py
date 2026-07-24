"""
Snow height data from the SLF IMIS measurement network.
Uses SNOW_FLAT stations (flat-field sensors) nearest to the region centre.
API: https://measurement-api.slf.ch

period_in_days: 1, 3, or 7 (API constraint).
"""

import math
from collections import defaultdict

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BASE = "https://measurement-api.slf.ch/public/api/imis"

_stations_cache: list[dict] | None = None


def _get_stations() -> list[dict]:
    global _stations_cache
    if _stations_cache is None:
        r = requests.get(f"{_BASE}/stations", timeout=10, verify=False)
        r.raise_for_status()
        _stations_cache = [s for s in r.json() if s["type"] == "SNOW_FLAT"]
    return _stations_cache


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def get_snow_height(
    lat: float,
    lon: float,
    period_in_days: int = 1,
    n_stations: int = 5,
    max_radius_km: float = 60,
) -> dict:
    """
    Return snow height data from the n nearest SNOW_FLAT IMIS stations.

    period_in_days: 1, 3, or 7 (API constraint).

    Returns a dict with:
      hs_cm       — median HS for the most recent date (None if no data)
      stations    — list of {code, label, elevation, hs_cm, dist_km} (most recent)
      n_with_data — number of stations with a valid reading on the most recent date
      history     — list of {date: str, hs_cm: float} sorted ascending (median per day)
                    only populated when period_in_days > 1
    """
    period_in_days = period_in_days if period_in_days in (1, 3, 7) else 1

    try:
        stations = _get_stations()

        def dist(s):
            return _haversine_km(lat, lon, s["lat"], s["lon"])

        nearby = sorted(stations, key=dist)
        nearby = [s for s in nearby if dist(s) <= max_radius_km][:n_stations]
        nearby_codes = {s["code"] for s in nearby}

        if not nearby:
            return {"hs_cm": None, "stations": [], "n_with_data": 0, "history": []}

        r = requests.get(
            f"{_BASE}/daily-snow",
            params={"period_in_days": period_in_days},
            timeout=15,
            verify=False,
        )
        r.raise_for_status()
        measurements = r.json()

        # Group HS values by date across nearby stations
        by_date: dict[str, list[float]] = defaultdict(list)
        # Also track latest HS per station (most recent date)
        latest_by_station: dict[str, tuple[str, float | None]] = {}

        for m in measurements:
            code = m["station_code"]
            if code not in nearby_codes:
                continue
            date = m["measure_date"][:10]
            hs = m.get("HS")
            if hs is not None:
                by_date[date].append(hs)
            # Keep the most recent entry per station
            if code not in latest_by_station or date > latest_by_station[code][0]:
                latest_by_station[code] = (date, hs)

        # Build history: median HS per day, sorted ascending
        history = [
            {"date": d, "hs_cm": round(_median(vals), 1)}
            for d, vals in sorted(by_date.items())
            if _median(vals) is not None
        ]

        # Most-recent-date summary per station
        result_stations = []
        hs_today = []
        for s in nearby:
            entry = latest_by_station.get(s["code"])
            hs = entry[1] if entry else None
            result_stations.append({
                "code":      s["code"],
                "label":     s["label"],
                "elevation": s["elevation"],
                "hs_cm":     hs,
                "dist_km":   round(dist(s), 1),
            })
            if hs is not None:
                hs_today.append(hs)

        return {
            "hs_cm":       _median(hs_today),
            "stations":    result_stations,
            "n_with_data": len(hs_today),
            "history":     history,
        }

    except Exception as e:
        print(f"[fetch_snow] Fehler: {e}")
        return {"hs_cm": None, "stations": [], "n_with_data": 0, "history": []}

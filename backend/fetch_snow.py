"""
Snow height data from the SLF IMIS measurement network.
Uses SNOW_FLAT stations (flat-field sensors) nearest to the region centre.
API: https://measurement-api.slf.ch
"""

import math
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
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_snow_height(lat: float, lon: float, n_stations: int = 5, max_radius_km: float = 60) -> dict:
    """
    Return median snow height (HS, cm) from the n nearest SNOW_FLAT IMIS stations.

    Returns a dict with:
      hs_cm      — median snow height in cm (None if no data)
      stations   — list of {code, label, elevation, hs_cm, dist_km} for nearby stations
      n_with_data — number of stations that returned a valid HS reading
    """
    try:
        stations = _get_stations()
        # Sort by distance to region centre
        def dist(s):
            return _haversine_km(lat, lon, s["lat"], s["lon"])

        nearby = sorted(stations, key=dist)
        nearby = [s for s in nearby if dist(s) <= max_radius_km][:n_stations]

        if not nearby:
            return {"hs_cm": None, "stations": [], "n_with_data": 0}

        # Fetch daily snow for all stations (one bulk call)
        r = requests.get(f"{_BASE}/daily-snow", params={"period_in_days": 1},
                         timeout=15, verify=False)
        r.raise_for_status()
        measurements = r.json()

        # Latest HS per station (measurements may contain multiple days)
        latest: dict[str, float | None] = {}
        for m in measurements:
            code = m["station_code"]
            hs = m.get("HS")
            if code not in latest or (hs is not None and latest[code] is None):
                latest[code] = hs

        result_stations = []
        hs_values = []
        for s in nearby:
            hs = latest.get(s["code"])
            result_stations.append({
                "code":      s["code"],
                "label":     s["label"],
                "elevation": s["elevation"],
                "hs_cm":     hs,
                "dist_km":   round(dist(s), 1),
            })
            if hs is not None:
                hs_values.append(hs)

        median_hs = None
        if hs_values:
            hs_values.sort()
            mid = len(hs_values) // 2
            median_hs = hs_values[mid] if len(hs_values) % 2 else (hs_values[mid - 1] + hs_values[mid]) / 2

        return {
            "hs_cm":       median_hs,
            "stations":    result_stations,
            "n_with_data": len(hs_values),
        }

    except Exception as e:
        print(f"[fetch_snow] Fehler: {e}")
        return {"hs_cm": None, "stations": [], "n_with_data": 0}

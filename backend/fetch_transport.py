"""
Public transport timetable via transport.opendata.ch (no API key needed).
Covers all Swiss public transport (SBB, BLS, PostAuto, narrow-gauge railways, etc.)
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BASE = "https://transport.opendata.ch/v1"


def get_nearest_stop(lat: float, lon: float) -> dict | None:
    """Return the nearest named public transport stop with a valid station ID."""
    try:
        r = requests.get(
            f"{_BASE}/locations",
            params={"x": lat, "y": lon, "type": "station"},
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        for s in r.json().get("stations", []):
            if s.get("id") and s.get("name"):
                return {
                    "id":       s["id"],
                    "name":     s["name"],
                    "distance": round(s.get("distance") or 0),
                }
    except Exception as e:
        print(f"[fetch_transport] Fehler nearest stop: {e}")
    return None


def search_stop(query: str) -> list[dict]:
    """Find stations matching a free-text query. Returns up to 5 results."""
    try:
        r = requests.get(
            f"{_BASE}/locations",
            params={"query": query, "type": "station"},
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        return [
            {"id": s["id"], "name": s["name"]}
            for s in r.json().get("stations", [])
            if s.get("id") and s.get("name")
        ][:5]
    except Exception as e:
        print(f"[fetch_transport] Fehler search_stop: {e}")
    return []


def get_connections(from_stop: str, to_stop: str, limit: int = 4) -> list[dict]:
    """
    Return the next `limit` connections from from_stop to to_stop.
    Each entry contains departure, arrival, duration, transfers, and line summary.
    """
    try:
        r = requests.get(
            f"{_BASE}/connections",
            params={"from": from_stop, "to": to_stop, "limit": limit},
            timeout=15,
            verify=False,
        )
        r.raise_for_status()
        connections = []
        for c in r.json().get("connections", []):
            lines = []
            for sec in c.get("sections", []):
                j = sec.get("journey")
                if j:
                    cat = j.get("category") or ""
                    num = j.get("number") or ""
                    line = f"{cat} {num}".strip().strip("?").strip()
                    if line:
                        lines.append(line)

            dep_raw = c.get("from", {}).get("departure", "")
            arr_raw = c.get("to", {}).get("arrival", "")
            platform = c.get("from", {}).get("platform") or ""

            connections.append({
                "departure":    _fmt_time(dep_raw),
                "arrival":      _fmt_time(arr_raw),
                "duration":     _fmt_duration(c.get("duration", "")),
                "transfers":    c.get("transfers", 0),
                "lines":        " → ".join(lines) if lines else "–",
                "platform":     platform,
                "dep_full":     dep_raw,
            })
        return connections
    except Exception as e:
        print(f"[fetch_transport] Fehler connections: {e}")
    return []


def _fmt_time(iso: str) -> str:
    """'2026-01-15T08:34:00+0100' → '08:34'"""
    if not iso:
        return "–"
    try:
        return iso[11:16]
    except Exception:
        return iso


def _fmt_duration(raw: str) -> str:
    """'00d01:35:00' → '1h 35m'"""
    if not raw:
        return "–"
    try:
        time_part = raw.split("d")[-1]   # '01:35:00'
        h, m, _ = time_part.split(":")
        h, m = int(h), int(m)
        if h and m:
            return f"{h}h {m:02d}m"
        if h:
            return f"{h}h"
        return f"{m}m"
    except Exception:
        return raw

"""
Lawinenbulletin vom SLF (WSL Institut für Schnee- und Lawinenforschung)
API: https://aws.slf.ch/api/bulletin/caaml/de/json
"""

import requests
from datetime import datetime

DANGER_LABELS = {
    "low":         {"de": "Gering",      "level": 1, "color": "#4CAF50"},
    "moderate":    {"de": "Mässig",      "level": 2, "color": "#FFEB3B"},
    "considerable":{"de": "Erheblich",   "level": 3, "color": "#FF9800"},
    "high":        {"de": "Gross",       "level": 4, "color": "#F44336"},
    "very_high":   {"de": "Sehr gross",  "level": 5, "color": "#7B1FA2"},
}

def get_avalanche_bulletin() -> list[dict]:
    """Lädt das aktuelle Lawinenbulletin vom SLF und gibt eine Liste von Regionen zurück."""
    url = "https://aws.slf.ch/api/bulletin/caaml/de/json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[fetch_avalanche] Fehler: {e}")
        return _fallback_regions()

    regions = []
    for bulletin in data.get("bulletins", []):
        danger_ratings = bulletin.get("dangerRatings", [])
        if not danger_ratings:
            continue

        # Gefahrenstufe: nimm den höchsten Wert wenn es zwei gibt (oben/unten)
        main_danger = danger_ratings[0].get("mainValue", "moderate")
        for dr in danger_ratings:
            d = dr.get("mainValue", "moderate")
            if DANGER_LABELS.get(d, {}).get("level", 0) > DANGER_LABELS.get(main_danger, {}).get("level", 0):
                main_danger = d

        for region in bulletin.get("regions", []):
            regions.append({
                "region_id":    region.get("regionID", ""),
                "region_name":  region.get("name", "Unbekannt"),
                "danger_key":   main_danger,
                "danger_level": DANGER_LABELS.get(main_danger, {}).get("level", 3),
                "danger_de":    DANGER_LABELS.get(main_danger, {}).get("de", "Erheblich"),
                "danger_color": DANGER_LABELS.get(main_danger, {}).get("color", "#FF9800"),
                "valid_until":  bulletin.get("validTime", {}).get("endTime", ""),
                "avalanche_problem": _extract_problem(bulletin),
            })
    return regions


def _extract_problem(bulletin: dict) -> str:
    problems = bulletin.get("avalancheProblems", [])
    if not problems:
        return "Keine Angabe"
    labels = {
        "new_snow":          "Neuschnee",
        "wind_slab":         "Triebschnee",
        "persistent_weak_layers": "Altschnee",
        "wet_snow":          "Nassschnee",
        "gliding_snow":      "Gleitschnee",
    }
    return ", ".join(labels.get(p.get("problemType", ""), p.get("problemType", "")) for p in problems[:2])


def _fallback_regions() -> list[dict]:
    """Fallback-Daten wenn die API nicht erreichbar ist (z.B. Sommer)."""
    return [
        {"region_id": "CH-7", "region_name": "Berner Oberland",    "danger_key": "moderate",     "danger_level": 2, "danger_de": "Mässig",    "danger_color": "#FFEB3B", "valid_until": "", "avalanche_problem": "Triebschnee"},
        {"region_id": "CH-8", "region_name": "Wallis",              "danger_key": "considerable", "danger_level": 3, "danger_de": "Erheblich", "danger_color": "#FF9800", "valid_until": "", "avalanche_problem": "Altschnee"},
        {"region_id": "CH-9", "region_name": "Graubünden",          "danger_key": "low",          "danger_level": 1, "danger_de": "Gering",    "danger_color": "#4CAF50", "valid_until": "", "avalanche_problem": "Keine Angabe"},
        {"region_id": "CH-1", "region_name": "Zentralschweiz",      "danger_key": "moderate",     "danger_level": 2, "danger_de": "Mässig",    "danger_color": "#FFEB3B", "valid_until": "", "avalanche_problem": "Neuschnee"},
    ]


def get_region_names(regions: list[dict]) -> list[str]:
    return sorted(set(r["region_name"] for r in regions))
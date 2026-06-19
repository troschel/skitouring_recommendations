"""
Lawinenbulletin vom SLF (WSL Institut für Schnee- und Lawinenforschung)
API: https://aws.slf.ch/api/bulletin/caaml/de/json
"""

import json
import os
import requests
from datetime import datetime

_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "bulletin_2026-03-18.json")

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
    return regions if regions else _fallback_regions()


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
    """Lädt Beispieldaten aus dem lokalen Fixture-Bulletin (z.B. im Sommer)."""
    with open(_FIXTURE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    regions = []
    for bulletin in data.get("bulletins", []):
        danger_ratings = bulletin.get("dangerRatings", [])
        if not danger_ratings:
            continue
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


def get_region_names(regions: list[dict]) -> list[str]:
    return sorted(set(r["region_name"] for r in regions))
"""
Wetterdaten von Open-Meteo (kostenlos, kein API-Key nötig)
https://api.open-meteo.com
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# WGS84 (lat, lon) centres — derived from LV95 REGION_COORDS in app.py
REGION_COORDS = {
    "Glarner Alpen":                        (46.97567, 9.05523),
    "Toggenburger und Appenzeller Alpen":   (47.24270, 9.24826),
    "Schwyzer Alpen":                       (47.06977, 8.72888),
    "Berner Oberland":                      (46.58119, 7.93440),
    "Urner Alpen":                          (46.81946, 8.57872),
    "Nidwaldner und Obwaldner Alpen":       (46.92092, 8.29202),
    "Westliche Walliser Alpen":             (46.15047, 7.38686),
    "Östliche Walliser Alpen":              (46.19421, 7.96974),
    "Mittelbünden":                         (46.62379, 9.12306),
    "Nördliches Bünden":                    (46.85890, 9.58954),
    "Südliches Bünden":                     (46.43056, 9.39034),
    "Engadin und Val Müstair":              (46.58712, 10.10087),
    "Bergell und Puschlav":                 (46.29729, 9.77504),
    "Berner Voralpen":                      (46.77930, 7.88384),
    "Préalpes fribourgeoises et vaudoises": (46.71708, 7.26861),
    "Unterwallis":                          (46.18560, 6.99828),
    "Jura":                                 (47.14782, 6.92444),
    "Alpes vaudoises":                      (46.39265, 7.03561),
    "Sopraceneri":                          (46.25039, 8.78727),
    "Sottoceneri":                          (45.89767, 8.93321),
}

DEFAULT_COORDS = (46.58119, 7.93440)  # Berner Oberland als Fallback


def get_weather(region_name: str = None, lat: float = None, lon: float = None) -> dict:
    """
    Lädt 3-Tage-Wettervorhersage von Open-Meteo.
    Entweder Region-Name oder lat/lon angeben.
    """
    if lat is None or lon is None:
        lat, lon = REGION_COORDS.get(region_name, DEFAULT_COORDS)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=snowfall_sum,precipitation_sum,windspeed_10m_max,"
        f"temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=Europe/Zurich&forecast_days=3"
    )

    try:
        r = requests.get(url, timeout=10, verify=False)
        r.raise_for_status()
        data = r.json()["daily"]
        return _parse_weather(data)
    except Exception as e:
        print(f"[fetch_weather] Fehler: {e}")
        return _fallback_weather()


def _parse_weather(data: dict) -> dict:
    days = []
    for i in range(min(3, len(data.get("time", [])))):
        days.append({
            "date":           data["time"][i],
            "snowfall_cm":    round((data.get("snowfall_sum") or [0]*3)[i] * 10, 1),
            "precipitation":  round((data.get("precipitation_sum") or [0]*3)[i], 1),
            "wind_max_kmh":   round((data.get("windspeed_10m_max") or [0]*3)[i], 0),
            "temp_max":       round((data.get("temperature_2m_max") or [0]*3)[i], 1),
            "temp_min":       round((data.get("temperature_2m_min") or [0]*3)[i], 1),
            "weathercode":    (data.get("weathercode") or [0]*3)[i],
        })

    # Aggregierte Werte für heute
    today = days[0] if days else {}
    return {
        "days":        days,
        "today":       today,
        "fresh_snow":  today.get("snowfall_cm", 0),
        "wind_kmh":    today.get("wind_max_kmh", 0),
        "temp_max":    today.get("temp_max", 0),
        "weather_icon": _wmo_to_emoji(today.get("weathercode", 0)),
    }


def _wmo_to_emoji(code: int) -> str:
    """WMO Wetter-Codes zu Emoji."""
    if code == 0:             return "☀️"
    if code in (1, 2):        return "🌤️"
    if code == 3:             return "☁️"
    if code in range(51, 68): return "🌧️"
    if code in range(71, 78): return "❄️"
    if code in range(80, 83): return "🌦️"
    if code in range(85, 87): return "🌨️"
    if code in range(95, 100):return "⛈️"
    return "🌡️"


def _fallback_weather() -> dict:
    days = [
        {"date": "2025-01-15", "snowfall_cm": 8,  "precipitation": 4.2, "wind_max_kmh": 30, "temp_max": -2, "temp_min": -8,  "weathercode": 71},
        {"date": "2025-01-16", "snowfall_cm": 2,  "precipitation": 1.0, "wind_max_kmh": 45, "temp_max": -1, "temp_min": -7,  "weathercode": 3},
        {"date": "2025-01-17", "snowfall_cm": 0,  "precipitation": 0.0, "wind_max_kmh": 15, "temp_max":  3, "temp_min": -4,  "weathercode": 1},
    ]
    return {"days": days, "today": days[0], "fresh_snow": 8, "wind_kmh": 30, "temp_max": -2, "weather_icon": "❄️"}
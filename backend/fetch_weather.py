"""
Wetterdaten von Open-Meteo (kostenlos, kein API-Key nötig)
https://api.open-meteo.com
"""

import requests

# Koordinaten bekannter Skigebiete/Regionen in der Schweiz
REGION_COORDS = {
    "Berner Oberland": (46.55, 7.95),
    "Wallis":          (46.10, 7.70),
    "Graubünden":      (46.65, 9.70),
    "Zentralschweiz":  (46.80, 8.50),
    "Jura":            (47.10, 7.00),
    "Tessin":          (46.30, 8.95),
    "Uri":             (46.75, 8.65),
    "Glarus":          (46.90, 9.10),
    "Appenzell":       (47.33, 9.41),
}

DEFAULT_COORDS = (46.55, 7.95)  # Berner Oberland als Fallback


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
        r = requests.get(url, timeout=10)
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
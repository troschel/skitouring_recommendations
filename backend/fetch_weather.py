# fetch_weather.py
import requests

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=snowfall_sum,precipitation_sum,windspeed_10m_max"
        f"&timezone=Europe/Zurich&forecast_days=3"
    )
    response = requests.get(url)
    return response.json()["daily"]
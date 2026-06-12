# fetch_avalanche.py
import requests

def get_avalanche_bulletin():
    url = "https://aws.slf.ch/api/bulletin/caaml/de/json"
    response = requests.get(url)
    data = response.json()
    # Gefahrenstufen pro Region extrahieren
    bulletins = data["bulletins"]
    regions = []
    for b in bulletins:
        regions.append({
            "region_id": b["regions"][0]["regionID"],
            "danger_level": b["dangerRatings"][0]["mainValue"],  # low/moderate/considerable/high/very_high
            "valid_until": b["validTime"]["endTime"]
        })
    return regions
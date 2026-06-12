# fetch_routes.py
import requests

def get_ski_routes(bbox="5.9,45.8,10.5,47.8"):
    url = (
        "https://api3.geo.admin.ch/rest/services/api/MapServer/find"
        f"?layer=ch.swisstopo-karto.skitouren&searchText=&bbox={bbox}"
        "&sr=4326&contains=true&geometryFormat=geojson"
    )
    response = requests.get(url)
    return response.json()
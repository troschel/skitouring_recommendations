# Skitouren-Empfehlungen Schweiz

A Streamlit app that recommends Swiss ski touring and snowshoeing routes based on current avalanche conditions, weather, and your chosen difficulty level.

## Features

- **Activity selector** — switch between ski touring (SAC Skitourenskala: L / WS / ZS / S / SS / AS / EX) and snowshoeing (SAC Schneeschuhtourenskala: WT1–WT5)
- **Avalanche bulletin** — fetches the current SLF bulletin live; falls back to a stored fixture in summer or when the API is unavailable
- **Weather input** — manual entry for fresh snow, wind speed, and temperature
- **Recommendation engine** — scores the outing based on danger level, difficulty, weather, and avalanche problem type
- **Interactive map** — swisstopo winter basemap (WMTS) with overlays for ski/snowshoe routes, slopes ≥ 30°, and wildlife protection zones
- **Route list** — suggested routes filtered to your region and difficulty, with ascent, time, and a link to the swisstopo route page
- **Highlighted routes** — suggested routes drawn as orange polylines on the map with hover tooltips

## Data sources

| Data | Source |
|---|---|
| Avalanche bulletin | [SLF API](https://aws.slf.ch/api/bulletin/caaml/de/json) |
| Weather | User input |
| Ski touring routes | swisstopo GeoPackage `ch.swisstopo-karto.skitouren` (via STAC API) |
| Snowshoe routes | swisstopo GeoPackage `ch.astra.schneeschuhwanderwege` (via STAC API) |
| Map tiles | [geo.admin.ch WMTS](https://wmts.geo.admin.ch) |

## Setup

```bash
git clone https://github.com/troschel/skitouring_recommendations.git
cd skitouring_recommendations
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
app.py                              Main Streamlit app
backend/
  fetch_avalanche.py                SLF bulletin fetcher with fixture fallback
  fetch_routes.py                   Route lookup from pre-processed fixtures
  fetch_weather.py                  Weather helpers
  geometry.py                       GeoPackage WKB parser + LV95→WGS84 converter
  recommender.py                    Scoring and recommendation logic
  fixtures/
    bulletin_2026-03-18.json        Off-season fixture bulletin (from SLF PDF)
    skitouren_by_region.json        2 558 ski touring routes indexed by region
    schneeschuh_by_region.json      259 snowshoe routes indexed by region
  data/
    ski_routes_2056.gpkg            Source geometry (swisstopo, LV95/EPSG:2056)
    schneeschuh_2056.gpkg           Source geometry (ASTRA, LV95/EPSG:2056)
```

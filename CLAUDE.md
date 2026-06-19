# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

Swiss ski touring recommendation app. Given a region and user-defined difficulty tolerance, it combines live avalanche bulletins, weather forecasts, and SAC difficulty ratings to produce a scored go/no-go recommendation.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app (entry point not yet created — expected at app.py or streamlit_app.py)
streamlit run app.py
```

No test suite exists yet. Backend modules can be exercised directly:

```bash
python -c "from backend.fetch_avalanche import get_avalanche_bulletin; print(get_avalanche_bulletin())"
python -c "from backend.fetch_weather import get_weather; print(get_weather('Wallis'))"
```

## Architecture

The project is a Streamlit app with a pure-Python backend (no database, no auth).

### Data flow

1. **`backend/fetch_avalanche.py`** — fetches the current SLF avalanche bulletin from `aws.slf.ch/api/bulletin/caaml/de/json`. Returns a list of region dicts with `danger_key` (low/moderate/considerable/high/very_high), numeric `danger_level` (1–5), and `avalanche_problem` (German label). Falls back to hardcoded sample data when the API is unreachable (common in summer).

2. **`backend/fetch_weather.py`** — fetches a 3-day forecast from Open-Meteo (no API key required) for a named Swiss region or explicit lat/lon. Returns aggregated `fresh_snow`, `wind_kmh`, `temp_max`, and a WMO-code emoji for today, plus a `days` list for the 3-day view. Has its own hardcoded fallback.

3. **`backend/fetch_routes.py`** — queries the swisstopo geo.admin.ch API for official ski touring routes in Switzerland (GeoJSON). Currently returns raw API JSON; not yet integrated into the recommendation flow.

4. **`backend/recommender.py`** — the core scoring engine. Takes a `TourInput` dataclass (region data + user preferences) and returns a `RecommendationResult` with a 0–100 score, a verdict (`Empfohlen` / `Bedingt empfohlen` / `Nicht empfohlen`), and lists of positive/negative reasons and safety tips. Scoring factors in order of weight: avalanche danger vs. user maximum → difficulty vs. danger level → avalanche problem type → fresh snow → wind → temperature.

### Key constants

- **SAC WT difficulty scale**: `DIFFICULTY_INFO` in `recommender.py` maps WT1–WT5 to safe danger-level thresholds.
- **Region coordinates**: `REGION_COORDS` in `fetch_weather.py` maps region names to lat/lon; extend this dict when adding regions.
- **Danger labels**: `DANGER_LABELS` in `fetch_avalanche.py` maps SLF API strings to German labels and hex colors.

### Language

Code comments, variable names, and user-facing strings are in German (Swiss alpine domain). Keep new user-facing text in German.

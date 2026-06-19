import streamlit as st
import folium
from streamlit_folium import st_folium
from backend.fetch_avalanche import get_avalanche_bulletin, get_region_names
from backend.fetch_weather import get_weather
from backend.recommender import TourInput, recommend, SKI_DIFFICULTY_INFO, SNOWSHOE_DIFFICULTY_INFO
from backend.fetch_routes import get_ski_routes, get_snowshoe_routes
from backend.geometry import get_ski_geometries, get_snow_geometries, lv95_to_wgs84

# Approximate LV95 (EPSG:2056) center coordinates per region
REGION_COORDS = {
    "Glarner Alpen":                        (2723000, 1204000),
    "Toggenburger und Appenzeller Alpen":   (2737000, 1234000),
    "Schwyzer Alpen":                       (2698000, 1214000),
    "Berner Oberland":                      (2638000, 1159000),
    "Urner Alpen":                          (2687000, 1186000),
    "Nidwaldner und Obwaldner Alpen":       (2665000, 1197000),
    "Westliche Walliser Alpen":             (2596000, 1111000),
    "Östliche Walliser Alpen":              (2641000, 1116000),
    "Mittelbünden":                         (2729000, 1165000),
    "Nördliches Bünden":                    (2764000, 1192000),
    "Südliches Bünden":                     (2750000, 1144000),
    "Engadin und Val Müstair":              (2804000, 1163000),
    "Bergell und Puschlav":                 (2780000, 1130000),
    "Berner Voralpen":                      (2634000, 1181000),
    "Préalpes fribourgeoises et vaudoises": (2587000, 1174000),
    "Unterwallis":                          (2566000, 1115000),
    "Jura":                                 (2561000, 1222000),
    "Alpes vaudoises":                      (2569000, 1138000),
    "Sopraceneri":                          (2704000, 1123000),
    "Sottoceneri":                          (2716000, 1084000),
}

st.set_page_config(
    page_title="Skitouren Empfehlungen",
    page_icon="⛷️",
    layout="wide",
)

st.title("⛷️ Schweizer Skitouren-Empfehlungen")
st.caption("Aktuelle Lawinenbulletins, Wetter und SAC-Schwierigkeitsgrade kombiniert.")

# ── Daten laden ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def load_bulletin():
    return get_avalanche_bulletin()

@st.cache_data(ttl=1800)
def load_weather(region_name: str):
    return get_weather(region_name)

with st.spinner("Lawinenbulletin wird geladen…"):
    regions = load_bulletin()

if not regions:
    st.error("Lawinenbulletin konnte nicht geladen werden. Bitte später erneut versuchen.")
    st.stop()

region_map = {r["region_name"]: r for r in regions}
region_names = sorted(region_map.keys())

# ── Sidebar: Benutzereinstellungen ─────────────────────────────────────────────

with st.sidebar:
    st.header("Einstellungen")

    selected_region = st.selectbox("Region", region_names)

    activity = st.radio(
        "Aktivität",
        options=["skitouring", "snowshoeing"],
        format_func=lambda a: "Skitour" if a == "skitouring" else "Schneeschuhtour",
        horizontal=True,
    )

    difficulty_info = SKI_DIFFICULTY_INFO if activity == "skitouring" else SNOWSHOE_DIFFICULTY_INFO
    scale_label = "Schwierigkeitsgrad (SAC Skitourenskala)" if activity == "skitouring" else "Schwierigkeitsgrad (SAC WT-Skala)"

    difficulty = st.selectbox(
        scale_label,
        options=list(difficulty_info.keys()),
        format_func=lambda k: difficulty_info[k]["label"],
    )

    max_danger = st.slider(
        "Maximale Lawinengefahr",
        min_value=1,
        max_value=5,
        value=3,
        help="1 = Gering, 2 = Mässig, 3 = Erheblich, 4 = Gross, 5 = Sehr gross",
    )

    st.divider()
    if st.button("🔄 Daten aktualisieren", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Aktuelle Bedingungen ───────────────────────────────────────────────────────

region_data = region_map[selected_region]
weather = load_weather(selected_region)
today = weather.get("today", {})

st.subheader(f"Aktuelle Bedingungen – {selected_region}")

col_av, col_snow, col_wind, col_temp = st.columns(4)

danger_color = region_data["danger_color"]
danger_level = region_data["danger_level"]
danger_de = region_data["danger_de"]

with col_av:
    st.metric("Lawinengefahr", f"{danger_level} – {danger_de}")
    st.markdown(
        f'<div style="background:{danger_color};border-radius:6px;height:8px;"></div>',
        unsafe_allow_html=True,
    )

with col_snow:
    st.metric("Neuschnee heute", f"{weather.get('fresh_snow', 0):.0f} cm")

with col_wind:
    st.metric("Wind max.", f"{weather.get('wind_kmh', 0):.0f} km/h")

with col_temp:
    icon = weather.get("weather_icon", "")
    st.metric("Temperatur max.", f"{weather.get('temp_max', 0):.1f} °C", delta=icon)

# 3-Tages-Vorschau
with st.expander("3-Tages-Wettervorschau"):
    days = weather.get("days", [])
    if days:
        cols = st.columns(len(days))
        for i, (col, day) in enumerate(zip(cols, days)):
            label = "Heute" if i == 0 else ("Morgen" if i == 1 else "Übermorgen")
            with col:
                st.markdown(f"**{label}** ({day['date']})")
                st.write(f"❄️ Schnee: {day['snowfall_cm']} cm")
                st.write(f"💨 Wind: {day['wind_max_kmh']:.0f} km/h")
                st.write(f"🌡️ {day['temp_min']}° / {day['temp_max']}°C")

# Lawinenproblem
problem = region_data.get("avalanche_problem", "Keine Angabe")
if region_data.get("valid_until"):
    st.caption(f"Lawinenprobleme: **{problem}** · Bulletin gültig bis: {region_data['valid_until'][:10]}")
else:
    st.caption(f"Lawinenprobleme: **{problem}**")

st.divider()

# ── Empfehlung berechnen ───────────────────────────────────────────────────────

inp = TourInput(
    region_name=selected_region,
    danger_level=danger_level,
    danger_key=region_data["danger_key"],
    avalanche_prob=problem,
    fresh_snow_cm=weather.get("fresh_snow", 0),
    wind_kmh=weather.get("wind_kmh", 0),
    temp_max=weather.get("temp_max", 0),
    difficulty=difficulty,
    max_danger=max_danger,
    activity=activity,
)

result = recommend(inp)

# ── Ergebnis anzeigen ──────────────────────────────────────────────────────────

st.subheader("Empfehlung")

col_verdict, col_score = st.columns([2, 1])

with col_verdict:
    st.markdown(
        f'<h2 style="color:{result.verdict_color}">'
        f'{result.verdict_emoji} {result.verdict}</h2>',
        unsafe_allow_html=True,
    )

with col_score:
    st.metric("Score", f"{result.score} / 100")
    st.progress(result.score / 100)

col_pos, col_neg = st.columns(2)

with col_pos:
    if result.reasons_pos:
        st.markdown("**✅ Positive Faktoren**")
        for r in result.reasons_pos:
            st.markdown(f"- {r}")

with col_neg:
    if result.reasons_neg:
        st.markdown("**⚠️ Warnungen**")
        for r in result.reasons_neg:
            st.markdown(f"- {r}")

if result.tips:
    with st.expander("🛡️ Sicherheitstipps"):
        for tip in result.tips:
            st.markdown(f"- {tip}")

st.divider()

# ── Karte ──────────────────────────────────────────────────────────────────────

st.subheader(f"Karte – {selected_region}")

easting, northing = REGION_COORDS.get(selected_region, (2660000, 1190000))
center_lon, center_lat = lv95_to_wgs84(easting, northing)

# Fetch geometries for the displayed routes
if activity == "skitouring":
    map_routes = get_ski_routes(selected_region, difficulty)
    fids = [r["fid"] for r in map_routes]
    geom_map = get_ski_geometries(fids)
    route_layer_id = "ch.swisstopo-karto.skitouren"
    extra_layer_id = "ch.swisstopo.bahnen-winter"
    extra_layer_name = "Bahnen & Skilifte"
else:
    map_routes = get_snowshoe_routes(selected_region, difficulty)
    fids = [r["fid"] for r in map_routes]
    geom_map = get_snow_geometries(fids)
    route_layer_id = "ch.swisstopo-karto.schneeschuhrouten"
    extra_layer_id = None
    extra_layer_name = None

def wmts(layer, ext="png"):
    return f"https://wmts.geo.admin.ch/1.0.0/{layer}/default/current/3857/{{z}}/{{x}}/{{y}}.{ext}"

m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles=None)

folium.TileLayer(wmts("ch.swisstopo.pixelkarte-farbe-winter", "jpeg"),
    attr="© swisstopo", name="Swisstopo Winter").add_to(m)
folium.TileLayer(wmts(route_layer_id),
    attr="© swisstopo", name="Routen", overlay=True).add_to(m)
folium.TileLayer(wmts("ch.swisstopo.hangneigung-ueber_30"),
    attr="© swisstopo", name="Hangneigung ≥30°", overlay=True, opacity=0.5).add_to(m)
folium.TileLayer(wmts("ch.bafu.wrz-wildruhezonen_portal"),
    attr="© BAFU", name="Wildruhezonen", overlay=True, opacity=0.65).add_to(m)
if extra_layer_id:
    folium.TileLayer(wmts(extra_layer_id),
        attr="© swisstopo", name=extra_layer_name, overlay=True).add_to(m)

# Highlighted suggested routes
for r in map_routes:
    coords = geom_map.get(r["fid"], [])
    if not coords:
        continue
    label = r.get("target") or r.get("name", "")
    folium.PolyLine(
        locations=[[c[1], c[0]] for c in coords],  # folium: [lat, lon]
        color="#FF5000",
        weight=4,
        opacity=0.9,
        tooltip=f"{label} – {r['difficulty']}",
    ).add_to(m)

folium.LayerControl().add_to(m)
st_folium(m, use_container_width=True, height=500, returned_objects=[])

st.divider()

# ── Passende Routen ────────────────────────────────────────────────────────────

if activity == "skitouring":
    st.subheader(f"Passende Skitouren – {selected_region}")
    routes = get_ski_routes(selected_region, difficulty)
    if not routes:
        st.info("Keine Routen für diese Region und Schwierigkeitsstufe gefunden.")
    else:
        st.caption(
            f"{len(routes)} Route(n) bis **{difficulty_info[difficulty]['label']}** "
            f"in {selected_region} (sortiert nach Schwierigkeit)"
        )
        for r in routes:
            with st.expander(f"**{r['target']}** – {r['name']} · {r['difficulty']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Schwierigkeit", r["difficulty"])
                col2.metric("Aufstieg", f"{r['ascent_m']} m" if r["ascent_m"] else "–")
                col3.metric("Gipfel", f"{r['target_alt']} m" if r["target_alt"] else "–")
                st.write(f"⏱️ {r['time']}" if r["time"] else "")
                if r["url"]:
                    st.markdown(f"[SAC Tourenportal ↗]({r['url']})")

else:
    st.subheader(f"Passende Schneeschuhtouren – {selected_region}")
    routes = get_snowshoe_routes(selected_region, difficulty)
    if not routes:
        st.info("Keine Routen für diese Region und Schwierigkeitsstufe gefunden.")
    else:
        st.caption(
            f"{len(routes)} Route(n) bis **{difficulty_info[difficulty]['label']}** "
            f"in {selected_region} (sortiert nach Schwierigkeit)"
        )
        for r in routes:
            label = f"**{r['name']}** · {r['difficulty']} ({r['diff_color']})"
            with st.expander(label):
                col1, col2, col3 = st.columns(3)
                col1.metric("Schwierigkeit", f"{r['difficulty']} ({r['diff_color']})")
                col2.metric("Aufstieg", f"{r['ascent_m']} m" if r["ascent_m"] else "–")
                col3.metric("Distanz", f"{r['length_km']} km" if r["length_km"] else "–")
                if r["start"] or r["end"]:
                    st.write(f"📍 {r['start']} → {r['end']}" if r["start"] != r["end"] else f"📍 {r['start']}")
                st.write(f"⏱️ {r['time']}" if r["time"] else "")
                if r["url"]:
                    st.markdown(f"[SchweizMobil ↗]({r['url']})")

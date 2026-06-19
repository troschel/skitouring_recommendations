"""
Empfehlungslogik für Schweizer Skitouren und Schneeschuhtouren.
Kombiniert Lawinengefahr, Wetter und Schwierigkeit zu einem Score.
"""

from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────────────────────
# Datenmodell
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TourInput:
    region_name:    str
    danger_level:   int       # 1–5
    danger_key:     str       # "low" | "moderate" | ...
    avalanche_prob: str       # z.B. "Triebschnee"
    fresh_snow_cm:  float     # Neuschnee heute in cm
    wind_kmh:       float     # Windgeschwindigkeit km/h
    temp_max:       float     # Temperatur Maximum °C
    difficulty:     str       # z.B. "WS", "ZS" oder "WT1", "WT2"
    max_danger:     int       # vom Benutzer gewählte max. Lawinengefahr (1–5)
    activity:       str = "skitouring"  # "skitouring" | "snowshoeing"


@dataclass
class RecommendationResult:
    score:          int        # 0–100
    verdict:        str        # "Empfohlen" | "Bedingt" | "Nicht empfohlen"
    verdict_color:  str        # hex
    verdict_emoji:  str
    reasons_pos:    list[str]  # positive Faktoren
    reasons_neg:    list[str]  # negative Faktoren / Warnungen
    tips:           list[str]  # Sicherheitstipps


# ──────────────────────────────────────────────────────────────────────────────
# SAC Schwierigkeitsgrade
# ──────────────────────────────────────────────────────────────────────────────

# SAC Skitourenskala (L / WS / ZS / S / SS / AS / EX)
# Quelle: SAC Schwierigkeitsskala für Skitouren, Bern September 2012
SKI_DIFFICULTY_INFO = {
    "L":  {"label": "L – Leicht",                       "max_safe_danger": 3, "slope": "bis 30°"},
    "WS": {"label": "WS – Wenig schwierig",             "max_safe_danger": 3, "slope": "ab 30°"},
    "ZS": {"label": "ZS – Ziemlich schwierig",          "max_safe_danger": 3, "slope": "ab 35°"},
    "S":  {"label": "S – Schwierig",                    "max_safe_danger": 2, "slope": "ab 40°"},
    "SS": {"label": "SS – Sehr schwierig",              "max_safe_danger": 2, "slope": "ab 45°"},
    "AS": {"label": "AS – Ausserordentlich schwierig",  "max_safe_danger": 1, "slope": "ab 50°"},
    "EX": {"label": "EX – Extrem schwierig",            "max_safe_danger": 1, "slope": "ab 55°"},
}

# SAC Schneeschuhtourenskala (WT1–WT5)
SNOWSHOE_DIFFICULTY_INFO = {
    "WT1": {"label": "WT1 – Leicht",            "max_safe_danger": 3},
    "WT2": {"label": "WT2 – Wenig schwierig",   "max_safe_danger": 3},
    "WT3": {"label": "WT3 – Ziemlich schwierig","max_safe_danger": 2},
    "WT4": {"label": "WT4 – Schwierig",         "max_safe_danger": 2},
    "WT5": {"label": "WT5 – Sehr schwierig",    "max_safe_danger": 1},
}

DIFFICULTY_INFO = SNOWSHOE_DIFFICULTY_INFO  # Rückwärtskompatibilität


# ──────────────────────────────────────────────────────────────────────────────
# Hauptfunktion
# ──────────────────────────────────────────────────────────────────────────────

def recommend(inp: TourInput) -> RecommendationResult:
    score = 50  # Ausgangspunkt
    reasons_pos = []
    reasons_neg = []
    tips = []

    difficulty_table = SKI_DIFFICULTY_INFO if inp.activity == "skitouring" else SNOWSHOE_DIFFICULTY_INFO
    fallback = "WS" if inp.activity == "skitouring" else "WT2"
    diff_info = difficulty_table.get(inp.difficulty, difficulty_table[fallback])

    # ── 1. Lawinengefahr (höchste Gewichtung) ─────────────────────────────────
    if inp.danger_level > inp.max_danger:
        score -= 40
        reasons_neg.append(
            f"Lawinengefahr {inp.danger_level} überschreitet dein Maximum ({inp.max_danger})"
        )
    elif inp.danger_level == 1:
        score += 20
        reasons_pos.append("Geringe Lawinengefahr – gute Voraussetzungen")
    elif inp.danger_level == 2:
        score += 10
        reasons_pos.append("Mässige Lawinengefahr – bei Beachtung der Verhältnisse vertretbar")
    elif inp.danger_level == 3:
        score -= 10
        reasons_neg.append("Erhebliche Lawinengefahr – erhöhte Vorsicht nötig")
        tips.append("Kritische Steilhänge (> 30°) meiden, besonders Hänge unter Wächten")
    elif inp.danger_level == 4:
        score -= 25
        reasons_neg.append("Grosse Lawinengefahr – Tour nur für Experten")
        tips.append("Nur auf flachen, lawinensicheren Routen unterwegs sein")
    else:
        score -= 40
        reasons_neg.append("Sehr grosse Lawinengefahr – Tourenabbruch empfohlen")

    # ── 2. Schwierigkeit vs. Lawinensituation ────────────────────────────────
    safe_max = diff_info["max_safe_danger"]
    if inp.danger_level > safe_max:
        score -= 15
        reasons_neg.append(
            f"{diff_info['label']}: empfohlen bis Gefahrenstufe {safe_max}, aktuell {inp.danger_level}"
        )
        tips.append("Einfachere Route oder Alternativziel wählen")
    else:
        score += 5
        reasons_pos.append(f"Schwierigkeit {inp.difficulty} passend zur aktuellen Gefahrenlage")

    # ── 3. Lawinenproblem ────────────────────────────────────────────────────
    if "Triebschnee" in inp.avalanche_prob:
        score -= 8
        reasons_neg.append("Triebschneeproblem – windabgewandte Hänge und Mulden meiden")
        tips.append("Vor der Tour Windexposition der Route prüfen")
    if "Altschnee" in inp.avalanche_prob:
        score -= 10
        reasons_neg.append("Altschneeproblem – schwer beurteilbar, besondere Vorsicht")
        tips.append("Ungünstige Expositionen (schattig, NW–NO) meiden")
    if "Nassschnee" in inp.avalanche_prob:
        score -= 6
        reasons_neg.append("Nassschneeproblem – früher Start, vor Erwärmung abstieg")
        tips.append("Frühzeitig umkehren wenn Schnee aufweicht")

    # ── 4. Neuschnee ─────────────────────────────────────────────────────────
    if inp.fresh_snow_cm >= 20:
        score += 15
        reasons_pos.append(f"Viel Neuschnee: {inp.fresh_snow_cm} cm – Pulver pur!")
        if inp.danger_level >= 3:
            tips.append("Neuschnee erhöht Lawinengefahr – trotz Frischschnee vorsichtig sein")
    elif inp.fresh_snow_cm >= 5:
        score += 8
        reasons_pos.append(f"Frischer Schnee: {inp.fresh_snow_cm} cm")
    elif inp.fresh_snow_cm == 0:
        score -= 3
        reasons_neg.append("Kein Neuschnee erwartet – möglicherweise windgepresster Schnee")

    # ── 5. Wind ──────────────────────────────────────────────────────────────
    if inp.wind_kmh > 70:
        score -= 20
        reasons_neg.append(f"Starker Wind: {inp.wind_kmh:.0f} km/h – Gipfel unzumutbar")
        tips.append("Windexponierte Grate und Gipfelpartien meiden")
    elif inp.wind_kmh > 50:
        score -= 10
        reasons_neg.append(f"Mässig starker Wind: {inp.wind_kmh:.0f} km/h")
        tips.append("Windchill einkalkulieren, Schutzkleidung mitführen")
    elif inp.wind_kmh > 30:
        score -= 3
        reasons_neg.append(f"Leichter Wind: {inp.wind_kmh:.0f} km/h – im Grat störend")
    else:
        score += 8
        reasons_pos.append(f"Ruhige Windbedingungen: {inp.wind_kmh:.0f} km/h")

    # ── 6. Temperatur ─────────────────────────────────────────────────────────
    if inp.temp_max > 5:
        score -= 5
        reasons_neg.append(f"Warm: {inp.temp_max}°C – Nassschneelawinenrisiko am Nachmittag")
        tips.append("Früh starten, spätestens mittags im Abstieg sein")
    elif -15 <= inp.temp_max <= 0:
        score += 5
        reasons_pos.append(f"Ideale Temperatur: {inp.temp_max}°C")
    elif inp.temp_max < -15:
        reasons_neg.append(f"Sehr kalt: {inp.temp_max}°C – Erfrierungsgefahr")
        tips.append("Extremer Kälteschutz zwingend, Finger/Zehen im Auge behalten")

    # ── Score normalisieren ───────────────────────────────────────────────────
    score = max(0, min(100, score))

    # ── Automatische Sicherheitstipps ─────────────────────────────────────────
    tips += _base_safety_tips(inp)

    # ── Urteil ────────────────────────────────────────────────────────────────
    if score >= 60 and inp.danger_level <= inp.max_danger:
        verdict, color, emoji = "Empfohlen",          "#2E7D32", "✅"
    elif score >= 35:
        verdict, color, emoji = "Bedingt empfohlen",  "#E65100", "⚠️"
    else:
        verdict, color, emoji = "Nicht empfohlen",    "#B71C1C", "❌"

    return RecommendationResult(
        score=score,
        verdict=verdict,
        verdict_color=color,
        verdict_emoji=emoji,
        reasons_pos=reasons_pos,
        reasons_neg=reasons_neg,
        tips=list(dict.fromkeys(tips)),  # deduplizieren, Reihenfolge behalten
    )


def _base_safety_tips(inp: TourInput) -> list[str]:
    tips = []
    if inp.danger_level >= 2:
        tips.append("LVS-Gerät, Sonde und Schaufel sind Pflicht")
        tips.append("Tourenplanung mit Kameraden besprechen, Rückzugsoptionen festlegen")
    if inp.activity == "skitouring" and inp.difficulty in ("S", "SS", "AS", "EX"):
        tips.append("Nur mit sehr erfahrenen Skialpinisten – sichere Spitzkehren und Quersprünge Voraussetzung")
    if inp.activity == "snowshoeing" and inp.difficulty in ("WT4", "WT5"):
        tips.append("Nur mit sehr erfahrenen Begleitpersonen und Alpinkenntnissen")
    tips.append("Aktuelles SLF-Bulletin kurz vor Tourenbeginn nochmals prüfen: slf.ch")
    return tips
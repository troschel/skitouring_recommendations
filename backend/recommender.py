# main_code.py
def recommend_tour(route, avalanche_level, weather, difficulty_filter="WT2"):
    score = 0
    reasons = []

    # Lawinengefahr (1=gering, 5=sehr gross)
    danger_map = {"low": 1, "moderate": 2, "considerable": 3, "high": 4, "very_high": 5}
    danger = danger_map.get(avalanche_level, 3)

    if danger <= 2:
        score += 3
        reasons.append("✅ Lawinengefahr gering")
    elif danger == 3:
        score += 1
        reasons.append("⚠️ Erhebliche Lawinengefahr")
    else:
        score -= 3
        reasons.append("❌ Hohe Lawinengefahr")

    # Wetter
    if weather["snowfall_sum"][0] > 5:
        score += 1
        reasons.append("✅ Frischer Schnee")
    if weather["windspeed_10m_max"][0] > 60:
        score -= 2
        reasons.append("❌ Starker Wind")

    return {"score": score, "empfehlung": score >= 3, "gruende": reasons}
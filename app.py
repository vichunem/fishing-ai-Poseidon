import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import math

st.set_page_config(page_title="Fishing AI Poseidon", page_icon="🎣")

AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# =========================
# 月齢
# =========================
def moon_phase():
    diff = datetime.utcnow() - datetime(2001,1,1)
    days = diff.days + (diff.seconds/86400)
    lunations = 0.20439731 + (days * 0.03386319269)
    return (lunations % 1) * 29.53

def moon_score():
    phase = moon_phase()
    if phase < 2 or phase > 27: return 20
    if 13 < phase < 16: return 20
    return 10

# =========================
# 海況取得（日本時間）
# =========================
@st.cache_data(ttl=600)
def get_data(lat, lon):
    marine = requests.get(
        f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,sea_surface_temperature&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m,windgusts_10m,surface_pressure&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    hour = datetime.now().hour

    return {
        "wave": marine["hourly"]["wave_height"][hour],
        "temp": marine["hourly"]["sea_surface_temperature"][hour],
        "wind": weather["hourly"]["windspeed_10m"][hour],
        "gust": weather["hourly"]["windgusts_10m"][hour],
        "pressure": weather["hourly"]["surface_pressure"][hour]
    }

# =========================
# BI近似ロジック
# =========================
def calculate_bi(sea, tide):
    score = 0

    # 波
    if 0.8 <= sea["wave"] <= 2.0:
        score += 20
    elif sea["wave"] > 2.5:
        score -= 10

    # 風（強すぎは減点）
    if 3 <= sea["wind"] <= 7:
        score += 15
    if sea["gust"] > 12:
        score -= 10

    # 気圧（1008〜1018が理想）
    if 1008 <= sea["pressure"] <= 1018:
        score += 20
    else:
        score += 5

    # 水温（12〜22が安定）
    if 12 <= sea["temp"] <= 22:
        score += 15

    # 潮位
    if tide == "上げ":
        score += 10

    # 月齢
    score += moon_score()

    return max(0, min(score, 100))

# =========================
# UI
# =========================
st.title("🎣 Fishing AI Poseidon – BI近似版")

tide = st.selectbox("潮位", ["上げ","下げ"])

for area,coords in AREAS.items():
    sea = get_data(*coords)
    bi = calculate_bi(sea, tide)

    st.subheader(area)
    st.metric("BI近似指数", f"{bi}")

    st.caption(
        f"波:{round(sea['wave'],1)}m "
        f"風:{round(sea['wind'],1)}m/s "
        f"最大:{round(sea['gust'],1)}m/s "
        f"気圧:{round(sea['pressure'],1)}hPa "
        f"水温:{round(sea['temp'],1)}℃ "
        f"月齢:{round(moon_phase(),1)}"
    )

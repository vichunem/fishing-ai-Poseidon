import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="POSEIDON")

# =====================
# タイトル
# =====================
st.markdown("""
<style>
.gold-title {
    font-size:48px;
    font-weight:900;
    text-align:center;
}
.sub-title {
    font-size:20px;
    text-align:center;
    margin-bottom:30px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='gold-title'>POSEIDON</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>－海の支配者－</div>", unsafe_allow_html=True)

# =====================
# データ保存
# =====================
DATA_FILE = "history.csv"

def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "日付","エリア","魚種","匹数","ルアー種類","カラー"
    ])

def save_history(df):
    df.to_csv(DATA_FILE, index=False)

history = load_history()

AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# =====================
# 月齢
# =====================
def moon_phase():
    diff = datetime.utcnow() - datetime(2001,1,1)
    days = diff.days + diff.seconds/86400
    lun = 0.20439731 + days*0.03386319269
    return (lun % 1) * 29.53

def moon_score():
    phase = moon_phase()
    if phase < 2 or phase > 27:
        return 15
    if 13 < phase < 16:
        return 15
    return 5

# =====================
# 海況取得
# =====================
@st.cache_data(ttl=600)
def get_data(lat, lon):
    marine = requests.get(
        f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,sea_surface_temperature&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m,windgusts_10m,winddirection_10m,surface_pressure&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    h = datetime.now().hour

    return {
        "wave": marine["hourly"]["wave_height"][h],
        "temp": marine["hourly"]["sea_surface_temperature"][h],
        "wind": weather["hourly"]["windspeed_10m"][h],
        "gust": weather["hourly"]["windgusts_10m"][h],
        "wind_dir": weather["hourly"]["winddirection_10m"][h],
        "pressure": weather["hourly"]["surface_pressure"][h]
    }

# =====================
# スコア
# =====================
def base_score(sea, tide):
    score = 0

    if 0.8 <= sea["wave"] <= 2.0:
        score += 20

    if 3 <= sea["wind"] <= 8:
        score += 15

    if sea["gust"] > 15:
        score -= 10

    if 250 <= sea["wind_dir"] <= 320:
        score += 10

    if 1008 <= sea["pressure"] <= 1018:
        score += 15

    if tide == "上げ":
        score += 10

    score += moon_score()

    return max(5, min(score, 95))

import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

st.set_page_config(page_title="Fishing AI Poseidon", page_icon="🎣")

DATA_FILE = "fishing_data.csv"

# ===============================
# エリア座標（リアル取得用）
# ===============================
AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# ===============================
# 海況取得（Open-Meteo）
# ===============================
@st.cache_data(ttl=900)
def get_sea(lat, lon):
    marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,sea_surface_temperature&forecast_days=1"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m&forecast_days=1"

    marine = requests.get(marine_url).json()
    weather = requests.get(weather_url).json()

    hour = datetime.utcnow().hour

    return {
        "wave": marine["hourly"]["wave_height"][hour],
        "temp": marine["hourly"]["sea_surface_temperature"][hour],
        "wind": weather["hourly"]["windspeed_10m"][hour],
    }

# ===============================
# 過去データ読み込み
# ===============================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["日付","エリア","匹数"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

st.title("🎣 Fishing AI Poseidon")

# ===============================
# 本日リアル予測
# ===============================
st.header("📊 本日のリアル期待度")

cols = st.columns(len(AREAS))

for i, (area, coords) in enumerate(AREAS.items()):
    sea = get_sea(*coords)

    score = 0

    # 波
    if 1.5 <= sea["wave"] <= 2.5:
        score += 30

    # 水温
    if sea["temp"] >= 18:
        score += 30

    # 風
    if sea["wind"] >= 4:
        score += 20

    # 過去成功率補正
    area_df = df[df["エリア"] == area]
    if not area_df.empty:
        success_rate = (area_df["匹数"] > 0).mean() * 20
        score += success_rate

    percent = min(round(score), 95)

    cols[i].metric(
        area,
        f"{percent}%",
        delta=f"波:{round(sea['wave'],1)}m 風:{round(sea['wind'],1)}m/s"
    )

# ===============================
# 釣果入力
# ===============================
st.header("📝 釣果入力")

with st.form("input_form"):
    date = st.date_input("日付")
    area = st.selectbox("エリア", list(AREAS.keys()))
    count = st.number_input("匹数", min_value=0)

    submitted = st.form_submit_button("保存")

if submitted:
    new_row = {
        "日付": str(date),
        "エリア": area,
        "匹数": count
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

    st.success("保存完了")    

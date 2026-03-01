import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="POSEIDON")

# =====================
# ラスボスCSS（固定）
# =====================
st.markdown("""
<style>
body {background-color:#0b0f19;}
.main {background-color:#0b0f19; color:white;}

.gold-title {
    font-size:56px;
    font-weight:900;
    text-align:center;
    background: linear-gradient(180deg,#fff6b7,#f0c75e,#b88900);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    text-shadow:0 0 15px rgba(255,215,0,0.8);
    letter-spacing:6px;
}

.sub-title {
    font-size:22px;
    text-align:center;
    color:#d4af37;
    letter-spacing:8px;
    margin-bottom:40px;
}

.block-container {padding-top:2rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='gold-title'>POSEIDON</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>－海の支配者－</div>", unsafe_allow_html=True)

# =====================
# データ保存（固定）
# =====================
DATA_FILE = "history.csv"

def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["日付","エリア","魚種","匹数","ルアー種類","カラー"])

def save_history(df):
    df.to_csv(DATA_FILE, index=False)

history = load_history()

# =====================
# エリア座標
# =====================
AREAS = {
    "九十九里": {
        "sea": (35.53, 140.45),
        "land": (35.66, 140.50)  # 横芝光付近
    },
    "南房総": {
        "sea": (35.00, 139.90),
        "land": (34.99, 139.87)  # 館山付近
    },
    "新舞子": {
        "sea": (35.30, 139.80),
        "land": (35.31, 139.82)  # 富津付近
    }
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
# current_weather取得
# =====================
def get_current_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=wave_height,sea_surface_temperature,surface_pressure"
        f"&timezone=Asia%2FTokyo"
    )
    r = requests.get(url).json()

    current = r.get("current_weather", {})
    hourly = r.get("hourly", {})
    hour_index = 0

    if "time" in hourly:
        now_hour = datetime.now().hour
        hour_index = now_hour if now_hour < len(hourly["time"]) else 0

    return {
        "wind": current.get("windspeed", 0),
        "wind_dir": current.get("winddirection", 0),
        "wave": hourly.get("wave_height", [0])[hour_index],
        "temp": hourly.get("sea_surface_temperature", [0])[hour_index],
        "pressure": hourly.get("surface_pressure", [1013])[hour_index]
    }

# =====================
# 本気スコア計算
# =====================
def base_score(sea, tide):
    score = 0

    # 波
    if 0.8 <= sea["wave"] <= 2.0:
        score += 20
    elif sea["wave"] > 2.5:
        score -= 20

    # 風（本気仕様）
    wind = sea["wind"]
    direction = sea["wind_dir"]

    if 0 <= wind <= 2:
        score += 10
    elif 3 <= wind <= 6:
        score += 15
    elif 7 <= wind <= 9:
        score += 5
    elif 10 <= wind <= 12:
        score -= 10
    elif 13 <= wind <= 15:
        score -= 20
    elif wind >= 16:
        score -= 35

    # 風向（西〜北西が有利）
    if 240 <= direction <= 320:
        score += 5
    elif 30 <= direction <= 140:
        score -= 10

    # 気圧
    if 1008 <= sea["pressure"] <= 1018:
        score += 15

    if tide == "上げ":
        score += 10

    score += moon_score()

    return max(5, min(score, 95))

def species_score(base, fish):
    if fish == "ヒラメ":
        return min(base + 5, 100)
    if fish == "青物":
        return min(base + 3, 100)
    if fish == "シーバス":
        return min(base + 7, 100)
    return base

# =====================
# UI（様式固定）
# =====================
tide = st.selectbox("潮位", ["上げ", "下げ"])

st.header("本日の期待値")

for area, coords in AREAS.items():

    sea_data = get_current_weather(*coords["sea"])
    land_data = get_current_weather(*coords["land"])

    # 重み付け（陸0.7 海0.3）
    combined_wind = land_data["wind"] * 0.7 + sea_data["wind"] * 0.3
    combined_dir = land_data["wind_dir"]

    sea = sea_data.copy()
    sea["wind"] = combined_wind
    sea["wind_dir"] = combined_dir

    base = base_score(sea, tide)

    hirame = species_score(base, "ヒラメ")
    aomono = species_score(base, "青物")
    seabass = species_score(base, "シーバス")
    total = round((hirame + aomono + seabass) / 3)

    st.subheader(area)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総合", f"{total}%")
    c2.metric("ヒラメ", f"{hirame}%")
    c3.metric("青物", f"{aomono}%")
    c4.metric("シーバス", f"{seabass}%")

    st.caption(
        f"波:{round(sea['wave'],1)}m | "
        f"風速:{round(sea['wind'],1)}m/s | "
        f"風向:{round(sea['wind_dir'],0)}° | "
        f"水温:{round(sea['temp'],1)}℃ | "
        f"気圧:{round(sea['pressure'],1)}hPa"
    )

# =====================
# 釣果記録（固定）
# =====================
st.header("釣果記録")

with st.form("record"):
    d = st.date_input("日付")
    a = st.selectbox("エリア", list(AREAS.keys()))
    f = st.selectbox("魚種", ["ヒラメ", "青物", "シーバス"])
    c = st.number_input("匹数", 0)
    lure_type = st.selectbox(
        "ルアー種類",
        ["シンペン", "トップ", "バイブ", "メタルジグ", "ミノー", "ワーム"]
    )
    color = st.text_input("カラー")
    btn = st.form_submit_button("保存")

if btn:
    new = {
        "日付": str(d),
        "エリア": a,
        "魚種": f,
        "匹数": c,
        "ルアー種類": lure_type,
        "カラー": color
    }
    history = pd.concat([history, pd.DataFrame([new])], ignore_index=True)
    save_history(history)
    st.success("記録された")

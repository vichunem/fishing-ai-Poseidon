import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import math

st.set_page_config(page_title="POSEIDON", page_icon=None)

# =========================
# タイトル（1行＋サブ小さめ）
# =========================
st.markdown("""
<h1 style='margin-bottom:0;'>
POSEIDON<span style='font-size:60%; font-weight:400;'>-海の支配者-</span>
</h1>
""", unsafe_allow_html=True)

# =========================
# 設定
# =========================
DATA_FILE = "history.csv"

AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# =========================
# 履歴
# =========================
def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["日付","エリア","魚種","匹数"])

def save_history(df):
    df.to_csv(DATA_FILE,index=False)

history = load_history()

# =========================
# 月齢
# =========================
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

# =========================
# 海況取得
# =========================
@st.cache_data(ttl=600)
def get_data(lat,lon):
    marine = requests.get(
        f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,sea_surface_temperature&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m,windgusts_10m,surface_pressure&forecast_days=1&timezone=Asia%2FTokyo"
    ).json()

    h = datetime.now().hour

    return {
        "wave": marine["hourly"]["wave_height"][h],
        "temp": marine["hourly"]["sea_surface_temperature"][h],
        "wind": weather["hourly"]["windspeed_10m"][h],
        "gust": weather["hourly"]["windgusts_10m"][h],
        "pressure": weather["hourly"]["surface_pressure"][h]
    }

# =========================
# BIロジック
# =========================
def base_score(sea,tide):
    score = 0

    if 0.8 <= sea["wave"] <= 2.0:
        score += 20

    if 3 <= sea["wind"] <= 8:
        score += 15

    if sea["gust"] > 15:
        score -= 10

    if 1008 <= sea["pressure"] <= 1018:
        score += 15

    if 12 <= sea["temp"] <= 22:
        score += 15

    if tide == "上げ":
        score += 10

    score += moon_score()

    return max(5, min(score, 95))

def species_adjust(base, fish):
    if fish == "ヒラメ":
        return min(base + 5, 100)
    if fish == "青物":
        return min(base + 3, 100)
    if fish == "シーバス":
        return min(base + 7, 100)
    return base

# =========================
# UI
# =========================
tide = st.selectbox("潮位", ["上げ", "下げ"])

st.header("本日の期待値")

for area,coords in AREAS.items():

    sea = get_data(*coords)
    base = base_score(sea,tide)

    hirame = species_adjust(base,"ヒラメ")
    aomono = species_adjust(base,"青物")
    seabass = species_adjust(base,"シーバス")

    total = round((hirame + aomono + seabass) / 3)

    st.subheader(area)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("総合", f"{total}%")
    c2.metric("ヒラメ", f"{hirame}%")
    c3.metric("青物", f"{aomono}%")
    c4.metric("シーバス", f"{seabass}%")

    st.caption(
        f"波:{round(sea['wave'],1)}m  "
        f"風:{round(sea['wind'],1)}m/s  "
        f"最大:{round(sea['gust'],1)}m/s  "
        f"気圧:{round(sea['pressure'],1)}hPa  "
        f"水温:{round(sea['temp'],1)}℃  "
        f"月齢:{round(moon_phase(),1)}"
    )

# =========================
# 釣果記録
# =========================
st.header("釣果記録")

with st.form("record"):
    d = st.date_input("日付")
    a = st.selectbox("エリア", list(AREAS.keys()))
    f = st.selectbox("魚種", ["ヒラメ","青物","シーバス"])
    c = st.number_input("匹数", 0)
    btn = st.form_submit_button("保存")

if btn:
    new = {"日付":str(d),"エリア":a,"魚種":f,"匹数":c}
    history = pd.concat([history,pd.DataFrame([new])],ignore_index=True)
    save_history(history)
    st.success("保存完了")

if not history.empty:
    st.header("勝率推移")
    history["成功"] = history["匹数"] > 0
    chart = history.groupby("日付")["成功"].mean() * 100
    st.line_chart(chart)

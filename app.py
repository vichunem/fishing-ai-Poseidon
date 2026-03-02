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
    return pd.DataFrame(columns=["日付","エリア","魚種","匹数","ルアー種類","カラー"])

def save_history(df):
    df.to_csv(DATA_FILE, index=False)

history = load_history()

# =====================
# エリア座標（海のみ使用）
# =====================
AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# =====================
# 海況取得（風なし）
# =====================
def get_marine(lat, lon):

    url = (
        f"https://marine-api.open-meteo.com/v1/marine?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=wave_height,sea_surface_temperature"
        f"&timezone=Asia%2FTokyo"
    )

    try:
        r = requests.get(url, timeout=10).json()
        hourly = r.get("hourly", {})
        now_hour = datetime.now().hour

        def safe(key, default=0):
            arr = hourly.get(key, [])
            if now_hour < len(arr) and arr[now_hour] is not None:
                return float(arr[now_hour])
            return default

        return {
            "wave": safe("wave_height", 0),
            "temp": safe("sea_surface_temperature", 0)
        }

    except:
        return {"wave":0,"temp":0}

# =====================
# スコア計算（中潮最強）
# =====================
def base_score(sea, tide_type):

    score = 0

    # ---- 波（最重要）----
    wave = sea["wave"]

    if 0.6 <= wave <= 1.2:
        score += 35
    elif 1.2 < wave <= 1.8:
        score += 25
    elif 0.3 <= wave < 0.6:
        score += 15
    elif wave > 2.5:
        score -= 25

    # ---- 潮（最強：中潮）----
    if tide_type == "中潮":
        score += 30
    elif tide_type == "大潮":
        score += 20
    elif tide_type == "小潮":
        score += 10
    else:
        score += 5

    # ---- 水温（簡易補正）----
    temp = sea["temp"]
    if 16 <= temp <= 23:
        score += 15
    elif 12 <= temp < 16:
        score += 8
    elif temp > 26:
        score -= 5

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
# UI
# =====================
tide_type = st.selectbox("潮", ["中潮","大潮","小潮","長潮","若潮"])

st.header("本日の期待値")

for area, coords in AREAS.items():

    sea = get_marine(*coords)
    base = base_score(sea, tide_type)

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
        f"水温:{round(sea['temp'],1)}℃"
    )

# =====================
# 釣果記録（維持）
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

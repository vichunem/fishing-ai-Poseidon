import streamlit as st
import requests
import pandas as pd
import os
import math
from datetime import datetime, timedelta

st.set_page_config(page_title="Fishing AI Poseidon", page_icon="🎣")

DATA_FILE = "fishing_history.csv"

AREAS = {
    "九十九里": (35.53, 140.45),
    "南房総": (35.00, 139.90),
    "新舞子": (35.30, 139.80),
}

# =========================
# データ保存
# =========================
def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["日付","エリア","魚種","匹数"])

def save_history(df):
    df.to_csv(DATA_FILE, index=False)

history = load_history()

# =========================
# 月齢
# =========================
def moon_phase():
    diff = datetime.utcnow() - datetime(2001,1,1)
    days = diff.days + (diff.seconds/86400)
    lunations = 0.20439731 + (days * 0.03386319269)
    return (lunations % 1) * 29.53

def moon_bonus():
    phase = moon_phase()
    if phase < 2 or phase > 27: return 15
    if 13 < phase < 16: return 15
    return 5

# =========================
# 擬似潮位
# =========================
def pseudo_tide():
    cycle = 44700
    now = datetime.utcnow()
    seconds = now.hour*3600 + now.minute*60
    position = (seconds % cycle)/cycle
    return "上げ" if position < 0.5 else "下げ"

# =========================
# 海況取得
# =========================
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

# =========================
# 学習補正
# =========================
def history_bonus(area, fish):
    df = history[(history["エリア"]==area)&(history["魚種"]==fish)]
    if df.empty:
        return 0
    success_rate = (df["匹数"]>0).mean()*20
    return round(success_rate)

# =========================
# 魚種AI
# =========================
def hirame_ai(wave,temp,tide,area):
    score=0
    if 1.2<=wave<=2.5: score+=35
    if 15<=temp<=22: score+=30
    if tide=="上げ": score+=10
    score+=moon_bonus()
    score+=history_bonus(area,"ヒラメ")
    return min(score,95)

def aomono_ai(wave,temp,wind,area):
    score=0
    if temp>=18: score+=30
    if wind>=4: score+=25
    if 1.0<=wave<=2.0: score+=20
    score+=moon_bonus()
    score+=history_bonus(area,"青物")
    return min(score,95)

def seabass_ai(wave,wind,tide,area):
    score=0
    if wind>=5: score+=30
    if wave>=1.0: score+=25
    if tide=="上げ": score+=10
    hour=datetime.now().hour
    if hour>=18 or hour<=4: score+=20
    score+=moon_bonus()
    score+=history_bonus(area,"シーバス")
    return min(score,95)

# =========================
st.title("🎣 Fishing AI Poseidon Ultimate")

tide=pseudo_tide()
st.caption(f"擬似潮位:{tide}  月齢補正:+{moon_bonus()}%")

st.header("📊 本日のエリア別期待値")

for area,coords in AREAS.items():
    sea=get_sea(*coords)
    h=hirame_ai(sea["wave"],sea["temp"],tide,area)
    a=aomono_ai(sea["wave"],sea["temp"],sea["wind"],area)
    s=seabass_ai(sea["wave"],sea["wind"],tide,area)
    total=round((h+a+s)/3)

    st.subheader(area)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("総合",f"{total}%")
    c2.metric("ヒラメ",f"{h}%")
    c3.metric("青物",f"{a}%")
    c4.metric("シーバス",f"{s}%")
    st.caption(f"波:{round(sea['wave'],1)}m 風:{round(sea['wind'],1)}m/s 水温:{round(sea['temp'],1)}℃")

# =========================
# 釣果入力
# =========================
st.header("📝 釣果記録")

with st.form("record"):
    date=st.date_input("日付")
    area=st.selectbox("エリア",list(AREAS.keys()))
    fish=st.selectbox("魚種",["ヒラメ","青物","シーバス"])
    count=st.number_input("匹数",0)
    submit=st.form_submit_button("保存")

if submit:
    new_row={"日付":str(date),"エリア":area,"魚種":fish,"匹数":count}
    history=pd.concat([history,pd.DataFrame([new_row])],ignore_index=True)
    save_history(history)
    st.success("保存完了")

# =========================
# 勝率推移グラフ
# =========================
if not history.empty:
    st.header("📈 勝率推移")
    history["成功"]=history["匹数"]>0
    grouped=history.groupby("日付")["成功"].mean()*100
    st.line_chart(grouped)

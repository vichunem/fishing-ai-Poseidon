import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fishing AI Poseidon", page_icon="🎣")

st.title("🎣 Fishing AI Poseidon")

st.header("📋 釣果入力 & 予測")

with st.form("fishing_form"):
    date = st.date_input("日付")
    location = st.text_input("場所")

    weather = st.selectbox("天気", ["晴れ", "曇り", "雨", "風強い"])
    tide = st.selectbox("潮", ["大潮", "中潮", "小潮", "長潮", "若潮"])
    time_zone = st.selectbox("時間帯", ["朝", "昼", "夕方", "夜"])

    fish_type = st.text_input("魚種")
    size = st.number_input("サイズ(cm)", min_value=0)
    count = st.number_input("匹数", min_value=0)

    submitted = st.form_submit_button("保存 & 予測")

if submitted:

    # ===== データ保存表示 =====
    data = {
        "日付": date,
        "場所": location,
        "天気": weather,
        "潮": tide,
        "時間帯": time_zone,
        "魚種": fish_type,
        "サイズ(cm)": size,
        "匹数": count,
    }

    df = pd.DataFrame([data])

    st.success("✅ 入力データ")
    st.dataframe(df)

    # ===== 予測ロジック =====
    score = 0

    # 天気スコア
    if weather == "曇り":
        score += 2
    elif weather == "雨":
        score += 3
    elif weather == "晴れ":
        score += 1

    # 潮スコア
    if tide == "大潮":
        score += 3
    elif tide == "中潮":
        score += 2

    # 時間帯スコア
    if time_zone in ["朝", "夕方"]:
        score += 3
    elif time_zone == "夜":
        score += 1

    # 実釣補正
    if count >= 5:
        score += 2
    elif count == 0:
        score -= 1

    # ===== 判定 =====
    if score >= 8:
        result = "🔥 激アツ！爆釣期待度 高"
    elif score >= 5:
        result = "⭕ そこそこ期待できる"
    else:
        result = "△ 厳しいかも"

    st.subheader("📊 釣れやすさ予測")
    st.success(result)

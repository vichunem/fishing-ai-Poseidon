import streamlit as st
import pandas as pd

st.title("🎣 Fishing AI Poseidon")

st.header("📋 釣果記録入力")

# 入力フォーム
with st.form("fishing_form"):
    date = st.date_input("日付")
    location = st.text_input("場所")
    weather = st.selectbox("天気", ["晴れ", "曇り", "雨", "風強い"])
    tide = st.selectbox("潮", ["大潮", "中潮", "小潮", "長潮", "若潮"])
    fish_type = st.text_input("魚種")
    size = st.number_input("サイズ(cm)", min_value=0)
    count = st.number_input("匹数", min_value=0)

    submitted = st.form_submit_button("保存")

if submitted:
    data = {
        "日付": date,
        "場所": location,
        "天気": weather,
        "潮": tide,
        "魚種": fish_type,
        "サイズ(cm)": size,
        "匹数": count,
    }

    df = pd.DataFrame([data])
    st.success("保存しました！")
    st.dataframe(df)

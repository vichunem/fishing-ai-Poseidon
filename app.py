import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="POSEIDON", page_icon=None)

# =========================
# ラスボスUI（固定）
# =========================
st.markdown("""
<style>
body {background-color:#0b0f19;}
.main {background-color:#0b0f19; color:white;}
.gold-title {
    font-size:52px;
    font-weight:900;
    text-align:center;
    background: linear-gradient(180deg,#fff6b7,#f0c75e,#b88900);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    text-shadow:0 0 12px rgba(255,215,0,0.7);
    letter-spacing:4px;
}
.sub-title {
    font-size:22px;
    text-align:center;
    color:#d4af37;
    letter-spacing:6px;
    margin-bottom:40px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='gold-title'>POSEIDON</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>－海の支配者－</div>", unsafe_allow_html=True)

DATA_FILE = "history.csv"

def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "日付

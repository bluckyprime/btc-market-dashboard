import streamlit as st
import pandas as pd
import zipfile
import json
import os
import re
from datetime import date, timedelta
import streamlit.components.v1 as components


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="BTC Market Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("₿ BTC Market Dashboard")


# ============================================================
# SETTINGS
# ============================================================

ZIP_PATH = "BTC_1m_2025_to_8.9.26.zip"


# ============================================================
# LOAD ZIP
# ============================================================

@st.cache_resource
def get_zip():

    z = zipfile.ZipFile(ZIP_PATH, "r")

    csv_files = [
        f for f in z.namelist()
        if f.lower().endswith(".csv")
    ]

    if not csv_files:
        raise FileNotFoundError("No CSV file found inside ZIP.")

    return z, csv_files[0]


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_all_data():

    z, csv_file = get_zip()

    with z.open(csv_file) as f:

        df = pd.read_csv(
            f,
            parse_dates=["timestamp"],
            low_memory=False
        )

    df = df[
        [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ]

    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna()

    df = df.sort_values("timestamp")

    df = df.set_index("timestamp")

    return df


# ============================================================
# TIMEFRAME RESAMPLING
# ============================================================

def resample_data(df, timeframe):

    rules = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1H": "1h",
        "4H": "4h",
        "1D": "1D",
    }

    rule = rules[timeframe]

    result = df.resample(rule).agg(
        {
            "open": "first

import streamlit as st
import pandas as pd
import altair as alt
from zipfile import ZipFile
from pathlib import Path

st.set_page_config(
    page_title="BTC Market Dashboard",
    page_icon="₿",
    layout="wide"
)

ZIP_FILE = Path("BTC_1m_2025_to_8.9.26.zip")


@st.cache_data
def load_data():
    with ZipFile(ZIP_FILE) as z:
        csv_files = [x for x in z.namelist() if x.lower().endswith(".csv")]

        if not csv_files:
            raise ValueError("No CSV file found inside ZIP")

        with z.open(csv_files[0]) as f:
            df = pd.read_csv(f, header=None)

    df = df.iloc[:, :6]
    df.columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms",
        errors="coerce"
    )

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()
    df = df.sort_values("timestamp")

    return df


df = load_data()

st.title("₿ BTC / USD Candlestick Dashboard")

timeframe = st.selectbox(
    "Candle timeframe",
    [
        "1 minute",
        "5 minutes",
        "15 minutes",
        "30 minutes",
        "1 hour",
        "4 hours",
        "1 day"
    ],
    index=4
)

rules = {
    "1 minute": "1min",
    "5 minutes": "5min",
    "15 minutes": "15min",
    "30 minutes": "30min",
    "1 hour": "1h",
    "4 hours": "4h",
    "1 day": "1D"
}

df = df.set_index("timestamp")

candles = df.resample(rules[timeframe]).agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last"
}).dropna().reset_index()

current_price = candles["close"].iloc[-1]

st.metric(
    "BTC Price",
    f"${current_price:,.2f}"
)

# Zoom / pan area
brush = alt.selection_interval(bind="scales")

# High-low wick
wick = alt.Chart(candles).mark_rule().encode(
    x=alt.X(
        "timestamp:T",
        title="Time"
    ),
    y=alt.Y(
        "low:Q",
        title="Price (USD)"
    ),
    y2="high:Q",
    color=alt.condition(
        alt.datum.close >= alt.datum.open,
        alt.value("#00c853"),
        alt.value("#ff1744")
    )
)

# Candle body
body = alt.Chart(candles).mark_bar().encode(
    x=alt.X(
        "timestamp:T",
        title="Time"
    ),
    y=alt.Y(
        "open:Q",
        title="Price (USD)"
    ),
    y2="close:Q",
    color=alt.condition(
        alt.datum.close >= alt.datum.open,
        alt.value("#00c853"),
        alt.value("#ff1744")
    ),
    tooltip=[
        alt.Tooltip("timestamp:T", title="Time"),
        alt.Tooltip("open:Q", title="Open", format=",.2f"),
        alt.Tooltip("high:Q", title="High", format=",.2f"),
        alt.Tooltip("low:Q", title="Low", format=",.2f"),
        alt.Tooltip("close:Q", title="Close", format=",.2f")
    ]
).properties(
    height=600
)

chart = (
    wick + body
).add_params(
    brush
).interactive()

st.altair_chart(
    chart,
    width="stretch"
)

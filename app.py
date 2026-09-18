# app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from zipfile import ZipFile
from pathlib import Path

st.set_page_config(
    page_title="BTC Market Dashboard",
    page_icon="₿",
    layout="wide"
)

st.title("₿ BTC / USD Candlestick Dashboard")

ZIP_FILE = Path("BTC_1m_2025_to_8.9.26.zip")


@st.cache_data
def load_data():
    with ZipFile(ZIP_FILE) as z:
        csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]

        if not csv_files:
            raise ValueError("No CSV file found inside ZIP.")

        file_name = csv_files[0]

        df = pd.read_csv(z.open(file_name))

    # Binance-style data without headers
    if "open" not in [str(c).lower() for c in df.columns]:
        if len(df.columns) >= 6:
            df = df.iloc[:, :6]
            df.columns = [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Find timestamp column
    timestamp_col = None
    for c in ["timestamp", "open_time", "datetime", "date", "time"]:
        if c in df.columns:
            timestamp_col = c
            break

    if timestamp_col is None:
        raise ValueError("Timestamp column not found.")

    df["timestamp"] = pd.to_datetime(
        df[timestamp_col],
        unit="ms",
        errors="coerce"
    )

    # If timestamp was already a normal datetime
    if df["timestamp"].isna().mean() > 0.5:
        df["timestamp"] = pd.to_datetime(
            df[timestamp_col],
            errors="coerce"
        )

    required = ["open", "high", "low", "close"]

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["timestamp", "open", "high", "low", "close"]
    )

    df = df.sort_values("timestamp")
    df = df.set_index("timestamp")

    return df


try:
    df = load_data()

    st.sidebar.header("Chart Settings")

    timeframe = st.sidebar.selectbox(
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

    timeframe_map = {
        "1 minute": "1min",
        "5 minutes": "5min",
        "15 minutes": "15min",
        "30 minutes": "30min",
        "1 hour": "1h",
        "4 hours": "4h",
        "1 day": "1D"
    }

    rule = timeframe_map[timeframe]

    start_date = st.sidebar.date_input(
        "Start date",
        df.index.min().date()
    )

    end_date = st.sidebar.date_input(
        "End date",
        df.index.max().date()
    )

    filtered = df.loc[
        str(start_date):str(end_date)
    ]

    if filtered.empty:
        st.error("No data available for this date range.")
        st.stop()

    # Convert 1-minute data into OHLC candles
    candles = filtered.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna()

    current_price = filtered["close"].iloc[-1]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "BTC Price",
        f"${current_price:,.2f}"
    )

    col2.metric(
        "Period High",
        f"${filtered['high'].max():,.2f}"
    )

    col3.metric(
        "Period Low",
        f"${filtered['low'].min():,.2f}"
    )

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=candles.index,
                open=candles["open"],
                high=candles["high"],
                low=candles["low"],
                close=candles["close"],
                increasing_line_color="#00c853",
                decreasing_line_color="#ff1744",
                increasing_fillcolor="#00c853",
                decreasing_fillcolor="#ff1744",
                name="BTC"
            )
        ]
    )

    fig.update_layout(
        title=f"BTC/USD — {timeframe} Candles",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=650,
        dragmode="zoom",
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        yaxis=dict(
            fixedrange=False
        ),
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": [
                "drawline",
                "drawopenpath",
                "eraseshape"
            ]
        }
    )

except Exception as e:
    st.error(f"Error loading data: {e}")

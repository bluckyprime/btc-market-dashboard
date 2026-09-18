import pandas as pd
import requests
import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(
    page_title="Binance Style BTC Dashboard", layout="wide", page_icon="🪙"
)

st.title("🪙 BTC / USD Real-Time Trading View")

# CoinGecko OHLC (Open, High, Low, Close) Data ගැනීම
url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=30"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])

    # Streamlit Lightweight Charts සඳහා අවශ්‍ය Time format එක
    df["time"] = df["time"] / 1000  # Unix timestamp to seconds

    current_price = df["close"].iloc[-1]
    prev_price = df["close"].iloc[0]
    price_change = ((current_price - prev_price) / prev_price) * 100

    # Binance Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("30D Change", f"{price_change:+.2f}%")
    col3.metric("30D High", f"${df['high'].max():,.2f}")
    col4.metric("30D Low", f"${df['low'].min():,.2f}")

    st.subheader("📊 Binance Style Candlestick Chart")

    # Candlestick chart configuration
    chart_options = {
        "height": 500,
        "layout": {"backgroundColor": "#131722", "textColor": "#d1d4dc"},
        "grid": {
            "vertLines": {"color": "#2B2B43"},
            "horzLines": {"color": "#2B2B43"},
        },
        "timeScale": {"timeVisible": True, "secondsVisible": False},
    }

    candle_series = [
        {
            "type": "Candlestick",
            "data": df.to_dict("records"),
            "options": {
                "upColor": "#089981",  # Green
                "downColor": "#F23645",  # Red
                "borderUpColor": "#089981",
                "borderDownColor": "#F23645",
                "wickUpColor": "#089981",
                "wickDownColor": "#F23645",
            },
        }
    ]

    renderLightweightCharts([{"chart": chart_options, "series": candle_series}])

else:
    st.error("Data Load කරගැනීමට නොහැකි විය. මොහොතකින් නැවත උත්සාහ කරන්න.")

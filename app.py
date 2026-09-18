import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Binance Style BTC Dashboard", layout="wide", page_icon="🪙"
)

st.title("🪙 BTC / USD Real-Time Price View")

# CoinGecko API එකෙන් BTC OHLC (Market Data) ලබා ගැනීම
url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=30"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    # Chart එක සඳහා Time Index සකස් කිරීම
    df.set_index("time", inplace=True)

    current_price = df["close"].iloc[-1]
    prev_price = df["close"].iloc[0]
    price_change = ((current_price - prev_price) / prev_price) * 100

    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("30D Change", f"{price_change:+.2f}%")
    col3.metric("30D High", f"${df['high'].max():,.2f}")
    col4.metric("30D Low", f"${df['low'].min():,.2f}")

    st.subheader("📈 Bitcoin Price Trend (30 Days)")

    # Pure Python / Built-in Streamlit Line Chart (No Extra Packages Required)
    st.line_chart(df[["close"]])

else:
    st.error(
        "Data load කරගැනීමට නොහැකි විය. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න."
    )

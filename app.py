import os
import subprocess
import sys

# matplotlib නැත්නම් automatic install කරගැනීම
try:
    import matplotlib.pyplot as plt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Binance Style BTC Dashboard", layout="wide", page_icon="🪙"
)

st.title("🪙 BTC / USD Real-Time Price View")

# CoinGecko API එකෙන් Data ලබා ගැනීම
url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=30"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    current_price = df["close"].iloc[-1]
    prev_price = df["close"].iloc[0]
    price_change = ((current_price - prev_price) / prev_price) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("30D Change", f"{price_change:+.2f}%")
    col3.metric("30D High", f"${df['high'].max():,.2f}")
    col4.metric("30D Low", f"${df['low'].min():,.2f}")

    st.subheader("📊 Candlestick Chart")

    fig, ax = plt.subplots(figsize=(12, 6))

    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    for idx, row in df.iterrows():
        color = "#089981" if row["close"] >= row["open"] else "#F23645"

        # High/Low Wick
        ax.plot(
            [row["time"], row["time"]],
            [row["low"], row["high"]],
            color=color,
            linewidth=1,
        )

        # Open/Close Body
        height = abs(row["close"] - row["open"])
        bottom = min(row["open"], row["close"])
        ax.bar(row["time"], height, bottom=bottom, color=color, width=0.6)

    ax.grid(True, color="#2b2b2b", linestyle="--", alpha=0.5)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#444")
    ax.spines["top"].set_color("#0e1117")
    ax.spines["left"].set_color("#444")
    ax.spines["right"].set_color("#0e1117")

    st.pyplot(fig)

else:
    st.error(
        "Data load කරගැනීමට නොහැකි විය. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න."
    )

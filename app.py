import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="BTC Dashboard",
    page_icon="₿",
    layout="wide"
)

st.title("₿ BTC / USD Dashboard")

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

params = {
    "vs_currency": "usd",
    "days": "30",
    "interval": "hourly"
}

try:
    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        st.error(f"CoinGecko API Error: {response.status_code}")
        st.code(response.text)
        st.stop()

    data = response.json()

except requests.RequestException as e:
    st.error("Could not connect to CoinGecko.")
    st.code(str(e))
    st.stop()

prices = data.get("prices", [])

if not prices:
    st.error("CoinGecko returned no price data.")
    st.stop()

df = pd.DataFrame(
    prices,
    columns=["timestamp", "price"]
)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    unit="ms"
)

df = df.set_index("timestamp")

current_price = df["price"].iloc[-1]
starting_price = df["price"].iloc[0]

change = (
    (current_price - starting_price)
    / starting_price
) * 100

high = df["price"].max()
low = df["price"].min()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "BTC Price",
    f"${current_price:,.2f}"
)

col2.metric(
    "30D Change",
    f"{change:+.2f}%"
)

col3.metric(
    "30D High",
    f"${high:,.2f}"
)

col4.metric(
    "30D Low",
    f"${low:,.2f}"
)

st.subheader("📈 BTC Price — 30 Days")

st.line_chart(
    df["price"],
    height=500
)

st.subheader("📋 Price History")

st.dataframe(
    df.tail(20),
    use_container_width=True
)

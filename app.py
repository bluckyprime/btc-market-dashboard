import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="BTC Market Dashboard", layout="wide")

st.title("₿ Bitcoin Market Dashboard")

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    prices = data["prices"]

    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

    current_price = df["price"].iloc[-1]
    st.metric(label="Current BTC Price (USD)", value=f"${current_price:,.2f}")

    st.subheader("Last 30 Days Price Trend")
    st.line_chart(df.set_index("date")["price"])
else:
    st.error(
        "Data load කරගැනීමට නොහැකි විය. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න."
    )

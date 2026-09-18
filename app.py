import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Binance Style BTC Dashboard", layout="wide", page_icon="🪙"
)

st.title("🪙 BTC / USD Real-Time Price View")

# CoinGecko API එකෙන් 30-Day OHLC Data ගැනීම
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

    st.subheader("📊 Candlestick Chart (Binance Style)")

    # Chart scaling සකස් කරගැනීම
    min_p = df["low"].min()
    max_p = df["high"].max()
    p_range = max_p - min_p if max_p != min_p else 1

    candles_html = ""
    for idx, row in df.iterrows():
        is_green = row["close"] >= row["open"]
        color = "#089981" if is_green else "#F23645"

        high_pct = ((row["high"] - min_p) / p_range) * 100
        low_pct = ((row["low"] - min_p) / p_range) * 100
        open_pct = ((row["open"] - min_p) / p_range) * 100
        close_pct = ((row["close"] - min_p) / p_range) * 100

        body_bottom = min(open_pct, close_pct)
        body_height = max(abs(close_pct - open_pct), 0.8)
        wick_height = high_pct - low_pct

        candles_html += f"""
        <div style="flex: 1; height: 100%; position: relative; display: flex; align-items: flex-end; justify-content: center;" title="Date: {row['time'].strftime('%Y-%m-%d')}&#10;Open: ${row['open']:,.2f}&#10;High: ${row['high']:,.2f}&#10;Low: ${row['low']:,.2f}&#10;Close: ${row['close']:,.2f}">
            <!-- Wick (High-Low) -->
            <div style="position: absolute; bottom: {low_pct}%; height: {wick_height}%; width: 1.5px; background-color: {color};"></div>
            <!-- Body (Open-Close) -->
            <div style="position: absolute; bottom: {body_bottom}%; height: {body_height}%; width: 70%; background-color: {color}; border-radius: 1px;"></div>
        </div>
        """

    # HTML/CSS Dark Theme Box එකක් ඇතුළේ Candles render කිරීම
    chart_ui = f"""
    <div style="background-color: #0e1117; border: 1px solid #2b2b2b; border-radius: 8px; padding: 20px 10px; height: 380px; display: flex; align-items: flex-end; gap: 2px;">
        {candles_html}
    </div>
    <div style="display: flex; justify-content: space-between; color: #888; font-size: 12px; margin-top: 6px;">
        <span>{df['time'].iloc[0].strftime('%b %d')}</span>
        <span>{df['time'].iloc[len(df)//2].strftime('%b %d')}</span>
        <span>{df['time'].iloc[-1].strftime('%b %d')}</span>
    </div>
    """

    st.markdown(chart_ui, unsafe_allow_html=True)

else:
    st.error(
        "Data load කරගැනීමට නොහැකි විය. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න."
    )

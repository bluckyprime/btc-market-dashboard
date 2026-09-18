import streamlit.components.v1 as components
import requests
import streamlit as st

st.set_page_config(
    page_title="Binance Style BTC Dashboard", layout="wide", page_icon="🪙"
)

st.title("🪙 BTC / USD Real-Time Price View")

# CoinGecko API එකෙන් OHLC Data ගැනීම
url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=30"
response = requests.get(url)

if response.status_code == 200:
    raw_data = response.json()

    # JavaScript TradingView Library එකට ගැලපෙන සේ Data සකස් කිරීම
    candlestick_data = []
    for item in raw_data:
        candlestick_data.append(
            {
                "time": int(item[0] / 1000),  # UNIX timestamp (seconds)
                "open": item[1],
                "high": item[2],
                "low": item[3],
                "close": item[4],
            }
        )

    current_price = candlestick_data[-1]["close"]
    prev_price = candlestick_data[0]["close"]
    price_change = ((current_price - prev_price) / prev_price) * 100

    col1, col2 = st.columns(2)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("30D Change", f"{price_change:+.2f}%")

    st.subheader("📊 Interactive Candlestick Chart (JavaScript / TradingView)")

    # JavaScript (Lightweight Charts) Code එක Embedded HTML එකක් ලෙස යැවීම
    js_chart_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; background-color: #0e1117; }}
            #chart {{ width: 100%; height: 450px; }}
        </style>
    </head>
    <body>
        <div id="chart"></div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
                layout: {{
                    backgroundColor: '#0e1117',
                    textColor: '#d1d4dc',
                }},
                grid: {{
                    vertLines: {{ color: '#2B2B43' }},
                    horzLines: {{ color: '#2B2B43' }},
                }},
                timeScale: {{
                    timeVisible: true,
                    secondsVisible: false,
                }},
            }});

            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#089981',
                downColor: '#F23645',
                borderVisible: false,
                wickUpColor: '#089981',
                wickDownColor: '#F23645',
            }});

            const data = {candlestick_data};
            candlestickSeries.setData(data);
            chart.timeScale().fitContent();
        </script>
    </body>
    </html>
    """

    # Streamlit Component එකක් ලෙස Render කිරීම
    components.html(js_chart_code, height=470)

else:
    st.error(
        "Data load කරගැනීමට නොහැකි විය. කරුණාකර මොහොතකින් නැවත උත්සාහ කරන්න."
    )

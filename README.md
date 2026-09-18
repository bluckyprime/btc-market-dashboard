# 🚀 Automated BTC/USDT Market Analytics Dashboard

An automated, high-fidelity Bitcoin market data pipeline and dynamic visualization app. Built with Python, GitHub Actions, and Streamlit.

🔗 **Live Interactive App:** [https://your-streamlit-app-link.streamlit.app](https://your-streamlit-app-link.streamlit.app) *(Replace with your actual link)*

---

## 📌 Features
- **Automated Data Ingestion:** GitHub Actions workflow updates 1-minute BTC kline archives daily without API rate limits.
- **Dynamic Indicators:** On-demand calculation of Moving Averages (MA7, MA25) and Relative Strength Index (RSI).
- **Interactive UI:** Ultra-responsive Plotly candlestick chart with multi-timeframe navigation (1D, 7D, 1M, 1Y).

---

## 🛠️ Tech Stack
- **Language:** Python
- **Data Engineering:** Pandas, Requests, Zipfile
- **Automation (CI/CD):** GitHub Actions
- **Visualization:** Plotly, Streamlit

---

## 🏗️ Architecture
1. **Fetch:** Daily incremental kline ZIPs from Binance Vision.
2. **Clean & Validate:** Automated timestamp normalization and fallback sequence reconstruction.
3. **Serve:** Processed data feeds directly into the interactive Streamlit dashboard.


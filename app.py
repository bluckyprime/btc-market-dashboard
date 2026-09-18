import os
import zipfile
import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="BTC Market Analytics Dashboard", layout="wide")

ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"

@st.cache_data(ttl=3600)
def load_data():
    if not os.path.exists(ZIP_FILE):
        return pd.DataFrame()
    
    with zipfile.ZipFile(ZIP_FILE, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        if not csv_files:
            return pd.DataFrame()
        
        with z.open(csv_files[0]) as f:
            df = pd.read_csv(f)
            
            # Map standard column names if unindexed
            if len(df.columns) >= 6:
                cols = list(df.columns)
                df = df.rename(columns={
                    cols[0]: 'open_time', cols[1]: 'open', cols[2]: 'high',
                    cols[3]: 'low', cols[4]: 'close', cols[5]: 'volume'
                })
            
            # Convert open_time to datetime
            if pd.api.types.is_numeric_dtype(df['open_time']):
                if df['open_time'].iloc[0] > 1e11:
                    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                else:
                    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
            else:
                df['open_time'] = pd.to_datetime(df['open_time'])
                
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            return df.sort_values('open_time').reset_index(drop=True)

st.title("🚀 BTC/USDT Market Analytics Dashboard")

df = load_data()

if df.empty:
    st.error("Data source file not found or empty.")
else:
    # Sidebar Filters
    st.sidebar.header("Navigation & Options")
    timeframe = st.sidebar.selectbox("Timeframe Window", ["1D", "7D", "1M", "1Y", "ALL"], index=1)
    
    # Calculate Indicators
    df['MA7'] = df['close'].rolling(window=7*1440).mean() if len(df) > 7*1440 else df['close'].rolling(7).mean()
    df['MA25'] = df['close'].rolling(window=25*1440).mean() if len(df) > 25*1440 else df['close'].rolling(25).mean()
    
    # RSI Calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Filter by selected range
    last_dt = df['open_time'].max()
    if timeframe == "1D":
        filtered_df = df[df['open_time'] >= (last_dt - pd.Timedelta(days=1))]
    elif timeframe == "7D":
        filtered_df = df[df['open_time'] >= (last_dt - pd.Timedelta(days=7))]
    elif timeframe == "1M":
        filtered_df = df[df['open_time'] >= (last_dt - pd.Timedelta(days=30))]
    elif timeframe == "1Y":
        filtered_df = df[df['open_time'] >= (last_dt - pd.Timedelta(days=365))]
    else:
        filtered_df = df.copy()

    # Resample for performance if dataset is large
    if len(filtered_df) > 5000:
        filtered_df = filtered_df.iloc[::max(1, len(filtered_df)//2000)]

    # Metrics Display
    c1, c2, c3, c4 = st.columns(4)
    latest_price = filtered_df['close'].iloc[-1]
    prev_price = filtered_df['close'].iloc[0]
    change = ((latest_price - prev_price) / prev_price) * 100
    
    c1.metric("Latest Price", f"${latest_price:,.2f}", f"{change:+.2f}%")
    c2.metric("High", f"${filtered_df['high'].max():,.2f}")
    c3.metric("Low", f"${filtered_df['low'].min():,.2f}")
    c4.metric("Volume", f"{filtered_df['volume'].sum():,.2f}")

    # Plotly Subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=filtered_df['open_time'],
        open=filtered_df['open'], high=filtered_df['high'],
        low=filtered_df['low'], close=filtered_df['close'],
        name="BTC Candle"
    ), row=1, col=1)

    # MA Lines
    fig.add_trace(go.Scatter(x=filtered_df['open_time'], y=filtered_df['MA7'], line=dict(color='orange', width=1), name="MA7"), row=1, col=1)
    fig.add_trace(go.Scatter(x=filtered_df['open_time'], y=filtered_df['MA25'], line=dict(color='blue', width=1), name="MA25"), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=filtered_df['open_time'], y=filtered_df['RSI'], line=dict(color='purple', width=1), name="RSI"), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)

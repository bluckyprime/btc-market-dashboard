import streamlit as st
import pandas as pd
import zipfile
import json
from datetime import timedelta


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="BTC Market Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("₿ BTC Market Dashboard")

ZIP_PATH = "BTC_1m_2025_to_8.9.26.zip"


# ============================================================
# DATA
# ============================================================

@st.cache_resource
def get_zip_info():
    z = zipfile.ZipFile(ZIP_PATH, "r")
    files = [x for x in z.namelist() if x.lower().endswith(".csv")]

    if not files:
        raise FileNotFoundError("No CSV found inside ZIP.")

    return z, files[0]


@st.cache_data
def load_data():
    z, csv_file = get_zip_info()

    with z.open(csv_file) as f:
        df = pd.read_csv(
            f,
            parse_dates=["timestamp"],
            low_memory=False,
        )

    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = df[cols]

    nums = ["open", "high", "low", "close", "volume"]
    df[nums] = df[nums].apply(pd.to_numeric, errors="coerce")

    df = df.dropna().sort_values("timestamp")
    return df.set_index("timestamp")


def resample_data(df, timeframe):
    rules = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1H": "1h",
        "4H": "4h",
        "1D": "1D",
    }

    return (
        df.resample(rules[timeframe])
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        .dropna()
    )


# ============================================================
# LOAD
# ============================================================

with st.spinner("Loading BTC market data..."):
    df = load_data()

data_start = df.index.min().date()
data_end = df.index.max().date()


# ============================================================
# CONTROLS
# ============================================================

st.markdown("### Chart Settings")

c1, c2, c3 = st.columns([1.1, 1.1, 2])

with c1:
    timeframe = st.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "30m", "1H", "4H", "1D"],
    )

with c2:
    range_option = st.selectbox(
        "Range",
        ["1D", "3D", "7D", "14D", "30D", "90D", "1Y", "ALL", "Custom"],
    )

with c3:
    if range_option == "ALL":
        start_date, end_date = data_start, data_end

    elif range_option == "Custom":
        selected = st.date_input(
            "Date range",
            value=(
                max(data_start, data_end - timedelta(days=7)),
                data_end,
            ),
            min_value=data_start,
            max_value=data_end,
        )

        if isinstance(selected, tuple) and len(selected) == 2:
            start_date, end_date = selected
        else:
            start_date = end_date = (
                selected[0] if isinstance(selected, tuple) else selected
            )

    else:
        days = 365 if range_option == "1Y" else int(range_option[:-1])
        end_date = data_end
        start_date = max(
            data_start,
            end_date - timedelta(days=days - 1),
        )


# ============================================================
# FILTER
# ============================================================

start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)

filtered = df[
    (df.index >= start_ts) &
    (df.index < end_ts)
]

range_days = (end_date - start_date).days + 1


# ============================================================
# AUTO RESOLUTION
# ============================================================

display_timeframe = timeframe

if range_days > 365:
    display_timeframe = "1D"
elif range_days > 180:
    display_timeframe = "4H"
elif range_days > 60:
    display_timeframe = "1H"

chart_df = resample_data(
    filtered,
    display_timeframe,
)


# ============================================================
# EMPTY DATA
# ============================================================

if chart_df.empty:
    st.warning("No market data available for this range.")
    st.stop()


# ============================================================
# METRICS
# ============================================================

first_close = chart_df["close"].iloc[0]
last_close = chart_df["close"].iloc[-1]

change = (
    (last_close - first_close)
    / first_close
    * 100
)

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Open",
    f"${chart_df['open'].iloc[0]:,.2f}",
)

m2.metric(
    "Close",
    f"${last_close:,.2f}",
)

m3.metric(
    "Change",
    f"{change:+.2f}%",
)

m4.metric(
    "Candles",
    f"{len(chart_df):,}",
)


# ============================================================
# PREPARE CHART DATA
# ============================================================

chart_data = [
    {
        "time": int(ts.timestamp()),
        "open": float(row.open),
        "high": float(row.high),
        "low": float(row.low),
        "close": float(row.close),
        "volume": float(row.volume),
    }
    for ts, row in chart_df.iterrows()
]

json_data = json.dumps(chart_data)


# ============================================================
# LIGHTWEIGHT CHART
# ============================================================

html = """
<!DOCTYPE html>

<html>
<head>

<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>

<style>

html, body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: #ffffff;
}

#chart {
    width: 100%;
    height: 600px;
}

</style>

</head>

<body>

<div id="chart"></div>

<script>

const data = __CHART_DATA__;

const chart = LightweightCharts.createChart(
    document.getElementById("chart"),
    {
        width: window.innerWidth,
        height: 600,

        layout: {
            background: { color: "#ffffff" },
            textColor: "#333333"
        },

        grid: {
            vertLines: { color: "#eeeeee" },
            horzLines: { color: "#eeeeee" }
        },

        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal
        },

        rightPriceScale: {
            borderColor: "#cccccc"
        },

        timeScale: {
            borderColor: "#cccccc",
            timeVisible: true,
            secondsVisible: false
        },

        handleScroll: true,
        handleScale: true
    }
);


const candles = chart.addSeries(
    LightweightCharts.CandlestickSeries,
    {
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickUpColor: "#26a69a",
        wickDownColor: "#ef5350"
    }
);


const volume = chart.addSeries(
    LightweightCharts.HistogramSeries,
    {
        priceFormat: {
            type: "volume"
        },

        priceScaleId: "volume",

        scaleMargins: {
            top: 0.80,
            bottom: 0
        }
    }
);


candles.setData(
    data.map(x => ({
        time: x.time,
        open: x.open,
        high: x.high,
        low: x.low,
        close: x.close
    }))
);


volume.setData(
    data.map(x => ({
        time: x.time,
        value: x.volume,
        color:
            x.close >= x.open
                ? "rgba(38,166,154,0.45)"
                : "rgba(239,83,80,0.45)"
    }))
);


chart.timeScale().fitContent();


window.addEventListener("resize", () => {
    chart.applyOptions({
        width: window.innerWidth
    });
});


document.addEventListener("dblclick", () => {
    chart.timeScale().fitContent();
});

</script>

</body>
</html>
"""

html = html.replace(
    "__CHART_DATA__",
    json_data,
)


# ============================================================
# DISPLAY
# ============================================================

st.iframe(
    html,
    height=620,
)


# ============================================================
# INFO
# ============================================================

st.caption(
    f"Data: {start_date} → {end_date}  |  "
    f"Requested: {timeframe}  |  "
    f"Displayed: {display_timeframe}  |  "
    f"Candles: {len(chart_df):,}"
)

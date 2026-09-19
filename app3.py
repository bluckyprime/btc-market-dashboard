import streamlit as st
import pandas as pd
import zipfile
import json
from datetime import date, timedelta
import streamlit.components.v1 as components


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BTC Market Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("₿ BTC Market Dashboard")


# ============================================================
# SETTINGS
# ============================================================

ZIP_PATH = "BTC_1m_2025_to_8.9.26.zip"


# ============================================================
# FIND CSV INSIDE ZIP
# ============================================================

@st.cache_resource
def get_zip_info():

    z = zipfile.ZipFile(ZIP_PATH, "r")

    csv_files = [
        name
        for name in z.namelist()
        if name.lower().endswith(".csv")
    ]

    if not csv_files:
        raise FileNotFoundError(
            "No CSV file found inside ZIP."
        )

    return z, csv_files[0]


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    z, csv_file = get_zip_info()

    with z.open(csv_file) as f:

        df = pd.read_csv(
            f,
            parse_dates=["timestamp"],
            low_memory=False,
        )

    required_columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    df = df[required_columns]

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna()

    df = df.sort_values("timestamp")

    df = df.set_index("timestamp")

    return df


# ============================================================
# RESAMPLE
# ============================================================

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

    rule = rules[timeframe]

    result = df.resample(rule).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )

    return result.dropna()


# ============================================================
# LOAD FULL DATA
# ============================================================

with st.spinner("Loading BTC market data..."):

    df = load_data()


# ============================================================
# AUTOMATIC DATA RANGE
# ============================================================

data_start = df.index.min().date()

data_end = df.index.max().date()


# ============================================================
# UI
# ============================================================

st.markdown("### Chart Settings")

col1, col2, col3 = st.columns(
    [1.2, 1.2, 2]
)


# ============================================================
# TIMEFRAME
# ============================================================

with col1:

    timeframe = st.selectbox(
        "Timeframe",
        [
            "1m",
            "5m",
            "15m",
            "30m",
            "1H",
            "4H",
            "1D",
        ],
        index=0,
    )


# ============================================================
# RANGE
# ============================================================

with col2:

    range_option = st.selectbox(
        "Range",
        [
            "1D",
            "3D",
            "7D",
            "14D",
            "30D",
            "90D",
            "1Y",
            "ALL",
            "Custom",
        ],
        index=0,
    )


# ============================================================
# DATE RANGE
# ============================================================

with col3:

    if range_option == "ALL":

        start_date = data_start

        end_date = data_end

    elif range_option == "Custom":

        selected_dates = st.date_input(
            "Date range",
            value=(
                max(
                    data_start,
                    data_end - timedelta(days=7)
                ),
                data_end,
            ),
            min_value=data_start,
            max_value=data_end,
        )

        if isinstance(selected_dates, tuple):

            if len(selected_dates) == 2:

                start_date = selected_dates[0]

                end_date = selected_dates[1]

            else:

                start_date = selected_dates[0]

                end_date = selected_dates[0]

        else:

            start_date = selected_dates

            end_date = selected_dates

    else:

        days = int(
            range_option.replace("D", "")
        ) if "D" in range_option else 365

        end_date = data_end

        start_date = max(
            data_start,
            end_date - timedelta(days=days - 1),
        )


# ============================================================
# FILTER
# ============================================================

start_timestamp = pd.Timestamp(start_date)

end_timestamp = (
    pd.Timestamp(end_date)
    + pd.Timedelta(days=1)
)


filtered = df[
    (df.index >= start_timestamp)
    & (df.index < end_timestamp)
]


# ============================================================
# AUTO RESOLUTION FOR LARGE RANGES
# ============================================================

range_days = (
    end_date - start_date
).days + 1


display_timeframe = timeframe


if range_option == "ALL":

    if range_days > 500:

        display_timeframe = "1D"

    elif range_days > 180:

        display_timeframe = "4H"

    elif range_days > 60:

        display_timeframe = "1H"


elif range_days > 365:

    display_timeframe = "1D"

elif range_days > 180:

    display_timeframe = "4H"

elif range_days > 60:

    display_timeframe = "1H"


# ============================================================
# RESAMPLE
# ============================================================

chart_df = resample_data(
    filtered,
    display_timeframe,
)


# ============================================================
# BASIC INFO
# ============================================================

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Candles",
        f"{len(chart_df):,}",
    )


with c2:

    st.metric(
        "Start",
        str(start_date),
    )


with c3:

    if len(chart_df) > 0:

        st.metric(
            "Close",
            f"${chart_df.iloc[-1]['close']:,.2f}",
        )


with c4:

    if len(chart_df) > 0:

        change = (
            (
                chart_df.iloc[-1]["close"]
                / chart_df.iloc[0]["open"]
            )
            - 1
        ) * 100

        st.metric(
            "Change",
            f"{change:+.2f}%",
        )


# ============================================================
# NO DATA
# ============================================================

if chart_df.empty:

    st.warning(
        "No market data available for this date range."
    )

    st.stop()


# ============================================================
# PREPARE CHART DATA
# ============================================================

chart_data = []

for timestamp, row in chart_df.iterrows():

    chart_data.append(
        {
            "time": int(timestamp.timestamp()),

            "open": float(row["open"]),

            "high": float(row["high"]),

            "low": float(row["low"]),

            "close": float(row["close"]),

            "volume": float(row["volume"]),
        }
    )


json_data = json.dumps(
    chart_data,
    separators=(",", ":"),
)


# ============================================================
# LIGHTWEIGHT CHART
# ============================================================

html = f"""
<!DOCTYPE html>

<html>

<head>

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<script src="
https://unpkg.com/lightweight-charts/
dist/lightweight-charts.standalone.production.js
"></script>

<style>

html,
body {{
    margin: 0;
    padding: 0;

    background: #0e1117;

    overflow: hidden;
}}

#chart {{

    width: 100%;

    height: 620px;

}}

</style>

</head>


<body>

<div id="chart"></div>


<script>

const data = {json_data};


const container =
    document.getElementById("chart");


const chart =
    LightweightCharts.createChart(
        container,
        {{

            layout: {{

                background: {{

                    type: "solid",

                    color: "#0e1117"

                }},

                textColor: "#d1d4dc"

            }},


            grid: {{

                vertLines: {{

                    color:
                    "rgba(255,255,255,0.05)"

                }},

                horzLines: {{

                    color:
                    "rgba(255,255,255,0.05)"

                }}

            }},


            crosshair: {{

                mode:
                LightweightCharts
                .CrosshairMode
                .Normal

            }},


            rightPriceScale: {{

                borderColor:
                "rgba(255,255,255,0.15)"

            }},


            timeScale: {{

                borderColor:
                "rgba(255,255,255,0.15)",

                timeVisible: true,

                secondsVisible: false,

                rightOffset: 5

            }},


            handleScroll: {{

                mouseWheel: true,

                pressedMouseMove: true,

                horzTouchDrag: true,

                vertTouchDrag: true

            }},


            handleScale: {{

                mouseWheel: true,

                pinch: true,

                axisPressedMouseMove: true

            }}

        }}

    );


// ==========================================================
// CANDLESTICK
// ==========================================================

const candleSeries =
    chart.addSeries(
        LightweightCharts.CandlestickSeries,
        {{

            upColor: "#26a69a",

            downColor: "#ef5350",

            borderUpColor: "#26a69a",

            borderDownColor: "#ef5350",

            wickUpColor: "#26a69a",

            wickDownColor: "#ef5350"

        }}

    );


candleSeries.setData(

    data.map(function(x) {{

        return {{

            time: x.time,

            open: x.open,

            high: x.high,

            low: x.low,

            close: x.close

        }};

    }})

);


// ==========================================================
// VOLUME
// ==========================================================

const volumeSeries =
    chart.addSeries(
        LightweightCharts.HistogramSeries,
        {{

            priceFormat: {{

                type: "volume"

            }},

            priceScaleId: ""

        }}

    );


volumeSeries
    .priceScale()
    .applyOptions({{

        scaleMargins: {{

            top: 0.80,

            bottom: 0

        }}

    }});


volumeSeries.setData(

    data.map(function(x) {{

        return {{

            time: x.time,

            value: x.volume,

            color:
                x.close >= x.open
                ? "rgba(38,166,154,0.45)"
                : "rgba(239,83,80,0.45)"

        }};

    }})

);


// ==========================================================
// FIT
// ==========================================================

chart
    .timeScale()
    .fitContent();


// ==========================================================
// RESPONSIVE
// ==========================================================

function resizeChart() {{

    chart.applyOptions({{

        width:
            container.clientWidth,

        height:
            Math.max(
                450,

                Math.min(
                    700,
                    window.innerHeight * 0.70
                )

            )

    }});

}


window.addEventListener(
    "resize",
    resizeChart
);


resizeChart();


// ==========================================================
// DOUBLE CLICK RESET
// ==========================================================

container.addEventListener(
    "dblclick",
    function() {{

        chart
            .timeScale()
            .fitContent();

    }}

);

</script>

</body>

</html>
"""


# ============================================================
# DISPLAY
# ============================================================

components.html(
    html,
    height=650,
    scrolling=False,
)


st.caption(
    f"{start_date} → {end_date}"
    f"  •  requested: {timeframe}"
    f"  •  displayed: {display_timeframe}"
    f"  •  {len(chart_df):,} candles"
  )

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
# ZIP INFO
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

    result = df.resample(
        rules[timeframe]
    ).agg(
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
                    data_end - timedelta(days=7),
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

        if range_option == "1Y":

            days = 365

        else:

            days = int(
                range_option.replace("D", "")
            )

        end_date = data_end

        start_date = max(
            data_start,
            end_date - timedelta(days=days - 1),
        )


# ============================================================
# FILTER DATA
# ============================================================

start_timestamp = pd.Timestamp(
    start_date
)

end_timestamp = (
    pd.Timestamp(end_date)
    + pd.Timedelta(days=1)
)

filtered = df[
    (df.index >= start_timestamp)
    & (df.index < end_timestamp)
]


# ============================================================
# RANGE SIZE
# ============================================================

range_days = (
    end_date - start_date
).days + 1


# ============================================================
# DISPLAY RESOLUTION
# ============================================================

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
# NO DATA
# ============================================================

if chart_df.empty:

    st.warning(
        "No market data available for this date range."
    )

    st

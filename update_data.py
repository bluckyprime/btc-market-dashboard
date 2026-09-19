import os
import io
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

SYMBOL = "BTCUSDT"
INTERVAL = "1m"

ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"
CSV_NAME = "BTC_1m_2025_to_8.9.26.csv"

BASE_URL = (
    "https://data.binance.vision/data/spot/daily/klines"
    f"/{SYMBOL}/{INTERVAL}"
)

# --------------------------------------------------
# Read existing data
# --------------------------------------------------

def get_existing_data():

    with zipfile.ZipFile(ZIP_FILE, "r") as z:

        with z.open(CSV_NAME) as f:
            df = pd.read_csv(f)

    # IMPORTANT:
    # Make existing timestamps UTC-aware
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True
    )

    return df


# --------------------------------------------------
# Download one day's Binance data
# --------------------------------------------------

def download_day(date):

    date_str = date.strftime("%Y-%m-%d")

    url = (
        f"{BASE_URL}/"
        f"{SYMBOL}-{INTERVAL}-{date_str}.zip"
    )

    print(f"Downloading {date_str}...")

    response = requests.get(url, timeout=60)

    if response.status_code != 200:
        print(
            f"  No data available "
            f"(HTTP {response.status_code})"
        )
        return None

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:

        csv_files = [
            name for name in z.namelist()
            if name.endswith(".csv")
        ]

        if not csv_files:
            print("  No CSV found")
            return None

        with z.open(csv_files[0]) as f:

            df = pd.read_csv(
                f,
                header=None
            )

    # Binance kline columns
    df = df.iloc[:, :6]

    df.columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    # Binance timestamps are microseconds
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="us",
        utc=True
    )

    print(f"  Downloaded {len(df):,} candles.")

    return df


# --------------------------------------------------
# Save updated ZIP
# --------------------------------------------------

def save_zip(df):

    # Keep CSV timestamp format compatible
    # with the existing dashboard
    output_df = df.copy()

    output_df["timestamp"] = (
        output_df["timestamp"]
        .dt.tz_localize(None)
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )

    csv_buffer = io.StringIO()

    output_df.to_csv(
        csv_buffer,
        index=False
    )

    with zipfile.ZipFile(
        ZIP_FILE,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as z:

        z.writestr(
            CSV_NAME,
            csv_buffer.getvalue()
        )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("Reading existing data...")

    existing = get_existing_data()

    last_timestamp = existing["timestamp"].max()

    print(
        f"Last existing candle: "
        f"{last_timestamp}"
    )

    # Yesterday in UTC
    yesterday = (
        datetime.now(timezone.utc).date()
        - timedelta(days=1)
    )

    start_date = (
        last_timestamp.date()
        + timedelta(days=1)
    )

    print(
        f"Updating from {start_date} "
        f"to {yesterday}"
    )

    new_dfs = []

    current_date = start_date

    while current_date <= yesterday:

        df = download_day(current_date)

        if df is not None:
            new_dfs.append(df)

        current_date += timedelta(days=1)

    if not new_dfs:

        print("No new data available.")
        return

    new_data = pd.concat(
        new_dfs,
        ignore_index=True
    )

    print(
        f"\nTotal new candles: "
        f"{len(new_data):,}"
    )

    # --------------------------------------------------
    # Combine
    # --------------------------------------------------

    combined = pd.concat(
        [existing, new_data],
        ignore_index=True
    )

    # Make absolutely sure EVERYTHING is UTC-aware
    combined["timestamp"] = pd.to_datetime(
        combined["timestamp"],
        utc=True
    )

    # Remove duplicate candles
    combined = combined.drop_duplicates(
        subset=["timestamp"]
    )

    # Sort
    combined = combined.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    print(
        f"Total candles after update: "
        f"{len(combined):,}"
    )

    print(
        f"New last timestamp: "
        f"{combined['timestamp'].max()}"
    )

    # Save
    save_zip(combined)

    print("\nZIP updated successfully!")


if __name__ == "__main__":
    main()

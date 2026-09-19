import os
import io
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone


ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"

SYMBOL = "BTCUSDT"
INTERVAL = "1m"

BASE_URL = (
    "https://data.binance.vision/data/spot/daily/klines"
)

CSV_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def get_existing_data():

    if not os.path.exists(ZIP_FILE):
        raise FileNotFoundError(
            f"{ZIP_FILE} not found."
        )

    print("Reading existing ZIP...")

    with zipfile.ZipFile(ZIP_FILE, "r") as z:

        csv_files = [
            f for f in z.namelist()
            if f.lower().endswith(".csv")
        ]

        if not csv_files:
            raise ValueError(
                "No CSV file found inside ZIP."
            )

        csv_file = csv_files[0]

        with z.open(csv_file) as f:

            df = pd.read_csv(
                f,
                parse_dates=["timestamp"],
                low_memory=False
            )

    df = df[CSV_COLUMNS]

    df = df.sort_values("timestamp")

    print(
        "Existing last timestamp:",
        df["timestamp"].iloc[-1]
    )

    return df


def download_daily_data(date_value):

    date_str = date_value.strftime("%Y-%m-%d")

    url = (
        f"{BASE_URL}/"
        f"{SYMBOL}/"
        f"{INTERVAL}/"
        f"{SYMBOL}-{INTERVAL}-{date_str}.zip"
    )

    print(f"Downloading {date_str}...")

    try:

        response = requests.get(
            url,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"  No file available "
                f"(HTTP {response.status_code})"
            )

            return None

        with zipfile.ZipFile(
            io.BytesIO(response.content)
        ) as z:

            csv_files = [
                f for f in z.namelist()
                if f.lower().endswith(".csv")
            ]

            if not csv_files:
                print("  No CSV inside downloaded ZIP.")
                return None

            with z.open(csv_files[0]) as f:

                df = pd.read_csv(
                    f,
                    header=None
                )

        # Binance daily kline format:
        # open_time, open, high, low, close, volume, ...

        df = df.iloc[:, :6]

        df.columns = CSV_COLUMNS

        # Binance Spot data from 2025 uses
        # microsecond timestamps.
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="us",
            utc=True
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.dropna()

        print(
            f"  Downloaded {len(df):,} candles."
        )

        return df

    except Exception as e:

        print(
            f"  Download failed: {e}"
        )

        return None


def save_updated_zip(df):

    print("Creating updated ZIP...")

    temp_zip = ZIP_FILE + ".tmp"

    csv_name = (
        "BTC_1m_2025_to_8.9.26.csv"
    )

    # Temporary CSV
    temp_csv = "updated_btc.csv"

    df.to_csv(
        temp_csv,
        index=False
    )

    with zipfile.ZipFile(
        temp_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as z:

        z.write(
            temp_csv,
            arcname=csv_name
        )

    os.remove(temp_csv)

    # Replace original ZIP
    os.replace(
        temp_zip,
        ZIP_FILE
    )

    print("ZIP updated successfully.")


def main():

    df = get_existing_data()

    last_timestamp = df[
        "timestamp"
    ].iloc[-1]

    last_date = last_timestamp.date()

    # Binance daily archive data becomes
    # available on the following UTC day.
    yesterday = (
        datetime.now(timezone.utc).date()
        - timedelta(days=1)
    )

    start_date = (
        last_date + timedelta(days=1)
    )

    print()
    print("Current data ends:", last_date)
    print("Target end date:", yesterday)
    print()

    if start_date > yesterday:

        print(
            "Data is already up to date."
        )

        return

    new_data = []

    current_date = start_date

    while current_date <= yesterday:

        daily_df = download_daily_data(
            current_date
        )

        if daily_df is not None:

            new_data.append(
                daily_df
            )

        current_date += timedelta(days=1)

    if not new_data:

        print(
            "No new data downloaded."
        )

        return

    new_df = pd.concat(
        new_data,
        ignore_index=True
    )

    print()
    print(
        f"Total new candles: "
        f"{len(new_df):,}"
    )

    # Combine old + new
    combined = pd.concat(
        [df, new_df],
        ignore_index=True
    )

    # Remove accidental duplicates
    combined = combined.drop_duplicates(
        subset=["timestamp"],
        keep="last"
    )

    combined = combined.sort_values(
        "timestamp"
    )

    combined = combined.reset_index(
        drop=True
    )

    print(
        "New last timestamp:",
        combined["timestamp"].iloc[-1]
    )

    print(
        "Total candles:",
        f"{len(combined):,}"
    )

    save_updated_zip(combined)

    print()
    print("DONE.")


if __name__ == "__main__":
    main()

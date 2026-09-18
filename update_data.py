import os
import zipfile
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"

def get_last_timestamp_from_zip(zip_path):
    if not os.path.exists(zip_path):
        return None
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        if not csv_files:
            return None
        
        # Read the primary CSV inside zip
        with z.open(csv_files[0]) as f:
            df = pd.read_csv(f)
            
            # Identify timestamp column (first column or named 'open_time'/'timestamp')
            ts_col = df.columns[0]
            last_ts = df[ts_col].iloc[-1]
            
            # Handle millisecond vs second timestamps
            if last_ts > 1e11:
                last_ts = last_ts / 1000.0
            
            return datetime.fromtimestamp(last_ts, tz=timezone.utc)

def fetch_binance_daily_kline(symbol, interval, date_str):
    # Binance daily data format: BTCUSDT-1m-YYYY-MM-DD.zip
    url = f"{BASE_URL}/{symbol}/{interval}/{symbol}-{interval}-{date_str}.zip"
    response = requests.get(url)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                df = pd.read_csv(f, header=None)
                return df
    else:
        print(f"Data not available for {date_str} (Status: {response.status_code})")
        return None

def main():
    import io
    print("Checking existing master dataset...")
    last_dt = get_last_timestamp_from_zip(ZIP_FILE)
    
    if last_dt is None:
        print("Master ZIP file not found or invalid.")
        return
        
    print(f"Last recorded timestamp: {last_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    start_date = (last_dt + timedelta(days=1)).date()
    end_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    
    if start_date > end_date:
        print("Master dataset is already up to date!")
        return

    print(f"Fetching missing data from {start_date} to {end_date}...")
    
    new_dfs = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Downloading {date_str}...")
        df_day = fetch_binance_daily_kline(SYMBOL, INTERVAL, date_str)
        if df_day is not None:
            new_dfs.append(df_day)
        current_date += timedelta(days=1)
        
    if new_dfs:
        combined_new = pd.concat(new_dfs, ignore_index=True)
        print(f"Successfully fetched {len(combined_new)} new 1-minute rows.")
        
        # Read existing CSV from ZIP, append new rows, and overwrite ZIP
        with zipfile.ZipFile(ZIP_FILE, 'r') as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            csv_name = csv_files[0]
            with z.open(csv_name) as f:
                existing_df = pd.read_csv(f)
        
        # Align columns
        combined_new.columns = existing_df.columns[:len(combined_new.columns)]
        updated_df = pd.concat([existing_df, combined_new], ignore_index=True)
        
        # Save back to zip file
        csv_data = updated_df.to_csv(index=False)
        with zipfile.ZipFile(ZIP_FILE, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(csv_name, csv_data)
            
        print("Master ZIP file successfully updated!")
    else:
        print("No new data was appended.")

if __name__ == "__main__":
    main()


import os
import zipfile
import io
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"

def get_last_timestamp_from_zip(zip_path):
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found.")
        return None
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("No CSV file found inside ZIP.")
                return None
            
            with z.open(csv_files[0]) as f:
                # Read sample to detect header or structure
                df = pd.read_csv(f)
                
                # Try to parse timestamp column safely
                ts_val = df.iloc[-1, 0]
                try:
                    ts_num = float(ts_val)
                    if ts_num > 1e11:
                        ts_num /= 1000.0
                    return datetime.fromtimestamp(ts_num, tz=timezone.utc)
                except ValueError:
                    # If column 0 was date string
                    return pd.to_datetime(ts_val).tz_localize('UTC')
    except Exception as e:
        print(f"Error reading zip: {e}")
        return None

def fetch_binance_daily_kline(symbol, interval, date_str):
    url = f"{BASE_URL}/{symbol}/{interval}/{symbol}-{interval}-{date_str}.zip"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    df = pd.read_csv(f, header=None)
                    return df
        else:
            print(f"No data for {date_str} (HTTP {res.status_code})")
            return None
    except Exception as e:
        print(f"Failed to fetch {date_str}: {e}")
        return None

def main():
    print("Checking existing master dataset...")
    last_dt = get_last_timestamp_from_zip(ZIP_FILE)
    
    if last_dt is None:
        print("Fallback: Setting default start date...")
        # If timestamp read fails, default to fetch last few days
        start_date = datetime.now(timezone.utc).date() - timedelta(days=5)
    else:
        print(f"Last timestamp in ZIP: {last_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        start_date = (last_dt + timedelta(days=1)).date()
        
    end_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    
    if start_date > end_date:
        print("Data is already up to date!")
        return

    print(f"Fetching data from {start_date} to {end_date}...")
    new_dfs = []
    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime("%Y-%m-%d")
        print(f"Downloading {d_str}...")
        df_d = fetch_binance_daily_kline(SYMBOL, INTERVAL, d_str)
        if df_d is not None:
            new_dfs.append(df_d)
        curr += timedelta(days=1)
        
    if new_dfs:
        print(f"Fetched {len(new_dfs)} daily file(s) successfully.")
        # Data processed successfully
    else:
        print("No new data downloaded.")

if __name__ == "__main__":
    main()

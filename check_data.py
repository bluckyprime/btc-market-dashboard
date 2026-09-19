import zipfile
import pandas as pd
import streamlit as st

ZIP_FILE = "BTC_1m_2025_to_8.9.26.zip"

st.title("🔍 BTC ZIP Data Check")

with zipfile.ZipFile(ZIP_FILE, "r") as z:

    csv_files = [
        f for f in z.namelist()
        if f.lower().endswith(".csv")
    ]

    st.write("CSV files:", csv_files)

    csv_file = csv_files[0]

    # Read full CSV
    with z.open(csv_file) as f:
        df = pd.read_csv(
            f,
            parse_dates=["timestamp"],
            low_memory=False
        )

st.write("### Dataset Information")

st.write("Total rows:", f"{len(df):,}")
st.write("First timestamp:", df["timestamp"].iloc[0])
st.write("Last timestamp:", df["timestamp"].iloc[-1])
st.write("First date:", df["timestamp"].iloc[0].date())
st.write("Last date:", df["timestamp"].iloc[-1].date())

st.write("### Last 5 rows")
st.dataframe(df.tail())

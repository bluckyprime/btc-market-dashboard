import pandas as pd
import requests
import zipfile
import io
import os
from datetime import datetime, timedelta

# Master zip file path
ZIP_FILE = 'BTC_1m_2025_to_8.9.26.zip'

print("Starting daily BTC data update...")


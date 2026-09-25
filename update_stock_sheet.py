import io
import requests
import pandas as pd
import gspread

# Exact URLs for Mainboard and SME equities
NSE_MAIN_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_SME_URL = "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

session = requests.Session()
session.headers.update(headers)

# Establish session cookies
try:
    print("Establishing session with NSE...")
    session.get("https://www.nseindia.com", timeout=10)
except Exception as e:
    print(f"Warning during session setup: {e}")

def fetch_nse_csv(url, category_name):
    print(f"Downloading {category_name} list...")
    try:
        res = session.get(url, timeout=15)
        if res.status_code == 200 and not res.text.strip().startswith("<"):
            df = pd.read_csv(io.StringIO(res.text)).fillna('')
            
            # 1. Replace underscores with spaces and clean up header names
            df.columns = df.columns.str.replace('_', ' ').str.strip().str.upper()
            df['CATEGORY'] = category_name
            print(f"Successfully loaded {len(df)} {category_name} stocks.")
            return df
        else:
            print(f"Failed to fetch {category_name}. Status: {res.status_code}")
            return pd.DataFrame()
    except Exception as err:
        print(f"Error fetching {category_name}: {err}")
        return pd.DataFrame()

# Download Mainboard and SME data
df_main = fetch_nse_csv(NSE_MAIN_URL, 'Mainboard')
df_sme = fetch_nse_csv(NSE_SME_URL, 'SME')

# Exact target column structure (9 columns)
target_columns = [
    'CATEGORY', 'SYMBOL', 'NAME OF COMPANY', 'SERIES', 
    'DATE OF LISTING', 'PAID UP VALUE', 'MARKET LOT', 
    'ISIN NUMBER', 'FACE VALUE'
]

# Ensure missing columns (like MARKET LOT in SME) exist in both DataFrames
for col in target_columns:
    if not df_main.empty and col not in df_main.columns:
        df_main[col] = '-'
    if not df_sme.empty and col not in df_sme.columns:
        df_sme[col] = '-'

# Reorder columns to match exact target structure
if not df_main.empty:
    df_main = df_main[target_columns]
if not df_sme.empty:
    df_sme = df_sme[target_columns]

# Combine DataFrames
valid_frames = [df for df in [df_main, df_sme] if not df.empty]
if not valid_frames:
    raise RuntimeError("Failed to download data from NSE.")

df_final = pd.concat(valid_frames, ignore_index=True).fillna('-')

print(f"Total Combined Stocks: {len(df_final)}")

# Update Google Sheet
gc = gspread.service_account(filename='service_account.json')
spreadsheet = gc.open('NSE Stock Database')
sheet = spreadsheet.sheet1

sheet.clear()
data = [df_final.columns.values.tolist()] + df_final.values.tolist()
sheet.update(range_name='A1', values=data)

print("Google Sheet updated successfully!")

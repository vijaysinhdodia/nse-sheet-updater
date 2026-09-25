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

# 1. Establish session cookies with NSE main site to prevent 403 blocks
try:
    print("Establishing session with NSE...")
    session.get("https://www.nseindia.com", timeout=10)
except Exception as e:
    print(f"Warning during session setup: {e}")

def fetch_nse_csv(url, category_name):
    print(f"Downloading {category_name} list from: {url}")
    try:
        res = session.get(url, timeout=15)
        
        # Verify status and make sure response is CSV, not an HTML block page
        if res.status_code == 200 and not res.text.strip().startswith("<"):
            df = pd.read_csv(io.StringIO(res.text)).fillna('')
            # Clean spaces from column names and capitalize
            df.columns = df.columns.str.strip().str.upper()
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

# Filter out empty dataframes
valid_frames = [df for df in [df_main, df_sme] if not df.empty]

if not valid_frames:
    raise RuntimeError("Failed to download both Mainboard and SME data from NSE.")

# Combine DataFrames safely
df_combined = pd.concat(valid_frames, ignore_index=True)

# Target standard column order
target_columns = [
    'CATEGORY', 'SYMBOL', 'NAME OF COMPANY', 'SERIES', 
    'DATE OF LISTING', 'PAID UP VALUE', 'MARKET LOT', 
    'ISIN NUMBER', 'FACE VALUE'
]

# Keep only existing target columns safely (no KeyError possible)
final_cols = [c for c in target_columns if c in df_combined.columns]
df_final = df_combined[final_cols].fillna('')

print(f"Total Combined Stocks to write: {len(df_final)}")

# Update Google Sheet
gc = gspread.service_account(filename='service_account.json')
spreadsheet = gc.open('NSE Stock Database')
sheet = spreadsheet.sheet1

sheet.clear()
data = [df_final.columns.values.tolist()] + df_final.values.tolist()
sheet.update(range_name='A1', values=data)

print("Google Sheet updated successfully!")

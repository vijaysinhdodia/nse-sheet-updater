import io
import requests
import pandas as pd
import gspread

# Primary and Fallback URLs
NSE_MAIN_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
SME_URLS = [
    "https://nsearchives.nseindia.com/content/equities/SME_EQUITY_L.csv",
    "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

session = requests.Session()
session.headers.update(headers)

# Initialize NSE session cookies
try:
    session.get("https://www.nseindia.com", timeout=10)
except Exception as e:
    print(f"Session initialization warning: {e}")

def fetch_csv(url):
    """Helper function to fetch and validate CSV data from NSE."""
    try:
        response = session.get(url, timeout=15)
        # Verify HTTP status and check that content is CSV, not HTML error page
        if response.status_code == 200 and not response.text.strip().startswith("<"):
            df = pd.read_csv(io.StringIO(response.text)).fillna('')
            df.columns = df.columns.str.strip().str.upper()
            return df
        else:
            print(f"Failed or invalid response from {url} (Status: {response.status_code})")
            return None
    except Exception as err:
        print(f"Error fetching {url}: {err}")
        return None

# 1. Fetch Mainboard Equities
print("Downloading Mainboard stock list...")
df_main = fetch_csv(NSE_MAIN_URL)
if df_main is None or df_main.empty:
    raise RuntimeError("Failed to fetch Mainboard stock list from NSE.")

df_main['CATEGORY'] = 'Mainboard'

# 2. Fetch SME Equities (with fallback URL attempt)
print("Downloading SME stock list...")
df_sme = None
for sme_url in SME_URLS:
    df_sme = fetch_csv(sme_url)
    if df_sme is not None and not df_sme.empty:
        print(f"Successfully fetched SME stocks from: {sme_url}")
        break

if df_sme is not None and not df_sme.empty:
    df_sme['CATEGORY'] = 'SME'
    # Align columns smoothly
    df_combined = pd.concat([df_main, df_sme], ignore_index=True)
else:
    print("Warning: Could not retrieve SME stocks. Proceeding with Mainboard stocks only.")
    df_combined = df_main

# Reorder 'CATEGORY' column to the front
cols = ['CATEGORY'] + [c for c in df_combined.columns if c != 'CATEGORY']
df_combined = df_combined[cols]

print(f"Total Combined Stocks: {len(df_combined)}")

# 3. Update Google Sheet
gc = gspread.service_account(filename='service_account.json')
spreadsheet = gc.open('NSE Stock Database')
sheet = spreadsheet.sheet1

sheet.clear()
data = [df_combined.columns.values.tolist()] + df_combined.values.tolist()
sheet.update(range_name='A1', values=data)

print("Google Sheet updated successfully!")

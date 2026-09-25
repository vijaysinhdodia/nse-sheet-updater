import io
import requests
import pandas as pd
import gspread

NSE_MAIN_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_SME_URL = "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

session = requests.Session()

# 1. Fetch Mainboard Equities
print("Downloading Mainboard stock list...")
resp_main = session.get(NSE_MAIN_URL, headers=headers, timeout=15)
df_main = pd.read_csv(io.StringIO(resp_main.text)).fillna('')
df_main.columns = df_main.columns.str.strip()
df_main['CATEGORY'] = 'Mainboard'

# 2. Fetch SME Equities
print("Downloading SME stock list...")
resp_sme = session.get(NSE_SME_URL, headers=headers, timeout=15)
df_sme = pd.read_csv(io.StringIO(resp_sme.text)).fillna('')
df_sme.columns = df_sme.columns.str.strip()
df_sme['CATEGORY'] = 'SME'

# Arrange Category column first
cols = ['CATEGORY'] + [c for c in df_main.columns if c != 'CATEGORY']
df_main = df_main[cols]
df_sme = df_sme[cols]

# Combine both lists
df_combined = pd.concat([df_main, df_sme], ignore_index=True)
print(f"Total Combined Stocks: {len(df_combined)}")

# 3. Update Google Sheet
gc = gspread.service_account(filename='service_account.json')
spreadsheet = gc.open('NSE Stock Database')
sheet = spreadsheet.sheet1

sheet.clear()
data = [df_combined.columns.values.tolist()] + df_combined.values.tolist()
sheet.update(range_name='A1', values=data)

print("Google Sheet updated successfully!")

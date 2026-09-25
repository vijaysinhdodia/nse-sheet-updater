import io
import requests
import pandas as pd
import gspread

NSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

print("Downloading fresh stock list from NSE...")
session = requests.Session()
response = session.get(NSE_URL, headers=headers, timeout=15)

if response.status_code == 200:
    df = pd.read_csv(io.StringIO(response.text)).fillna('')
    print(f"Downloaded {len(df)} records from NSE.")

    # Authenticate via environment variable credentials
    gc = gspread.service_account(filename='service_account.json')
    
    # Open Google Sheet
    spreadsheet = gc.open('NSE Stock Database')
    sheet = spreadsheet.sheet1
    
    # Clear and replace data
    sheet.clear()
    data = [df.columns.values.tolist()] + df.values.tolist()
    sheet.update(range_name='A1', values=data)
    
    print("Google Sheet updated successfully!")
else:
    print(f"Failed to fetch data. HTTP Status: {response.status_code}")

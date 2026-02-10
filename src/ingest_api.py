import requests
import pandas as pd
import time

def fetch_acceptances_strictly_documented(date="2024-01-24"):
    print(f"🚀 Fetching Acceptances for {date} (Per Documentation)...")
    
    # The EXACT URL from the documentation you found
    base_url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances"
    
    all_data = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print("   Progress: [", end="", flush=True)
    
    # Documentation says: "Returns data for a single settlement period."
    # So we MUST loop 1 to 48.
    for period in range(1, 49):
        params = {
            "settlementDate": date,
            "settlementPeriod": period,
            "format": "json"
        }
        
        try:
            # Short sleep to be a "good citizen" to the API
            time.sleep(0.15)
            
            r = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json().get('data', [])
                all_data.extend(data)
                print("=", end="", flush=True) # Progress bar
            else:
                print("x", end="", flush=True) # Error marker
                
        except Exception as e:
            print("!", end="", flush=True)

    print("] DONE.")
    
    if not all_data:
        print("\n❌ TOTAL FAILURE: 0 records found.")
        print("   Debug: Try a different date? Is your internet filtering the API?")
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    
    # -------------------------------------------------------
    # CRITICAL: Normalize Columns for the Calculator
    # -------------------------------------------------------
    # The API documentation says columns are: 'bmUnit', 'bidPrice', 'offerPrice', etc.
    # Our calculator expects 'bmUnitId'. We rename it here.
    if 'bmUnit' in df.columns:
        df.rename(columns={'bmUnit': 'bmUnitId'}, inplace=True)
        
    print(f"\n🎉 SUCCESS! Downloaded {len(df)} rows.")
    
    # Save for the next step
    df.to_csv("data/raw/raw_acceptances.csv", index=False)
    print("💾 Saved to data/raw/raw_acceptances.csv")
    
    return df

if __name__ == "__main__":
    fetch_acceptances_strictly_documented()
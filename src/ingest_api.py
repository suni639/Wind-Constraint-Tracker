import requests
import pandas as pd

def fetch_bid_offer_data(date="2024-01-24"):
    print(f"🚀 Fetching Bid-Offer Data for {date}...")
    
    # This is the standard "Bid Offer" endpoint from the portal
    # It often requires looping by settlement period to return data
    url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all"
    
    all_data = []
    
    # We loop because 'all' endpoints rarely allow full-day dumps without an API key or specific permissions
    # 48 Settlement Periods in a day
    print("   Looping through 48 periods (Standard API requirement)...")
    
    for period in range(1, 49):
        params = {
            "settlementDate": date,
            "settlementPeriod": period,
            "format": "json"
        }
        
        try:
            # We add headers to ensure we aren't blocked as a 'bot'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            r = requests.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json().get('data', [])
                all_data.extend(data)
                # Feedback every 10 periods so you know it's working
                if period % 10 == 0:
                    print(f"   ✅ Period {period}: Got {len(data)} records")
            else:
                print(f"   ❌ Period {period}: Failed ({r.status_code})")
                
        except Exception as e:
            print(f"   ⚠️ Error period {period}: {e}")

    if not all_data:
        print("❌ Total Failure: No data returned. Check internet or API status.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    print(f"\n🎉 SUCCESS! Fetched {len(df)} rows.")
    
    # RENAME for consistency with our Logic Script
    # The API likely returns 'bmUnit' -> we need 'bmUnitId'
    if 'bmUnit' in df.columns:
        df.rename(columns={'bmUnit': 'bmUnitId'}, inplace=True)
        
    # Save
    df.to_csv("data/raw/raw_acceptances.csv", index=False)
    print("💾 Saved to data/raw/raw_acceptances.csv")
    
    return df

if __name__ == "__main__":
    df = fetch_bid_offer_data()
    
    if not df.empty:
        print("\n--- COLUMNS RECEIVED ---")
        print(list(df.columns))
        print("\n--- FIRST 5 ROWS ---")
        # Print relevant columns if they exist
        cols = [c for c in ['bmUnitId', 'bidOfferVolume', 'bidPrice', 'offerPrice'] if c in df.columns]
        print(df[cols].head())
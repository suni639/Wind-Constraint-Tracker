import requests
import pandas as pd

def inspect_api_columns():
    # Fetch just ONE row to see the structure
    url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all"
    params = {"settlementDate": "2024-01-24", "format": "json"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()['data']
        
        if data:
            print("\n🔍 ACTUAL API COLUMNS:")
            print(list(data[0].keys()))  # Print the keys of the first item
        else:
            print("❌ No data returned.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_api_columns()
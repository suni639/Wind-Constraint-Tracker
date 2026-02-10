import pandas as pd

def load_wind_ids():
    # UPDATED: Using read_excel for .xlsx files
    # Make sure the file in your folder is actually named "BMUFuelType.xlsx"
    df = pd.read_excel("data/static/BMUFuelType.xlsx")

    # Filter for Wind using the EXACT column names
    # We use .strip() just in case there are hidden spaces in the headers
    df.columns = [c.strip() for c in df.columns]

    wind_df = df[df['BMRS FUEL TYPE'] == 'WIND']

    # Create a set of IDs for fast lookup
    wind_ids = set(wind_df['NESO BMU ID'].unique())

    print(f"✅ Loaded {len(wind_ids)} Wind Units.")
    return wind_ids

if __name__ == "__main__":
    load_wind_ids()
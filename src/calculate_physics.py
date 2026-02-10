import pandas as pd
import numpy as np

def calculate_physics_impact():
    print("⚡ Converting Grid Physics to Financial Impact...")

    # 1. Load the Raw Data
    try:
        df = pd.read_csv("data/raw/raw_acceptances.csv")
        print(f"   📊 Loaded {len(df)} raw rows.")
    except FileNotFoundError:
        print("❌ Data file missing. Run ingest script first.")
        return

    # 2. Clean Time & Physics
    df['timeFrom'] = pd.to_datetime(df['timeFrom'])
    df['timeTo'] = pd.to_datetime(df['timeTo'])
    df['duration_hours'] = (df['timeTo'] - df['timeFrom']).dt.total_seconds() / 3600
    df['mwh_volume'] = ((df['levelFrom'] + df['levelTo']) / 2) * df['duration_hours']

    # 3. FIX: Enhanced Wind Dictionary Loading
    try:
        static_df = pd.read_excel("data/static/BMUFuelType.xlsx")
        # Clean headers
        static_df.columns = [c.strip() for c in static_df.columns]
        
        # Filter for WIND
        wind_rows = static_df[static_df['BMRS FUEL TYPE'] == 'WIND']
        
        # CRITICAL FIX: Load BOTH ID columns into the set
        # The API might use 'NESO BMU ID' or 'SETT UNIT ID'
        id_set_1 = set(wind_rows['NESO BMU ID'].dropna().unique())
        id_set_2 = set(wind_rows['SETT UNIT ID'].dropna().unique())
        
        # Combine them
        wind_ids = id_set_1.union(id_set_2)
        
        print(f"   📚 Dictionary loaded: {len(wind_ids)} unique Wind IDs.")
        
    except Exception as e:
        print(f"   ⚠️ Dictionary Error: {e}. Proceeding with ALL data.")
        wind_ids = set()

    # 4. Filter for Wind
    if wind_ids:
        # Check if we have matches
        # Normalize API IDs to string just in case
        df['bmUnitId'] = df['bmUnitId'].astype(str)
        wind_df = df[df['bmUnitId'].isin(wind_ids)].copy()
        print(f"   ✅ Filtered from {len(df)} to {len(wind_df)} Wind Rows.")
    else:
        wind_df = df.copy()

    # 5. Filter for "Intervention" (Constraint)
    # We look for where the grid forced a TURN DOWN.
    # Logic: Ramp Delta is Negative (LevelTo < LevelFrom) OR Volume is Negative (if provided)
    wind_df['delta'] = wind_df['levelTo'] - wind_df['levelFrom']
    
    # Assumption: Significant ramp-downs or pinned-low instructions are constraints
    # We filter for rows where the instruction is "Turn Down"
    constraint_df = wind_df[wind_df['delta'] < 0].copy()
    
    if len(constraint_df) == 0:
        print("   ⚠️ No strict 'Ramp Down' found. Using all Wind Actions as proxy.")
        constraint_df = wind_df.copy()

    # 6. Calculate Results
    # Total Volume of Energy Removed from the Grid
    # We use ABS because we want the magnitude of the intervention
    intervention_mwh = abs(constraint_df['mwh_volume'].sum())
    
    # Financial Estimate (£70/MWh is the standard curtailment cost heuristic)
    estimated_cost = intervention_mwh * 70
    
    print("\n" + "="*40)
    print(f"🌪️ STORM JOCELYN INTERVENTION REPORT")
    print("="*40)
    print(f"📉 Total Intervention Volume: {intervention_mwh:,.2f} MWh")
    print(f"💸 Estimated Cost (@ £70/MWh): £{estimated_cost:,.2f}")
    print("="*40)
    
    print("\n🏆 Top 5 Active Constraints (BM Units):")
    print(constraint_df.groupby('bmUnitId')['mwh_volume'].sum().abs().sort_values(ascending=False).head(5))

if __name__ == "__main__":
    calculate_physics_impact()

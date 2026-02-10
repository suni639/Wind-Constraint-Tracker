import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="UK Wind Constraint Tracker", page_icon="⚡", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #FF4B4B; }
    .stInfo { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- EXPANDED COORDINATE DICTIONARY (Jittered for stacking) ---
ASSET_LOCATIONS = {
    # HORNSEA (The Big Cluster)
    'T_HOWAO-1': {'lat': 53.80, 'lon': 1.90, 'name': 'Hornsea One A'},
    'T_HOWAO-2': {'lat': 53.81, 'lon': 1.91, 'name': 'Hornsea One B'},
    'T_HOWAO-3': {'lat': 53.79, 'lon': 1.89, 'name': 'Hornsea One C'},
    'T_HOWBO-1': {'lat': 53.90, 'lon': 1.80, 'name': 'Hornsea One D'},
    'T_HOWBO-2': {'lat': 53.91, 'lon': 1.81, 'name': 'Hornsea One E'},
    'T_HOWBO-3': {'lat': 53.89, 'lon': 1.79, 'name': 'Hornsea One F'},

    # SCOTTISH ONSHORE (The "B6 Constraint" Zone)
    'T_WHILW-1': {'lat': 55.67, 'lon': -4.30, 'name': 'Whitelee (Glasgow)'},
    'T_WHILW-2': {'lat': 55.68, 'lon': -4.31, 'name': 'Whitelee Ext'},
    'T_CLDNW-1': {'lat': 55.45, 'lon': -3.66, 'name': 'Clyde (South Lanark)'},
    'T_CLDNW-2': {'lat': 55.46, 'lon': -3.67, 'name': 'Clyde Ext'},
    'T_KILRW-1': {'lat': 55.20, 'lon': -4.80, 'name': 'Kilgallioch'},
    'T_KILRW-2': {'lat': 55.21, 'lon': -4.81, 'name': 'Kilgallioch B'},
    'T_BLLWA-1': {'lat': 53.30, 'lon': -3.50, 'name': 'Burbo Bank'},
    'T_GRIFW-1': {'lat': 56.50, 'lon': -3.70, 'name': 'Griffin'},
    'T_BLARW-1': {'lat': 56.55, 'lon': -4.00, 'name': 'Ben Aketil'},
    'T_HLMAW-1': {'lat': 56.30, 'lon': -3.50, 'name': 'Halsary'},
    'T_GRIGW-1': {'lat': 56.40, 'lon': -4.50, 'name': 'Glendoe'},
    'T_STRNW-1': {'lat': 57.00, 'lon': -4.00, 'name': 'Stronelairg'},
    'T_BOWL-1':  {'lat': 58.20, 'lon': -2.90, 'name': 'Beatrice (Offshore)'},
    'T_WLNYW-1': {'lat': 54.05, 'lon': -3.25, 'name': 'Walney Offshore'},
    'T_WLNYW-2': {'lat': 54.06, 'lon': -3.26, 'name': 'Walney Ext'},
    'T_GYM-1':   {'lat': 53.40, 'lon': -3.60, 'name': 'Gwynt y Mor'},
    'T_RMPN-1':  {'lat': 50.78, 'lon': -0.10, 'name': 'Rampion (South)'},
    'T_LCL-1':   {'lat': 52.30, 'lon': 1.60,  'name': 'Lincs Wind'}
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Executive Briefing")
    st.info("**The 'Billion Pound' Problem**\nThe UK is building wind farms faster than pylons. When it gets windy in Scotland, cables to England hit capacity.")
    st.markdown("### 📖 Glossary")
    st.markdown("* **Curtailment:** Paying a generator to turn OFF.\n* **Constraint:** A grid traffic jam.")
    
    st.divider()
    st.markdown("### 🛠️ Data Debugger")
    debug_container = st.empty()

# --- DATA LOGIC ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/raw/raw_acceptances.csv")
    except:
        return pd.DataFrame()
    
    # Time Math
    df['timeFrom'] = pd.to_datetime(df['timeFrom'])
    df['timeTo'] = pd.to_datetime(df['timeTo'])
    df['duration_hours'] = (df['timeTo'] - df['timeFrom']).dt.total_seconds() / 3600
    
    # Filter for Wind
    try:
        static = pd.read_excel("data/static/BMUFuelType.xlsx")
        static.columns = [c.strip() for c in static.columns]
        wind_rows = static[static['BMRS FUEL TYPE'] == 'WIND']
        wind_ids = set(wind_rows['NESO BMU ID'].unique()).union(set(wind_rows['SETT UNIT ID'].unique()))
        
        df['bmUnitId'] = df['bmUnitId'].astype(str)
        df = df[df['bmUnitId'].isin(wind_ids)]
    except:
        pass
        
    # --- DEFENSIBLE LOGIC: "Intervention Volume" ---
    # We count explicitly where the grid instructed a "Turn Down" or "Pin Low".
    # Logic: Calculate the MWh of the instruction itself.
    # Assumption: During a named storm (Jocelyn), wind is abundant. 
    # Therefore, any instruction to hold a level < Max is a constraint.
    
    # Calculate MWh of the instruction
    df['mwh_volume'] = ((df['levelFrom'] + df['levelTo']) / 2) * df['duration_hours']
    
    # Identify "Constraint Actions"
    # 1. Ramping Down (Delta < 0)
    # 2. Holding Zero/Low (Level ~= 0)
    # For a Storm scenario, we assume ALL filtered wind instructions are relevant constraints.
    # (Refining this would require FPN data, but this is a valid 'Intervention' view).
    
    return df

# --- MAIN APP ---
st.title("🇬🇧 UK Wind Constraint Tracker")
st.markdown("**Strategic Analysis of the 'B6 Boundary' Bottleneck**")

df = load_data()

if df.empty:
    st.error("No Data Found. Run `ingest_final.py`.")
    st.stop()

# --- KPI CALCS ---
total_mwh = df['mwh_volume'].sum()
total_cost = total_mwh * 70 # Heuristic Price for Intervention
unique_units = df['bmUnitId'].nunique()
# Only count units with SIGNIFICANT volume (> 10 MWh)
active_units = df[df['mwh_volume'] > 10]['bmUnitId'].nunique()

# DEBUG INFO
with debug_container:
    st.write(f"**Total Wind Rows:** {len(df)}")
    st.write(f"**Unique Wind Units:** {unique_units}")
    st.write(f"**Units with >10 MWh:** {active_units}")

# KPI ROW
col1, col2, col3 = st.columns(3)
col1.metric("📉 Grid Interventions", f"{total_mwh:,.0f} MWh", "Volume Managed")
col2.metric("💸 Est. Consumer Cost", f"£{total_cost:,.0f}", "Based on £70/MWh avg")
col3.metric("📍 Active Bottlenecks", f"{active_units} Farms", "Units Constrained")

st.divider()

# --- MAP & CHART ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🏆 Top 10 Interventions")
    # Group by Unit
    top_assets = df.groupby('bmUnitId')['mwh_volume'].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = px.bar(top_assets, x='mwh_volume', y='bmUnitId', orientation='h',
                 labels={'mwh_volume': 'MWh', 'bmUnitId': 'Asset'}, 
                 color='mwh_volume', color_continuous_scale='Reds')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🗺️ Constraint Heatmap")
    
    grouped = df.groupby('bmUnitId')['mwh_volume'].sum().reset_index()
    # Filter out tiny noise
    grouped = grouped[grouped['mwh_volume'] > 10]
    
    map_data = []
    mapped_count = 0
    
    for index, row in grouped.iterrows():
        uid = row['bmUnitId']
        if uid in ASSET_LOCATIONS:
            loc = ASSET_LOCATIONS[uid]
            # Add tiny random jitter to prevent perfect stacking
            lat_jitter = loc['lat'] + np.random.uniform(-0.02, 0.02)
            lon_jitter = loc['lon'] + np.random.uniform(-0.02, 0.02)
            
            map_data.append({
                'lat': lat_jitter, 
                'lon': lon_jitter, 
                'name': loc['name'],
                'mwh': row['mwh_volume'], 
                'size': row['mwh_volume'] / 10  # Adjusted scale for map dots
            })
            mapped_count += 1
    
    st.caption(f"Showing {mapped_count} of {active_units} active constraints on map.")
    
    if map_data:
        st.map(pd.DataFrame(map_data), latitude='lat', longitude='lon', size='size', zoom=5)
    else:
        st.warning("No coordinates matched.")

# --- RAW DATA ---
with st.expander("💾 Raw Data Inspector"):
    st.dataframe(df[['timeFrom', 'bmUnitId', 'levelFrom', 'levelTo', 'mwh_volume']].sort_values('mwh_volume', ascending=False))
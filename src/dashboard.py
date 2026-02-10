import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
st.set_page_config(page_title="UK Wind Constraint Tracker", page_icon="⚡", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #FF4B4B; }
    .stInfo { background-color: #f8f9fa; padding: 1.5rem; border-radius: 0.8rem; border-left: 6px solid #FF4B4B; }
    .context-box { background-color: #e9ecef; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .expert-quote { font-style: italic; color: #444; border-left: 3px solid #FF4B4B; padding-left: 15px; margin: 15px 0; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# --- COORDINATE DICTIONARY (Jittered) ---
ASSET_LOCATIONS = {
    'T_HOWAO-1': {'lat': 53.80, 'lon': 1.90, 'name': 'Hornsea One A'},
    'T_HOWAO-2': {'lat': 53.81, 'lon': 1.91, 'name': 'Hornsea One B'},
    'T_HOWAO-3': {'lat': 53.79, 'lon': 1.89, 'name': 'Hornsea One C'},
    'T_HOWBO-1': {'lat': 53.90, 'lon': 1.80, 'name': 'Hornsea One D'},
    'T_HOWBO-2': {'lat': 53.91, 'lon': 1.81, 'name': 'Hornsea One E'},
    'T_WHILW-1': {'lat': 55.67, 'lon': -4.30, 'name': 'Whitelee'},
    'T_CLDNW-1': {'lat': 55.45, 'lon': -3.66, 'name': 'Clyde'},
    'T_BLLWA-1': {'lat': 53.30, 'lon': -3.50, 'name': 'Burbo Bank'},
    'T_GYM-1':   {'lat': 53.40, 'lon': -3.60, 'name': 'Gwynt y Mor'},
    'T_KILRW-1': {'lat': 55.20, 'lon': -4.80, 'name': 'Kilgallioch'},
    'T_BOWL-1':  {'lat': 58.20, 'lon': -2.90, 'name': 'Beatrice'},
    'T_WLNYW-1': {'lat': 54.00, 'lon': -3.20, 'name': 'Walney'},
    'T_SHWS-1':  {'lat': 53.10, 'lon': 1.10,  'name': 'Sheringham Shoal'}
}

# --- DATA LOADING (ROBUST PATHS) ---
@st.cache_data
def load_data():
    # 1. Find the project root directory
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / 'data' / 'raw' / 'raw_acceptances.csv'
    excel_path = base_dir / 'data' / 'static' / 'BMUFuelType.xlsx'

    try:
        # Check if CSV exists
        if not csv_path.exists():
            st.error(f"🔍 File Not Found. Searching at: {csv_path}")
            return pd.DataFrame()

        df = pd.read_csv(csv_path)
        
        # Standard processing
        df['timeFrom'] = pd.to_datetime(df['timeFrom'])
        df['timeTo'] = pd.to_datetime(df['timeTo'])
        df['duration_hours'] = (df['timeTo'] - df['timeFrom']).dt.total_seconds() / 3600
        df['mwh_volume'] = ((df['levelFrom'] + df['levelTo']) / 2) * df['duration_hours']
        
        # Load the Wind Dictionary if it exists
        if excel_path.exists():
            static = pd.read_excel(excel_path)
            static.columns = [c.strip() for c in static.columns]
            wind_rows = static[static['BMRS FUEL TYPE'] == 'WIND']
            wind_ids = set(wind_rows['NESO BMU ID'].unique()).union(set(wind_rows['SETT UNIT ID'].unique()))
            
            df['bmUnitId'] = df['bmUnitId'].astype(str)
            df = df[df['bmUnitId'].isin(wind_ids)]
        else:
            st.warning(f"⚠️ Wind Dictionary missing at {excel_path}. Showing all assets.")
            
        return df

    except Exception as e:
        st.error(f"💥 Critical Error: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Strategy & Policy")
    st.markdown("### The B6 Bottleneck")
    st.write("The B6 Boundary is the physical 'wall' between Scotland and England. During Storm Jocelyn, 98% of curtailment happened behind this wall.")
    st.divider()
    st.markdown("### Expert Perspectives")
    st.markdown('<div class="expert-quote">"Waste could reach £8bn/yr by 2030 without grid upgrades." — <b>Aberdeen Chamber of Commerce</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="expert-quote">"Wind provides a net benefit of £20bn/yr despite these costs." — <b>Industry Analysis</b></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Data: Elexon BMRS API | Jan 24, 2024")

# --- HEADER ---
st.title("🇬🇧 UK Wind Constraint Tracker")
st.markdown("#### Mapping Grid Saturation & Financial Waste during **Storm Jocelyn**")

# --- STRATEGIC SUMMARY TABS ---
tab_overview, tab_lmp, tab_method, tab_sources = st.tabs(["📉 The Billion Pound Problem", "🏗️ Locational Pricing (LMP)", "🧪 Methodology", "📚 Sources & Reading"])

with tab_overview:
    st.info("""
    **The Cost of Bottlenecks:** Wind curtailment costs exceeded **£1 billion** by October 2025. 
    This arises from 'constraint payments' to switch off wind farms—primarily in Scotland—due to physical grid bottlenecks. 
    On average, this adds roughly **£34 to every UK household bill.**
    """)
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Why it happens:** Transmission lines (specifically the B6 Boundary) hit thermal limits. Power trapped in the North is replaced by firing up expensive gas plants in the South.")
    with col_b:
        st.write("**The Impact:** Without infrastructure upgrades, annual waste is projected to soar to £8 billion by 2030, threatening Net Zero targets.")

with tab_lmp:
    st.markdown("""
    ### Why this project supports LMP (Zonal Pricing)
    **The Problem:** Currently, the UK has a single 'National' price for electricity. This makes the market 'geographically blind.' 
    
    **The Solution (LMP):** Locational Marginal Pricing creates different price zones. 
    1. **In Scotland (The North):** During storms, prices would drop (or go negative). This signals **Demand** (Data Centers, Hydrogen) to move there to use the 'trapped' energy.
    2. **In London (The South):** Prices would reflect the scarcity of local wind, signaling **Developers** to build more generation closer to demand.
    
    **This Project's Evidence:** The map below proves that power is abundant in the North but cannot reach the South. LMP would solve this by incentivizing demand to follow supply.
    """)

with tab_method:
    st.markdown("""
    ### Valuation Methodology: The Economics of £70/MWh
    The figure of £70/MWh is not an arbitrary estimate. It reflects the **Economic Stack** that wind farms demand to break even when curtailed.
    
    #### 1. The Subsidy Trap
    Most UK wind farms operate under the **Renewables Obligation (RO)** or **Contracts for Difference (CfD)** schemes.
    * **The Incentive:** They are paid a subsidy (e.g., ~£55/MWh for RO) *only when they generate power*.
    * **The Loss:** If the grid asks them to turn off, they lose that subsidy immediately.
    
    #### 2. The Negative Bid
    To avoid losing money, wind farms submit **Negative Bids** to the grid. They effectively say:
    > *"I will turn off, but you must pay me the subsidy I am losing (~£55) plus a margin for lost wholesale revenue (~£15)."*
    
    #### 3. The Result
    This creates a "Constraint Cost" of roughly **£70/MWh**. This is money paid by the consumer to a wind farm to **not** produce energy, simply to make the farm "financially whole."
    """)

with tab_sources:
    st.markdown("""
    ### Primary Data Sources
    * **Telemetry:** [Elexon Insights API](https://developer.data.elexon.co.uk/) (Bid-Offer Acceptances)
    * **Metadata:** [NESO BM Unit Register](https://www.neso.energy/data-and-insights/bm-unit-registers) (Fuel Type Mapping)
    * **Context:** [Met Office Storm Jocelyn Report](https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/weather/learn-about/uk-past-events/interesting/2024/2024_02_storm_jocelyn.pdf)
    
    ### Further Reading
    * [Carbon Tracker: The Billion Pound Problem](https://carbontracker.org/reports/the-billion-pound-problem/)
    * [NESO: Network Constraint Insights](https://www.neso.energy/data-and-insights/network-constraints)
    * [LCP Delta: Zonal Pricing Savings Analysis](https://www.lcpdelta.com/insights/zonal-market-design/)
    """)

# --- MAIN DATA SECTION ---
df = load_data()

if not df.empty:
    total_mwh = abs(df['mwh_volume'].sum())
    total_cost = total_mwh * 70 
    active_units = df['bmUnitId'].nunique()

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("📉 Wasted Green Energy", f"{total_mwh:,.0f} MWh", "Discarded Power")
    col2.metric("💸 Est. Consumer Bill Impact", f"£{total_cost:,.2f}", "Storm Jocelyn Cost")
    col3.metric("📍 Active Bottlenecks", f"{active_units} Wind Farms", "Units Curtailed")

    st.divider()

    # --- VISUALS ---
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📊 Top 10 Curtailed Assets")
        top_assets = df.groupby('bmUnitId')['mwh_volume'].sum().abs().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_assets, x='mwh_volume', y='bmUnitId', orientation='h',
                     color='mwh_volume', color_continuous_scale='Reds')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🗺️ Geographic Grid Saturation")
        map_data = []
        grouped = df.groupby('bmUnitId')['mwh_volume'].sum().abs().reset_index()
        for index, row in grouped.iterrows():
            uid = row['bmUnitId']
            if uid in ASSET_LOCATIONS:
                loc = ASSET_LOCATIONS[uid]
                map_data.append({
                    'lat': loc['lat'] + np.random.uniform(-0.02, 0.02),
                    'lon': loc['lon'] + np.random.uniform(-0.02, 0.02),
                    'name': loc['name'], 'size': row['mwh_volume'] / 10 
                })
        if map_data:
            st.map(pd.DataFrame(map_data), latitude='lat', longitude='lon', size='size', zoom=4.5)
            st.caption("Dots represent physical locations of curtailed wind farms (B6 Boundary emphasis).")
    
    with st.expander("💾 Raw Grid Telemetry Inspector"):
        st.dataframe(df[['timeFrom', 'bmUnitId', 'levelFrom', 'levelTo', 'mwh_volume']].sort_values('mwh_volume', ascending=False))

else:
    st.error("No data found. Ensure 'raw_acceptances.csv' exists.")
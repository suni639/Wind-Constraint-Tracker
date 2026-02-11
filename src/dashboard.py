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
    .expert-quote { font-style: italic; border-left: 3px solid #FF4B4B; padding-left: 15px; margin: 15px 0; font-size: 0.95rem; }
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
    st.title("⚡ Supplementary Info")
    st.markdown("### The B6 Bottleneck")
    st.write("The B6 Boundary is the physical 'wall' between Scotland and England. During Storm Jocelyn, 98% of curtailment happened behind this wall.")
    st.divider()
    st.markdown("### Nuanced Perspectives")
    st.markdown('<div class="expert-quote">"Curtailment waste could reach £8bn/yr by 2030 without grid upgrades." <b>— NESO</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="expert-quote">"UK investment in wind energy generated a net financial benefit of more than £100bn for energy consumers between 2010 and 2023, challenging misconceptions about the cost of the green energy transition." <b>— UCL Open Environment</b></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Data: Elexon BMRS API | Jan 24, 2024")

# --- HEADER ---
st.title("UK Wind Constraint Tracker")
st.markdown("#### Mapping Grid Limitations & Financial Waste during **Storm Jocelyn**")

# --- STRATEGIC SUMMARY TABS ---
tab_execsum, tab_overview, tab_lmp, tab_method, tab_example, tab_sources = st.tabs(["📈 Executive Summary", "📉 The Billion Pound Problem", "🏗️ Locational Pricing (LMP)", "🧪 Methodology", "📊 Worked Example", "📚 Sources & Reading"])

with tab_execsum:
    st.markdown("""
    On January 24, 2024, the UK experienced 80mph winds during Storm Jocelyn. While the nation's wind farms were capable of powering millions of homes with cheap, renewable energy, the physical grid hit a wall. 
    
    This project uses real-time telemetry from the Elexon Insights API to quantify the energy discarded during this event and the resulting financial burden placed on UK consumers.
    
    **🌪️ The Case Study:** Storm Jocelyn
    
    During the 24-hour period of Storm Jocelyn, the North of the UK was a green energy powerhouse, yet the grid was forced into massive interventions.

    * **Total Energy Discarded:** ~170,000 MWh
    * **Estimated Intervention Cost:** ~£12 Million
    * **Consumer Impact:** Enough clean energy to power roughly 12,000 homes for a full year was lost in just 24 hours.
    """)

with tab_overview:
    st.info("""
    **The Cost of Bottlenecks:** Wind curtailment costs exceeded **£1 billion** by October 2025. 
    This arises from 'constraint payments' to switch off wind farms—primarily in Scotland—due to physical grid bottlenecks. 
    On average, this adds roughly **£40 to every UK household bill.** per year (with the potential to rise sharply by 2030 without infrastructure upgrades).
    """)
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Why it happens:** Transmission lines (specifically the B6 Boundary) hit thermal limits. Power trapped in the North is replaced by firing up expensive gas plants in the South.")
    with col_b:
        st.write("**The Impact:** Without infrastructure upgrades, annual waste is projected to soar to £8 billion by 2030, threatening Net Zero targets.")

with tab_lmp:
    st.markdown("""
    ### Should we move to LMP (Zonal Pricing)?
    **The Problem:** Currently, the UK has a single 'National' price for electricity. This makes the market geographically blind. 
    
    **The Solution (LMP):** Locational Marginal Pricing creates different price zones. 
    1. **In Scotland (The North):** During storms, prices would drop (or go negative). This signals **Demand** (Data Centers, Hydrogen) to move there to use the 'trapped' energy.
    2. **In London (The South):** Prices would reflect the scarcity of local wind, signaling **Developers** to build more generation closer to demand.
    
    **The Evidence:** The map below shows that power is abundant in the North but cannot reach the South. LMP would solve this by incentivizing demand to follow supply.
    """)

with tab_method:
    st.markdown("""
    ### 1. Data Ingestion (Elexon BMRS API)
    A Python pipeline was developed to query the **Elexon Insights API**. 
    * **Target Data:** Bid-Offer Acceptances (BOAs)—the literal instructions sent by the grid to generators.
    * **Logic:** Because the API limits data to single 30-minute chunks, a loop was used to reconstruct the full 24-hour picture across all 48 settlement periods.

    ### 2. Identity Resolution (NESO Register)
    Raw grid data uses cryptic codes (e.g., `T_HOWAO-1`). The **NESO BM Unit Register** was used to map these codes to their physical fuel type, allowing us to isolate **WIND** assets and filter out gas or nuclear data.

    ### 3. Physics-to-Finance (The Math)
    Power is measured in **Megawatts (MW)**, but we pay for **Megawatt-hours (MWh)**. Applying **Trapezoidal Rule** to calculate the volume (a fancy term you probably learned in school to work out the area under a curve):
    """)
    
    # This renders the beautiful math formula using LaTeX in Streamlit
    st.latex(r"\text{Volume (MWh)} = \frac{\text{LevelFrom} + \text{LevelTo}}{2} \times \text{Duration (Hours)}")

    st.markdown("""
    ### 4. Valuation Assumption (£70/MWh)
    A flat rate of **£70/MWh** was applied to the wasted volume. This represents the **Opportunity Cost**:
    * **Subsidy Loss:** Wind farms lose ~£55/MWh in government subsidies (ROCs/CfDs) when they stop.
    * **Market Loss:** ~£15/MWh in lost wholesale revenue.
    * **Total:** £70/MWh is the minimum compensation required to make the wind farm "financially whole."
    """)

with tab_example:
    st.markdown("### 🧩 Worked Example: The 'Missing' Energy Math")
    
    # 1. Top Section: Image on Left, Calculation on Right
    col_img, col_math = st.columns([1, 1], gap="large")

    with col_img:
        st.markdown("#### 📸 Visual Evidence")
        image_path = Path(__file__).resolve().parent.parent / "data" / "static" / "curtailment_example.png"
        
        if image_path.exists():
            st.image(str(image_path), width=600)
            st.caption("🔗 Source: [Jungle.ai](https://www.jungle.ai/blog-posts/automatic-detection-of-turbine-power-curtailment)")
        else:
            st.warning("📸 Image not found at 'data/static/curtailment_example.png'")

    with col_math:
        st.markdown("#### 🧪 The Step-by-Step Calculation")
        st.markdown("""
        **Parameters from the Graph:**
                    
        See formula in "Methodology" tab for reference.
                    
        * **Gap at 06:00 (Start):** 700 kW missing
        * **Gap at 18:00 (End):** 700 kW missing
        * **Duration:** 12 Hours
        """)

        # The Trapezoidal Formula
        st.latex(r"\text{Volume (kWh)} = \frac{700 + 700}{2} \times 12")
        
        st.write("Total Lost Energy: **8,400 kWh (8.4 MWh)**")
        
        st.markdown("**Financial Impact:**")
        st.latex(r"8.4\text{ MWh} \times £70 = £588")
        st.success("**Total Intervention Cost (1x Turbine): £588**")

    # 2. Bottom Section: Explanatory text spanning the full width
    st.divider()
    
    st.markdown("#### 🧐 Why we use this specific math")
    st.write("""
    * **Measuring the 'Delta':** The 'Delta', i.e. the gap between potential and actual, represents the wasted opportunity cost to the grid.
    * **The Trapezoidal Rule:** Notice in the graph how the power 'ramps' down at 06:00 and up at 18:00. By using the Trapezoidal Rule, we can capture the area of these slopes, ensuring our £12 Million total is mathematically precise.
    * **The Scalability:** While this example shows a single turbine event costing **£588**, Storm Jocelyn triggered similar constraints across **147 wind farms** simultaneously. The dashboard aggregates these thousands of tiny 'missing areas' to show the true scale of national grid saturation.
    """)

with tab_sources:
    st.markdown("""
    ### Primary Data Sources
    * **Telemetry:** [Elexon Insights API](https://developer.data.elexon.co.uk/) (Bid-Offer Acceptances)
    * **Metadata:** [Elexon BM Fuel Type xlsx](https://www.elexon.co.uk/documents/data/operational-data/bmu-fuel-type/) (Fuel Type Mapping)
    * **Context:** [Met Office Storm Jocelyn Report](https://weather.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/weather/learn-about/uk-past-events/interesting/2024/2024_02_storms_isha_jocelyn.pdf)
    
    ### Further Reading
    * [Carbon Tracker: Britain wastes enough wind generation to power 1 million homes](https://carbontracker.org/britain-wastes-enough-wind-generation-to-power-1-million-homes/)
    * [NESO: Network Constraint Payments](https://www.neso.energy/energy-101/electricity-explained/how-do-we-balance-grid/what-are-constraints-payments)
    * [LCP: Zonal Pricing Savings Analysis](https://www.lcp.com/en/insights/publications/zonal-pricing-in-great-britain)
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
            st.caption("Dots represent physical locations of curtailed wind farms (B6 Boundary emphasis). Note that the Scottish farms are huge, so several assets may be clustered due to proximity and aren't individually distinguishable in the map.")
    
    with st.expander("💾 Raw Grid Telemetry Inspector"):
        st.dataframe(df[['timeFrom', 'bmUnitId', 'levelFrom', 'levelTo', 'mwh_volume']].sort_values('mwh_volume', ascending=False))

else:
    st.error("No data found. Ensure 'raw_acceptances.csv' exists.")
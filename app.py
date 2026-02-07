import streamlit as st
import pandas as pd
import plotly.express as px
import os
from rapidfuzz import process, fuzz

# --- 1. PAGE CONFIGURATION (UI/UX Rubric) ---
st.set_page_config(
    page_title="Property Investment Insights",
    page_icon="🏠",
    layout="wide"
)

# --- 2. DATA PIPELINE (Data Integration Objective) ---
@st.cache_data
def load_and_merge_data():
    # Absolute pathing to support the Standard Folder Structure
    base_path = os.path.dirname(os.path.abspath(__file__))
    demo_path = os.path.join(base_path, 'data', 'demographics.csv')
    list_path = os.path.join(base_path, 'data', 'listings.csv')
    
    # Safety check for file existence
    if not os.path.exists(demo_path) or not os.path.exists(list_path):
        st.error(f"Missing data files in 'data/' folder. Please check path: {demo_path}")
        return pd.DataFrame()

    # Ingest disparate sources
    demo_df = pd.read_csv(demo_path)
    listings_df = pd.read_csv(list_path)

    # Resolve naming inconsistencies: Format ZIP codes as 5-digit strings
    demo_df['zip_code'] = demo_df['zip_code'].astype(str).str.zfill(5)
    # Extract only digits for messy postal codes (e.g., '325XX' -> '325')
    listings_df['zip_prefix'] = listings_df['postal_code'].astype(str).str.extract(r'(\d+)')

    # Advanced Fuzzy Matching (Levenshtein distance) for messy listings
    def find_best_zip(prefix):
        if pd.isna(prefix): return None
        choices = demo_df['zip_code'].unique()
        # Use partial_ratio to handle incomplete codes like '325' vs '32599'
        match = process.extractOne(prefix, choices, scorer=fuzz.partial_ratio)
        return match[0] if match and match[1] >= 80 else None

    listings_df['matched_zip'] = listings_df['zip_prefix'].apply(find_best_zip)

    # Dynamic Data Merging into a Single Source of Truth
    merged_df = pd.merge(
        listings_df, 
        demo_df, 
        left_on='matched_zip', 
        right_on='zip_code', 
        how='inner'
    )
    
    # Calculate required KPI
    merged_df['price_per_sqft'] = merged_df['listing_price'] / merged_df['sq_ft']
    return merged_df

# --- 3. UI EXECUTION ---
df = load_and_merge_data()

if df.empty:
    st.warning("Please verify demographics.csv and listings.csv are in the 'data/' folder.")
else:
    # --- 4. SIDEBAR FILTERS (User Filtering Objective) ---
    st.sidebar.header("Investment Filters")
    st.sidebar.info("Analyze price vs. demographics")
    
    zip_selection = st.sidebar.multiselect(
        "ZIP Code Filter", 
        options=sorted(df['zip_code'].unique()),
        default=sorted(df['zip_code'].unique())[:3]
    )

    price_limit = st.sidebar.slider(
        "Price Range ($)", 
        int(df['listing_price'].min()), 
        int(df['listing_price'].max()), 
        (int(df['listing_price'].min()), int(df['listing_price'].max()))
    )

    # Apply filters to data
    mask = (df['zip_code'].isin(zip_selection)) & (df['listing_price'].between(price_limit[0], price_limit[1]))
    filtered_df = df[mask]

    # --- 5. DASHBOARD UI (KPI & Visualization Objective) ---
    st.title("🏙️ Property Investment Insights")
    st.caption("Visualizing property value vs. neighborhood demographics")
    
    # KPI Metrics
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Listings", len(filtered_df))
    k2.metric("Avg Listing Price", f"${filtered_df['listing_price'].mean():,.0f}")
    k3.metric("Avg Price / SqFt", f"${filtered_df['price_per_sqft'].mean():,.2f}")
    k4.metric("Avg School Rating", f"{filtered_df['school_rating'].mean():.1f}/10")

    st.markdown("---")

    # Interactive Visuals
    st.subheader("Price vs. Crime & School Quality")
    # UPDATED GRAPH: Price (X), Crime Rating (Y), School Rating (Color)
    fig = px.scatter(
        filtered_df, 
        x="listing_price", 
        y="crime_index",
        color="school_rating", 
        size="sq_ft", 
        hover_name="raw_address",
        labels={
            "listing_price": "Listing Price ($)", 
            "crime_index": "Crime Rating",
            "school_rating": "School Rating (1-10)"
        },
        color_continuous_scale="Viridis",
        template="plotly_white",
        category_orders={"crime_index": ["Low", "Medium", "High"]} # Logical Y-axis order
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Secondary Visualization
    st.subheader("Property Value by ZIP Code")
    st.bar_chart(filtered_df, x="zip_code", y="listing_price", color="crime_index")

    # Drill-down capability
    with st.expander("🔍 Detailed Property View"):
        st.dataframe(filtered_df.drop(columns=['zip_prefix', 'matched_zip']))
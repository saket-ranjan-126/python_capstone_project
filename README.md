# Property Investment Dashboard

An interactive Streamlit dashboard for real estate investors.

## Key Features
- **Data Integration:** Merges messy street-level listings with structured demographic data.
- **Fuzzy Matching:** Uses `RapidFuzz` to resolve structural mismatches in postal codes (e.g., matching '325XX' to '32599').
- **Interactive UI:** Dark mode dashboard with "Excel-style" slicers for crime ratings and ZIP codes.
- **Performance:** Implements `@st.cache_data` for optimized data processing.

## Setup
1. `pip install -r requirements.txt`
2. `streamlit run app.py`

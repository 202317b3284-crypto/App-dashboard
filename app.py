import streamlit as st
import pandas as pd

st.set_page_config(page_title="Real Estate Dashboard", layout="wide")

# ------------------------------------------
# Helper: Normalize column names
# ------------------------------------------
def normalize_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("(", "")
        .str.replace(")", "")
    )
    return df

# ------------------------------------------
# Load datasets
# ------------------------------------------
@st.cache_data
def load_data():
    india = pd.read_csv("india_state_data.csv")
    city = pd.read_csv("city_level_data.csv")

    india = normalize_columns(india)
    city = normalize_columns(city)

    return india, city

india_df, city_df = load_data()

# ------------------------------------------
# Standardize key column names
# ------------------------------------------
# India dataset
COLUMN_MAP_INDIA = {
    "state": "state",
    "region": "region",
    "market_tier": "market_tier",
    "price_sqft_₹": "price_sqft",
    "price_sqft": "price_sqft",
    "median_house_price_₹_lakh_-2025": "median_price_2025"
}

for col in COLUMN_MAP_INDIA:
    if col in india_df.columns:
        india_df.rename(columns={col: COLUMN_MAP_INDIA[col]}, inplace=True)

# City dataset
if "city" not in city_df.columns:
    st.error("City column not found in city-level dataset.")
    st.stop()

# ------------------------------------------
# Session state
# ------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "INDIA"
if "state" not in st.session_state:
    st.session_state.state = None
if "city" not in st.session_state:
    st.session_state.city = None

# ------------------------------------------
# INDIA VIEW (Your responsibility)
# ------------------------------------------
def show_india_view():
    st.title("🇮🇳 Indian Real Estate Overview")

    # Filters
    region = st.selectbox(
        "Select Region",
        ["All"] + sorted(india_df["region"].dropna().unique().tolist())
    )

    tier = st.selectbox(
        "Select Market Tier",
        ["All"] + sorted(india_df["market_tier"].dropna().unique().tolist())
    )

    filtered = india_df.copy()

    if region != "All":
        filtered = filtered[filtered["region"] == region]

    if tier != "All":
        filtered = filtered[filtered["market_tier"] == tier]

    st.subheader("State Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    selected_state = st.selectbox(
        "Select a State",
        filtered["state"].unique()
    )

    if st.button("View State Details"):
        st.session_state.state = selected_state
        st.session_state.view = "STATE"

# ------------------------------------------
# STATE VIEW
# ------------------------------------------
def show_state_view():
    st.title(f"📍 State Details – {st.session_state.state}")

    state_data = india_df[india_df["state"] == st.session_state.state]
    st.dataframe(state_data, use_container_width=True)

    cities = city_df["city"].unique().tolist()
    selected_city = st.selectbox("Select City", cities)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"

    with col2:
        if st.button("View City Deep‑Dive →"):
            st.session_state.city = selected_city
            st.session_state.view = "CITY"

# ------------------------------------------
# CITY VIEW (City + State comparison)
# ------------------------------------------
def show_city_view():
    st.title(f"🏙️ City Deep‑Dive – {st.session_state.city}")

    city_data = city_df[city_df["city"] == st.session_state.city]
    state_data = india_df[india_df["state"] == st.session_state.state]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("City Level Details")
        st.dataframe(city_data, use_container_width=True)

    with col2:
        st.subheader("State Benchmark")
        if not state_data.empty and "price_sqft" in state_data.columns:
            st.metric(
                "Avg Price / Sqft",
                f"₹ {int(state_data['price_sqft'].iloc[0]):,}"
            )
        if "median_price_2025" in state_data.columns:
            st.metric(
                "Median Price 2025",
                f"₹ {round(state_data['median_price_2025'].iloc[0], 2)} L"
            )

    if st.button("← Back to State"):
        st.session_state.view = "STATE"

# ------------------------------------------
# App Controller
# ------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()
elif st.session_state.view == "STATE":
    show_state_view()
elif st.session_state.view == "CITY":
    show_city_view()

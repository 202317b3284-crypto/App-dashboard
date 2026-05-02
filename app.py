import streamlit as st
import pandas as pd

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Helper: Normalize column names
# -------------------------------------------------
def normalize_columns(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("(", "")
        .str.replace(")", "")
    )
    return df

# -------------------------------------------------
# Load Data
# -------------------------------------------------
@st.cache_data
def load_data():
    india_df = pd.read_csv("india_state_data.csv")
    city_df = pd.read_csv("city_level_data.csv")

    india_df = normalize_columns(india_df)
    city_df = normalize_columns(city_df)

    return india_df, city_df

india_df, city_df = load_data()

# -------------------------------------------------
# Required columns check
# -------------------------------------------------
required_city_cols = {"state", "city"}
if not required_city_cols.issubset(city_df.columns):
    st.error("city_level_data.csv must contain both 'state' and 'city' columns.")
    st.stop()

# -------------------------------------------------
# Session State Initialization
# -------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "INDIA"

if "selected_state" not in st.session_state:
    st.session_state.selected_state = None

if "selected_city" not in st.session_state:
    st.session_state.selected_city = None

# -------------------------------------------------
# INDIA LEVEL VIEW (Person 1)
# -------------------------------------------------
def show_india_view():
    st.title("🇮🇳 Indian Real Estate Market Overview")

    region_filter = (
        ["All"] + sorted(india_df["region"].dropna().unique())
        if "region" in india_df.columns else ["All"]
    )

    tier_filter = (
        ["All"] + sorted(india_df["market_tier"].dropna().unique())
        if "market_tier" in india_df.columns else ["All"]
    )

    region = st.selectbox("Select Region", region_filter)
    tier = st.selectbox("Select Market Tier", tier_filter)

    filtered_df = india_df.copy()

    if region != "All" and "region" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["region"] == region]

    if tier != "All" and "market_tier" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["market_tier"] == tier]

    st.subheader("State‑Level Market Data")
    st.dataframe(filtered_df, use_container_width=True)

    # ✅ States sourced from city-level dataset
    available_states = sorted(city_df["state"].unique())

    selected_state = st.selectbox(
        "Select a State to view details",
        available_states
    )

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE LEVEL DETAIL VIEW (Person 2)
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    # State benchmark from India dataset
    state_benchmark = india_df[india_df["state"] == state]

    if not state_benchmark.empty:
        st.subheader("State‑Level Benchmark")
        st.dataframe(state_benchmark, use_container_width=True)

    # ✅ Cities come from city dataset based on selected state
    state_cities = sorted(
        city_df[city_df["state"] == state]["city"].unique()
    )

    selected_city = st.selectbox(
        "Select a City for Deep‑Dive",
        state_cities
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to India Overview"):
            st.session_state.view = "INDIA"
            st.session_state.selected_state = None

    with col2:
        if st.button("View City Deep‑Dive →"):
            st.session_state.selected_city = selected_city
            st.session_state.view = "CITY"

# -------------------------------------------------
# CITY LEVEL DEEP‑DIVE + STATE COMPARISON
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state

    st.title(f"🏙️ City Deep‑Dive – {city}")
    st.caption(f"Compared with {state} State Benchmarks")

    city_data = city_df[
        (city_df["city"] == city) &
        (city_df["state"] == state)
    ]

    state_data = india_df[india_df["state"] == state]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("City‑Level Data")
        st.dataframe(city_data, use_container_width=True)

    with col2:
        st.subheader("State Benchmarks")

        if not state_data.empty:
            if "price_sqft" in state_data.columns:
                st.metric(
                    "State Avg Price / Sqft",
                    f"₹ {int(state_data['price_sqft'].iloc[0]):,}"
                )
            if "median_house_price_₹_lakh_-2025" in state_data.columns:
                st.metric(
                    "Median Price 2025",
                    f"₹ {round(state_data['median_house_price_₹_lakh_-2025'].iloc[0],2)} L"
                )

    if st.button("← Back to State View"):
        st.session_state.view = "STATE"
        st.session_state.selected_city = None

# -------------------------------------------------
# App Controller
# -------------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()

elif st.session_state.view == "STATE":
    show_state_view()

elif st.session_state.view == "CITY":
    show_city_view()

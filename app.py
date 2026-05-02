import streamlit as st
import pandas as pd
import re

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Robust Column Normalization
# -------------------------------------------------
def normalize_columns(df):
    cleaned_cols = []
    for col in df.columns:
        col_clean = col.lower().strip()
        col_clean = re.sub(r"[^a-z0-9]+", "_", col_clean)
        col_clean = re.sub(r"_+", "_", col_clean).strip("_")
        cleaned_cols.append(col_clean)
    df.columns = cleaned_cols
    return df

# -------------------------------------------------
# Load Data
# -------------------------------------------------
@st.cache_data
def load_data():
    india = pd.read_csv("india_state_data.csv")
    city = pd.read_csv("city_level_data.csv")

    india = normalize_columns(india)
    city = normalize_columns(city)

    return india, city

india_df, city_df = load_data()

# -------------------------------------------------
# Detect State & City Columns (City Dataset)
# -------------------------------------------------
def find_column(df, keyword):
    for col in df.columns:
        if keyword in col:
            return col
    return None

STATE_COL = find_column(city_df, "state")
CITY_COL = find_column(city_df, "city")

if STATE_COL is None or CITY_COL is None:
    st.error(f"Required state/city columns not detected. Found columns: {list(city_df.columns)}")
    st.stop()

city_df.rename(columns={STATE_COL: "state", CITY_COL: "city"}, inplace=True)

# -------------------------------------------------
# Session State
# -------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "INDIA"
if "selected_state" not in st.session_state:
    st.session_state.selected_state = None
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None

# -------------------------------------------------
# INDIA LEVEL VIEW
# -------------------------------------------------
def show_india_view():
    st.title("🇮🇳 Indian Real Estate Market Overview")

    region = st.selectbox(
        "Select Region",
        ["All"] + sorted(india_df["region"].dropna().unique())
        if "region" in india_df.columns else ["All"]
    )

    tier = st.selectbox(
        "Select Market Tier",
        ["All"] + sorted(india_df["market_tier"].dropna().unique())
        if "market_tier" in india_df.columns else ["All"]
    )

    filtered = india_df.copy()
    if region != "All" and "region" in filtered.columns:
        filtered = filtered[filtered["region"] == region]
    if tier != "All" and "market_tier" in filtered.columns:
        filtered = filtered[filtered["market_tier"] == tier]

    st.subheader("State‑Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    available_states = sorted(city_df["state"].unique())
    selected_state = st.selectbox("Select a State", available_states)

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE LEVEL VIEW
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    state_data = india_df[india_df.get("state", "") == state]
    if not state_data.empty:
        st.subheader("State‑Level Benchmarks")
        st.dataframe(state_data, use_container_width=True)

    cities = sorted(city_df[city_df["state"] == state]["city"].unique())
    selected_city = st.selectbox("Select City for Deep‑Dive", cities)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"
            st.session_state.selected_state = None
    with col2:
        if st.button("View City Deep‑Dive →"):
            st.session_state.selected_city = selected_city
            st.session_state.view = "CITY"

# -------------------------------------------------
# CITY DEEP‑DIVE + STATE COMPARISON (WITH GRAPHS)
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state

    st.title(f"🏙️ City vs State Comparison – {city}")
    st.caption(f"City deep‑dive with {state} benchmarks")

    city_data = city_df[
        (city_df["city"] == city) &
        (city_df["state"] == state)
    ]
    state_data = india_df[india_df.get("state", "") == state]

    # -------------------------------
    # KPI COMPARISON
    # -------------------------------
    col1, col2 = st.columns(2)

    city_avg = city_data["price_per_sqft"].mean()
    state_avg = state_data["price_sqft"].iloc[0] if "price_sqft" in state_data.columns else None

    col1.metric("City Avg Price / Sqft", f"₹ {int(city_avg):,}")
    if state_avg:
        col2.metric("State Avg Price / Sqft", f"₹ {int(state_avg):,}")

    st.markdown("---")

    # -------------------------------
    # BAR CHART COMPARISON (Like reference image)
    # -------------------------------
    st.subheader("📊 Average Price Comparison")

    compare_df = pd.DataFrame({
        "Level": ["City", "State"],
        "Avg Price per Sqft": [city_avg, state_avg]
    }).set_index("Level")

    st.bar_chart(compare_df)

    # -------------------------------
    # LOCALITY LEVEL BAR CHART (City)
    # -------------------------------
    if "locality" in city_data.columns:
        st.subheader("📍 Average Price by Locality (City)")
        locality_df = (
            city_data
            .groupby("locality")["price_per_sqft"]
            .mean()
            .sort_values(ascending=False)
        )
        st.bar_chart(locality_df)

    # -------------------------------
    # DATA TABLES
    # -------------------------------
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.subheader("City‑Level Data")
        st.dataframe(city_data, use_container_width=True)
    with col_r:
        st.subheader("State Benchmarks")
        st.dataframe(state_data, use_container_width=True)

    if st.button("← Back to State"):
        st.session_state.view = "STATE"

# -------------------------------------------------
# APP CONTROLLER
# -------------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()
elif st.session_state.view == "STATE":
    show_state_view()
elif st.session_state.view == "CITY":
    show_city_view()

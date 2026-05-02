import streamlit as st
import pandas as pd

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Load Data
# -------------------------------------------------
@st.cache_data
def load_data():
    india_df = pd.read_csv("india_state_data.csv")
    city_df = pd.read_csv("city_level_data.csv")

    # Clean column names
    india_df.columns = india_df.columns.str.strip()
    city_df.columns = city_df.columns.str.strip()

    return india_df, city_df

india_df, city_df = load_data()

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
# INDIA LEVEL VIEW (Person 1 scope)
# -------------------------------------------------
def show_india_view():
    st.title("🇮🇳 Indian Real Estate Market Overview")

    # Filters
    region = st.selectbox(
        "Select Region",
        ["All"] + sorted(india_df["Region"].unique().tolist())
    )

    tier = st.selectbox(
        "Select Market Tier",
        ["All"] + sorted(india_df["Market Tier"].unique().tolist())
    )

    filtered_df = india_df.copy()

    if region != "All":
        filtered_df = filtered_df[filtered_df["Region"] == region]

    if tier != "All":
        filtered_df = filtered_df[filtered_df["Market Tier"] == tier]

    st.subheader("State-wise Market Data")
    st.dataframe(filtered_df, use_container_width=True)

    selected_state = st.selectbox(
        "Select a State to view details",
        filtered_df["State / Union Territory"].unique()
    )

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE LEVEL DETAIL VIEW (Person 2 scope)
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    state_df = india_df[india_df["State / Union Territory"] == state]
    st.dataframe(state_df, use_container_width=True)

    # Cities under the state
    cities = city_df[city_df["City"].notnull()]["City"].unique().tolist()

    selected_city = st.selectbox("Select a City for Deep‑Dive", cities)

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
# CITY DEEP-DIVE + STATE COMPARISON (Person 3 & 4 scope)
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state

    st.title(f"🏙️ City Deep‑Dive – {city}")
    st.caption(f"Benchmarking against {state}")

    city_data = city_df[city_df["City"] == city]
    state_data = india_df[india_df["State / Union Territory"] == state]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("City‑Level Details")
        st.dataframe(city_data, use_container_width=True)

    with col2:
        st.subheader("State Benchmark")
        st.metric(
            "State Avg Price / Sqft",
            f"₹ {int(state_data['Price/sqft (₹)'].values[0]):,}"
        )
        st.metric(
            "State Median Price 2025",
            f"₹ {round(state_data['Median House Price (₹ Lakh) -2025'].values[0], 2)} L"
        )

    if st.button("← Back to State View"):
        st.session_state.view = "STATE"
        st.session_state.selected_city = None

# -------------------------------------------------
# VIEW CONTROLLER
# -------------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()

elif st.session_state.view == "STATE":
    show_state_view()

elif st.session_state.view == "CITY":
    show_city_view()

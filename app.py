import streamlit as st
import pandas as pd
import re
import altair as alt

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Robust column normalization
# -------------------------------------------------
def normalize_columns(df):
    cleaned_cols = []
    for col in df.columns:
        col_clean = col.lower().strip()
        col_clean = re.sub(r"[^a-z0-9_]", "_", col_clean)
        col_clean = re.sub(r"_+", "_", col_clean)
        cleaned_cols.append(col_clean.rstrip("_"))
    df.columns = cleaned_cols
    return df

# -------------------------------------------------
# Load data
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
# Detect state & city columns in city dataset
# -------------------------------------------------
def find_column(df, keyword):
    for col in df.columns:
        if keyword in col:
            return col
    return None

STATE_COL = find_column(city_df, "state")
CITY_COL = find_column(city_df, "city")

if STATE_COL is None or CITY_COL is None:
    st.error(
        f"Required columns not detected.\n\nDetected columns: {list(city_df.columns)}"
    )
    st.stop()

city_df.rename(columns={STATE_COL: "state", CITY_COL: "city"}, inplace=True)

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "INDIA"
if "selected_state" not in st.session_state:
    st.session_state.selected_state = None
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None

# -------------------------------------------------
# INDIA VIEW (UPDATED WITH GRAPHS)
# -------------------------------------------------
def show_india_view():
    st.title("🏘️💹 Indian Real Estate Market Overview")

    # Filters
    region = (
        st.selectbox(
            "Select Region",
            ["All"] + sorted(india_df["region"].dropna().unique())
        ) if "region" in india_df.columns else "All"
    )

    tier = (
        st.selectbox(
            "Select Market Tier",
            ["All"] + sorted(india_df["market_tier"].dropna().unique())
        ) if "market_tier" in india_df.columns else "All"
    )

    # Apply filters
    filtered = india_df.copy()

    if region != "All" and "region" in filtered.columns:
        filtered = filtered[filtered["region"] == region]

    if tier != "All" and "market_tier" in filtered.columns:
        filtered = filtered[filtered["market_tier"] == tier]

    # -------------------------------
    # Market Analysis Graphs
    # -------------------------------
    st.subheader("📊 Market Analysis")

    col1, col2 = st.columns(2)

    # Avg Price per Sqft by State
    if "price_sqft" in filtered.columns:
        with col1:
            st.caption("Average Price per Sqft by State")
            price_df = (
                filtered
                .groupby("state")["price_sqft"]
                .mean()
                .sort_values(ascending=False)
            )
            st.bar_chart(price_df)

    # Median House Price 2025 by State
    if "median_house_price_lakh_2025" in filtered.columns:
        with col2:
            st.caption("Median House Price (2025) by State")
            median_df = (
                filtered
                .groupby("state")["median_house_price_lakh_2025"]
                .mean()
                .sort_values(ascending=False)
            )
            st.bar_chart(median_df)

    # Region-wise Avg Price (optional but useful)
    if "region" in filtered.columns and "price_sqft" in filtered.columns:
        st.caption("Region-wise Average Price per Sqft")
        region_df = (
            filtered
            .groupby("region")["price_sqft"]
            .mean()
            .sort_values(ascending=False)
        )
        st.bar_chart(region_df)

    st.divider()

    # -------------------------------
    # State-Level Table (Filtered)
    # -------------------------------
    st.subheader("📋 State‑Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    # -------------------------------
    # Navigation to State View
    # -------------------------------
    available_states = sorted(filtered["state"].unique())
    selected_state = st.selectbox("Select a State", available_states)

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE VIEW
# -------------------------------------------------

def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    st.subheader("Benchmark Metrics")
    st.dataframe(
        india_df[india_df.get("state", "") == state],
        use_container_width=True
    )

    # City-level data for state
    state_city_df = city_df[city_df["state"] == state]

    st.subheader("🏙️ City-Level Market Data")
    st.dataframe(state_city_df, use_container_width=True)

    st.divider()

    # -------------------------------
    # Checkbox-Based Question Selection
    # -------------------------------
    st.subheader("💬 Market Analysis Assistant")

    questions = [
        "Which city is priced higher than its state average?",
        "Is this city more affordable compared to its state?",
        "How fast is the city growing compared to the state?",
        "Which localities outperform the state average?",
        "Does this city belong to a high-growth state?",
        "How does property size affect city prices vs state?",
        "Is the city driven by premium or affordable housing?",
        "How does metro/IT proximity affect city prices?",
        "Which city offers the best value for money?",
        "What if property attributes change in this city?"
    ]

    st.write("🤖 Select one or more analysis goals:")

    selected_questions = st.multiselect(
        "Analysis questions",
        questions
    )

    st.session_state.selected_question = selected_questions

    selected_city = st.selectbox(
        "Select City for Deep‑Dive",
        sorted(state_city_df["city"].unique())
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"
            st.session_state.selected_state = None

    with col2:
        if st.button("Proceed to City Comparison →"):
            st.session_state.selected_city = selected_city
            st.session_state.view = "CITY"
# -------------------------------------------------
# CITY VIEW
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state

    st.title(f"🏙️ City Deep‑Dive & Comparision – {city}")
    st.caption(f"State context: {state}")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("City‑Level Data")
        st.dataframe(
            city_df[
                (city_df["city"] == city) &
                (city_df["state"] == state)
            ],
            use_container_width=True
        )

    with col2:
        st.subheader("State Benchmarks")
        state_row = india_df[india_df.get("state", "") == state]
        if not state_row.empty and "price_sqft" in state_row.columns:
            st.metric(
                "State Avg Price / Sqft",
                f"₹ {int(state_row['price_sqft'].iloc[0]):,}"
            )

    if st.button("← Back to State"):
        st.session_state.view = "STATE"

# -------------------------------------------------
# App Controller
# -------------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()
elif st.session_state.view == "STATE":
    show_state_view()
elif st.session_state.view == "CITY":
    show_city_view()

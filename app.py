import streamlit as st
import pandas as pd
import re

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Column normalization
# -------------------------------------------------
def normalize_columns(df):
    cols = []
    for c in df.columns:
        c = c.lower().strip()
        c = re.sub(r"[^a-z0-9_]", "_", c)
        c = re.sub(r"_+", "_", c)
        cols.append(c.rstrip("_"))
    df.columns = cols
    return df

# -------------------------------------------------
# Load data
# -------------------------------------------------
@st.cache_data
def load_data():
    india = normalize_columns(pd.read_csv("india_state_data.csv"))
    city = normalize_columns(pd.read_csv("city_level_data.csv"))
    return india, city

india_df, city_df = load_data()

# -------------------------------------------------
# Detect columns
# -------------------------------------------------
def find_column(df, keywords):
    for col in df.columns:
        if all(k in col for k in keywords):
            return col
    return None

STATE_COL = find_column(city_df, ["state"])
CITY_COL = find_column(city_df, ["city"])
PRICE_COL_CITY = find_column(city_df, ["price", "sqft"])
PRICE_COL_STATE = find_column(india_df, ["price", "sqft"])

city_df.rename(columns={STATE_COL: "state", CITY_COL: "city"}, inplace=True)

# -------------------------------------------------
# Session state
# -------------------------------------------------
st.session_state.setdefault("view", "INDIA")
st.session_state.setdefault("selected_state", None)
st.session_state.setdefault("selected_city", None)
st.session_state.setdefault("selected_question", [])

# -------------------------------------------------
# INDIA VIEW (UNCHANGED)
# -------------------------------------------------
def show_india_view():
    st.title("🏘️💹 Indian Real Estate Market Overview")

    region = (
        st.selectbox("Select Region", ["All"] + sorted(india_df["region"].dropna().unique()))
        if "region" in india_df.columns else "All"
    )

    tier = (
        st.selectbox("Select Market Tier", ["All"] + sorted(india_df["market_tier"].dropna().unique()))
        if "market_tier" in india_df.columns else "All"
    )

    filtered = india_df.copy()
    if region != "All":
        filtered = filtered[filtered["region"] == region]
    if tier != "All":
        filtered = filtered[filtered["market_tier"] == tier]

    st.subheader("📊 Market Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(filtered.groupby("state")["price_sqft"].mean())
    with col2:
        st.bar_chart(filtered.groupby("state")["median_house_price_lakh_2025"].mean())

    st.subheader("📋 State‑Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    selected_state = st.selectbox("Select a State", sorted(filtered["state"].unique()))
    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE VIEW (UNCHANGED STRUCTURE, ALL 10 QUESTIONS)
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    st.subheader("Benchmark Metrics")
    st.dataframe(india_df[india_df["state"] == state], use_container_width=True)

    state_city_df = city_df[city_df["state"] == state]
    st.subheader("🏙️ City‑Level Market Data")
    st.dataframe(state_city_df, use_container_width=True)

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

    st.session_state.selected_question = st.multiselect(
        "Select analysis objectives:",
        questions
    )

    st.session_state.selected_city = st.selectbox(
        "Select City for Deep‑Dive",
        sorted(state_city_df["city"].unique())
    )

    if st.button("Proceed to City Comparison →"):
        st.session_state.view = "CITY"

# -------------------------------------------------
# CITY VIEW (LOCALITY‑BASED, NUMERIC SAFE)
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state
    selected_questions = st.session_state.selected_question

    # -------------------------------------------------
    # Helper to find price-per-sqft column dynamically
    # -------------------------------------------------
    def find_price_column(df):
        for col in df.columns:
            if "price" in col and "sqft" in col:
                return col
        return None

    # -------------------------------------------------
    # Header & Context
    # -------------------------------------------------
    st.title(f"🏙️ City–State Comparison – {city}")
    st.caption(f"Comparing **{city}** with **{state}** benchmarks")

    # -------------------------------------------------
    # Selected Analysis Objectives
    # -------------------------------------------------
    st.subheader("🎯 Selected Analysis Objectives")

    if selected_questions:
        for q in selected_questions:
            st.write(f"• {q}")
    else:
        st.info("No specific analysis objectives selected. Showing general comparison.")

    st.divider()

    # -------------------------------------------------
    # Load & Prepare Data
    # -------------------------------------------------
    city_df_filtered = city_df[
        (city_df["city"] == city) & (city_df["state"] == state)
    ]
    state_df_filtered = india_df[india_df["state"] == state]

    price_col_city = find_price_column(city_df_filtered)
    price_col_state = find_price_column(state_df_filtered)

    # -------------------------------------------------
    # KPI Calculation (FIXED)
    # -------------------------------------------------
    city_avg_price = (
        city_df_filtered[price_col_city].mean()
        if price_col_city and not city_df_filtered.empty
        else None
    )

    state_avg_price = (
        state_df_filtered[price_col_state].iloc[0]
        if price_col_state and not state_df_filtered.empty
        else None
    )

    # -------------------------------------------------
    # KPI Display
    # -------------------------------------------------
    st.subheader("📌 Key Comparison Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        if city_avg_price is not None:
            st.metric(
                "City Avg Price / Sqft",
                f"₹ {int(city_avg_price):,}"
            )
        else:
            st.metric("City Avg Price / Sqft", "N/A")

    with col2:
        if state_avg_price is not None:
            st.metric(
                "State Avg Price / Sqft",
                f"₹ {int(state_avg_price):,}"
            )
        else:
            st.metric("State Avg Price / Sqft", "N/A")

    with col3:
        if city_avg_price is not None and state_avg_price is not None:
            diff = city_avg_price - state_avg_price
            st.metric(
                "Difference",
                f"₹ {int(diff):,}"
            )
        else:
            st.metric("Difference", "N/A")

    st.divider()

    # -------------------------------------------------
    # Dynamic Analysis Section (placeholder, correct layout)
    # -------------------------------------------------
    st.subheader("📊 Analysis Based on Selected Objectives")

    if not selected_questions:
        st.info(
            "Select analysis objectives on the State page to see "
            "question‑driven insights here."
        )
    else:
        for q in selected_questions:
            st.markdown(f"### 🔹 {q}")
            st.write(
                "Relevant charts and insights for this question will appear here."
            )
            st.info("Visualization logic will be added in the next stage.")
            st.markdown("---")

    # -------------------------------------------------
    # Detailed Tables
    # -------------------------------------------------
    st.subheader("📋 Detailed Comparison Data")

    col_left, col_right = st.columns(2)

    with col_left:
        st.caption("City‑Level Data (All Localities)")
        st.dataframe(city_df_filtered, use_container_width=True)

    with col_right:
        st.caption("State‑Level Benchmarks")
        st.dataframe(state_df_filtered, use_container_width=True)

    # -------------------------------------------------
    # Navigation
    # -------------------------------------------------
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

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
# ✅ CRITICAL FIX: create numeric price column ONCE
# -------------------------------------------------
city_df["price_numeric"] = (
    city_df[PRICE_COL_CITY]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
    .astype(float)
)

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

    region = st.selectbox("Select Region", ["All"] + sorted(india_df["region"].unique()))
    tier = st.selectbox("Select Market Tier", ["All"] + sorted(india_df["market_tier"].unique()))

    filtered = india_df.copy()
    if region != "All":
        filtered = filtered[filtered["region"] == region]
    if tier != "All":
        filtered = filtered[filtered["market_tier"] == tier]

    st.subheader("📊 Market Analysis")
    col1, col2 = st.columns(2)
    col1.bar_chart(filtered.groupby("state")[PRICE_COL_STATE].mean())
    col2.bar_chart(filtered.groupby("state")["median_house_price_lakh_2025"].mean())

    st.subheader("📋 State‑Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    selected_state = st.selectbox("Select a State", sorted(filtered["state"].unique()))
    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE VIEW (UNCHANGED STRUCTURE – ALL 10 QUESTIONS)
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
# CITY VIEW (LOCALITY‑BASED, SAFE)
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state
    questions = st.session_state.selected_question

    df = city_df[
        (city_df["city"] == city) &
        (city_df["state"] == state)
    ].copy()

    city_avg = df["price_numeric"].mean()
    state_avg = india_df[india_df["state"] == state][PRICE_COL_STATE].iloc[0]

    st.title(f"🏙️ City–State Comparison – {city}")
    st.caption(f"Locality‑level analysis benchmarked against **{state}**")

    st.subheader("📌 Key Comparison Metrics")
    c1, c2, c3 = st.columns(3)
    c1.metric("City Avg Price / Sqft", f"₹ {int(city_avg):,}")
    c2.metric("State Avg Price / Sqft", f"₹ {int(state_avg):,}")
    c3.metric("Difference", f"₹ {int(city_avg - state_avg):,}")

    st.subheader("🎯 Selected Analysis Objectives")
    for q in questions:
        st.write(f"• {q}")

    st.subheader("📊 Locality‑Level Price Comparison")
    locality_avg = (
        df.groupby("locality")["price_numeric"]
        .mean()
        .sort_values(ascending=False)
    )
    st.bar_chart(locality_avg)
    st.caption(f"Reference State Avg Price: ₹ {int(state_avg):,}")

    st.subheader("📋 Locality‑Level Data")
    st.dataframe(df, use_container_width=True)

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

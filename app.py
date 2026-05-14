import streamlit as st
import pandas as pd
import re

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Column normalization (unchanged)
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
# Load data (UPDATED → Excel support)
# -------------------------------------------------
@st.cache_data
def load_data():
    india = normalize_columns(pd.read_csv("india_state_data.csv"))

    city = pd.read_excel("city_level_data.xlsx", engine="openpyxl")
    city = normalize_columns(city)

    return india, city

india_df, city_df = load_data()

# -------------------------------------------------
# Column detection
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
# ✅ FIX: Safe numeric conversion (MOST IMPORTANT)
# -------------------------------------------------
city_df["price_numeric"] = pd.to_numeric(
    city_df[PRICE_COL_CITY]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip(),
    errors="coerce"
)

# -------------------------------------------------
# Session state
# -------------------------------------------------
st.session_state.setdefault("view", "INDIA")
st.session_state.setdefault("selected_state", None)
st.session_state.setdefault("selected_city", None)
st.session_state.setdefault("selected_question", [])

# -------------------------------------------------
# PAGE 1 → INDIA VIEW (UNCHANGED)
# -------------------------------------------------
def show_india_view():
    st.title("🏘️💹 Indian Real Estate Market Overview")

    region = st.selectbox(
        "Select Region",
        ["All"] + sorted(india_df["region"].dropna().unique())
    )

    tier = st.selectbox(
        "Select Market Tier",
        ["All"] + sorted(india_df["market_tier"].dropna().unique())
    )

    filtered = india_df.copy()
    if region != "All":
        filtered = filtered[filtered["region"] == region]
    if tier != "All":
        filtered = filtered[filtered["market_tier"] == tier]

    st.subheader("📊 Market Analysis")

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(filtered.groupby("state")[PRICE_COL_STATE].mean())
    with col2:
        st.bar_chart(filtered.groupby("state")["median_house_price_lakh_2025"].mean())

    st.subheader("📋 State‑Level Market Data")
    st.dataframe(filtered, use_container_width=True)

    selected_state = st.selectbox(
        "Select a State", sorted(filtered["state"].unique())
    )

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# PAGE 2 → STATE VIEW (10 QUESTIONS – UNCHANGED)
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    st.subheader("Benchmark Metrics")
    st.dataframe(india_df[india_df["state"] == state], use_container_width=True)

    state_city_df = city_df[city_df["state"] == state]

    st.subheader("🏙️ City-Level Market Data")
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

   # ✅ Navigation (INSIDE function, properly indented)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"
            st.session_state.selected_state = None

    with col2:
        if st.button("Proceed to City Comparison →"):
            st.session_state.view = "CITY"


# -------------------------------------------------
# PAGE 3 → CITY VIEW (FIXED & FINAL)
# -------------------------------------------------
def show_city_view():
    city = st.session_state.selected_city
    state = st.session_state.selected_state
    questions = st.session_state.selected_question

    df = city_df[
        (city_df["city"] == city) &
        (city_df["state"] == state)
    ].copy()

    # ✅ Safe KPI calculation
    city_avg = df["price_numeric"].mean()
    state_avg = india_df[india_df["state"] == state][PRICE_COL_STATE].iloc[0]

    # -----------------------------
    # Header
    # -----------------------------
    st.title(f"🏙️ City–State Comparison – {city}")
    st.caption(f"Locality-level analysis vs **{state}** benchmark")

    # -----------------------------
    # KPI Section
    # -----------------------------
    st.subheader("📌 Key Comparison Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("City Avg Price / Sqft", f"₹ {int(city_avg):,}")
    c2.metric("State Avg Price / Sqft", f"₹ {int(state_avg):,}")
    c3.metric("Difference", f"₹ {int(city_avg - state_avg):,}")

    # -----------------------------
    # Selected Questions
    # -----------------------------
    st.subheader("🎯 Selected Analysis Insights")

for q in questions:

    if "priced higher" in q:
        if city_avg > state_avg:
            st.success(f"The city is priced higher than the state by ₹{int(city_avg - state_avg):,} per sqft.")
        else:
            st.info("The city is priced lower than the state average.")

    elif "affordable" in q:
        if city_avg < state_avg:
            st.success("The city is more affordable compared to the state.")
        else:
            st.warning("The city is less affordable due to higher prices.")

    elif "growing" in q:
        growth_ratio = city_avg / state_avg if state_avg else 0
        st.info(f"The city shows a growth ratio of {round(growth_ratio, 2)}× compared to the state.")

    elif "localities outperform" in q:
        outperform = df[df["price_numeric"] > state_avg]["locality"].unique()
        st.success(f"Outperforming localities: {', '.join(outperform[:5])}")

    elif "premium" in q:
        market_type = "Premium" if city_avg > state_avg else "Affordable"
        st.info(f"The city is a **{market_type} housing market**.")

    else:
        st.info("Detailed analysis for this question will be enhanced in next iteration.")
    # -----------------------------
    # Core Analysis (locality driven)
    # -----------------------------
    st.subheader("📊 Locality‑Level Price Analysis")

    locality_avg = (
        df.groupby("locality")["price_numeric"]
        .mean()
        .sort_values(ascending=False)
    )

    st.bar_chart(locality_avg)
    st.caption(f"State Benchmark: ₹ {int(state_avg):,}")

    # -----------------------------
    # Data Table
    # -----------------------------
    st.subheader("📋 Locality Data")
    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # Navigation
    # -----------------------------
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

import streamlit as st
import pandas as pd
import re

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Real Estate Market Analyzer", layout="wide")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def normalize_columns(df):
    df.columns = [
        re.sub(r"_+", "_",
               re.sub(r"[^a-z0-9]+", "_", col.lower().strip())).strip("_")
        for col in df.columns
    ]
    return df

def find_column(df, keywords):
    for col in df.columns:
        for key in keywords:
            if key in col:
                return col
    return None

# -------------------------------------------------
# Load Datasets
# -------------------------------------------------
@st.cache_data
def load_data():
    india = normalize_columns(pd.read_csv("india_state_data.csv"))
    city = normalize_columns(pd.read_csv("city_level_data.csv"))
    return india, city

india_df, city_df = load_data()

# -------------------------------------------------
# Detect Required Columns
# -------------------------------------------------
state_col = find_column(city_df, ["state"])
city_col = find_column(city_df, ["city"])
price_col_city = find_column(city_df, ["price_per_sqft"])
price_col_state = find_column(india_df, ["price", "sqft"])

if not state_col or not city_col or not price_col_city:
    st.error("Required columns not found. Please verify CSV headers.")
    st.stop()

city_df.rename(columns={state_col: "state", city_col: "city"}, inplace=True)

# -------------------------------------------------
# Session State
# -------------------------------------------------
st.session_state.setdefault("view", "INDIA")
st.session_state.setdefault("selected_state", None)
st.session_state.setdefault("selected_city", None)

# -------------------------------------------------
# INDIA VIEW
# -------------------------------------------------
def show_india_view():
    st.title("🇮🇳 Indian Real Estate Market Overview")

    st.dataframe(india_df, use_container_width=True)

    states = sorted(city_df["state"].unique())
    selected_state = st.selectbox("Select a State", states)

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE VIEW
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    st.dataframe(
        india_df[india_df.get("state", "") == state],
        use_container_width=True
    )

    cities = sorted(city_df[city_df["state"] == state]["city"].unique())
    selected_city = st.selectbox("Select City", cities)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"
    with col2:
        if st.button("View City Deep‑Dive →"):
            st.session_state.selected_city = selected_city
            st.session_state.view = "CITY"

# -------------------------------------------------
# CITY VIEW (WITH COMPARISON GRAPHS)
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

    city_avg = city_data[price_col_city].mean()
    state_avg = (
        state_data[price_col_state].iloc[0]
        if price_col_state in state_data.columns and not state_data.empty
        else None
    )

    # KPIs
    col1, col2 = st.columns(2)
    col1.metric("City Avg Price / Sqft", f"₹ {int(city_avg):,}")
    if state_avg:
        col2.metric("State Avg Price / Sqft", f"₹ {int(state_avg):,}")

    st.markdown("---")

    # City vs State bar chart (matches example image intent)
    st.subheader("📊 City vs State Avg Price Comparison")

    compare_df = pd.DataFrame(
        {"Avg Price per Sqft": [city_avg, state_avg]},
        index=["City", "State"]
    )

    st.bar_chart(compare_df)

    # Locality ranking (city)
    if "locality" in city_data.columns:
        st.subheader("📍 Avg Price per Sqft by Locality (City)")
        locality_df = city_data.groupby("locality")[price_col_city].mean().sort_values(ascending=False)
        st.bar_chart(locality_df)

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

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
    india = normalize_columns(pd.read_csv("india_state_data.csv"))
    city = normalize_columns(pd.read_csv("city_level_data.csv"))
    return india, city

india_df, city_df = load_data()

# -------------------------------------------------
# Detect state & city columns
# -------------------------------------------------
def find_column(df, keyword):
    for col in df.columns:
        if keyword in col:
            return col
    return None

city_df.rename(columns={
    find_column(city_df, "state"): "state",
    find_column(city_df, "city"): "city"
}, inplace=True)

# -------------------------------------------------
# Session state
# -------------------------------------------------
st.session_state.setdefault("view", "INDIA")
st.session_state.setdefault("selected_state", None)
st.session_state.setdefault("selected_city", None)
st.session_state.setdefault("selected_question", None)

# -------------------------------------------------
# INDIA VIEW (unchanged logic)
# -------------------------------------------------
def show_india_view():
    st.title("🏘️💹 Indian Real Estate Market Overview")

    filtered = india_df.copy()
    st.dataframe(filtered, use_container_width=True)

    selected_state = st.selectbox("Select a State", sorted(city_df["state"].unique()))
    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# STATE VIEW (UPDATED)
# -------------------------------------------------
def show_state_view():
    state = st.session_state.selected_state
    st.title(f"📍 State Market Details – {state}")

    # -------------------------------
    # Benchmark Table
    # -------------------------------
    st.subheader("Benchmark Metrics")
    st.dataframe(india_df[india_df["state"] == state], use_container_width=True)

    # Filter city data for state
    state_city_df = city_df[city_df["state"] == state]

    # -------------------------------
    # TWO PIE CHARTS
    # -------------------------------
    st.subheader("📊 State-Level Market Distribution")

    col1, col2 = st.columns(2)

    # Pie 1: Property Type Distribution
    if "property_type" in state_city_df.columns:
        with col1:
            st.caption("Property Type Distribution")
            prop_series = state_city_df["property_type"].value_counts()
            st.pyplot(
                prop_series.plot.pie(autopct="%1.1f%%", ylabel="").figure
            )

    # Pie 2: Avg Price Contribution by City
    with col2:
        st.caption("Average Price Contribution by City")
        price_city = (
            state_city_df.groupby("city")["price_per_sqft"].mean()
        )
        st.pyplot(
            price_city.plot.pie(autopct="%1.1f%%", ylabel="").figure
        )

    st.divider()

    # -------------------------------
    # CITY-LEVEL DATA TABLE (Moved here)
    # -------------------------------
    st.subheader("🏙️ City-Level Market Data")
    st.dataframe(state_city_df, use_container_width=True)

    st.divider()

    # -------------------------------
    # CHAT-STYLE QUESTION SELECTION
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
        "What-if property attributes change in this city?"
    ]

    st.write("🤖 **Assistant:** What would you like to explore next?")

    selected_question = st.radio(
        "Select a question to proceed:",
        questions
    )

    st.session_state.selected_question = selected_question

    # -------------------------------
    # CITY SELECTION & NAVIGATION
    # -------------------------------
    selected_city = st.selectbox(
        "Select City for Deep-Dive",
        sorted(state_city_df["city"].unique())
    )

    colA, colB = st.columns(2)
    with colA:
        if st.button("← Back to India"):
            st.session_state.view = "INDIA"
            st.session_state.selected_state = None

    with colB:
        if st.button("Proceed to City Comparison →"):
            st.session_state.selected_city = selected_city
            st.session_state.view = "CITY"

# -------------------------------------------------
# CITY VIEW (unchanged logic placeholder)
# -------------------------------------------------
def show_city_view():
    st.title(f"🏙️ City–State Comparison – {st.session_state.selected_city}")
    st.info(f"Selected Question: {st.session_state.selected_question}")

    st.write("City vs State graphs and analytics will adapt based on the selected question.")

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

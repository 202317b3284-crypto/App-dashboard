import streamlit as st
import pandas as pd

# --------------------------------
# Page Configuration
# --------------------------------
st.set_page_config(
    page_title="Indian Real Estate Dashboard",
    layout="wide"
)

st.title("🏠 Indian Real Estate Market Dashboard")
st.write("State and region-wise housing price analysis (2024–2025)")

# --------------------------------
# Load Data from GitHub Repository
# --------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("Real_estate_data.csv")

df = load_data()

# --------------------------------
# Sidebar Filters
# --------------------------------
st.sidebar.header("🔍 Filter Options")

region_filter = st.sidebar.multiselect(
    "Select Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

state_filter = st.sidebar.multiselect(
    "Select State / Union Territory",
    options=df["State / Union Territory"].unique(),
    default=df["State / Union Territory"].unique()
)

filtered_df = df[
    (df["Region"].isin(region_filter)) &
    (df["State / Union Territory"].isin(state_filter))
]

# --------------------------------
# Dataset Preview
# --------------------------------
st.subheader("📋 Dataset Preview")
st.dataframe(filtered_df, use_container_width=True)

# --------------------------------
# Key Metrics
# --------------------------------
st.subheader("📌 Key Market Metrics")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Average Price / Sqft",
    f"₹ {int(filtered_df['Price/sqft (₹)'].mean()):,}"
)

col2.metric(
    "Avg Median Price 2024",
    f"₹ {round(filtered_df['Median House Price (₹ Lakh) - 2024'].mean(), 2)} L"
)

col3.metric(
    "Avg Median Price 2025",
    f"₹ {round(filtered_df['Median House Price (₹ Lakh) - 2025'].mean(), 2)} L"
)

# --------------------------------
# Price Comparison Chart (Streamlit Native)
# --------------------------------
st.subheader("📊 Median House Price Comparison (2024 vs 2025)")

chart_df = filtered_df[
    ["State / Union Territory",
     "Median House Price (₹ Lakh) - 2024",
     "Median House Price (₹ Lakh) - 2025"]
].set_index("State / Union Territory")

st.bar_chart(chart_df)

# --------------------------------
# Footer
# --------------------------------
st.markdown("---")
st.caption(
    "Built using Python, Streamlit & GitHub | Real Estate What‑If Market Analyzer"
)
``

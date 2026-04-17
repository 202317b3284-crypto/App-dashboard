# App-dashboard
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------
# Page Configuration
# --------------------------------
st.set_page_config(
    page_title="Indian Real Estate Dashboard",
    layout="wide"
)

st.title("🏠 Indian Real Estate Market Dashboard")
st.write("State & region-wise housing price insights (2024–2025)")

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
st.sidebar.header("🔎 Filters")

region_selected = st.sidebar.multiselect(
    "Select Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

state_selected = st.sidebar.multiselect(
    "Select State / UT",
    options=df["State / Union Territory"].unique(),
    default=df["State / Union Territory"].unique()
)

filtered_df = df[
    (df["Region"].isin(region_selected)) &
    (df["State / Union Territory"].isin(state_selected))
]

# --------------------------------
# Dataset Preview
# --------------------------------
st.subheader("📋 Dataset Preview")
st.dataframe(filtered_df)

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
# Visualization: Price Comparison
# --------------------------------
st.subheader("📊 Median House Price Comparison (2024 vs 2025)")

fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(
    filtered_df["State / Union Territory"],
    filtered_df["Median House Price (₹ Lakh) - 2024"],
    label="2024",
    alpha=0.7
)

ax.bar(
    filtered_df["State / Union Territory"],
    filtered_df["Median House Price (₹ Lakh) - 2025"],
    label="2025",
    alpha=0.7
)

ax.set_xticklabels(
    filtered_df["State / Union Territory"],
    rotation=45,
    ha="right"
)

ax.set_ylabel("Median House Price (₹ Lakh)")
ax.legend()

st.pyplot(fig)

# --------------------------------
# Footer
# --------------------------------
st.markdown("---")
st.caption("Built using Python, Streamlit & GitHub | Real Estate What‑If Market Analyzer")

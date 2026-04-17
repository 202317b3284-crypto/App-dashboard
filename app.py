import streamlit as st
import pandas as pd

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(
    page_title="Indian Real Estate Market Dashboard",
    layout="wide"
)

st.title("🏠 Indian Real Estate Market Dashboard")
st.write("State and region-wise housing price analysis (2024–2025)")

# --------------------------------
# Load and Clean CSV
# --------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Real_estate_data.csv")

    # ✅ Standardize column names (CRITICAL)
    df.columns = [
        "rank",
        "state",
        "region",
        "price_per_sqft",
        "median_price_2024_lakh",
        "median_price_2025_lakh",
        "median_price_cr",
        "median_price_usd",
        "lot_area_sqm",
        "living_area_sqft",
        "avg_bedrooms",
        "avg_bathrooms",
        "avg_house_age",
        "overall_quality",
        "median_income_lakh",
        "price_to_income_ratio",
        "proximity",
        "market_tier"
    ]

    return df

df = load_data()

# --------------------------------
# Sidebar Filters
# --------------------------------
st.sidebar.header("🔍 Filter Options")

region_filter = st.sidebar.multiselect(
    "Select Region",
    options=sorted(df["region"].unique()),
    default=sorted(df["region"].unique())
)

tier_filter = st.sidebar.multiselect(
    "Select Market Tier",
    options=sorted(df["market_tier"].unique()),
    default=sorted(df["market_tier"].unique())
)

filtered_df = df[
    (df["region"].isin(region_filter)) &
    (df["market_tier"].isin(tier_filter))
]

# --------------------------------
# Dataset Preview
# --------------------------------
st.subheader("📋 Dataset Preview")
st.dataframe(filtered_df, use_container_width=True)

# --------------------------------
# Key Metrics
# --------------------------------
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Avg Price / Sqft",
    f"₹ {int(filtered_df['price_per_sqft'].mean()):,}"
)

col2.metric(
    "Median Price 2024 (₹ Lakh)",
    round(filtered_df["median_price_2024_lakh"].mean(), 2)
)

col3.metric(
    "Median Price 2025 (₹ Lakh)",
    round(filtered_df["median_price_2025_lakh"].mean(), 2)
)

# --------------------------------
# Growth Calculation
# --------------------------------
filtered_df["growth_lakh"] = (
    filtered_df["median_price_2025_lakh"]
    - filtered_df["median_price_2024_lakh"]
)

# --------------------------------
# Price Comparison Chart
# --------------------------------
st.subheader("📊 Median House Price Comparison")

chart_df = filtered_df[
    ["state", "median_price_2024_lakh", "median_price_2025_lakh"]
].set_index("state")

st.bar_chart(chart_df)

# --------------------------------
# Growth Chart
# --------------------------------
st.subheader("📈 Price Growth (2024 → 2025)")

growth_chart = filtered_df[["state", "growth_lakh"]].set_index("state")
st.bar_chart(growth_chart)

# --------------------------------
# Footer
# --------------------------------
st.markdown("---")
st.caption("Built using Python, Streamlit & GitHub | Real Estate What‑If Market Analyzer")

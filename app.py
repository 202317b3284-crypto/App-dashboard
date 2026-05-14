import streamlit as st
import pandas as pd
import re

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
    city = normalize_columns(pd.read_excel("city_level_data.xlsx", engine="openpyxl"))
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
# Numeric conversion
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
# PAGE 1 → INDIA VIEW (ADD WHAT-IF BUTTON)
# -------------------------------------------------
def show_india_view():

    colA, colB = st.columns([8, 2])

    with colA:
        st.title("🏘️💹 Indian Real Estate Market Overview")

    with colB:
        if st.button("🧮 What‑If"):
            st.session_state.view = "WHATIF"

    region = st.selectbox("Select Region", ["All"] + sorted(india_df["region"].dropna().unique()))
    tier = st.selectbox("Select Market Tier", ["All"] + sorted(india_df["market_tier"].dropna().unique()))

    filtered = india_df.copy()
    if region != "All":
        filtered = filtered[filtered["region"] == region]
    if tier != "All":
        filtered = filtered[filtered["market_tier"] == tier]

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(filtered.groupby("state")[PRICE_COL_STATE].mean())

    with col2:
        st.bar_chart(filtered.groupby("state")["median_house_price_lakh_2025"].mean())

    st.subheader("📋 State Data")
    st.dataframe(filtered)

    selected_state = st.selectbox("Select State", filtered["state"].unique())

    if st.button("View State Details"):
        st.session_state.selected_state = selected_state
        st.session_state.view = "STATE"

# -------------------------------------------------
# PAGE 2 → STATE VIEW
# -------------------------------------------------
def show_state_view():

    state = st.session_state.selected_state
    st.title(f"📍 {state}")

    st.dataframe(india_df[india_df["state"] == state])

    state_city_df = city_df[city_df["state"] == state]

    st.dataframe(state_city_df)

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

    st.session_state.selected_question = st.multiselect("Select Questions", questions)

    st.session_state.selected_city = st.selectbox("Select City", state_city_df["city"].unique())

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back"):
            st.session_state.view = "INDIA"

    with col2:
        if st.button("Proceed"):
            st.session_state.view = "CITY"

# -------------------------------------------------
# PAGE 3 → CITY VIEW
# -------------------------------------------------
def show_city_view():

    city = st.session_state.selected_city
    state = st.session_state.selected_state
    questions = st.session_state.selected_question

    df = city_df[(city_df["city"] == city) & (city_df["state"] == state)]

    city_avg = df["price_numeric"].mean()
    state_avg = india_df[india_df["state"] == state][PRICE_COL_STATE].iloc[0]

    st.title(f"🏙️ {city} vs {state}")

    c1, c2, c3 = st.columns(3)
    c1.metric("City Avg", int(city_avg))
    c2.metric("State Avg", int(state_avg))
    c3.metric("Diff", int(city_avg - state_avg))

    st.subheader("Insights")

    for q in questions:

        if "priced higher" in q:
            st.write("Price comparison done")

        elif "affordable" in q:
            st.write("Affordability analyzed")

        elif "localities outperform" in q:
            outperform = df[df["price_numeric"] > state_avg]["locality"]
            st.write(outperform.head(5))

        else:
            st.info("Analysis available")

    st.bar_chart(df.groupby("locality")["price_numeric"].mean())

    if st.button("Back"):
        st.session_state.view = "STATE"

# -------------------------------------------------
# PAGE 4 → WHAT-IF CALCULATOR
# -------------------------------------------------
def show_whatif_view():

    st.title("🧮 What‑If Price Calculator")

    state = st.session_state.get("selected_state")
    city = st.session_state.get("selected_city")

    if not state or not city:
        st.warning("Select State & City first")
        if st.button("← Back"):
            st.session_state.view = "INDIA"
        return

    df = city_df[(city_df["city"] == city) & (city_df["state"] == state)]

    base_price = df["price_numeric"].mean()

    area = st.slider("Area", 500, 5000, 1500)
    beds = st.slider("Bedrooms", 1, 5, 3)
    baths = st.slider("Bathrooms", 1, 4, 2)
    age = st.slider("Age", 0, 30, 10)

    price = base_price + beds*300 + baths*200 - age*100
    estimated = price * area

    st.success(f"Estimated Price: ₹ {int(estimated):,}")

    matches = df[
        (df["price_numeric"] * area >= estimated * 0.8) &
        (df["price_numeric"] * area <= estimated * 1.2)
    ]

    st.subheader("Matching Localities")
    st.dataframe(matches)

    # ✅ DOWNLOAD
    csv = matches.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Data",
        csv,
        "localities.csv",
        "text/csv"
    )

    if st.button("← Back"):
        st.session_state.view = "INDIA"

# -------------------------------------------------
# CONTROLLER
# -------------------------------------------------
if st.session_state.view == "INDIA":
    show_india_view()
elif st.session_state.view == "STATE":
    show_state_view()
elif st.session_state.view == "CITY":
    show_city_view()
elif st.session_state.view == "WHATIF":
    show_whatif_view()

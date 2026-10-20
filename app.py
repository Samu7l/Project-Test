import streamlit as st
import pandas as pd
import numpy as np

# Set page layout & title
st.set_page_config(page_title="My First Dashboard", layout="wide")

st.title("📊 Simple Sales Dashboard")
st.write("Welcome to your interactive Streamlit dashboard!")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")
category = st.sidebar.selectbox("Select Category", ["All", "Electronics", "Clothing", "Home"])
sample_size = st.sidebar.slider("Number of Data Points", min_value=10, max_value=100, value=50)

# --- CREATE DUMMY DATA ---
np.random.seed(42)
data = pd.DataFrame({
    "Day": pd.date_range(start="2026-01-01", periods=sample_size),
    "Sales ($)": np.random.randint(100, 500, size=sample_size),
    "Profit ($)": np.random.randint(20, 150, size=sample_size),
    "Category": np.random.choice(["Electronics", "Clothing", "Home"], size=sample_size)
})

# Filter data based on sidebar selection
if category != "All":
    filtered_data = data[data["Category"] == category]
else:
    filtered_data = data

# --- KEY METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${filtered_data['Sales ($)'].sum():,}")
col2.metric("Total Profit", f"${filtered_data['Profit ($)'].sum():,}")
col3.metric("Average Sale", f"${filtered_data['Sales ($)'].mean():.2f}")

st.divider()

# --- CHARTS SECTION ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Sales Over Time")
    st.line_chart(filtered_data.set_index("Day")["Sales ($)"])

with col_right:
    st.subheader("📊 Profit vs Sales")
    st.bar_chart(filtered_data.set_index("Day")[["Sales ($)", "Profit ($)"]])

# --- DATA TABLE ---
with st.expander("🔍 View Raw Data"):
    st.dataframe(filtered_data, use_container_width=True)
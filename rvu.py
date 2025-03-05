import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - MILV Logo
st.sidebar.image("milv.png", width=250)  # Load logo in sidebar

st.title("📊 MILV Daily Productivity")

# Define storage path for the latest uploaded file
FILE_STORAGE_PATH = "latest_rvu.xlsx"

def load_data(file_path):
    """Loads data from an Excel file and ensures correct formatting."""
    xls = pd.ExcelFile(file_path)
    df = xls.parse(xls.sheet_names[0])

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # Convert "date" column
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])  # Drop invalid dates

    return df

# Load last uploaded file if exists
if os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
    latest_file_status = "✅ Using last uploaded file."
else:
    df = None
    latest_file_status = "⚠️ No previously uploaded file found."

# File Upload Section
uploaded_file = st.file_uploader("Upload the RVU Excel File (Optional)", type=["xlsx"])

if uploaded_file:
    with open(FILE_STORAGE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    df = load_data(FILE_STORAGE_PATH)
    st.success("✅ File uploaded successfully! Using new file.")

# If no upload, but previous file exists, load it
if df is not None:
    st.sidebar.info(latest_file_status)

    # Ensure "date" column exists before filtering
    if "date" not in df.columns:
        st.error("❌ The uploaded file does not contain a 'date' column. Please check your file.")
        st.stop()

    # Sidebar Filters
    st.sidebar.subheader("📅 Filter Data")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])  # Ensure no NaT values

    min_date = df["date"].min().date()
    latest_date = df["date"].max().date()
    max_date = latest_date  # Most recent date in dataset

    # Date range selector with latest date as default
    date_selection = st.sidebar.date_input(
        "Select Date Range",
        value=(latest_date, latest_date),
        min_value=min_date,
        max_value=max_date
    )

    # Handle date selection
    start_date = pd.to_datetime(date_selection[0])
    end_date = pd.to_datetime(date_selection[1])

    # Validate date order
    if start_date > end_date:
        st.sidebar.error("Error: End date must be after start date")
        st.stop()

    # Sidebar - Provider Selection
    st.sidebar.subheader("👩‍⚕️ Provider Selection")
    providers = df["author"].unique().tolist()
    all_option = "ALL Providers"

    selected_providers = st.sidebar.multiselect("Select Provider(s)", [all_option] + providers, default=[all_option])

    # Selection logic
    if all_option in selected_providers or not selected_providers:
        selected_providers = providers  # Select all providers

    # Filtering data
    df_filtered = df[
        (df["date"] >= start_date) & 
        (df["date"] <= end_date) & 
        (df["author"].isin(selected_providers))
    ]

    # Aggregate Metrics
    date_range_text = (
        f"for {start_date.strftime('%Y-%m-%d')}" 
        if start_date == end_date
        else f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    
    st.subheader(f"📊 Aggregate Measures {date_range_text}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Total Points", df_filtered["points"].sum())
    col2.metric("🛠️ Total Procedures", df_filtered["procedure"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["turnaround"].mean(), 2))

    # Detailed Data Display
    st.subheader("📄 Detailed Data Overview")
    df_sorted = df_filtered.sort_values(by=["turnaround"], ascending=[True])
    st.dataframe(df_sorted)

    # Download Feature
    csv = df_sorted.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download CSV",
        csv,
        f"MILV_Daily_Productivity_{start_date.date()}_to_{end_date.date()}.csv",
        "text/csv"
    )

else:
    st.warning("Please upload an Excel file to start analyzing data.")
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re  # For regex filtering of employment type

# Load MILV logo from GitHub
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"

# File path for storing the latest uploaded file
LAST_FILE_PATH = "latest_uploaded_file.xlsx"
ROSTER_FILE_PATH = "MILVRoster.csv"

# Function to load the last uploaded file
def load_last_uploaded_file():
    if os.path.exists(LAST_FILE_PATH):
        return pd.read_excel(LAST_FILE_PATH)
    return None

# Function to save uploaded file persistently
def save_uploaded_file(uploaded_file):
    with open(LAST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return pd.read_excel(LAST_FILE_PATH)

# Convert Turnaround Time safely to minutes
def convert_turnaround(time_value):
    try:
        return pd.to_timedelta(time_value).total_seconds() / 60
    except:
        return None  # Return None for invalid values

# Load MILV Roster Data
def load_roster():
    if os.path.exists(ROSTER_FILE_PATH):
        return pd.read_csv(ROSTER_FILE_PATH)
    return None

# Function to clean Employment Type (remove brackets and content inside)
def clean_employment_type(value):
    return re.sub(r"\s*\[.*?\]", "", str(value)).strip()

# Set Streamlit theme settings
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - Logo & Filters
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)

    # Load Roster Data
    roster_df = load_roster()

    # Load RVU Data
    df = load_last_uploaded_file()

    if df is not None:
        df = df.rename(columns={
            "Author": "Provider",
            "Procedure": "Total Procedures",
            "Points": "Total Points",
            "Turnaround": "Turnaround Time",
            "Points/half day": "Points per Half-Day",
            "Procedure/half": "Procedures per Half-Day"
        })

    # Merge Roster Data with RVU Data
    if df is not None and roster_df is not None:
        df = df.merge(roster_df, on="Provider", how="left")

        # Clean Employment Type column
        if "Employment Type" in df.columns:
            df["Employment Type"] = df["Employment Type"].apply(clean_employment_type)

    # Ensure 'Date' column is formatted correctly
    if df is not None and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        # Load default data as the latest date in dataset
        latest_date = df["Date"].max()
        df_filtered = df[df["Date"] == latest_date]

        # Date Filter UI
        st.subheader("📅 Select Date or Range")
        date_filter_option = st.radio("Select Date Filter:", ["Single Date", "Date Range"], horizontal=True)

        if date_filter_option == "Single Date":
            selected_date = st.date_input("Select Date", latest_date)
            df_filtered = df[df["Date"] == selected_date]
        else:
            start_date = st.date_input("Start Date", df["Date"].min())
            end_date = st.date_input("End Date", latest_date)
            df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

        # Provider Filter
        if "Provider" in df_filtered.columns:
            st.subheader("👨‍⚕️ Providers")
            provider_options = df_filtered["Provider"].dropna().unique()
            provider_options = ["ALL"] + list(provider_options)

            selected_providers = st.multiselect("Select Provider(s)", provider_options, default=["ALL"])

            if "ALL" not in selected_providers:
                df_filtered = df_filtered[df_filtered["Provider"].isin(selected_providers)]

        # Employment Type Filter
        if "Employment Type" in df_filtered.columns:
            st.subheader("💼 Employment Type")
            employment_options = df_filtered["Employment Type"].dropna().unique()
            employment_options = ["ALL"] + list(employment_options)

            selected_employment = st.multiselect("Select Employment Type", employment_options, default=["ALL"])

            if "ALL" not in selected_employment:
                df_filtered = df_filtered[df_filtered["Employment Type"].isin(selected_employment)]

        # Primary Subspecialty Filter
        if "Primary Subspecialty" in df_filtered.columns:
            st.subheader("🔬 Primary Subspecialty")
            subspecialty_options = df_filtered["Primary Subspecialty"].dropna().unique()
            subspecialty_options = ["ALL"] + list(subspecialty_options)

            selected_subspecialties = st.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])

            if "ALL" not in selected_subspecialties:
                df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(selected_subspecialties)]

# Load data from uploaded file
if uploaded_file:
    df = save_uploaded_file(uploaded_file)
    st.sidebar.success("✅ File uploaded successfully!")
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    latest_date = df["Date"].max()

# Ensure valid data for visualization
if df is not None and not df_filtered.empty:
    if "Turnaround Time" in df_filtered.columns:
        df_filtered["Turnaround Time"] = df_filtered["Turnaround Time"].astype(str).apply(convert_turnaround)
        df_filtered = df_filtered.dropna(subset=["Turnaround Time"])

    df_filtered = df_filtered.drop(columns=[col for col in df_filtered.columns if "Unnamed" in col], errors="ignore")

    # Ensure only dates, no timestamps
    df_filtered["Date"] = df_filtered["Date"].astype(str)

    # Display Summary Statistics
    st.title("📊 MILV Daily Productivity Dashboard")
    st.subheader(f"📋 Productivity Summary for {latest_date}")

    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    if "Turnaround Time" in df_filtered.columns:
        avg_turnaround = df_filtered["Turnaround Time"].mean()
        metrics_col1.metric("⏳ Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")

    if "Procedures per Half-Day" in df_filtered.columns:
        avg_procs = df_filtered["Procedures per Half-Day"].mean()
        metrics_col2.metric("🔬 Avg Procedures per Half Day", f"{avg_procs:.2f}")

    if "Points per Half-Day" in df_filtered.columns:
        avg_points = df_filtered["Points per Half-Day"].mean()
        metrics_col3.metric("📈 Avg Points per Half Day", f"{avg_points:.2f}")

    # Visualization
    st.subheader("📊 Performance Insights")

    # Color Code by Primary Subspecialty
    category_order = df_filtered["Date"].unique().tolist()

    # Turnaround Time Trends
    if "Turnaround Time" in df_filtered.columns:
        fig1 = px.line(df_filtered, x="Date", y="Turnaround Time", color="Primary Subspecialty",
                       title="Turnaround Time Trends (Minutes)", markers=True,
                       hover_data=["Provider", "Employment Type"],
                       category_orders={"Date": category_order})
        st.plotly_chart(fig1, use_container_width=True)

    # Display filtered data
    st.subheader("📋 Detailed Data")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.warning("⚠️ No data available for the selected filters. Please adjust your selections.")

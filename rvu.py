import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# Load MILV logo from GitHub
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"

# File paths
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
    if pd.isna(value) or value == "":
        return None
    return re.sub(r"\s*\[.*?\]", "", str(value)).strip()

# Function to format provider names as "Last, First"
def format_provider_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return None
    parts = name.split()
    if len(parts) > 1:
        return f"{parts[-1].capitalize()}, {' '.join(parts[:-1]).capitalize()}"
    return name.capitalize()

# Set Streamlit theme settings
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - Logo & Filters
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)

    # Load Roster Data
    roster_df = load_roster()

    # Upload File Section
    st.markdown("---")
    st.subheader("📂 Upload Daily RVU File")
    uploaded_file = st.file_uploader("", type=["xlsx"])

    # Load RVU Data
    df = save_uploaded_file(uploaded_file) if uploaded_file else load_last_uploaded_file()

# **Ensure df is initialized to avoid NameError**
df_filtered = pd.DataFrame()

if df is not None and not df.empty:
    df = df.rename(columns={
        "Author": "Provider",
        "Procedure": "Total Procedures",
        "Points": "Total Points",
        "Turnaround": "Turnaround Time",
        "Points/half day": "Points per Half-Day",
        "Procedure/half": "Procedures per Half-Day"
    })

    # Merge Roster Data with RVU Data
    if roster_df is not None:
        roster_df["Provider"] = roster_df["Provider"].str.strip().str.lower()
        df["Provider"] = df["Provider"].str.strip().str.lower()
        df = df.merge(roster_df, on="Provider", how="left")

    # Ensure 'Date' column is formatted correctly
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # Format Provider names as "Last, First"
    df["Provider"] = df["Provider"].apply(format_provider_name)

    # Get latest available date
    latest_date = df["Date"].max()

    # Apply filtering if latest_date exists
    if latest_date:
        df_filtered = df[df["Date"] == latest_date].copy()

        # Drop NaN values before filtering
        df_filtered.dropna(subset=["Employment Type", "Primary Subspecialty", "Turnaround Time"], inplace=True)

# **Ensure df_filtered exists before calculations**
if not df_filtered.empty:
    # Convert numeric fields properly
    df_filtered["Turnaround Time"] = pd.to_numeric(df_filtered["Turnaround Time"], errors="coerce")
    df_filtered["Procedures per Half-Day"] = pd.to_numeric(df_filtered["Procedures per Half-Day"], errors="coerce")
    df_filtered["Points per Half-Day"] = pd.to_numeric(df_filtered["Points per Half-Day"], errors="coerce")

    # Drop rows where critical data is missing
    df_filtered.dropna(subset=["Turnaround Time", "Procedures per Half-Day", "Points per Half-Day"], inplace=True)

    # Compute Aggregate Metrics (Prevent NaN values)
    avg_turnaround = df_filtered["Turnaround Time"].mean() if not df_filtered["Turnaround Time"].isna().all() else 0
    avg_procs = df_filtered["Procedures per Half-Day"].mean() if not df_filtered["Procedures per Half-Day"].isna().all() else 0
    avg_points = df_filtered["Points per Half-Day"].mean() if not df_filtered["Points per Half-Day"].isna().all() else 0

    # **Display Dashboard Title & Summary**
    st.title("📊 MILV Daily Productivity")
    st.subheader(f"📋 Productivity Summary: {df_filtered['Date'].min()} - {df_filtered['Date'].max()}")

    col1, col2, col3 = st.columns(3)
    col1.metric("⏳ Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")
    col2.metric("📑 Avg Procedures per Half-Day", f"{avg_procs:.2f}")
    col3.metric("📈 Avg Points per Half-Day", f"{avg_points:.2f}")

    # **Turnaround Time - Grouped Bar Chart (Subspecialty & Providers)**
    df_filtered.sort_values(by="Turnaround Time", ascending=False, inplace=True)
    fig1 = px.bar(df_filtered, x="Provider", y="Turnaround Time", color="Primary Subspecialty",
                  title="Turnaround Time by Provider within Subspecialty",
                  hover_data=["Provider", "Employment Type"],
                  barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    # **Procedures per Half-Day - Sorted Bar Chart**
    df_filtered.sort_values(by="Procedures per Half-Day", ascending=False, inplace=True)
    fig2 = px.bar(df_filtered, x="Provider", y="Procedures per Half-Day", color="Primary Subspecialty",
                  title="Procedures per Half Day by Provider")
    st.plotly_chart(fig2, use_container_width=True)

    # **Points per Half-Day - Line Chart for trends, Bar Chart if 1-day**
    if df_filtered["Date"].nunique() > 1:
        fig3 = px.line(df_filtered, x="Date", y="Points per Half-Day", color="Primary Subspecialty",
                       title="Points per Half Day Over Time", markers=True)
    else:
        fig3 = px.bar(df_filtered, x="Provider", y="Points per Half-Day", color="Primary Subspecialty",
                      title="Points per Half Day by Provider")

    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("⚠️ No valid data available. Try uploading a new file or adjusting the filters.")

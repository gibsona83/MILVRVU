import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re  # For regex filtering of employment type

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

# Load Roster Data
roster_df = load_roster()

# Sidebar - File Upload
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)
    st.markdown("---")
    st.subheader("📂 Upload Daily RVU File")
    uploaded_file = st.file_uploader("", type=["xlsx"])

    # Load RVU Data
    df = save_uploaded_file(uploaded_file) if uploaded_file else load_last_uploaded_file()

# Ensure data exists
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

    # Load latest data
    latest_date = df["Date"].max()
    df_filtered = df[df["Date"] == latest_date].copy()

    # Drop NaN values before plotting
    df_filtered.dropna(subset=["Turnaround Time", "Primary Subspecialty"], inplace=True)

    # Ensure Turnaround Time is numeric
    df_filtered["Turnaround Time"] = df_filtered["Turnaround Time"].astype(str).apply(convert_turnaround)
    df_filtered.dropna(subset=["Turnaround Time"], inplace=True)

    # Ensure at least one row exists before plotting
    if df_filtered.empty:
        st.warning("⚠️ No data available for the selected date.")
    else:
        # **Turnaround Time - Box Plot**
        fig1 = px.box(df_filtered, y="Turnaround Time", color="Primary Subspecialty",
                      title="Turnaround Time Distribution by Subspecialty")
        st.plotly_chart(fig1, use_container_width=True)

        # **Procedures per Half-Day - Bar Chart**
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
    st.warning("⚠️ No data available. Please upload an RVU file.")

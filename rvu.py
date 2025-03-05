import streamlit as st
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt

# GitHub Raw URL for the latest file
GITHUB_URL = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/RVU%20Daily%20Master%2011-2024.xlsx"

@st.cache_data
def load_data():
    """Fetch the latest data from GitHub and return a DataFrame."""
    response = requests.get(GITHUB_URL)
    if response.status_code == 200:
        file = io.BytesIO(response.content)
        xls = pd.ExcelFile(file)
        df = xls.parse(xls.sheet_names[0])
        df["Date"] = pd.to_datetime(df["Date"])
        df["Turnaround"] = pd.to_timedelta(df["Turnaround"]).dt.total_seconds() / 60  # Convert to minutes
        return df
    else:
        st.error("Failed to load data from GitHub.")
        return None

# Load data
df = load_data()
if df is not None:
    # Default to latest date
    latest_date = df["Date"].max()
    selected_date = st.sidebar.date_input("Select Date", latest_date)

    # Filter data by selected date
    df_filtered = df[df["Date"] == pd.to_datetime(selected_date)]

    # Summary Metrics
    st.title("📊 MILV RVU Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Latest Date", latest_date.strftime("%Y-%m-%d"))
    col2.metric("🔢 Total Points", df_filtered["Points"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["Turnaround"].mean(), 2))

    # Visualization - Turnaround Time Trends
    st.subheader("⏳ Turnaround Time Trends")
    fig, ax = plt.subplots()
    df.groupby("Date")["Turnaround"].mean().plot(ax=ax, marker="o")
    ax.set_ylabel("Minutes")
    ax.set_xlabel("Date")
    ax.set_title("Average Turnaround Time Over Time")
    st.pyplot(fig)

    # Visualization - Points per Half-Day
    st.subheader("📈 Points per Half-Day")
    fig, ax = plt.subplots()
    df_filtered.groupby("Shift")["Points/half day"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Points")
    ax.set_xlabel("Shift")
    ax.set_title("Points per Half-Day by Shift")
    st.pyplot(fig)

    # Visualization - Procedures per Half-Day
    st.subheader("🛠️ Procedures per Half-Day")
    fig, ax = plt.subplots()
    df_filtered.groupby("Shift")["Procedure/half"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Procedures")
    ax.set_xlabel("Shift")
    ax.set_title("Procedures per Half-Day by Shift")
    st.pyplot(fig)

else:
    st.error("No data available. Check your GitHub file URL.")

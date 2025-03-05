import streamlit as st
import pandas as pd
import os
import io
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV RVU Dashboard", layout="wide")

st.title("📊 MILV RVU Dashboard")

# Define storage path for the latest uploaded file
FILE_STORAGE_PATH = "latest_rvu.xlsx"

def load_data(file_path):
    """Loads data from an Excel file."""
    xls = pd.ExcelFile(file_path)
    df = xls.parse(xls.sheet_names[0])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Turnaround"] = pd.to_timedelta(df["Turnaround"]).dt.total_seconds() / 60  # Convert TAT to minutes
    return df

# Check if there is a stored file
if os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
    latest_file_status = "✅ Using last uploaded file."
else:
    df = None
    latest_file_status = "⚠️ No previously uploaded file found."

# File Upload Section
uploaded_file = st.file_uploader("Upload the RVU Excel File (Optional)", type=["xlsx"])

if uploaded_file:
    # Save the uploaded file
    with open(FILE_STORAGE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load the newly uploaded file
    df = load_data(FILE_STORAGE_PATH)
    st.success("✅ File uploaded successfully! Using new file.")

# If no upload happened, but a previous file exists, load it
if df is not None:
    st.info(latest_file_status)

    # Get the latest date
    latest_date = df["Date"].max()
    selected_date = st.sidebar.date_input("Select Date", latest_date)

    # Filter data for selected date
    df_filtered = df[df["Date"] == pd.to_datetime(selected_date)]

    # Summary Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Latest Date", latest_date.strftime("%Y-%m-%d"))
    col2.metric("🔢 Total Points", df_filtered["Points"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["Turnaround"].mean(), 2))

    # Turnaround Time Trends
    st.subheader("⏳ Turnaround Time Trends")
    fig, ax = plt.subplots()
    df.groupby("Date")["Turnaround"].mean().plot(ax=ax, marker="o")
    ax.set_ylabel("Minutes")
    ax.set_xlabel("Date")
    ax.set_title("Average Turnaround Time Over Time")
    st.pyplot(fig)

    # Points per Half-Day
    st.subheader("📈 Points per Half-Day")
    fig, ax = plt.subplots()
    df_filtered.groupby("Shift")["Points/half day"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Points")
    ax.set_xlabel("Shift")
    ax.set_title("Points per Half-Day by Shift")
    st.pyplot(fig)

    # Procedures per Half-Day
    st.subheader("🛠️ Procedures per Half-Day")
    fig, ax = plt.subplots()
    df_filtered.groupby("Shift")["Procedure/half day"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Procedures")
    ax.set_xlabel("Shift")
    ax.set_title("Procedures per Half-Day by Shift")
    st.pyplot(fig)

else:
    st.warning("Please upload an Excel file to start analyzing data.")

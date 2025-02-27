import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import io

# Define storage file for persistence
DATA_FILE = "latest_rvu_data.xlsx"
LOGO_PATH = "milv.png"  # Path to MILV logo

st.set_page_config(page_title="Daily Productivity Dashboard", layout="wide")

# Display the MILV logo and title
st.image(LOGO_PATH, width=250)
st.title("Daily Productivity Report Dashboard")

# File upload section
uploaded_file = st.file_uploader("Upload the latest RVU Daily Master file", type=["xlsx"])

if uploaded_file is not None:
    # Save uploaded file for persistence
    with open(DATA_FILE, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("File uploaded successfully!")

# Load data from the last uploaded file
if os.path.exists(DATA_FILE):
    df = pd.read_excel(DATA_FILE, sheet_name="powerscribe Data", engine="openpyxl")
    st.sidebar.info(f"Loaded data from: {DATA_FILE}")
else:
    st.warning("No file uploaded yet. Please upload an RVU Daily Master file.")
    st.stop()

# Ensure date column is in datetime format
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Convert Turnaround Time from string to total seconds
def convert_time_to_seconds(time_str):
    try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return np.nan  # Handle errors by returning NaN

# Ensure "Turnaround" column is a string before conversion
if "Turnaround" in df.columns:
    df["Turnaround"] = df["Turnaround"].astype(str)
    df["Turnaround_Seconds"] = df["Turnaround"].apply(convert_time_to_seconds)
else:
    st.error("The column 'Turnaround' is missing in the dataset.")
    st.stop()

# Handle blank shift values (NaN) - assign them a half-day shift for comparison but flag them as 'No Shift in Qgenda'
df["shift"] = df["shift"].fillna(1).replace(0, 1)  # Assign a half-day shift for comparison purposes
df["Shift Type"] = df["shift"].apply(lambda x: "No Shift in Qgenda" if x == 1 else "Scheduled Shift")

# Compute per half-day metrics
df["Points per Half-Day"] = df["Points"] / df["shift"]
df["Procedures per Half-Day"] = df["Procedure"] / df["shift"]

# Sidebar filters
st.sidebar.header("Filters")
date_selection = st.sidebar.date_input("Select a date range", [df["Date"].min(), df["Date"].max()],
                                       min_value=df["Date"].min(), max_value=df["Date"].max())

# Dropdown for provider selection
providers = ["ALL"] + list(df["Author"].unique())
selected_providers = st.sidebar.multiselect("Select Providers", providers, default=["ALL"])

# Filter data based on selections
if isinstance(date_selection, tuple) or isinstance(date_selection, list):
    start_date, end_date = date_selection
    filtered_data = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
else:
    filtered_data = df[df["Date"] == pd.to_datetime(date_selection)]

if "ALL" not in selected_providers:
    filtered_data = filtered_data[filtered_data["Author"].isin(selected_providers)]

# Update overview dynamically based on filtered data
latest_data = filtered_data.copy()

# Calculate mean turnaround time in seconds
avg_turnaround = latest_data["Turnaround_Seconds"].mean()

# Convert back to H:M:S for display
if not np.isnan(avg_turnaround):
    avg_turnaround_hms = f"{int(avg_turnaround // 3600)}:{int((avg_turnaround % 3600) // 60)}:{int(avg_turnaround % 60)}"
else:
    avg_turnaround_hms = "N/A"

st.subheader("📊 Overview Based on Selection")

# Display KPI metrics with tooltips
col1, col2, col3 = st.columns([1, 1, 1])
col1.metric("Total Procedures", latest_data["Procedure"].sum(), help="Total number of procedures completed in the selected range.")
col2.metric("Total Points", latest_data["Points"].sum(), help="Custom productivity metric based on workload weighting in the selected range.")
col3.metric("Avg Turnaround Time", avg_turnaround_hms, help="Average time taken to complete a report, calculated from submission to finalization.")

# Visualization: Points per Half-Day
st.subheader("📈 Points per Half-Day (Descending)")
fig, ax = plt.subplots(figsize=(10, 6))
filtered_data.groupby("Author")["Points per Half-Day"].sum().sort_values(ascending=False).plot(kind="barh", ax=ax, color="steelblue", fontsize=10)
ax.set_xlabel("Total Points per Half-Day", fontsize=12)
ax.set_ylabel("Provider", fontsize=12)
st.pyplot(fig)

# Visualization: Procedures per Half-Day
st.subheader("📈 Procedures per Half-Day (Descending)")
fig, ax = plt.subplots(figsize=(10, 6))
filtered_data.groupby("Author")["Procedures per Half-Day"].sum().sort_values(ascending=False).plot(kind="barh", ax=ax, color="darkorange", fontsize=10)
ax.set_xlabel("Total Procedures per Half-Day", fontsize=12)
ax.set_ylabel("Provider", fontsize=12)
st.pyplot(fig)

# Turnaround Time (TAT) View
st.subheader("⏳ Turnaround Time (Ascending)")
fig, ax = plt.subplots(figsize=(10, 6))
filtered_data.groupby("Author")["Turnaround_Seconds"].mean().sort_values(ascending=True).plot(kind="barh", ax=ax, color="orangered", fontsize=10)
ax.set_xlabel("Average Turnaround Time (seconds)", fontsize=12)
ax.set_ylabel("Provider", fontsize=12)
st.pyplot(fig)

# Downloadable filtered data
st.subheader(f"📂 Filtered Data for {start_date} to {end_date}")
st.dataframe(filtered_data)

# Convert dataframe to CSV for download
csv = filtered_data.to_csv(index=False)
buffer = io.BytesIO()
buffer.write(csv.encode())
buffer.seek(0)
st.download_button("Download Filtered Data as CSV", buffer, "filtered_data.csv", "text/csv", key="download-csv")

import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime as dt

# Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Load MILV logo
MILV_LOGO_PATH = "milv.png"  # Ensure this file is in the same directory
if os.path.exists(MILV_LOGO_PATH):
    st.sidebar.image(MILV_LOGO_PATH)

# MILV color scheme
PRIMARY_COLOR = "#003366"  # Dark blue
ACCENT_COLOR = "#0099CC"   # Light blue
TEXT_COLOR = "#FFFFFF"     # White

# File storage path
UPLOAD_DIR = "./uploaded_files"
SAVED_FILE_PATH = os.path.join(UPLOAD_DIR, "latest_uploaded_file.xlsx")

# Ensure the directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Upload new file
st.sidebar.header("Upload New Excel File")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is not None:
    with open(SAVED_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("File uploaded successfully!")

# Load the latest available file
if os.path.exists(SAVED_FILE_PATH):
    try:
        df = pd.read_excel(SAVED_FILE_PATH, sheet_name="powerscribe Data")  # Load correct sheet
        st.sidebar.info("Using the latest uploaded file.")
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()
else:
    st.warning("No file uploaded yet. Please upload an Excel file.")
    st.stop()

# Convert date column to datetime
df["Date"] = pd.to_datetime(df["Date"], errors='coerce')

# Sidebar filtering options
st.sidebar.header("Filters")
st.sidebar.subheader("Date Filters")
selected_date = st.sidebar.date_input("Select a Single Date", df["Date"].max())
date_range = st.sidebar.date_input("Select Date Range", [])
selected_day_of_week = st.sidebar.multiselect("Select Day of the Week", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=[])
selected_month = st.sidebar.multiselect("Select Month", options=df["Date"].dt.month_name().unique(), default=[])

st.sidebar.subheader("Provider Selection")
selected_providers = st.sidebar.multiselect("Select Providers", options=df["Author"].unique(), default=df["Author"].unique())

# Apply filters
filtered_data = df[df["Author"].isin(selected_providers)]
if date_range:
    filtered_data = filtered_data[(filtered_data["Date"] >= pd.to_datetime(date_range[0])) &
                                  (filtered_data["Date"] <= pd.to_datetime(date_range[1]))]
if selected_day_of_week:
    filtered_data = filtered_data[filtered_data["Date"].dt.day_name().isin(selected_day_of_week)]
if selected_month:
    filtered_data = filtered_data[filtered_data["Date"].dt.month_name().isin(selected_month)]

# Compute Points per Day and Procedures per Day
filtered_data["Points per Day"] = filtered_data["Points/half day"] * 2
filtered_data["Procedures per Day"] = filtered_data["Procedure/half"] * 2

# Default number of providers for visualization clarity
default_top_n = 10

# Create side-by-side visualizations for top and bottom performers
st.markdown(f"<h2 style='color: {ACCENT_COLOR};'>Top & Bottom Performers by Points per Day</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

top_points = filtered_data.nlargest(default_top_n, "Points per Day")
bottom_points = filtered_data.nsmallest(default_top_n, "Points per Day")

ax[0].barh(top_points["Author"], top_points["Points per Day"], color=ACCENT_COLOR)
ax[0].set_xlabel("Points per Day")
ax[0].set_title("Top Performers")

ax[1].barh(bottom_points["Author"], bottom_points["Points per Day"], color=PRIMARY_COLOR)
ax[1].set_xlabel("Points per Day")
ax[1].set_title("Bottom Performers")

st.pyplot(fig)

st.markdown(f"<h2 style='color: {ACCENT_COLOR};'>Top & Bottom Performers by Procedures per Day</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

top_procedures = filtered_data.nlargest(default_top_n, "Procedures per Day")
bottom_procedures = filtered_data.nsmallest(default_top_n, "Procedures per Day")

ax[0].barh(top_procedures["Author"], top_procedures["Procedures per Day"], color=ACCENT_COLOR)
ax[0].set_xlabel("Procedures per Day")
ax[0].set_title("Top Performers")

ax[1].barh(bottom_procedures["Author"], bottom_procedures["Procedures per Day"], color=PRIMARY_COLOR)
ax[1].set_xlabel("Procedures per Day")
ax[1].set_title("Bottom Performers")

st.pyplot(fig)

st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>Top & Bottom Performers by Turnaround Time</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

top_tat = filtered_data.nsmallest(default_top_n, "Turnaround")
bottom_tat = filtered_data.nlargest(default_top_n, "Turnaround")

ax[0].barh(top_tat["Author"], top_tat["Turnaround"], color=ACCENT_COLOR)
ax[0].set_xlabel("Turnaround Time (TAT)")
ax[0].set_title("Fastest Turnaround")

ax[1].barh(bottom_tat["Author"], bottom_tat["Turnaround"], color=PRIMARY_COLOR)
ax[1].set_xlabel("Turnaround Time (TAT)")
ax[1].set_title("Slowest Turnaround")

st.pyplot(fig)

# Summary statistics
st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>📈 Summary Statistics</h2>", unsafe_allow_html=True)
st.write(filtered_data[["Points per Day", "Procedures per Day", "Turnaround"]].describe())

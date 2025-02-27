import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Load MILV logo
MILV_LOGO_PATH = "milv.png"  # Ensure this file is in the same directory
if os.path.exists(MILV_LOGO_PATH):
    st.sidebar.image(MILV_LOGO_PATH, use_column_width=True)

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

# Display dataset overview
st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>📊 MILV Daily Productivity Overview</h1>", unsafe_allow_html=True)
st.write("### First 5 Rows of Data")
st.dataframe(df.head())

# Sidebar filtering options
st.sidebar.header("Filters")
selected_providers = st.sidebar.multiselect("Select Providers", options=df["Author"].unique(), default=df["Author"].unique())
date_range = st.sidebar.date_input("Select Date Range", [])

# Filter data
filtered_data = df[df["Author"].isin(selected_providers)]
if date_range:
    filtered_data = filtered_data[(filtered_data["Date"] >= pd.to_datetime(date_range[0])) &
                                  (filtered_data["Date"] <= pd.to_datetime(date_range[1]))]

# Compute Points per Day and Procedures per Day
filtered_data["Points per Day"] = filtered_data["Points/half day"] * 2
filtered_data["Procedures per Day"] = filtered_data["Procedure/half"] * 2

# Create visualizations
st.markdown(f"<h2 style='color: {ACCENT_COLOR};'>Top Performers by Points per Day</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots()
sorted_data = filtered_data.sort_values("Points per Day", ascending=False)
ax.barh(sorted_data["Author"], sorted_data["Points per Day"], color=ACCENT_COLOR)
ax.set_xlabel("Points per Day")
ax.set_title("Top Performers by Points per Day")
st.pyplot(fig)

st.markdown(f"<h2 style='color: {ACCENT_COLOR};'>Top Performers by Procedures per Day</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots()
sorted_data = filtered_data.sort_values("Procedures per Day", ascending=False)
ax.barh(sorted_data["Author"], sorted_data["Procedures per Day"], color=ACCENT_COLOR)
ax.set_xlabel("Procedures per Day")
ax.set_title("Top Performers by Procedures per Day")
st.pyplot(fig)

st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>Turnaround Time by Provider</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots()
sorted_data = filtered_data.sort_values("Turnaround", ascending=True)
ax.barh(sorted_data["Author"], sorted_data["Turnaround"], color=PRIMARY_COLOR)
ax.set_xlabel("Turnaround Time (TAT)")
ax.set_title("Turnaround Time by Provider")
st.pyplot(fig)

# Summary statistics
st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>📈 Summary Statistics</h2>", unsafe_allow_html=True)
st.write(filtered_data[["Points per Day", "Procedures per Day", "Turnaround"].describe()])

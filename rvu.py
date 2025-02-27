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
st.markdown("""
    <style>
        body {
            background-color: #f5f5f5;
        }
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff;
        }
        [data-testid="stSidebar"] {
            background-color: #e0e0e0;
        }
        [data-theme="dark"] [data-testid="stAppViewContainer"] {
            background-color: #1e1e1e;
        }
        [data-theme="dark"] [data-testid="stSidebar"] {
            background-color: #333333;
        }
    </style>
""", unsafe_allow_html=True)

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
    df = pd.read_excel(DATA_FILE, sheet_name='powerscribe Data', engine="openpyxl")
    st.sidebar.info(f"Loaded data from: {DATA_FILE}")
else:
    st.warning("No file uploaded yet. Please upload an RVU Daily Master file.")
    st.stop()

# Ensure date column is in datetime format
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Sidebar filters
st.sidebar.header("Filters")
date_selection = st.sidebar.date_input("Select a date range", [df['Date'].min(), df['Date'].max()], min_value=df['Date'].min(), max_value=df['Date'].max())

# Dropdown for provider selection
providers = ['ALL'] + list(df['Author'].unique())
selected_providers = st.sidebar.multiselect("Select Providers", providers, default=['ALL'])

# Filter data based on selections
if isinstance(date_selection, tuple) or isinstance(date_selection, list):
    start_date, end_date = date_selection
    filtered_data = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
else:
    filtered_data = df[df['Date'] == pd.to_datetime(date_selection)]

if 'ALL' not in selected_providers:
    filtered_data = filtered_data[filtered_data['Author'].isin(selected_providers)]

# Get latest day for KPIs
latest_day = df['Date'].max()
latest_data = df[df['Date'] == latest_day]

st.subheader(f"📊 Latest Day Overview: {latest_day.strftime('%Y-%m-%d')}")

# Display KPI metrics with tooltips
col1, col2, col3 = st.columns([1, 1, 1])
col1.metric("Total Procedures", latest_data['Procedure'].sum(), help="Total number of procedures completed on this date.")
col2.metric("Total Points", latest_data['Points'].sum(), help="Custom productivity metric based on workload weighting.")
col3.metric("Avg Turnaround Time", latest_data['Turnaround'].mean(), help="Average time taken to complete a report, calculated from submission to finalization.")

# Visualization: Bar chart for productivity per half day, with improved readability
st.subheader("📈 Productivity per Half-Day")
fig, ax = plt.subplots(figsize=(12, 6))
filtered_plot_data = filtered_data.groupby('Author')['Points/half day'].sum().sort_values()
filtered_plot_data.plot(kind='barh', ax=ax, color='skyblue', fontsize=10)
ax.set_xlabel("Total Points per Half-Day", fontsize=12)
ax.set_ylabel("Provider", fontsize=12)
ax.set_title("Provider Productivity per Half-Day", fontsize=14)
plt.xticks(fontsize=10)
plt.yticks(fontsize=8)
st.pyplot(fig)

# Downloadable filtered data
st.subheader(f"📂 Filtered Data for {start_date} to {end_date}")
st.dataframe(filtered_data)

# Convert dataframe to CSV for download
csv = filtered_data.to_csv(index=False)
buffer = io.BytesIO()
buffer.write(csv.encode())
buffer.seek(0)
st.download_button("Download Filtered Data as CSV", buffer, "filtered_data.csv", "text/csv", key='download-csv')

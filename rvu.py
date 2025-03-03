import streamlit as st
import pandas as pd
import numpy as np
import os
import requests

# Define GitHub repository details
GITHUB_REPO = "gibsona83/milvrvu"
LATEST_FILE_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/latest_uploaded_file.xlsx"
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"
LATEST_FILE_PATH = "latest_uploaded_file.xlsx"

# Function to download the latest file from GitHub
def download_latest_file():
    try:
        response = requests.get(LATEST_FILE_URL)
        if response.status_code == 200:
            with open(LATEST_FILE_PATH, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        st.sidebar.error(f"Error fetching file from GitHub: {e}")
    return False

# Function to clean and process uploaded data
def clean_and_process_data(uploaded_file):
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        df = pd.read_excel(xls, sheet_name='powerscribe Data')

        # Drop unnecessary columns
        df = df.drop(columns=[col for col in df.columns if 'Unnamed' in col], errors='ignore')

        # Ensure Turnaround is properly formatted
        def clean_turnaround(time_str):
            try:
                if pd.isna(time_str):
                    return np.nan
                if isinstance(time_str, str):
                    if '.' in time_str:
                        time_str = time_str.replace('.', ' days ')
                    return pd.to_timedelta(time_str, errors='coerce')
                return np.nan
            except:
                return np.nan

        df['Turnaround'] = df['Turnaround'].astype(str).apply(clean_turnaround)
        return df
    return None

# Streamlit UI
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Apply custom styling
st.markdown(
    """
    <style>
        .main {background-color: #f4f4f4;}
        [data-testid="stSidebar"] {background-color: #002F6C; color: white;}
        h1, h2, h3, h4, h5, h6 {color: #002F6C !important;}
        .stButton>button {background-color: #004B87 !important; color: white; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Display logo
st.image(LOGO_URL, width=300)
st.title("MILV Daily Productivity Dashboard")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload RVU Daily Master Excel File", type=["xlsx"])

# Save the uploaded file if it exists
if uploaded_file is not None:
    with open(LATEST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("File uploaded successfully! Data will persist until a new file is uploaded.")

# Download the latest file from GitHub if no new file is uploaded
if uploaded_file is None and not os.path.exists(LATEST_FILE_PATH):
    if download_latest_file():
        st.sidebar.success("Latest file downloaded from GitHub repository.")
    else:
        st.sidebar.error("No file found locally or on GitHub.")

# Load the latest available file
if os.path.exists(LATEST_FILE_PATH):
    df = clean_and_process_data(LATEST_FILE_PATH)
else:
    df = None

if df is not None:
    st.sidebar.subheader("Filters")
    
    # Date filter
    date_options = df['Date'].dropna().unique()
    selected_dates = st.sidebar.multiselect("Select Date(s)", date_options, default=date_options[-1:])
    
    # Author filter
    author_options = df['Author'].dropna().unique()
    selected_authors = st.sidebar.multiselect("Select Author(s)", author_options, default=author_options)
    
    # Filter Data
    filtered_df = df[df['Date'].isin(selected_dates) & df['Author'].isin(selected_authors)]
    
    # KPI Summary
    st.subheader("Summary Statistics")
    st.metric("Avg Points/Half Day", round(filtered_df['Points/half day'].mean(), 2))
    st.metric("Avg Procedures/Half Day", round(filtered_df['Procedure/half'].mean(), 2))
    st.metric("Avg Turnaround Time", str(filtered_df['Turnaround'].mean()))
    
    # Show Data
    st.subheader("Filtered Data")
    st.dataframe(filtered_df)
    
    # Charts
    st.subheader("Performance Visualization")
    st.line_chart(filtered_df.groupby('Date')[['Points/half day', 'Procedure/half']].mean())

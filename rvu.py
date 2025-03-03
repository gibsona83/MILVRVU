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

        # Drop unnecessary columns and remove leading numeric index from Date
        df = df.drop(columns=[col for col in df.columns if 'Unnamed' in col], errors='ignore')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Keep full datetime

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
        .st-multi-select div[data-baseweb="select"] {height: 40px; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Display logo
st.image(LOGO_URL, width=300)
st.title("MILV Daily Productivity Dashboard")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload RVU Daily Master Excel File", type=["xlsx"])

# Save the uploaded file if it exists and push to GitHub storage
if uploaded_file is not None:
    with open(LATEST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("File uploaded successfully! Data will persist until a new file is uploaded.")

# Ensure the latest uploaded file is loaded for all users
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
    
    # Determine min and max dates dynamically from the data
    df['Date'] = df['Date'].dt.date  # Convert to just date for selection
    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date, format="YYYY-MM-DD")
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date
    
    # Provider filter with dropdown, defaulting to all providers and allowing search/multi-select
    author_options = df['Author'].dropna().unique()
    selected_authors = st.sidebar.multiselect("Select Provider(s)", author_options, default=author_options, help="Select one or more providers from the dropdown")
    
    # Filter Data by Date range and selected providers
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date) & df['Author'].isin(selected_authors)]
    
    # KPI Summary with improved display
    st.subheader("Summary Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Points/Half Day", round(filtered_df['Points/half day'].mean(), 2))
    col2.metric("Avg Procedures/Half Day", round(filtered_df['Procedure/half'].mean(), 2))
    avg_turnaround = str(filtered_df['Turnaround'].mean()).split(' days ')[-1].split('.')[0] if pd.notna(filtered_df['Turnaround'].mean()) else "N/A"
    col3.metric("Avg Turnaround Time", avg_turnaround)
    
    # Show Data without numeric prefixes
    st.subheader("Filtered Data")
    st.dataframe(filtered_df.drop(columns=['Shift'], errors='ignore'))
    
    # Charts
    st.subheader("Performance Visualization")
    st.line_chart(filtered_df.groupby('Date')[['Points/half day', 'Procedure/half']].mean())

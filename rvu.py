import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Display logo
st.image("/mnt/data/milv.png", width=250)

st.title("📊 MILV Daily Productivity")

# Sidebar for filters and file upload
with st.sidebar:
    st.header("Upload RVU File")
    uploaded_file = st.file_uploader("Drag and drop RVU Master file here", type=["xlsx"])

# Define colors for Primary Subspecialty (adjust for dark/light mode)
SUBSPECIALTY_COLORS = {
    "Interventional": "#1F77B4",  # Blue
    "Neuroradiology": "#FF7F0E",  # Orange
    "Diagnostic": "#2CA02C",  # Green
    "Neuro-Interventional": "#D62728",  # Red
    "Body": "#9467BD",  # Purple
    "Pediatrics": "#8C564B",  # Brown
    "Nuclear Med": "#E377C2",  # Pink
    "Cardiac": "#7F7F7F",  # Gray
    "Unknown": "#17BECF"  # Default cyan
}

@st.cache_data
def load_roster():
    """Downloads the MILV Roster from GitHub and loads it."""
    github_url = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/MILVRoster.csv"
    local_path = "/mnt/data/MILVRoster.csv"

    try:
        if not os.path.exists(local_path):
            response = requests.get(github_url, timeout=10)
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(response.content)
            else:
                st.warning(f"⚠️ Failed to download MILVRoster.csv (HTTP {response.status_code}). Using default values.")
                return None

        df = pd.read_csv(local_path)
        df["Employment Type"] = df["Employment Type"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()
        df["Employment Type"].fillna("Unknown", inplace=True)

        return df
    except Exception as e:
        st.error(f"Error loading MILV Roster: {e}")
        return None

def convert_turnaround(time_value):
    """Converts turnaround time from HH:MM:SS or float to minutes."""
    if pd.isna(time_value):
        return 0

    if isinstance(time_value, float):  # Already a decimal format
        return round(time_value * 60)

    if isinstance(time_value, str):
        parts = time_value.split(":")
        if len(parts) == 3:  
            try:
                hours, minutes, seconds = map(int, parts)
                return hours * 60 + minutes  
            except ValueError:
                return 0  

    return 0  

@st.cache_data
def load_data(file):
    """Loads and processes the RVU Daily Master file."""
    try:
        rvu_df = pd.read_excel(file, sheet_name="powerscribe Data")

        rvu_df.rename(columns={
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }, inplace=True)

        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date
        rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        roster_df = load_roster()
        if roster_df is not None:
            rvu_df = rvu_df.merge(roster_df, on="Provider", how="left")
        else:
            rvu_df["Employment Type"] = "Unknown"
            rvu_df["Primary Subspecialty"] = "Unknown"

        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def filter_data(df, date_range, employment_type, subspecialty):
    """Filters data based on selected criteria."""
    start_date, end_date = date_range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if employment_type and "ALL" not in employment_type:
        df_filtered = df_filtered[df_filtered["Employment Type"].isin(employment_type)]

    if subspecialty and "ALL" not in subspecialty:
        df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(subspecialty)]

    return df_filtered

def plot_bar_chart(df, x_col, y_col, title):
    """Generates a bar chart with Primary Subspecialty color coding."""
    if y_col in df.columns and not df.empty:
        df = df.sort_values(by=y_col, ascending=True)  # Sort in ascending order
        fig = px.bar(df, x=x_col, y=y_col, color="Primary Subspecialty",
                     title=title, color_discrete_map=SUBSPECIALTY_COLORS)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"'{y_col}' column is missing or no data available.")

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.info("📂 Please upload an RVU Master file.")

if uploaded_file and df is not None:
    st.success(f"✅ Loaded {len(df)} records with Employment Type & Subspecialty")

    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    employment_options = ["ALL"] + sorted(df["Employment Type"].dropna().unique().tolist())
    selected_employment = st.sidebar.multiselect("Select Employment Type", employment_options, default=["ALL"])

    subspecialty_options = ["ALL"] + sorted(df["Primary Subspecialty"].dropna().unique().tolist())
    selected_subspecialty = st.sidebar.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])

    df_filtered = filter_data(df, date_range, selected_employment, selected_subspecialty)
    st.success(f"✅ Showing {len(df_filtered)} records after filtering.")

    st.write("Filtered Data:", df_filtered.head())

    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider (Ascending)")
        plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider (Ascending)")
        plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider (Ascending)")

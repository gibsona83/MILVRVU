import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")
st.title("📊 MILV Daily Productivity")

# Sidebar for manual file upload
with st.sidebar:
    st.header("Upload RVU File")
    uploaded_file = st.file_uploader("Drag and drop RVU Master file here", type=["xlsx"])

@st.cache_data
def load_roster():
    """Downloads the MILV Roster from GitHub and loads it."""
    github_url = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/MILVRoster.csv"
    local_path = "/mnt/data/MILVRoster.csv"

    try:
        if not os.path.exists(local_path):
            response = requests.get(github_url)
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(response.content)  # Save locally
            else:
                st.warning("⚠️ Unable to download MILVRoster.csv. Using default values.")
                return None

        df = pd.read_csv(local_path)

        # Clean up Employment Type formatting
        df["Employment Type"] = df["Employment Type"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()
        df["Employment Type"].fillna("Unknown", inplace=True)  # Ensure no NaN

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

    if isinstance(time_value, str):  # Check for HH:MM:SS format
        parts = time_value.split(":")
        if len(parts) == 3:  # HH:MM:SS
            try:
                hours, minutes, seconds = map(int, parts)
                return hours * 60 + minutes  
            except ValueError:
                return 0  

    return 0  

@st.cache_data
def load_data(file):
    """Loads and processes the selected or uploaded RVU file."""
    try:
        rvu_df = pd.read_excel(file, sheet_name="powerscribe Data")

        # Rename columns for consistency
        rvu_df.rename(columns={
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }, inplace=True)

        # Convert 'Date' column to datetime
        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date

        # Convert Turnaround Time to minutes
        rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        # Load and merge MILV Roster
        roster_df = load_roster()
        if roster_df is not None:
            rvu_df = rvu_df.merge(roster_df, on="Provider", how="left")
        else:
            # If no roster file, add default values
            rvu_df["Employment Type"] = "Unknown"
            rvu_df["Primary Subspecialty"] = "Unknown"

        # Drop NaNs in essential columns
        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def plot_bar_chart(df, x_col, y_col, title, color_col=None):
    """Generates a bar chart if the required columns are present."""
    if y_col in df.columns and not df.empty:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"'{y_col}' column is missing or no data available.")

# Ensure there is an RVU file to load
if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.info("📂 Please upload an RVU Master file.")

if uploaded_file and df is not None:
    st.success(f"✅ Loaded {len(df)} records with Employment Type & Subspecialty")

    # Get latest date in data
    latest_date = df["Date"].max()

    # Apply filtering to show only the latest date
    df_filtered = df[df["Date"] == latest_date]
    st.success(f"✅ Showing data for latest date: {latest_date}")

    # Display data
    st.write("Filtered Data:", df_filtered.head())

    if df_filtered.empty:
        st.warning("No data available for the latest date.")
    else:
        # Visualizations
        plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider", "Primary Subspecialty")
        plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider", "Primary Subspecialty")
        plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider", "Primary Subspecialty")

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Correct RAW URLs for downloading files
GITHUB_IMAGE_URL = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/milv.png"
GITHUB_ROSTER_URL = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/MILVRoster.csv"

def fetch_csv_from_github(url):
    """Fetch CSV file directly from GitHub and handle encoding issues."""
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            st.success("✅ Successfully fetched MILVRoster.csv from GitHub")
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')), encoding='utf-8')
        else:
            st.error(f"❌ Failed to fetch MILVRoster.csv (HTTP {response.status_code})")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching MILVRoster.csv: {e}")
        return None

# Load `milv.png` directly from GitHub
try:
    response = requests.get(GITHUB_IMAGE_URL, timeout=10)
    if response.status_code == 200:
        st.image(io.BytesIO(response.content), width=250)
    else:
        st.warning("⚠️ Could not load logo image from GitHub. Using default styling.")
except Exception as e:
    st.warning(f"⚠️ Error loading logo image: {e}")

st.title("📊 MILV Daily Productivity")

# Sidebar for file upload
with st.sidebar:
    st.header("Upload RVU File")
    uploaded_file = st.file_uploader("Drag and drop RVU Master file here", type=["xlsx"])

@st.cache_data
def load_roster():
    """Loads MILV Roster directly from GitHub without local storage."""
    st.info("📥 Attempting to load MILVRoster.csv from GitHub...")
    df = fetch_csv_from_github(GITHUB_ROSTER_URL)
    
    if df is not None:
        try:
            # Ensure column names are clean
            df.columns = df.columns.str.strip()
            
            # Debugging: Show column names to confirm correct structure
            st.write("✅ Columns in MILVRoster.csv:", df.columns.tolist())

            # Ensure the required columns exist
            if "Employment Type" not in df.columns or "Primary Subspecialty" not in df.columns:
                st.error("❌ MILVRoster.csv is missing required columns. Please check the file format.")
                return None

            # Clean up Employment Type formatting
            df["Employment Type"] = df["Employment Type"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()
            df["Employment Type"].fillna("Unknown", inplace=True)

            # Assign "NON MILV" if Primary Subspecialty is missing
            df["Primary Subspecialty"].fillna("NON MILV", inplace=True)

            return df
        except Exception as e:
            st.error(f"❌ Error processing MILV Roster: {e}")
            return None
    return None

def convert_turnaround(time_value):
    """Converts turnaround time from HH:MM:SS or float to minutes."""
    if pd.isna(time_value):
        return 0

    if isinstance(time_value, float):
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
        if file is None:
            return None  # Prevent errors if no file is uploaded

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
            rvu_df["Primary Subspecialty"] = "NON MILV"

        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

if uploaded_file:
    df = load_data(uploaded_file)
else:
    df = None
    st.info("📂 Please upload an RVU Master file.")

if df is not None:
    st.success(f"✅ Loaded {len(df)} records with Employment Type & Subspecialty")

    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    employment_options = ["ALL"] + sorted(df["Employment Type"].dropna().unique().tolist())
    selected_employment = st.sidebar.multiselect("Select Employment Type", employment_options, default=["ALL"])

    subspecialty_options = ["ALL"] + sorted(df["Primary Subspecialty"].dropna().unique().tolist())
    selected_subspecialty = st.sidebar.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])

    def filter_data(df, date_range, employment_type, subspecialty):
        """Filters data based on selected criteria."""
        start_date, end_date = date_range
        df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        if employment_type and "ALL" not in employment_type:
            df_filtered = df_filtered[df_filtered["Employment Type"].isin(employment_type)]

        if subspecialty and "ALL" not in subspecialty:
            df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(subspecialty)]

        return df_filtered

    df_filtered = filter_data(df, date_range, selected_employment, selected_subspecialty)
    st.success(f"✅ Showing {len(df_filtered)} records after filtering.")

    st.write("Filtered Data:", df_filtered.head())

    def plot_bar_chart(df, x_col, y_col, title):
        """Generates a bar chart sorted in ascending order."""
        if y_col in df.columns and not df.empty:
            df = df.sort_values(by=y_col, ascending=True)
            fig = px.bar(df, x=x_col, y=y_col, color="Primary Subspecialty", title=title)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"'{y_col}' column is missing or no data available.")

    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider (Ascending)")
        plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider (Ascending)")
        plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider (Ascending)")

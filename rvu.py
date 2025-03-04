import streamlit as st
import pandas as pd
import plotly.express as px

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")
st.title("📊 MILV Daily Productivity")

# Sidebar for file upload
with st.sidebar:
    st.header("Upload RVU File")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["xlsx"])

@st.cache_data
def load_roster():
    """Loads the MILV Roster to get Employment Type and Primary Subspecialty."""
    roster_path = "/mnt/data/MILVRoster.csv"
    try:
        roster_df = pd.read_csv(roster_path)

        # Clean up employment type formatting and remove NaN values
        roster_df["Employment Type"] = roster_df["Employment Type"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()
        roster_df["Employment Type"].fillna("Unknown", inplace=True)  # Ensure no NaN

        return roster_df
    except Exception as e:
        st.error(f"Error loading MILV Roster: {e}")
        return None

def convert_turnaround(time_value):
    """Converts turnaround time from HH:MM:SS or float to minutes."""
    if pd.isna(time_value):  # Handle NaN values
        return 0

    if isinstance(time_value, float):  # Already a decimal format
        return round(time_value * 60)  # Convert to minutes

    if isinstance(time_value, str):  # Check for HH:MM:SS format
        parts = time_value.split(":")
        if len(parts) == 3:  # HH:MM:SS
            try:
                hours, minutes, seconds = map(int, parts)
                return hours * 60 + minutes  # Convert to total minutes
            except ValueError:
                return 0  # Return 0 if conversion fails

    return 0  # Default return value for unexpected formats

def load_data(file):
    """Loads and processes the RVU Daily Master data."""
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

        # Fill missing Employment Type with "Unknown"
        rvu_df["Employment Type"].fillna("Unknown", inplace=True)

        # Drop NaNs in essential columns
        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def filter_data(df, date_range, providers, employment_type, subspecialty):
    """Filters data based on selected criteria."""
    start_date, end_date = date_range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if providers and "ALL" not in providers:
        df_filtered = df_filtered[df_filtered["Provider"].isin(providers)]
    
    if employment_type and "ALL" not in employment_type:
        df_filtered = df_filtered[df_filtered["Employment Type"].isin(employment_type)]

    if subspecialty and "ALL" not in subspecialty:
        df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(subspecialty)]

    return df_filtered

def plot_bar_chart(df, x_col, y_col, title, color_col=None):
    """Generates a bar chart if the required columns are present."""
    if y_col in df.columns and not df.empty:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"'{y_col}' column is missing or no data available.")

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success(f"✅ Loaded {len(df)} records with Employment Type & Subspecialty")

        # Sidebar filters
        min_date, max_date = df['Date'].min(), df['Date'].max()
        
        # Date range selection
        date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        provider_options = ["ALL"] + sorted(df["Provider"].dropna().unique().tolist())
        selected_providers = st.sidebar.multiselect("Select Provider(s)", provider_options, default=["ALL"])

        employment_options = ["ALL"] + sorted(df["Employment Type"].unique().tolist())
        selected_employment = st.sidebar.multiselect("Select Employment Type", employment_options, default=["ALL"])

        subspecialty_options = ["ALL"] + sorted(df["Primary Subspecialty"].dropna().unique().tolist())
        selected_subspecialty = st.sidebar.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])

        # Apply filters
        df_filtered = filter_data(df, date_range, selected_providers, selected_employment, selected_subspecialty)
        st.success(f"✅ Records after filtering: {len(df_filtered)}")

        # Display data
        st.write("Filtered Data:", df_filtered.head())

        if df_filtered.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Visualizations
            plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider", "Primary Subspecialty")
            plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider", "Primary Subspecialty")
            plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider", "Primary Subspecialty")
else:
    st.info("Please upload an Excel file to proceed.")

import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - MILV Logo & File Upload
st.sidebar.image("milv.png", width=250)
st.sidebar.title("Upload Daily RVU File")
uploaded_file = st.sidebar.file_uploader("Upload RVU Excel File", type=["xlsx"])

# Define storage path
FILE_STORAGE_PATH = "latest_rvu.xlsx"

def load_data(file_path):
    """Load and preprocess data from Excel file."""
    try:
        xls = pd.ExcelFile(file_path)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Ensure required columns exist
        required_columns = {"date", "author", "points", "procedure"}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])

        # Extract Last Names to Reduce Clutter
        df["last_name"] = df["author"].str.split(",").str[0]

        # Convert numeric columns
        for col in ["points", "procedure"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert non-numeric values to NaN

        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

# Load existing data
if uploaded_file:
    try:
        with open(FILE_STORAGE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        df = load_data(FILE_STORAGE_PATH)
        if df is not None:
            st.success("✅ File uploaded successfully!")
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
elif os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
else:
    df = None

# Ensure data is available
if df is not None:
    # Sort by date and get min/max dates
    df = df.sort_values("date")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    # Title
    st.title("MILV Daily Productivity")

    # Create Tabs
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 2: Date Range Analysis**
    with tab2:
        st.subheader("📊 Select Date Range for Analysis")

        # Date Input - Forces two selections
        date_selection = st.date_input(
            "Select Date Range",
            value=(max_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_selector"
        )

        # **Force users to select a valid date range**
        if isinstance(date_selection, tuple) and len(date_selection) == 2:
            start_date, end_date = map(pd.to_datetime, date_selection)
        elif isinstance(date_selection, pd.Timestamp):
            start_date = end_date = pd.to_datetime(date_selection)  # Ensures both start and end exist
        else:
            st.error("⚠️ Please select a valid date range before proceeding.")
            st.stop()  # Prevents execution if no valid date range is selected

        # **Validate date order**
        if start_date > end_date:
            st.error("❌ End date must be after or the same as the start date.")
            st.stop()

        # Provider selection
        providers = df["author"].unique().tolist()
        selected_providers = st.multiselect(
            "Select Providers",
            options=["ALL"] + providers,
            default=["ALL"],
            key="provider_selector"
        )

        if "ALL" in selected_providers:
            selected_providers = providers

        # Filter data
        mask = (
            (df["date"] >= start_date) & 
            (df["date"] <= end_date) & 
            (df["author"].isin(selected_providers))
        )
        df_filtered = df.loc[mask]

        st.subheader(f"📊 Data for {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")

        if df_filtered.empty:
            st.warning("⚠️ No data available for the selected filters.")
        else:
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Points", df_filtered["points"].sum())
            with col2:
                st.metric("Total Procedures", df_filtered["procedure"].sum())

            # Data Table
            st.subheader("🔍 Detailed Data")
            st.dataframe(df_filtered, use_container_width=True, height=400)

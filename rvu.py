import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - File Upload
st.sidebar.title("Upload File")
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
        required_columns = {"date", "author", "points", "procedure", "turnaround"}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])

        # Convert numeric columns
        for col in ["points", "procedure", "turnaround"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Invalid values become NaN
        
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

    # Create Tabs
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 1: Latest Date Data**
    with tab1:
        st.subheader(f"📅 Data for {max_date}")

        df_latest = df[df["date"] == pd.Timestamp(max_date)]

        if df_latest.empty:
            st.warning("⚠️ No data available for the latest date.")
        else:
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", df_latest["points"].sum())
            with col2:
                st.metric("Total Procedures", df_latest["procedure"].sum())
            with col3:
                avg_turnaround = df_latest["turnaround"].mean()
                st.metric("Avg Turnaround", f"{avg_turnaround:.1f} min" if pd.notna(avg_turnaround) else "N/A")

            # Data Table
            st.subheader("🔍 Detailed Data")
            st.dataframe(df_latest, use_container_width=True, height=400)

            # **Visualizations**
            st.subheader("📊 Data Visualizations")

            # Points per half-day
            fig, ax = plt.subplots(figsize=(8, 4))
            df_latest.groupby(df_latest["date"].dt.strftime('%p'))["points"].sum().plot(kind="bar", ax=ax)
            ax.set_title("Points per Half-Day")
            ax.set_ylabel("Points")
            ax.grid(True)
            st.pyplot(fig)

            # Procedures per half-day
            fig, ax = plt.subplots(figsize=(8, 4))
            df_latest.groupby(df_latest["date"].dt.strftime('%p'))["procedure"].sum().plot(kind="bar", ax=ax)
            ax.set_title("Procedures per Half-Day")
            ax.set_ylabel("Procedures")
            ax.grid(True)
            st.pyplot(fig)

            # Daily Trends
            fig, ax = plt.subplots(figsize=(10, 4))
            df.groupby("date")["points"].sum().plot(kind="line", ax=ax, marker="o")
            ax.set_title("Daily Points Overview")
            ax.grid(True)
            st.pyplot(fig)

    # **TAB 2: Date Range Analysis**
    with tab2:
        st.subheader("📊 Select Date Range for Analysis")

        # Date Input
        date_selection = st.date_input(
            "Select Date Range",
            value=(max_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_selector"
        )

        # Handle date selection
        if isinstance(date_selection, tuple):
            start_date, end_date = map(pd.to_datetime, date_selection)
        else:
            start_date = end_date = pd.to_datetime(date_selection)

        # Validate date order
        if start_date > end_date:
            st.error("❌ End date must be after start date")
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

        if df_filtered.empty:
            st.warning("⚠️ No data available for the selected filters.")
        else:
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", df_filtered["points"].sum())
            with col2:
                st.metric("Total Procedures", df_filtered["procedure"].sum())
            with col3:
                avg_turnaround = df_filtered["turnaround"].mean()
                st.metric("Avg Turnaround", f"{avg_turnaround:.1f} min" if pd.notna(avg_turnaround) else "N/A")

            # Data Table
            st.subheader("🔍 Detailed Data")
            st.dataframe(df_filtered, use_container_width=True, height=400)

            # **Visualizations**
            st.subheader("📊 Data Visualizations")

            # Points per half-day
            fig, ax = plt.subplots(figsize=(8, 4))
            df_filtered.groupby(df_filtered["date"].dt.strftime('%p'))["points"].sum().plot(kind="bar", ax=ax)
            ax.set_title("Points per Half-Day")
            ax.set_ylabel("Points")
            ax.grid(True)
            st.pyplot(fig)

            # Procedures per half-day
            fig, ax = plt.subplots(figsize=(8, 4))
            df_filtered.groupby(df_filtered["date"].dt.strftime('%p'))["procedure"].sum().plot(kind="bar", ax=ax)
            ax.set_title("Procedures per Half-Day")
            ax.set_ylabel("Procedures")
            ax.grid(True)
            st.pyplot(fig)

            # Daily Trends
            fig, ax = plt.subplots(figsize=(10, 4))
            df_filtered.groupby("date")["points"].sum().plot(kind="line", ax=ax, marker="o")
            ax.set_title("Daily Points Overview")
            ax.grid(True)
            st.pyplot(fig)

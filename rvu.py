import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - MILV Logo
st.sidebar.image("milv.png", width=250)

st.title("📊 MILV Daily Productivity")

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

# Load existing data or initialize
if os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
    latest_file_status = "✅ Using last uploaded file."
else:
    df = None
    latest_file_status = "⚠️ No previous file found."

# File upload handling
uploaded_file = st.file_uploader("Upload RVU Excel File (Optional)", type=["xlsx"])
if uploaded_file:
    try:
        with open(FILE_STORAGE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        df = load_data(FILE_STORAGE_PATH)
        if df is not None:
            st.success("✅ File uploaded successfully!")
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")

# Ensure data is available
if df is not None:
    st.sidebar.info(latest_file_status)
    
    if "date" not in df.columns:
        st.error("❌ Missing 'date' column in data")
        st.stop()

    # Sort by date and get min/max dates
    df = df.sort_values("date")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    # Tab layout: Latest Day Data | Date Range Analysis
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 1: Automatically Load Latest Date**
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
                avg_turnaround_display = f"{avg_turnaround:.1f} min" if pd.notna(avg_turnaround) else "N/A"
                st.metric("Avg Turnaround", avg_turnaround_display)

            # Data Table
            st.subheader("🔍 Detailed Data")
            st.dataframe(
                df_latest.sort_values("turnaround", ascending=True),
                use_container_width=True,
                height=400
            )

            # Visualization
            fig, ax = plt.subplots(figsize=(10, 4))
            daily_points = df_latest.groupby("date")["points"].sum()
            daily_points.plot(kind="bar", ax=ax)
            ax.set_title("Daily Points Overview")
            ax.grid(True)
            st.pyplot(fig)

    # **TAB 2: Custom Date Range Selection**
    with tab2:
        st.subheader("📊 Select Date Range for Analysis")

        # Date input for filtering
        date_selection = st.sidebar.date_input(
            "Select Date Range",
            value=(max_date, max_date) if min_date != max_date else max_date,
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
            st.sidebar.error("❌ End date must be after start date")
            st.stop()

        # Provider selection
        providers = df["author"].unique().tolist()
        selected_providers = st.sidebar.multiselect(
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
                avg_turnaround_display = f"{avg_turnaround:.1f} min" if pd.notna(avg_turnaround) else "N/A"
                st.metric("Avg Turnaround", avg_turnaround_display)

            # Data Table
            st.subheader("🔍 Detailed Data")
            st.dataframe(
                df_filtered.sort_values("turnaround", ascending=True),
                use_container_width=True,
                height=400
            )

            # Download Button
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "💾 Download Filtered Data",
                data=csv,
                file_name=f"MILV_data_{start_date.date()}_to_{end_date.date()}.csv",
                mime="text/csv"
            )

            # Visualization
            st.subheader("📅 Daily Trends")
            fig, ax = plt.subplots(figsize=(10, 4))
            daily_points = df_filtered.groupby("date")["points"].sum()
            daily_points.plot(kind="line", ax=ax, marker="o")
            ax.set_title("Daily Points Overview")
            ax.grid(True)
            st.pyplot(fig)

else:
    st.warning("⚠️ Please upload an Excel file to begin analysis.")

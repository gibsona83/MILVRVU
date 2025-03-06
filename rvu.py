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
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert non-numeric values to NaN
        
        # Fill missing turnaround values with 0 (or another placeholder)
        df["turnaround"] = df["turnaround"].fillna(0)

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

# Function to improve visualization
def plot_bar_chart(df, x_col, y_col, title, ylabel, horizontal=False):
    """Generates a sorted bar chart with improved readability."""
    
    # Ensure numeric conversion and drop NaNs
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df_sorted = df.dropna(subset=[y_col]).sort_values(by=y_col, ascending=True)

    # Handle cases where no valid data exists
    if df_sorted.empty:
        st.warning(f"⚠️ No valid data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))  # Increased size for better readability
    
    if horizontal:
        ax.barh(df_sorted[x_col], df_sorted[y_col], color='steelblue', edgecolor='black')
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_ylabel("Providers", fontsize=12)
    else:
        ax.bar(df_sorted[x_col], df_sorted[y_col], color='steelblue', edgecolor='black')
        ax.set_ylabel(ylabel, fontsize=12)
    
    # Aesthetics
    ax.set_title(title, fontsize=14, fontweight="bold")

    if len(df_sorted[x_col]) > 10:
        if horizontal:
            ax.set_yticklabels(df_sorted[x_col], fontsize=10)
        else:
            ax.set_xticklabels(df_sorted[x_col], rotation=45, ha="right", fontsize=10)  # Rotate labels for clarity
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Show plot
    st.pyplot(fig)

# Ensure data is available
if df is not None:
    # Sort by date and get min/max dates
    df = df.sort_values("date")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    formatted_max_date = pd.to_datetime(max_date).strftime("%B %d, %Y")  # Format: "March 5, 2025"

    # Create Tabs
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 1: Latest Date Data**
    with tab1:
        st.subheader(f"📅 Data for {formatted_max_date}")

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

            plot_bar_chart(df_latest, "author", "turnaround", "Turnaround Times (Ascending)", "Turnaround Time (minutes)", horizontal=True)
            plot_bar_chart(df_latest, "author", "points", "Points per Provider (Ascending)", "Points", horizontal=False)
            plot_bar_chart(df_latest, "author", "procedure", "Procedures per Provider (Ascending)", "Procedures", horizontal=False)

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

        formatted_start_date = start_date.strftime("%B %d, %Y")
        formatted_end_date = end_date.strftime("%B %d, %Y")

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

        st.subheader(f"📊 Data for {formatted_start_date} to {formatted_end_date}")

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

            # Visualizations
            plot_bar_chart(df_filtered, "author", "turnaround", "Turnaround Times (Ascending

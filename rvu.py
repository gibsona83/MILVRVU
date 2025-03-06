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

# Function for two-part visualizations
def plot_split_chart(df, x_col, y_col, title_top, title_bottom, ylabel):
    """Generates two sorted bar charts for better readability."""

    # Ensure numeric conversion and drop NaNs
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df_sorted = df.dropna(subset=[y_col]).sort_values(by=y_col, ascending=False)

    # Handle cases where no valid data exists
    if df_sorted.empty:
        st.warning(f"⚠️ No valid data available for {title_top} and {title_bottom}.")
        return

    # Get top and bottom performers
    top_df = df_sorted.head(10)   # Top 10
    bottom_df = df_sorted.tail(10) # Bottom 10

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))  # Two side-by-side plots

    # Top performers
    axes[0].barh(top_df[x_col], top_df[y_col], color='darkblue', edgecolor='black')
    axes[0].set_title(title_top, fontsize=14, fontweight="bold")
    axes[0].invert_yaxis()
    axes[0].set_xlabel(ylabel)

    # Bottom performers
    axes[1].barh(bottom_df[x_col], bottom_df[y_col], color='darkred', edgecolor='black')
    axes[1].set_title(title_bottom, fontsize=14, fontweight="bold")
    axes[1].set_xlabel(ylabel)

    plt.tight_layout()
    st.pyplot(fig)

# Ensure data is available
if df is not None:
    # Sort by date and get min/max dates
    df = df.sort_values("date")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    formatted_max_date = pd.to_datetime(max_date).strftime("%B %d, %Y")  # Format: "March 5, 2025"

    # Title
    st.title("MILV Daily Productivity")
    st.subheader(f"📅 Data for {formatted_max_date}")

    # Create Tabs
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 1: Latest Date Data**
    with tab1:
        df_latest = df[df["date"] == pd.Timestamp(max_date)]

        if df_latest.empty:
            st.warning("⚠️ No data available for the latest date.")
        else:
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Points", df_latest["points"].sum())
            with col2:
                st.metric("Total Procedures", df_latest["procedure"].sum())

            # Searchable Data Table
            st.subheader("🔍 Searchable Detailed Data")
            search_query = st.text_input("Search for a provider:")
            if search_query:
                df_filtered = df_latest[df_latest["author"].str.contains(search_query, case=False, na=False)]
            else:
                df_filtered = df_latest
            st.dataframe(df_filtered, use_container_width=True, height=400)

            # **Visualizations**
            st.subheader("📊 Data Visualizations")

            plot_split_chart(df_latest, "last_name", "points", 
                             "Top 10 Providers by Points", "Bottom 10 Providers by Points", "Points")

            plot_split_chart(df_latest, "last_name", "procedure", 
                             "Top 10 Providers by Procedures", "Bottom 10 Providers by Procedures", "Procedures")

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
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Points", df_filtered["points"].sum())
            with col2:
                st.metric("Total Procedures", df_filtered["procedure"].sum())

            # **Visualizations**
            plot_split_chart(df_filtered, "last_name", "points", 
                             "Top 10 Providers by Points", "Bottom 10 Providers by Points", "Points")

            plot_split_chart(df_filtered, "last_name", "procedure", 
                             "Top 10 Providers by Procedures", "Bottom 10 Providers by Procedures", "Procedures")

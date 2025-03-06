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
        required_columns = {"date", "author", "points", "procedure", "shift"}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])

        # Convert numeric columns
        for col in ["points", "procedure", "shift"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)  # Convert non-numeric values to NaN, fill NaN with 0

        # Compute Points/Half-Day (Avoiding division errors)
        df = df[df["shift"] > 0]  # Exclude providers where shift = 0
        df["points_half_day"] = df["points"] / df["shift"]

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

# Function to plot top/bottom charts
def plot_split_chart(df, x_col, y_col, title_top, title_bottom, ylabel):
    """Generates two sorted bar charts for better readability, ensuring valid data is always plotted."""

    df_sorted = df.dropna(subset=[y_col]).sort_values(by=y_col, ascending=False)

    if df_sorted.empty:
        st.warning(f"⚠️ Not enough valid data for {title_top} and {title_bottom}.")
        return

    # Get top and bottom performers (handle cases with fewer than 10)
    top_df = df_sorted.head(10) if len(df_sorted) >= 10 else df_sorted
    bottom_df = df_sorted.tail(10) if len(df_sorted) >= 10 else df_sorted

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

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

# Function to plot average trends over time
def plot_average_trends(df, y_col, title, ylabel):
    """Generates a trend line chart for average values over time."""
    df_avg = df.groupby("date")[y_col].mean()

    if df_avg.empty:
        st.warning(f"⚠️ Not enough valid data for {title}.")
        return

    fig, ax = plt.subplots(figsize=(12, 5))
    df_avg.plot(kind="line", marker="o", ax=ax, color="darkgreen")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    st.pyplot(fig)

# Ensure data is available
if df is not None:
    df = df.sort_values("date")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    st.title("MILV Daily Productivity")

    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # **TAB 1: Latest Day**
    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%B %d, %Y')}")
        
        df_latest = df[df["date"] == pd.Timestamp(max_date)]

        if df_latest.empty:
            st.warning("⚠️ No data available for the latest date.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", df_latest["points"].sum())
            with col2:
                st.metric("Total Procedures", df_latest["procedure"].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_latest['points_half_day'].mean():.2f}")

            st.subheader("📊 Data Visualizations")

            plot_split_chart(df_latest, "author", "points_half_day", "Top 10 Providers by Points/Half-Day", 
                             "Bottom 10 Providers by Points/Half-Day", "Points per Half-Day")

    # **TAB 2: Date Range Analysis**
    with tab2:
        st.subheader("📊 Select Date Range for Analysis")

        date_selection = st.date_input(
            "Select Date Range",
            value=(max_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_selector"
        )

        if isinstance(date_selection, tuple) and len(date_selection) == 2:
            start_date, end_date = map(pd.to_datetime, date_selection)
        elif isinstance(date_selection, pd.Timestamp):
            start_date = end_date = pd.to_datetime(date_selection)
        else:
            st.error("⚠️ Please select a valid date range before proceeding.")
            st.stop()

        if start_date > end_date:
            st.error("❌ End date must be after or the same as the start date.")
            st.stop()

        df_filtered = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        st.subheader(f"📊 Data for {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")

        if df_filtered.empty:
            st.warning("⚠️ No data available for the selected filters.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", df_filtered["points"].sum())
            with col2:
                st.metric("Total Procedures", df_filtered["procedure"].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_filtered['points_half_day'].mean():.2f}")

            st.subheader("📊 Aggregate Trends Over Time")

            plot_average_trends(df_filtered, "points_half_day", "Average Points/Half-Day Over Time", "Avg Points/Half-Day")
            plot_average_trends(df_filtered, "procedure", "Average Procedures Over Time", "Avg Procedures")

            st.subheader("📊 Data Visualizations")

            plot_split_chart(df_filtered, "author", "points_half_day", "Top 10 Providers by Points/Half-Day", 
                             "Bottom 10 Providers by Points/Half-Day", "Points per Half-Day")

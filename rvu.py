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

        # Extract Last Names to Reduce Clutter
        df["last_name"] = df["author"].str.split(",").str[0]

        # Convert numeric columns
        for col in ["points", "procedure", "shift"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert non-numeric values to NaN

        # Compute Points/Half-Day & Procedures/Half-Day
        df["points_half_day"] = df["points"] / df["shift"]
        df["procedures_half_day"] = df["procedure"] / df["shift"]

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

# Function to plot bar charts
def plot_bar_chart(df, x_col, y_col, title, ylabel):
    """Generates a horizontal bar chart for better readability."""

    df_sorted = df.sort_values(by=y_col, ascending=False)

    if df_sorted.empty:
        st.warning(f"⚠️ No valid data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(df_sorted[x_col], df_sorted[y_col], color='steelblue', edgecolor='black')

    ax.set_xlabel(ylabel, fontsize=12)
    ax.set_ylabel("Providers", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()
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
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Points", df_latest["points"].sum())
            with col2:
                st.metric("Total Procedures", df_latest["procedure"].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_latest['points_half_day'].mean():.2f}")
            with col4:
                st.metric("Avg Procedures/Half-Day", f"{df_latest['procedures_half_day'].mean():.2f}")

            st.subheader("🔍 Detailed Data")
            st.dataframe(df_latest, use_container_width=True, height=400)

            st.subheader("📊 Data Visualizations")

            plot_bar_chart(df_latest, "last_name", "points_half_day", "Points per Half-Day (Descending)", "Points per Half-Day")
            plot_bar_chart(df_latest, "last_name", "procedures_half_day", "Procedures per Half-Day (Descending)", "Procedures per Half-Day")

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

        providers = df["author"].unique().tolist()
        selected_providers = st.multiselect(
            "Select Providers",
            options=["ALL"] + providers,
            default=["ALL"],
            key="provider_selector"
        )

        if "ALL" in selected_providers:
            selected_providers = providers

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
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Points", df_filtered["points"].sum())
            with col2:
                st.metric("Total Procedures", df_filtered["procedure"].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_filtered['points_half_day'].mean():.2f}")
            with col4:
                st.metric("Avg Procedures/Half-Day", f"{df_filtered['procedures_half_day'].mean():.2f}")

            st.subheader("📊 Data Visualizations")

            plot_bar_chart(df_filtered, "last_name", "points_half_day", "Points per Half-Day (Descending)", "Points per Half-Day")
            plot_bar_chart(df_filtered, "last_name", "procedures_half_day", "Procedures per Half-Day (Descending)", "Procedures per Half-Day")

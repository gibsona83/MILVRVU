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
        
        # Clean column names (preserve original capitalization)
        df.columns = df.columns.str.strip()
        
        # Ensure required columns exist
        required_columns = {"Date", "Author", "Procedure", "Points", "Shift", 
                           "Points/half day", "Procedure/half"}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert date column
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["Date"])

        # Convert numeric columns (using original column names)
        numeric_cols = ["Points", "Procedure", "Shift", "Points/half day", "Procedure/half"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Clean author names (preserve original capitalization)
        df["Author"] = df["Author"].str.strip()

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
    """Generates two sorted bar charts with original column names."""
    df_sorted = df.sort_values(by=y_col, ascending=False)

    if df_sorted.empty:
        st.warning(f"⚠️ Not enough data for {title_top} and {title_bottom}.")
        return

    top_df = df_sorted.head(10)
    bottom_df = df_sorted.tail(10)

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

# Main display
if df is not None:
    df = df.sort_values("Date")
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()

    st.title("MILV Daily Productivity")

    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # TAB 1: Latest Day
    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%B %d, %Y')}")
        df_latest = df[df["Date"] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Points", df_latest["Points"].sum())
            with col2:
                st.metric("Total Procedures", df_latest["Procedure"].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_latest['Points/half day'].mean():.2f}")
            with col4:
                st.metric("Avg Procedures/Half-Day", f"{df_latest['Procedure/half'].mean():.2f}")

            # Searchable Data Table
            st.subheader("🔍 Searchable Detailed Data")
            search_query = st.text_input("Search for a provider (Tab 1):")
            filtered = df_latest[df_latest["Author"].str.contains(search_query, case=False, na=False)] if search_query else df_latest
            st.dataframe(filtered, use_container_width=True, height=400)

            # Visualizations
            st.subheader("📊 Performance Metrics")
            plot_split_chart(filtered, "Author", "Points/half day", 
                            "Top 10 by Points/Half-Day", "Bottom 10 by Points/Half-Day", 
                            "Points per Half-Day")
            
    # TAB 2: Date Range Analysis
    with tab2:
        st.subheader("📊 Select Date Range")
        date_selection = st.date_input(
            "Select Range",
            value=(max_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(date_selection) == 2:
            start_date, end_date = date_selection
            df_range = df[(df["Date"] >= pd.Timestamp(start_date)) & 
                         (df["Date"] <= pd.Timestamp(end_date))]
            
            if not df_range.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Points", df_range["Points"].sum())
                with col2:
                    st.metric("Total Procedures", df_range["Procedure"].sum())
                with col3:
                    st.metric("Avg Points/Half-Day", f"{df_range['Points/half day'].mean():.2f}")
                with col4:
                    st.metric("Avg Procedures/Half-Day", f"{df_range['Procedure/half'].mean():.2f}")

                st.subheader("🔍 Searchable Data")
                search_query = st.text_input("Search for a provider (Tab 2):")
                filtered_range = df_range[df_range["Author"].str.contains(search_query, case=False, na=False)] if search_query else df_range
                st.dataframe(filtered_range, use_container_width=True, height=400)

                st.subheader("📊 Performance Over Time")
                plot_split_chart(filtered_range, "Author", "Points/half day", 
                                "Top 10 by Points/Half-Day", "Bottom 10 by Points/Half-Day", 
                                "Points per Half-Day")
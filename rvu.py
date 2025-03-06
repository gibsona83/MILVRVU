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
        
        # Clean column names (case-insensitive)
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()
        
        # Ensure required columns exist (case-insensitive check)
        required_columns = {"date", "author", "procedure", "points", "shift", 
                           "points/half day", "procedure/half"}
        missing_columns = [col for col in required_columns 
                          if col not in lower_columns.values]
        
        if missing_columns:
            display_names = [col.title() for col in missing_columns]
            st.error(f"❌ Missing required columns: {', '.join(display_names)}")
            return None
        
        # Map actual column names to lowercase for processing
        col_mapping = {col.lower(): col for col in df.columns}
        
        # Convert date column
        date_col = col_mapping["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df = df.dropna(subset=[date_col])

        # Convert numeric columns using actual column names
        numeric_map = {
            "points": col_mapping["points"],
            "procedure": col_mapping["procedure"],
            "shift": col_mapping["shift"],
            "points/half day": col_mapping["points/half day"],
            "procedure/half": col_mapping["procedure/half"]
        }
        
        for key, col in numeric_map.items():
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Clean author names
        author_col = col_mapping["author"]
        df[author_col] = df[author_col].astype(str).str.strip()

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

# Rest of the code remains the same but uses original column names for display
# ... [keep the rest of the original code but update column references using col_mapping]

def plot_split_chart(df, x_col, y_col, title_top, title_bottom, ylabel):
    """Generates two sorted bar charts using original column names."""
    # Get actual column names from the DataFrame
    x_col_actual = [col for col in df.columns if col.lower() == x_col.lower()][0]
    y_col_actual = [col for col in df.columns if col.lower() == y_col.lower()][0]
    
    df_sorted = df.sort_values(by=y_col_actual, ascending=False)

    if df_sorted.empty:
        st.warning(f"⚠️ Not enough data for {title_top} and {title_bottom}.")
        return

    top_df = df_sorted.head(10)
    bottom_df = df_sorted.tail(10)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Top performers
    axes[0].barh(top_df[x_col_actual], top_df[y_col_actual], color='darkblue', edgecolor='black')
    axes[0].set_title(title_top, fontsize=14, fontweight="bold")
    axes[0].invert_yaxis()
    axes[0].set_xlabel(ylabel)

    # Bottom performers
    axes[1].barh(bottom_df[x_col_actual], bottom_df[y_col_actual], color='darkred', edgecolor='black')
    axes[1].set_title(title_bottom, fontsize=14, fontweight="bold")
    axes[1].set_xlabel(ylabel)

    plt.tight_layout()
    st.pyplot(fig)

# Main display logic with original column names
if df is not None:
    # Get display column names
    display_cols = {
        "date": [col for col in df.columns if col.lower() == "date"][0],
        "author": [col for col in df.columns if col.lower() == "author"][0],
        "points": [col for col in df.columns if col.lower() == "points"][0],
        "procedure": [col for col in df.columns if col.lower() == "procedure"][0],
        "shift": [col for col in df.columns if col.lower() == "shift"][0],
        "points/half day": [col for col in df.columns if col.lower() == "points/half day"][0],
        "procedure/half": [col for col in df.columns if col.lower() == "procedure/half"][0]
    }

    df = df.sort_values(display_cols["date"])
    min_date = df[display_cols["date"]].min().date()
    max_date = df[display_cols["date"]].max().date()

    st.title("MILV Daily Productivity")

    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    # TAB 1: Latest Day
    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%B %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Points", df_latest[display_cols["points"]].sum())
            with col2:
                st.metric("Total Procedures", df_latest[display_cols["procedure"]].sum())
            with col3:
                st.metric("Avg Points/Half-Day", f"{df_latest[display_cols['points/half day']].mean():.2f}")
            with col4:
                st.metric("Avg Procedures/Half-Day", f"{df_latest[display_cols['procedure/half']].mean():.2f}")

            # Searchable Data Table
            st.subheader("🔍 Searchable Detailed Data")
            search_query = st.text_input("Search for a provider (Tab 1):")
            filtered = df_latest[df_latest[display_cols["author"]].str.contains(search_query, case=False, na=False)] if search_query else df_latest
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
            df_range = df[(df[display_cols["date"]] >= pd.Timestamp(start_date)) & 
                         (df[display_cols["date"]] <= pd.Timestamp(end_date))]
            
            if not df_range.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Points", df_range[display_cols["points"]].sum())
                with col2:
                    st.metric("Total Procedures", df_range[display_cols["procedure"]].sum())
                with col3:
                    st.metric("Avg Points/Half-Day", f"{df_range[display_cols['points/half day']].mean():.2f}")
                with col4:
                    st.metric("Avg Procedures/Half-Day", f"{df_range[display_cols['procedure/half']].mean():.2f}")

                st.subheader("🔍 Searchable Data")
                search_query = st.text_input("Search for a provider (Tab 2):")
                filtered_range = df_range[df_range[display_cols["author"]].str.contains(search_query, case=False, na=False)] if search_query else df_range
                st.dataframe(filtered_range, use_container_width=True, height=400)

                st.subheader("📊 Performance Over Time")
                plot_split_chart(filtered_range, "Author", "Points/half day", 
                                "Top 10 by Points/Half-Day", "Bottom 10 by Points/Half-Day", 
                                "Points per Half-Day")
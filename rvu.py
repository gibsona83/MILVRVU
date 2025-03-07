import streamlit as st
import pandas as pd
import os
import plotly.express as px
import numpy as np

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# ---- Constants ----
FILE_STORAGE_PATH = "latest_rvu.xlsx"
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "turnaround", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = "Viridis"

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Load and preprocess data from an Excel file."""
    try:
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Clean and validate column names
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()
        
        # Check for duplicate columns after cleaning
        if len(df.columns) != len(set(lower_columns)):
            duplicates = df.columns[df.columns.duplicated()].tolist()
            st.error(f"❌ Duplicate columns detected after cleaning: {', '.join(duplicates)}")
            return None

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in lower_columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Create column mapping
        col_map = {col.lower(): col for col in df.columns}

        # Process date column
        date_col = col_map["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df.dropna(subset=[date_col], inplace=True)

        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS 
                       if col not in ["date", "author", "turnaround"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

        # Process turnaround time
        turnaround_col = col_map["turnaround"]
        df[turnaround_col] = pd.to_timedelta(
            df[turnaround_col].astype(str), 
            errors="coerce"
        ).dt.total_seconds() / 60  # Convert to minutes
        df[turnaround_col] = df[turnaround_col].fillna(0)  # Handle missing values

        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

# ---- Main Application ----
def main():
    # Sidebar setup
    st.sidebar.image("milv.png", width=200)
    uploaded_file = st.sidebar.file_uploader("📤 Upload RVU File", type=["xlsx"])

    # File handling
    if uploaded_file:
        try:
            with open(FILE_STORAGE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state["last_uploaded"] = uploaded_file.name
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

    # Load data
    if os.path.exists(FILE_STORAGE_PATH):
        with st.spinner("📊 Processing data..."):
            df = load_data(FILE_STORAGE_PATH)
    else:
        st.sidebar.info("📅 Latest Date: No data uploaded yet.")
        return st.info("ℹ️ Please upload a file to begin analysis")

    if df is None:
        st.sidebar.info("📅 Latest Date: No data available.")
        return

    # Column mapping and date info
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    date_col = display_cols["date"]
    author_col = display_cols["author"]
    points_half_col = display_cols["points/half day"]
    procedure_half_col = display_cols["procedure/half"]
    turnaround_col = display_cols["turnaround"]

    latest_date = df[date_col].max().date()
    st.sidebar.success(f"📅 Latest Date: {latest_date.strftime('%b %d, %Y')}")
    st.sidebar.info(f"📂 Last Uploaded File: {st.session_state.get('last_uploaded', 'No file uploaded')}")

    # Main interface
    st.title("📊 MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])

    # ---- Daily View ----
    with tab1:
        st.subheader(f"📅 Data for {latest_date.strftime('%b %d, %Y')}")
        df_latest = df[df[date_col] == pd.Timestamp(latest_date)]

        if not df_latest.empty:
            selected_providers = st.multiselect(
                "🔍 Select providers:",
                options=df_latest[author_col].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}",
            )

            filtered_latest = df_latest
            if selected_providers:
                filtered_latest = df_latest[df_latest[author_col].isin(selected_providers)]

            st.subheader("📋 Detailed Data")
            st.dataframe(filtered_latest, use_container_width=True)
        else:
            st.warning("⚠️ No data available for the latest date")

    # ---- Trend Analysis ----
    with tab2:
        st.subheader("📈 Date Range Analysis")
        min_date, max_date = df[date_col].min().date(), df[date_col].max().date()

        dates = st.date_input(
            "🗓️ Select Date Range (Start - End)",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date,
        )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            return

        df_range = df[df[date_col].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]

        if df_range.empty:
            st.warning("⚠️ No data available for the selected range")
            return

        # Performance trends
        st.subheader("📊 Average Daily Performance Trends")
        trend_data = df_range.groupby(date_col).mean(numeric_only=True).reset_index()
        fig = px.line(
            trend_data,
            x=date_col,
            y=[points_half_col, procedure_half_col],
            title="📈 Average Points & Procedures Per Half-Day",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Provider analysis
        st.subheader("📊 Provider-Level Performance (Averages)")
        provider_summary = df_range.groupby(author_col).agg({
            points_half_col: "mean",
            procedure_half_col: "mean",
            turnaround_col: "mean",
        }).reset_index()

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.bar(
                    provider_summary.sort_values(points_half_col, ascending=False),
                    x=points_half_col,
                    y=author_col,
                    orientation="h",
                    text=np.round(provider_summary[points_half_col], 1),
                    color=points_half_col,
                    color_continuous_scale=COLOR_SCALE,
                    title="🏆 Avg Points per Half-Day",
                ),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                px.bar(
                    provider_summary.sort_values(turnaround_col, ascending=False),
                    x=turnaround_col,
                    y=author_col,
                    orientation="h",
                    text=np.round(provider_summary[turnaround_col], 1),
                    color=turnaround_col,
                    color_continuous_scale=COLOR_SCALE,
                    title="⏳ Avg Turnaround Time (mins)",
                ),
                use_container_width=True,
            )

        st.subheader("📋 Detailed Data")
        st.dataframe(df_range, use_container_width=True)

if __name__ == "__main__":
    main()
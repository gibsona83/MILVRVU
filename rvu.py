import streamlit as st
import pandas as pd
import os
import plotly.express as px

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
        # ✅ Validate File Before Loading
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            st.error(f"🚨 Error: Invalid file format or corrupt file. Please upload a valid XLSX file.\nDetails: {e}")
            return None
        
        df = xls.parse(xls.sheet_names[0])

        # Clean column names (case-insensitive)
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in lower_columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Map actual column names
        col_map = {col.lower(): col for col in df.columns}

        # Process date column
        date_col = col_map["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df.dropna(subset=[date_col], inplace=True)

        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author", "turnaround"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

        # ✅ Fix Turnaround Time Conversion (Handles Empty or Malformed Values)
        turnaround_col = col_map["turnaround"]
        df[turnaround_col] = df[turnaround_col].astype(str)  # Convert to string first
        df[turnaround_col] = pd.to_timedelta(df[turnaround_col], errors="coerce").dt.total_seconds() / 60  # Convert to minutes

        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

# ---- Main Application ----
def main():
    # Sidebar (including latest uploaded date)
    st.sidebar.image("milv.png", width=200)
    
    # File uploader
    uploaded_file = st.sidebar.file_uploader("📤 Upload RVU File", type=["xlsx"])

    # Handle file storage
    if uploaded_file:
        try:
            with open(FILE_STORAGE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())  # Save file locally
            st.session_state["last_uploaded"] = uploaded_file.name  # Store filename in session state
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

    # Load the latest available file if it exists
    if os.path.exists(FILE_STORAGE_PATH):
        with st.spinner("📊 Processing data..."):
            df = load_data(FILE_STORAGE_PATH)
    else:
        st.sidebar.info("📅 Latest Date: No data uploaded yet.")
        return st.info("ℹ️ Please upload a file to begin analysis")

    if df is None:
        st.sidebar.info("📅 Latest Date: No data available.")
        return

    # Extract latest available date
    latest_date = df[df.columns[df.columns.str.lower() == "date"][0]].max().date()
    st.sidebar.success(f"📅 Latest Date: {latest_date.strftime('%b %d, %Y')}")

    # Display last uploaded file name
    last_uploaded_file = st.session_state.get("last_uploaded", "No file uploaded")
    st.sidebar.info(f"📂 Last Uploaded File: {last_uploaded_file}")

    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}

    min_date, max_date = df[display_cols["date"]].min().date(), df[display_cols["date"]].max().date()

    st.title("📊 MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])

    # ---- Daily View ----
    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            selected_providers = st.multiselect(
                "🔍 Select providers:",
                options=df_latest[display_cols["author"]].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}",
            )

            filtered_latest = df_latest[df_latest[display_cols["author"]].isin(selected_providers)] if selected_providers else df_latest

            st.subheader("📋 Detailed Data")
            st.dataframe(filtered_latest, use_container_width=True)

    # ---- Trend Analysis ----
    with tab2:
        st.subheader("📈 Date Range Analysis")

        dates = st.date_input(
            "🗓️ Select Date Range (Start - End)",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date,
        )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            return

        df_range = df[df[display_cols["date"]].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]

        if df_range.empty:
            st.warning("⚠️ No data available for the selected range")
            return

        st.subheader("📊 Average Daily Performance Trends")
        fig = px.line(
            df_range.groupby(display_cols["date"]).mean(numeric_only=True).reset_index(),
            x=display_cols["date"],
            y=[display_cols["points/half day"], display_cols["procedure/half"]],
            title="📈 Average Points & Procedures Per Half-Day",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Detailed Data")
        st.dataframe(df_range, use_container_width=True)

if __name__ == "__main__":
    main()

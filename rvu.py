import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "turnaround", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = "Viridis"

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    """Load and preprocess data from an uploaded Excel file using BytesIO."""
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getbuffer()))

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

        # ✅ Fix Turnaround Time Conversion
        turnaround_col = col_map["turnaround"]
        df[turnaround_col] = df[turnaround_col].astype(str)
        df[turnaround_col] = pd.to_timedelta(df[turnaround_col], errors="coerce").dt.total_seconds() / 60

        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

# ---- Main Application ----
def main():
    # Sidebar
    st.sidebar.image("milv.png", width=200)
    uploaded_file = st.sidebar.file_uploader("📤 Upload RVU File", type=["xlsx"])

    if not uploaded_file:
        st.sidebar.info("📅 Latest Date: No data uploaded yet.")
        return st.info("ℹ️ Please upload a file to begin analysis")

    # Load Data
    with st.spinner("📊 Processing data..."):
        df = load_data(uploaded_file)

    if df is None:
        st.sidebar.info("📅 Latest Date: No data available.")
        return

    # Extract latest available date
    latest_date = df[df.columns[df.columns.str.lower() == "date"][0]].max().date()
    st.sidebar.success(f"📅 Latest Date: {latest_date.strftime('%b %d, %Y')}")

    # Display last uploaded file name
    st.sidebar.info(f"📂 Last Uploaded File: {uploaded_file.name}")

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
            st.subheader("📋 Detailed Data")
            st.dataframe(df_latest, use_container_width=True)

    # ---- Trend Analysis ----
    with tab2:
        st.subheader("📈 Performance Trends")

        # ✅ Daily Performance Trends (Line Chart)
        fig = px.line(df, x=display_cols["date"], y=[display_cols["points/half day"], display_cols["procedure/half"]],
                      title="📈 Daily Points & Procedures Per Half-Day", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # ✅ Turnaround Time Trends (Line Chart)
        fig = px.line(df, x=display_cols["date"], y=display_cols["turnaround"], title="⏳ Turnaround Time Trends",
                      markers=True, color_discrete_sequence=["red"])
        st.plotly_chart(fig, use_container_width=True)

        # ✅ Provider-Level Turnaround Time (Bar Chart)
        turnaround_by_provider = df.groupby(display_cols["author"])[display_cols["turnaround"]].mean().reset_index()
        fig = px.bar(turnaround_by_provider, x=display_cols["turnaround"], y=display_cols["author"],
                     title="⏳ Avg Turnaround Time by Provider", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

        # ✅ Shift Distribution (Histogram)
        fig = px.histogram(df, x=display_cols["shift"], nbins=10, title="📌 Shift Distribution Across Providers")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Detailed Data")
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()

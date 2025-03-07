import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# ---- Page Configuration ----
st.set_page_config(
    page_title="MILV Productivity",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half", "turnaround"}
COLOR_SCALE = 'Viridis'
DATE_FORMAT = "%b %d, %Y"
NUMERIC_COLS = ['points', 'points/half day', 'procedure/half', 'turnaround']

# ---- Session State Initialization ----
if 'last_upload' not in st.session_state:
    st.session_state.last_upload = None

# ---- Helper Functions ----
@st.cache_data(show_spinner=False, ttl=3600)
def load_data(uploaded_file):
    """Optimized data loading and preprocessing with persistent caching"""
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getbuffer()), 
                          sheet_name=0, 
                          engine='openpyxl')

        # Clean and validate columns
        df.columns = df.columns.str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Process date column
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['date']).copy()
        
        # Convert numeric columns
        df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Convert turnaround time
        df['turnaround'] = pd.to_timedelta(df['turnaround'].astype(str), errors="coerce").dt.total_seconds() / 60

        # Clean string columns
        df['author'] = df['author'].astype(str).str.strip().str.title()
        df['shift'] = pd.to_numeric(df['shift'], errors='coerce').fillna(0).astype(int)

        # Add derived metrics
        df['week_number'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month_name()
        df['day_of_week'] = df['date'].dt.day_name()

        return df.sort_values('date', ascending=False)
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def create_combined_chart(df, x_col, y_cols, title):
    """Create interactive line chart with multiple traces"""
    fig = go.Figure()
    for col in y_cols:
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode='lines+markers',
            name=col.title(),
            line=dict(width=2)
        ))
    fig.update_layout(
        title=title,
        xaxis_title=x_col.title(),
        yaxis_title="Value",
        hovermode="x unified",
        template="plotly_dark",
        height=400
    )
    return fig

# ---- Main Application ----
def main():
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader(
            "📤 Upload File",
            type=["xlsx"],
            help="XLSX files only",
            key="file_uploader"
        )
        if uploaded_file:
            st.session_state.last_upload = uploaded_file
        elif st.session_state.last_upload is not None:
            uploaded_file = st.session_state.last_upload

    if not uploaded_file:
        return st.info("📁 Please upload a file to begin analysis")

    with st.spinner("📊 Processing data..."):
        df = load_data(uploaded_file)
    
    if df is None:
        return

    # Date range calculations
    max_date = df['date'].max().date()
    min_date = df['date'].min().date()
    
    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    tab1, tab2, tab3 = st.tabs(["📅 Daily Performance", "📈 Trend Analysis", "🔍 Deep Insights"])

    # ---- Daily Performance ----
    with tab1:
        st.subheader(f"🗓️ {max_date.strftime(DATE_FORMAT)}")
        df_daily = df[df['date'].dt.date == max_date].copy()

        if df_daily.empty:
            st.warning("⚠️ No data available for latest date")

        st.dataframe(df_daily, use_container_width=True)  # ✅ Ensure tab always loads

    # ---- Trend Analysis ----
    with tab2:
        st.subheader("📈 Date Range Analysis")
        
        dates = st.date_input(
            "🗓️ Date Range",
            value=[max_date - timedelta(days=7), max_date],
            min_value=min_date,
            max_value=max_date
        )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            st.stop()

        df_range = df[df['date'].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))].copy()
        
        if df_range.empty:
            st.warning("⚠️ No data in selected range")

        st.plotly_chart(create_combined_chart(df_range, "date", ["points/half day", "procedure/half"], "📈 Daily Performance Trends"), use_container_width=True)

        valid_data = df_range.dropna(subset=["points/half day", "procedure/half", "turnaround"])
        if not valid_data.empty:  # ✅ Fix: Ensure scatter plot has data
            st.plotly_chart(px.scatter(valid_data, x="points/half day", y="procedure/half", color="author", size="turnaround", title="📊 Productivity Correlation Analysis", height=400, size_max=15), use_container_width=True)

    # ---- Deep Insights ----
    with tab3:
        st.subheader("🔍 Advanced Analytics")

        if not df.empty:  # ✅ Fix: Ensure Deep Insights tab loads
            st.plotly_chart(px.histogram(df, x="day_of_week", color="shift", barmode="group", title="📅 Weekly Shift Distribution", height=400), use_container_width=True)
            st.plotly_chart(px.density_heatmap(df, x="date", y="author", z="points/half day", title="🔥 Productivity Heatmap", height=400), use_container_width=True)

            scatter_matrix_data = df.dropna(subset=["points/half day", "procedure/half", "turnaround"])
            if not scatter_matrix_data.empty:
                st.plotly_chart(px.scatter_matrix(scatter_matrix_data, dimensions=["points/half day", "procedure/half", "turnaround"], color="shift", title="📌 Multi-Dimensional Analysis", height=600), use_container_width=True)

if __name__ == "__main__":
    main()

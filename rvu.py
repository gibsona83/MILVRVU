import streamlit as st
import pandas as pd
import io
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Productivity", layout="wide", page_icon="📊")

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half", "turnaround"}
COLOR_SCALE = 'Viridis'
DATE_FORMAT = "%b %d, %Y"

# ---- Helper Functions ----
@st.cache_data(show_spinner=False, ttl=3600)
def load_data(uploaded_file):
    """Load and preprocess Excel data using BytesIO for memory efficiency."""
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getbuffer()), sheet_name=0, engine='openpyxl')

        # Clean and validate columns
        df.columns = df.columns.str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Process date column
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.normalize()
        df.dropna(subset=['date'], inplace=True)

        # Convert numeric columns
        numeric_cols = ['points', 'points/half day', 'procedure/half', 'turnaround']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Convert turnaround time
        df['turnaround'] = pd.to_timedelta(df['turnaround'].astype(str), errors="coerce").dt.total_seconds() / 60

        # Format author names
        df['author'] = df['author'].astype(str).str.strip().str.title()

        # Categorize shifts
        df['shift_category'] = df['shift'].apply(lambda x: "Half Day" if x == 1 else "Full Day")

        # Sort by date (newest first)
        df.sort_values('date', ascending=False, inplace=True)

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def create_bar_chart(data, x, y, title, color_col):
    """Create a bar chart with consistent formatting."""
    return px.bar(
        data.sort_values(x, ascending=False),
        x=x,
        y=y,
        orientation='h',
        color=color_col,
        color_continuous_scale=COLOR_SCALE,
        title=title,
        text=np.round(data[x], 1),
        height=400
    ).update_layout(showlegend=False, margin=dict(l=50, r=20, t=45, b=20))

# ---- Main Application ----
def main():
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader("📤 Upload File", type=["xlsx"], help="XLSX files only")

    if not uploaded_file:
        return st.info("📁 Please upload a file to begin analysis")

    with st.spinner("📊 Processing data..."):
        df = load_data(uploaded_file)

    if df is None:
        return

    # Get date range
    max_date = df['date'].max().date()
    min_date = df['date'].min().date()

    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    tab1, tab2 = st.tabs(["📅 Daily Performance", "📈 Trend Analysis"])

    # ---- Daily Performance Tab ----
    with tab1:
        st.subheader(f"🗓️ {max_date.strftime(DATE_FORMAT)}")
        df_daily = df[df['date'].dt.date == max_date].copy()

        if df_daily.empty:
            st.warning("⚠️ No data available for the latest date")

        # 🔍 **Provider Searchable Dropdown**
        provider_options = ["👤 " + name for name in df_daily['author'].unique()]
        selected_provider = st.selectbox("🔍 Search providers:", ["👤 All"] + provider_options)

        # Filter DataFrame
        if selected_provider != "👤 All":
            selected_provider_name = selected_provider.replace("👤 ", "")
            df_daily = df_daily[df_daily['author'] == selected_provider_name]

        # Metrics
        cols = st.columns(3)
        cols[0].metric("Total Providers", df_daily['author'].nunique())
        cols[1].metric("Avg Points/HD", f"{df_daily['points/half day'].mean():.1f}")
        cols[2].metric("Avg Procedures/HD", f"{df_daily['procedure/half'].mean():.1f}")

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(df_daily, 'points/half day', 'author', "🏆 Points per Half-Day", 'points/half day'), use_container_width=True)
        with col2:
            st.plotly_chart(create_bar_chart(df_daily, 'procedure/half', 'author', "⚡ Procedures per Half-Day", 'procedure/half'), use_container_width=True)

        # Data table
        with st.expander("📋 View Detailed Data"):
            st.dataframe(df_daily, use_container_width=True)

    # ---- Trend Analysis Tab ----
    with tab2:
        st.subheader("📈 Date Range Analysis")

        dates = st.date_input("🗓️ Date Range", value=[max_date - timedelta(days=7), max_date], min_value=min_date, max_value=max_date)

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            st.stop()

        df_range = df[df['date'].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))].copy()

        if df_range.empty:
            return st.warning("⚠️ No data in selected range")

        # 🔍 **Provider Searchable Dropdown for Trend Analysis**
        provider_options_trend = ["👤 " + name for name in df_range['author'].unique()]
        selected_provider_trend = st.selectbox("🔍 Search providers (Trend Analysis):", ["👤 All"] + provider_options_trend)

        # Filter DataFrame
        if selected_provider_trend != "👤 All":
            selected_provider_trend_name = selected_provider_trend.replace("👤 ", "")
            df_range = df_range[df_range['author'] == selected_provider_trend_name]

        # Line Chart - Performance Trends
        st.plotly_chart(px.line(df_range, x='date', y=['points/half day', 'procedure/half'], title="📈 Performance Trends", markers=True), use_container_width=True)

        # Provider-Level Trends
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(df_range.groupby('author')['points/half day'].mean().reset_index(), 'points/half day', 'author', "🏆 Avg Points per Half-Day", 'points/half day'), use_container_width=True)
        with col2:
            st.plotly_chart(create_bar_chart(df_range.groupby('author')['procedure/half'].mean().reset_index(), 'procedure/half', 'author', "⚡ Avg Procedures per Half-Day", 'procedure/half'), use_container_width=True)

        # ✅ **Updated Shift Distribution Chart**
        st.plotly_chart(px.histogram(df_range, x="shift_category", title="📌 Shift Distribution (Half vs Full Day)", color="shift_category", barmode="group"), use_container_width=True)

        # Data Table
        with st.expander("📋 View Detailed Data"):
            st.dataframe(df_range, use_container_width=True)

if __name__ == "__main__":
    main()

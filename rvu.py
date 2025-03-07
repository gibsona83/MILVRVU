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
        df['turnaround'] = pd.to_timedelta(
            df['turnaround'].astype(str), errors="coerce"
        ).dt.total_seconds() / 60

        # Clean string columns
        df['author'] = df['author'].astype(str).str.strip().str.title()
        df['shift'] = df['shift'].astype(str).str.strip().str.title()

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
        )
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
        elif st.session_state.last_upload:
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

    # ---- Daily View ----
    with tab1:
        st.subheader(f"🗓️ {max_date.strftime(DATE_FORMAT)}")
        df_daily = df[df['date'].dt.date == max_date].copy()

        if df_daily.empty:
            return st.warning("⚠️ No data available for latest date")

        # Provider selection
        selected_providers = st.multiselect(
            "🔍 Filter providers:", 
            options=df_daily['author'].unique(),
            default=None,
            placeholder="Type or select provider...",
            format_func=lambda x: f"👤 {x}"
        )

        filtered = df_daily if not selected_providers else df_daily[df_daily['author'].isin(selected_providers)]

        # Metrics row
        cols = st.columns(4)
        cols[0].metric("Total Providers", filtered['author'].nunique())
        cols[1].metric("Avg Points/HD", f"{filtered['points/half day'].mean():.1f}")
        cols[2].metric("Avg Procedures/HD", f"{filtered['procedure/half'].mean():.1f}")
        cols[3].metric("Avg Turnaround", f"{filtered['turnaround'].mean():.1f} min")

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                filtered.sort_values('points/half day', ascending=False),
                x='points/half day',
                y='author',
                orientation='h',
                color='points/half day',
                color_continuous_scale=COLOR_SCALE,
                title="🏆 Points per Half-Day",
                text=np.round(filtered['points/half day'], 1),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                filtered.sort_values('procedure/half', ascending=False),
                x='procedure/half',
                y='author',
                orientation='h',
                color='procedure/half',
                color_continuous_scale=COLOR_SCALE,
                title="⚡ Procedures per Half-Day",
                text=np.round(filtered['procedure/half'], 1),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Data table
        with st.expander("📋 View Detailed Data"):
            st.dataframe(filtered, use_container_width=True)

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
            return st.warning("⚠️ No data in selected range")

        # Enhanced visualizations
        col1, col2 = st.columns(2)
        with col1:
            # Daily performance trends
            try:
                df_daily = df_range.set_index('date')[NUMERIC_COLS].resample('D').mean().reset_index()
                st.plotly_chart(create_combined_chart(
                    df_daily,
                    'date',
                    ['points/half day', 'procedure/half'],
                    "📈 Daily Performance Trends"
                ), use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering daily trends: {str(e)}")

        with col2:
            try:
                valid_data = df_range.dropna(subset=['points/half day', 'procedure/half', 'turnaround'])
                fig = px.scatter(
                    valid_data,
                    x='points/half day',
                    y='procedure/half',
                    color='author',
                    size='turnaround',
                    title="📊 Productivity Correlation Analysis",
                    height=400,
                    hover_data=['date', 'shift'],
                    size_max=15
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering correlation analysis: {str(e)}")

        col3, col4 = st.columns(2)
        with col3:
            try:
                df_weekly = df_range.set_index('date')[['turnaround']].resample('W').mean().reset_index()
                st.plotly_chart(create_combined_chart(
                    df_weekly,
                    'date',
                    ['turnaround'],
                    "⏳ Weekly Turnaround Trends"
                ), use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering weekly trends: {str(e)}")

        with col4:
            try:
                fig = px.box(
                    df_range,
                    x='shift',
                    y='points/half day',
                    color='shift',
                    title="📦 Points Distribution by Shift",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering shift distribution: {str(e)}")

    # ---- Deep Insights ----
    with tab3:
        st.subheader("🔍 Advanced Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            try:
                st.plotly_chart(px.histogram(
                    df,
                    x='day_of_week',
                    color='shift',
                    barmode='group',
                    title="📅 Weekly Shift Distribution",
                    height=400
                ), use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering shift distribution: {str(e)}")

        with col2:
            try:
                st.plotly_chart(px.density_heatmap(
                    df,
                    x='date',
                    y='author',
                    z='points/half day',
                    title="🔥 Productivity Heatmap",
                    height=400
                ), use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering heatmap: {str(e)}")

        try:
            st.plotly_chart(px.scatter_matrix(
                df,
                dimensions=['points/half day', 'procedure/half', 'turnaround'],
                color='shift',
                title="📌 Multi-Dimensional Analysis",
                height=600
            ), use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering scatter matrix: {str(e)}")

if __name__ == "__main__":
    main()
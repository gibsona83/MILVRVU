import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Productivity", layout="wide", page_icon="📊")

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = 'Viridis'

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    """Optimized data loading and preprocessing function."""
    try:
        # Read Excel directly for better memory management
        df = pd.read_excel(uploaded_file, sheet_name=0, engine='openpyxl')
        
        # Clean and validate columns
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()
        
        # Check for duplicate columns
        if len(lower_columns) != len(set(lower_columns)):
            duplicates = df.columns[lower_columns.duplicated()].tolist()
            st.error(f"❌ Duplicate columns detected: {', '.join(duplicates)}")
            return None

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in lower_columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Create column mapping
        col_map = {col.lower(): col for col in df.columns}
        date_col = col_map["date"]
        author_col = col_map["author"]

        # Process date column with efficient datetime conversion
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.normalize()
        df = df.dropna(subset=[date_col]).copy()
        
        # Convert numeric columns using vectorized operations
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS 
                      if col not in {"date", "author"}]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Format author names using vectorized string operations
        df[author_col] = df[author_col].astype(str).str.strip().str.title()

        # Ensure proper date sorting for latest date retrieval
        df = df.sort_values(date_col, ascending=False)
        
        return df, col_map
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def create_bar_chart(data, x, y, title, color_col):
    """Optimized chart creation with consistent formatting."""
    return px.bar(
        data.sort_values(x, ascending=False),
        x=x,
        y=y,
        orientation='h',
        color=color_col,
        color_continuous_scale=COLOR_SCALE,
        title=title,
        text=np.round(data[x], 1),  # Explicit rounding for consistency
        height=400
    ).update_layout(showlegend=False, margin=dict(l=50, r=20, t=45, b=20))

# ---- Main Application ----
def main():
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader("📤 Upload File", type=["xlsx"], 
                                        help="XLSX files only")

    if not uploaded_file:
        return st.info("📁 Please upload a file to begin analysis")

    with st.spinner("📊 Processing data..."):
        result = load_data(uploaded_file)
    
    if not result:
        return
    
    df, col_map = result
    date_col = col_map["date"]
    author_col = col_map["author"]
    points_col = col_map["points/half day"]
    procedure_col = col_map["procedure/half"]

    # Get date range from sorted data
    max_date = df[date_col].iloc[0].date()
    min_date = df[date_col].iloc[-1].date()

    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    tab1, tab2 = st.tabs(["📅 Daily Performance", "📈 Trend Analysis"])

    # Daily View Tab - Optimized filtering
    with tab1:
        st.subheader(f"🗓️ {max_date.strftime('%b %d, %Y')}")
        df_daily = df[df[date_col].dt.date == max_date].copy()

        if df_daily.empty:
            return st.warning("⚠️ No data available for latest date")

        # Provider selection with efficient filtering
        selected_providers = st.multiselect(
            "🔍 Filter providers:", 
            options=df_daily[author_col].unique(),
            default=None,
            placeholder="Type or select provider...",
            format_func=lambda x: f"👤 {x}"
        )

        filtered = df_daily if not selected_providers else \
                 df_daily[df_daily[author_col].isin(selected_providers)]

        # Metrics with rounded values
        cols = st.columns(3)
        cols[0].metric("Total Providers", filtered[author_col].nunique())
        cols[1].metric("Avg Points/HD", f"{filtered[points_col].mean():.1f}")
        cols[2].metric("Avg Procedures/HD", f"{filtered[procedure_col].mean():.1f}")

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(filtered, points_col, author_col, 
                                          "🏆 Points per Half-Day", points_col), 
                          use_container_width=True)
        with col2:
            st.plotly_chart(create_bar_chart(filtered, procedure_col, author_col, 
                                          "⚡ Procedures per Half-Day", procedure_col), 
                          use_container_width=True)

        # Data table with lazy loading
        with st.expander("📋 View Detailed Data"):
            st.dataframe(filtered, use_container_width=True)

    # Trend Analysis Tab
    with tab2:
        st.subheader("📈 Date Range Analysis")
        
        # Date selection with validation
        dates = st.date_input(
            "🗓️ Date Range",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date
        )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            st.stop()

        # Provider filter
        selected_providers = st.multiselect(
            "🔍 Filter providers:", 
            options=df[author_col].unique(),
            default=None,
            placeholder="Type or select provider...",
            key="trend_providers",
            format_func=lambda x: f"👤 {x}"
        )

        # Efficient date filtering
        date_mask = df[date_col].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))
        provider_mask = df[author_col].isin(selected_providers) if selected_providers else True
        
        df_range = df[date_mask & provider_mask].copy()
        
        if df_range.empty:
            return st.warning("⚠️ No data in selected range")

        # Aggregated data
        df_agg = df_range.groupby(author_col).agg(
            **{points_col: (points_col, 'mean'),
               procedure_col: (procedure_col, 'mean')}
        ).reset_index()

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(df_agg, points_col, author_col, 
                                          "🏆 Avg Points/HD", points_col), 
                          use_container_width=True)
        with col2:
            st.plotly_chart(create_bar_chart(df_agg, procedure_col, author_col, 
                                          "⚡ Avg Procedures/HD", procedure_col), 
                          use_container_width=True)

        # Trend analysis with resampled data
        st.subheader("📅 Daily Trends")
        trend_df = df_range.set_index(date_col).resample('D').mean(numeric_only=True)
        fig = px.line(trend_df.reset_index(), 
                    x=date_col, 
                    y=[points_col, procedure_col], 
                    markers=True, 
                    title="Daily Performance Trends")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
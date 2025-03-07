import streamlit as st
import pandas as pd
import plotly.express as px

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Productivity", layout="wide", page_icon="📊")

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = 'Viridis'

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    """Load and preprocess data from an uploaded Excel file."""
    try:
        uploaded_file.seek(0)  # Reset file pointer
        xls = pd.ExcelFile(uploaded_file)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean column names
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
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()
        
        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def create_bar_chart(data, x, y, title, color_col):
    """Create standardized horizontal bar charts."""
    return px.bar(
        data.sort_values(x, ascending=False),
        x=x,
        y=y,
        orientation='h',
        color=color_col,
        color_continuous_scale=COLOR_SCALE,
        title=title,
        text_auto='.1f'
    ).update_layout(showlegend=False)

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
    
    # Column mapping
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    date_col = display_cols["date"]
    author_col = display_cols["author"]

    # Date range
    min_date, max_date = df[date_col].min().date(), df[date_col].max().date()

    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    tab1, tab2 = st.tabs(["📅 Daily Performance", "📈 Trend Analysis"])

    # Daily View Tab
    with tab1:
        st.subheader(f"🗓️ {max_date.strftime('%b %d, %Y')}")
        df_daily = df[df[date_col] == pd.Timestamp(max_date)].copy()
        
        if not df_daily.empty:
            # Provider search with multi-select
            selected_providers = st.multiselect(
                "🔍 Filter providers:", 
                options=df_daily[author_col].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}"
            )

            # Apply filtering
            filtered = df_daily[df_daily[author_col].isin(selected_providers)] if selected_providers else df_daily
            
            # Metrics
            cols = st.columns(3)
            cols[0].metric("Total Providers", filtered[author_col].nunique())
            cols[1].metric("Avg Points/HD", f"{filtered[display_cols['points/half day']].mean():.1f}")
            cols[2].metric("Avg Procedures/HD", f"{filtered[display_cols['procedure/half']].mean():.1f}")

            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_bar_chart(filtered, display_cols["points/half day"], author_col, "🏆 Points per Half-Day", display_cols["points/half day"]), use_container_width=True)
            with col2:
                st.plotly_chart(create_bar_chart(filtered, display_cols["procedure/half"], author_col, "⚡ Procedures per Half-Day", display_cols["procedure/half"]), use_container_width=True)

            # Data table
            with st.expander("📋 View Detailed Data"):
                st.dataframe(filtered, use_container_width=True)

    # Trend Analysis Tab
    with tab2:
        st.subheader("📈 Date Range Analysis")
        
        # Controls
        col1, col2 = st.columns(2)
        with col1:
            dates = st.date_input(
                "🗓️ Date Range",
                value=[max_date - pd.DateOffset(days=7), max_date],
                min_value=min_date,
                max_value=max_date
            )
        with col2:
            selected_providers = st.multiselect(
                "🔍 Filter providers:", 
                options=df[author_col].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}"
            )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            st.stop()

        # Filter data
        df_range = df[
            (df[date_col].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))) & 
            (df[author_col].isin(selected_providers) if selected_providers else True)
        ].copy()
        
        if df_range.empty:
            return st.warning("⚠️ No data in selected range")

        # Aggregate data
        df_agg = df_range.groupby(author_col).agg({
            display_cols["points/half day"]: 'mean',
            display_cols["procedure/half"]: 'mean'
        }).reset_index()

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_bar_chart(df_agg, display_cols["points/half day"], author_col, "🏆 Avg Points/HD", display_cols["points/half day"]), use_container_width=True)
        with col2:
            st.plotly_chart(create_bar_chart(df_agg, display_cols["procedure/half"], author_col, "⚡ Avg Procedures/HD", display_cols["procedure/half"]), use_container_width=True)

        # Trend lines
        st.subheader("📅 Daily Trends")
        fig = px.line(df_range.groupby(date_col).mean(numeric_only=True).reset_index(), x=date_col, y=[display_cols["points/half day"], display_cols["procedure/half"]], markers=True, title="Daily Performance Trends")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
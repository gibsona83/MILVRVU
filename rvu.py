import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Constants
FILE_STORAGE_PATH = "latest_rvu.xlsx"
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Load and preprocess data from Excel file with caching."""
    try:
        xls = pd.ExcelFile(file_path)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip().str.lower()
        col_map = {col: col for col in df.columns}

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing)}. Please check your uploaded file.")
            return None

        # Process date column
        date_col = col_map["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df = df.dropna(subset=[date_col])

        # Convert numeric columns
        numeric_cols = [col for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()
        
        return df
    except Exception as e:
        st.error(f"🚨 Error: {str(e)}")
        return None

def create_performance_chart(df, metric_col, author_col, title):
    """Create descending sorted bar chart."""
    df_sorted = df.sort_values(metric_col, ascending=False)
    
    fig = px.bar(
        df_sorted,
        x=metric_col,
        y=author_col,
        orientation='h',
        text=metric_col,
        color=metric_col,
        color_continuous_scale='Viridis',
        title=title,
        height=600
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total descending'},
        xaxis_title=metric_col,
        yaxis_title="Provider",
        hovermode='y unified',
        coloraxis_colorbar=dict(title=metric_col),
    )
    
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside',
        marker_line_width=1,
        marker_line_color='black'
    )
    fig.update_yaxes(autorange="reversed")
    return fig

def create_trend_chart(df, date_col, metrics):
    """Create a time series trend chart with correct aggregation."""
    df = df.copy()
    df['date_only'] = df[date_col].dt.date

    # Aggregate data per date
    trend_df = df.groupby(['date_only'])[metrics].mean().reset_index().dropna()

    if trend_df.empty:
        return None

    # Melt the dataframe to long format for Plotly
    trend_df_melted = trend_df.melt(id_vars=['date_only'], var_name='Metric', value_name='Value')

    # Create line chart
    fig = px.line(
        trend_df_melted,
        x='date_only',
        y='Value',
        color='Metric',
        title="Performance Trends Over Time",
        labels={'date_only': 'Date', 'Value': 'Metric Value'},
        height=500,
        markers=True
    )

    fig.update_traces(line_width=2, marker_size=6, marker_line_width=1.5)
    fig.update_xaxes(tickformat="%b %d", rangeslider_visible=True)
    fig.update_yaxes(tickformat=".2f")

    return fig

# ---- Main Application ----
def main():
    st.sidebar.image("milv.png", width=250)
    uploaded_file = st.sidebar.file_uploader("Upload RVU File", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_uploaded = pd.read_excel(uploaded_file)
            df_uploaded.to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")
    
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    st.title("MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])
    
    # TAB 1: Latest Day
    with tab1:
        st.subheader(f"Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df["date"] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            # Searchable Table
            search_query = st.text_input("Search Providers:")
            if search_query:
                df_latest = df_latest[df_latest["author"].str.contains(search_query, case=False, na=False)]

            st.dataframe(df_latest, use_container_width=True)

            st.subheader("📊 Performance")
            col1, col2 = st.columns(2)
            with col1:
                fig = create_performance_chart(df_latest, "points/half day", "author", "Points per Half-Day")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = create_performance_chart(df_latest, "procedure/half", "author", "Procedures per Half-Day")
                st.plotly_chart(fig, use_container_width=True)

    # TAB 2: Trend Analysis
    with tab2:
        st.subheader("📈 Trends Over Time")
        
        # Date range selection
        dates = st.date_input(
            "Select Date Range",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date
        )

        if len(dates) != 2:
            st.error("❌ Please select both start and end dates")
            st.stop()
        if dates[0] > dates[1]:
            st.error("❌ End date must be after start date")
            st.stop()

        start, end = dates
        df_range = df[df["date"].between(pd.Timestamp(start), pd.Timestamp(end))]

        if df_range.empty:
            st.warning("⚠️ No data available for the selected date range.")
            st.stop()

        trend_metrics = ["points/half day", "procedure/half"]
        valid_metrics = [col for col in trend_metrics if col in df_range.columns]

        if valid_metrics:
            trend_fig = create_trend_chart(df_range, "date", valid_metrics)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.warning("⚠️ No valid metrics available for trend analysis.")

        # Searchable Table
        st.subheader("🔍 Filtered Data")
        search_query = st.text_input("Search Providers in Trends:")
        if search_query:
            df_range = df_range[df_range["author"].str.contains(search_query, case=False, na=False)]
        
        st.dataframe(df_range, use_container_width=True)

if __name__ == "__main__":
    main()
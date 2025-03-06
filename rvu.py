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
    """Create descending sorted bar chart for provider-level performance."""
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
        height=500
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
    """Create a clean and improved time series line chart."""
    df = df.copy()
    df['date_only'] = df[date_col].dt.date

    # Aggregate data by date
    trend_df = df.groupby('date_only', as_index=False)[metrics].sum()

    if trend_df.empty:
        return None

    # Melt the dataframe for Plotly
    trend_df_melted = trend_df.melt(
        id_vars=['date_only'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Value'
    )

    # Create an improved line chart
    fig = px.line(
        trend_df_melted,
        x='date_only',
        y='Value',
        color='Metric',
        title="📈 Aggregate Performance Trends",
        labels={'date_only': 'Date', 'Value': 'Total Value'},
        height=500,
        markers=True,
        line_shape='spline',  # Makes the graph smoother
        color_discrete_sequence=["#1f77b4", "#ff7f0e"]
    )

    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=6, symbol='circle', opacity=0.8),
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%b %d",
            rangeslider=dict(visible=True),
            gridcolor='#EAEAEA'
        ),
        yaxis=dict(
            tickformat=".2f",
            gridcolor='#EAEAEA'
        ),
        plot_bgcolor='white',
        hovermode='x unified'
    )

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
    tab1, tab2, tab3 = st.tabs(["📅 Daily View", "📊 Provider Analysis", "📈 Trend Analysis"])

    # Daily View (Default to most recent date)
    with tab1:
        st.subheader("📊 Daily Provider Performance")
        df_latest = df[df["date"] == pd.Timestamp(max_date)]
        st.dataframe(df_latest, use_container_width=True)

        st.plotly_chart(create_performance_chart(df_latest, "points/half day", "author", "Points per Half-Day"))
        st.plotly_chart(create_performance_chart(df_latest, "procedure/half", "author", "Procedures per Half-Day"))

    # Provider Analysis (Date & Provider Filtering)
    with tab2:
        st.subheader("📊 Provider Analysis Over Time")

        # Date Range Selection
        date_range = st.date_input("Select Date Range", [max_date - pd.DateOffset(days=7), max_date], min_value=min_date, max_value=max_date)

        if len(date_range) != 2 or date_range[0] > date_range[1]:
            st.error("❌ Please select a valid date range.")
            return

        df_prov = df[df["date"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))]

        # Provider Selection as a Dropdown with Search
        with st.expander("🔍 Select Providers (Default: All)"):
            selected_providers = st.multiselect(
                "Search and Select Providers",
                df_prov["author"].unique(),
                default=df_prov["author"].unique()
            )

        if not selected_providers:
            selected_providers = df_prov["author"].unique()

        df_prov = df_prov[df_prov["author"].isin(selected_providers)]
        st.dataframe(df_prov, use_container_width=True)

        st.plotly_chart(create_performance_chart(df_prov, "points/half day", "author", "Points per Half-Day"))
        st.plotly_chart(create_performance_chart(df_prov, "procedure/half", "author", "Procedures per Half-Day"))

    # Aggregate Trends
    with tab3:
        st.subheader("📈 Aggregate Trends Over Time")
        trend_fig = create_trend_chart(df, "date", ["points/half day", "procedure/half"])
        st.plotly_chart(trend_fig)

if __name__ == "__main__":
    main()

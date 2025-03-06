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
        df = pd.read_excel(file_path)
        
        # Clean column names (handle spaces and special characters)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_', regex=False).str.replace('/', '_', regex=False)
        
        # Validate required columns
        if missing := REQUIRED_COLUMNS - set(df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')):
            st.error(f"❌ Missing required columns: {', '.join(missing)}")
            return None

        # Convert and filter dates
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        initial_count = len(df)
        df = df.dropna(subset=["date"])
        if diff := initial_count - len(df):
            st.warning(f"⚠️ Removed {diff} rows with invalid dates")

        # Convert numeric columns
        numeric_cols = ["points", "procedure", "shift", "points_half_day", "procedure_half"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Preserve original author name formatting
        df["author"] = df["author"].astype(str).str.strip()
        
        return df.sort_values("date")
    except Exception as e:
        st.error(f"🚨 Data loading error: {str(e)}")
        return None

def display_metrics(df, prefix=""):
    """Display standardized metrics in columns."""
    cols = st.columns(4)
    metrics = {
        "Total Points": df["points"].sum(),
        "Total Procedures": df["procedure"].sum(),
        "Points/Half-Day": df["points_half_day"].mean(),
        "Procedures/Half-Day": df["procedure_half"].mean()
    }
    
    for (title, value), col in zip(metrics.items(), cols):
        col.metric(
            label=f"{prefix}{title}",
            value=f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
        )

def plot_performance_chart(df, y_col, title):
    """Create interactive performance chart with proper sorting."""
    df_sorted = df.dropna(subset=[y_col]).sort_values(y_col, ascending=False)
    
    if df_sorted.empty:
        st.warning("⚠️ Insufficient data for visualization")
        return

    fig = px.bar(
        df_sorted, 
        x=y_col, 
        y="author", 
        orientation='h',
        text=y_col,
        color=y_col,
        color_continuous_scale='Viridis',
        title=title,
        height=600
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total descending'},
        xaxis_title=y_col.replace('_', ' ').title(),
        yaxis_title="Provider",
        hovermode='y unified',
        coloraxis_colorbar=dict(title=y_col.replace('_', ' ').title())
    )
    
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def plot_interactive_trend(df):
    """Display time series trend of daily metrics."""
    daily = df.groupby("date").agg({
        'points': 'sum',
        'procedure': 'sum',
        'points_half_day': 'mean',
        'procedure_half': 'mean'
    }).reset_index().sort_values('date')

    fig = px.line(
        daily, 
        x="date", 
        y=["points_half_day", "procedure_half"],
        title="Daily Efficiency Trends",
        labels={'value': 'Metric Value', 'variable': 'Metrics'},
        height=400
    )
    
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    st.plotly_chart(fig, use_container_width=True)

# ---- UI Components ----
def render_file_upload():
    """Render file upload section."""
    st.sidebar.image("milv.png", width=250)
    st.sidebar.title("Upload Daily RVU File")
    return st.sidebar.file_uploader("Upload RVU Excel File", type=["xlsx"])

def render_data_table(df, search_key):
    """Render searchable data table with consistency."""
    search = st.text_input(f"Search provider ({search_key}):")
    if search:
        df = df[df["author"].str.contains(search, case=False, na=False)]
    st.dataframe(
        df.rename(columns={
            "points_half_day": "Points/Half Day",
            "procedure_half": "Procedures/Half Day"
        }),
        use_container_width=True,
        height=400,
        hide_index=True
    )

# ---- Main App Logic ----
def main():
    # File handling
    uploaded_file = render_file_upload()
    if uploaded_file:
        try:
            pd.read_excel(uploaded_file).to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File processed successfully!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    # Data loading
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file to begin")

    # Date range calculation
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    
    st.title("MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Latest Day", "📊 Date Range Analysis"])

    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%B %d, %Y')}")
        latest_df = df[df["date"] == pd.Timestamp(max_date)]
        
        if not latest_df.empty:
            display_metrics(latest_df)
            render_data_table(latest_df, "tab1")
            
            col1, col2 = st.columns(2)
            with col1:
                plot_performance_chart(latest_df, "points_half_day", "Points per Half-Day")
            with col2:
                plot_performance_chart(latest_df, "procedure_half", "Procedures per Half-Day")
        else:
            st.warning("⚠️ No data for latest date")

    with tab2:
        st.subheader("📊 Date Range Analysis")
        start, end = st.date_input(
            "Select Range", value=(max_date, max_date),
            min_value=min_date, max_value=max_date
        )
        
        range_df = df[df["date"].between(pd.Timestamp(start), pd.Timestamp(end))]
        if not range_df.empty:
            display_metrics(range_df, "Cumulative ")
            render_data_table(range_df, "tab2")
            plot_interactive_trend(range_df)
            
            col1, col2 = st.columns(2)
            with col1:
                plot_performance_chart(range_df, "points_half_day", "Points per Half-Day")
            with col2:
                plot_performance_chart(range_df, "procedure_half", "Procedures per Half-Day")
        else:
            st.warning("⚠️ No data in selected range")

if __name__ == "__main__":
    main()
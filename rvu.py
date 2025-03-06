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
        df = df.dropna(subset=[date_col])
        
        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()
        
        return df
    except Exception as e:
        st.error(f"🚨 Error loading data: {str(e)}")
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
    """Create a time series trend chart with enhanced visibility."""
    df = df.copy()
    df['date_only'] = df[date_col].dt.date
    
    trend_df = df.groupby('date_only')[metrics].mean().reset_index().dropna()
    
    if trend_df.empty:
        return None
    
    fig = px.line(
        trend_df,
        x='date_only',
        y=metrics,
        title="Performance Trends Over Time",
        labels={'date_only': 'Date', 'value': 'Metric Value'},
        height=400,
        markers=True,
        line_shape='linear',
        color_discrete_sequence=['#FF4B4B', '#0068C9']
    )
    
    fig.update_traces(
        line_width=4,
        marker_size=10,
        marker_line_width=2,
        marker_line_color='black'
    )
    
    fig.update_xaxes(
        tickformat="%b %d",
        rangeslider_visible=True,
        gridcolor='#F0F2F6'
    )
    
    fig.update_yaxes(
        tickformat=".2f",
        gridcolor='#F0F2F6'
    )
    
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Arial"
        ),
        plot_bgcolor='white'
    )
    
    return fig

# ---- Main Application ----
def main():
    st.sidebar.image("milv.png", width=250)
    uploaded_file = st.sidebar.file_uploader("Upload RVU File", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df.to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")
    
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    
    min_date = df[display_cols["date"]].min().date()
    max_date = df[display_cols["date"]].max().date()
    
    st.title("MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])
    
    with tab1:
        st.subheader(f"Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]
        
        if not df_latest.empty:
            cols = st.columns(4)
            metrics = {
                "Total Points": display_cols["points"],
                "Total Procedures": display_cols["procedure"],
                "Points/Half-Day": display_cols["points/half day"],
                "Procedures/Half-Day": display_cols["procedure/half"]
            }
            for (title, col), c in zip(metrics.items(), cols):
                value = df_latest[col].sum() if "Total" in title else df_latest[col].mean()
                c.metric(title, f"{value:,.2f}")
            
            st.subheader("🔍 Detailed Data")
            search = st.text_input("Search providers:")
            filtered = df_latest[df_latest[display_cols["author"]].str.contains(search, case=False)] if search else df_latest
            st.dataframe(filtered, use_container_width=True)
            
            st.subheader("📊 Performance")
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_performance_chart(filtered, display_cols["points/half day"], 
                                                         display_cols["author"], "Points per Half-Day"), 
                                use_container_width=True)
            with col2:
                st.plotly_chart(create_performance_chart(filtered, display_cols["procedure/half"], 
                                                         display_cols["author"], "Procedures per Half-Day"), 
                                use_container_width=True)
    
    # TAB 2: Trend Analysis (unchanged)

if __name__ == "__main__":
    main()

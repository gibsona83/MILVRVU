import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

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
        df.dropna(subset=[date_col], inplace=True)
        
        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()
        
        return df
    except Exception as e:
        st.error(f"🚨 Error: {str(e)}")
        return None

def create_heatmap(df, date_col, author_col, metric_col):
    """Create a heatmap visualization of provider performance over time."""
    pivot_df = df.pivot_table(index=author_col, columns=date_col, values=metric_col, aggfunc='sum').fillna(0)
    
    fig = px.imshow(
        pivot_df,
        labels={'x': 'Date', 'y': 'Provider', 'color': metric_col},
        aspect='auto',
        color_continuous_scale='Viridis',
        title=f"{metric_col} Heatmap by Provider"
    )
    
    fig.update_layout(height=600, xaxis_title="Date", yaxis_title="Provider")
    return fig

# ---- Main Application ----
def main():
    st.sidebar.image("milv.png", width=250)
    uploaded_file = st.sidebar.file_uploader("Upload RVU File", type=["xlsx"])
    
    if uploaded_file:
        try:
            pd.read_excel(uploaded_file).to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")
    
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    
    min_date, max_date = df[display_cols["date"]].min().date(), df[display_cols["date"]].max().date()
    st.title("MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])
    
    with tab2:
        st.subheader("Date Range Analysis")
        
        if 'date_range' not in st.session_state:
            st.session_state.date_range = [max_date - pd.DateOffset(days=7), max_date]
        
        dates = st.date_input("Select Range (Start - End)", value=st.session_state.date_range,
                              min_value=min_date, max_value=max_date)
        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            return
        
        df_range = df[df[display_cols["date"]].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
        if df_range.empty:
            st.warning("⚠️ No data in selected range")
            return
        
        st.subheader("📈 Trends")
        fig = px.area(df_range, x=display_cols["date"], 
                      y=[display_cols["points/half day"], display_cols["procedure/half"]],
                      title="Performance Trends", 
                      labels={display_cols["date"]: "Date", "value": "Value"},
                      height=400, markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🔥 Heatmap View")
        heatmap_fig = create_heatmap(df_range, display_cols["date"], display_cols["author"], display_cols["points/half day"])
        st.plotly_chart(heatmap_fig, use_container_width=True)
        
        st.subheader("🔍 Detailed Data")
        search = st.text_input("Search providers (Trends):")
        filtered_range = df_range[df_range[display_cols["author"]].str.contains(search, case=False)] if search else df_range
        st.dataframe(filtered_range, use_container_width=True)

if __name__ == "__main__":
    main()

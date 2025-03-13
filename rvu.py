import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Productivity", layout="wide", page_icon="📊")

# ---- Constants ----
UPLOAD_FOLDER = "uploaded_data"
FILE_PATH = os.path.join(UPLOAD_FOLDER, "latest_upload.xlsx")
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = 'Viridis'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Helper Functions ----
@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: lambda _: None})
def load_data(filepath):
    """Load and preprocess data from a saved Excel file."""
    try:
        if not os.path.exists(filepath):
            return None

        xls = pd.ExcelFile(filepath)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Validate required columns
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()} in uploaded file.")
            return None
        
        # Convert date column & remove time component
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize().dt.tz_localize(None)
        df.dropna(subset=["date"], inplace=True)
        
        # Convert numeric columns
        numeric_cols = list(REQUIRED_COLUMNS - {"date", "author"})
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        df["author"] = df["author"].astype(str).str.strip().str.title()

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

        if uploaded_file:
            # Save file persistently
            with open(FILE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Clear cache to ensure fresh load
            load_data.clear()
            st.success("✅ File uploaded successfully!")

    # Load the last uploaded file if available
    if os.path.exists(FILE_PATH):
        with st.spinner("📊 Loading data..."):
            df = load_data(FILE_PATH)
    else:
        st.info("📁 No file found. Please upload one.")
        return

    if df is None:
        return

    # Column mapping
    display_cols = {col: col for col in REQUIRED_COLUMNS}
    date_col, author_col = "date", "author"

    # Date range
    min_date, max_date = df[date_col].min().date(), df[date_col].max().date()

    # Debugging: Ensure max_date is correct
    st.write(f"🔎 Debug: Max Date in File = {max_date}")

    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    st.write(f"📂 Latest Uploaded File: `{FILE_PATH}`")

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

if __name__ == "__main__":
    main()

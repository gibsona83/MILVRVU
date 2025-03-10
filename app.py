import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---- Page Configuration ----
st.set_page_config(
    page_title="MILV Productivity",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ---- Constants ----
UPLOAD_FOLDER = "uploaded_data"
FILE_PATH = os.path.join(UPLOAD_FOLDER, "latest_upload.xlsx")
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", "points/half day", "procedure/half"}
COLOR_SCALE = 'Viridis'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(filepath):
    """Load and preprocess data from Excel file."""
    try:
        xls = pd.ExcelFile(filepath)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean and validate data
        df.columns = df.columns.str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None
        
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])
        
        numeric_cols = list(REQUIRED_COLUMNS - {"date", "author"})
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        df["author"] = df["author"].astype(str).str.strip().str.title()
        df["shift"] = pd.to_numeric(df["shift"], errors='coerce').fillna(0).astype(int)

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def render_filters(df, min_date, max_date, key_suffix):
    """Render consistent filter components with unique keys."""
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.date_input(
            "📆 Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date,
            key=f"date_{key_suffix}"
        )
    with col2:
        selected_providers = st.multiselect(
            "👤 Providers",
            df["author"].unique(),
            key=f"providers_{key_suffix}"
        )
    return date_range, selected_providers

def filter_data(df, date_range, selected_providers):
    """Apply date and provider filters to dataframe."""
    filtered = df[
        (df["date"] >= pd.Timestamp(date_range[0])) & 
        (df["date"] <= pd.Timestamp(date_range[1]))
    ]
    if selected_providers:
        filtered = filtered[filtered["author"].isin(selected_providers)]
    return filtered

# ... [Keep all previous imports and constants] ...

def main():
    # ... [Keep previous sidebar and data loading logic] ...

    # ---- Main Interface ----
    st.title("📈 MILV Productivity Dashboard")
    st.caption(f"Latest data: {max_date.strftime('%Y-%m-%d')}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Daily Performance", 
        "📊 Shift Analysis", 
        "🏆 Leaderboard", 
        "⏳ Turnaround", 
        "📈 Trends"
    ])

    # ... [Keep tabs 1-3 implementation from previous version] ...

    # ---- ⏳ Turnaround Efficiency Tab ----
    with tab4:
        st.subheader("Procedure Efficiency Analysis")
        date_range, providers = render_filters(df, min_date, max_date, "turnaround")
        filtered = filter_data(df, date_range, providers)

        if not filtered.empty:
            # Efficiency Metrics
            cols = st.columns(3)
            cols[0].metric("Avg Procedures/Shift", f"{filtered.groupby('shift')['procedure'].mean().mean():.1f}")
            cols[1].metric("Points per Procedure", f"{(filtered['points'].sum()/filtered['procedure'].sum()):.2f}")
            cols[2].metric("Peak Efficiency Day", filtered.loc[filtered['procedure/half'].idxmax()]['date'].strftime('%b %d'))
            
            # Procedure-Points Relationship
            st.plotly_chart(px.scatter(
                filtered,
                x="procedure",
                y="points",
                color="author",
                size="shift",
                title="Procedure vs Points Relationship",
                trendline="lowess"
            ), use_container_width=True)

            # Shift Efficiency Breakdown
            shift_eff = filtered.groupby("shift").agg({
                'procedure': 'sum',
                'points/half day': 'mean'
            }).reset_index()
            st.plotly_chart(px.bar(
                shift_eff,
                x="shift",
                y=["procedure", "points/half day"],
                title="Shift Efficiency Comparison",
                labels={"value": "Metric Value"}
            ), use_container_width=True)

    # ---- 📈 Trends Tab ----
    with tab5:
        st.subheader("Temporal Trends Analysis")
        date_range, providers = render_filters(df, min_date, max_date, "trends")
        filtered = filter_data(df, date_range, providers)

        if not filtered.empty:
            # Time Series Analysis
            daily_trend = filtered.resample('D', on='date').agg({
                'points': 'sum',
                'procedure': 'sum'
            }).reset_index()

            st.plotly_chart(px.line(
                daily_trend,
                x="date",
                y=["points", "procedure"],
                title="Daily Productivity Trend",
                labels={"value": "Count"}
            ), use_container_width=True)

            # Rolling Average
            rolling_avg = daily_trend.set_index('date').rolling('7D').mean().reset_index()
            st.plotly_chart(px.line(
                rolling_avg,
                x="date",
                y=["points", "procedure"],
                title="7-Day Rolling Average",
                labels={"value": "Average"}
            ), use_container_width=True)

            # Heatmap Calendar
            heatmap_data = filtered.pivot_table(
                index=filtered['date'].dt.date,
                columns='author',
                values='procedure',
                aggfunc='sum'
            ).fillna(0)
            st.plotly_chart(px.imshow(
                heatmap_data.T,
                labels=dict(x="Date", y="Provider", color="Procedures"),
                title="Daily Procedure Heatmap"
            ), use_container_width=True)

            # Cumulative Performance
            cumulative = daily_trend[['date', 'points', 'procedure']].cumsum()
            cumulative['date'] = daily_trend['date']
            st.plotly_chart(px.area(
                cumulative,
                x="date",
                y=["points", "procedure"],
                title="Cumulative Performance Over Time"
            ), use_container_width=True)

if __name__ == "__main__":
    main()
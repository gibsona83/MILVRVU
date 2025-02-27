# rvu.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Configure page settings
st.set_page_config(
    page_title="MILV RVU Dashboard",
    page_icon="📊",
    layout="wide"
)

# Main header
st.title("MILV Radiology Productivity Dashboard")
st.markdown("""
**Instructions:**  
1. Upload the latest `RVU Daily Master.xlsx` file
2. Use filters in the sidebar to analyze data
3. Click charts to explore details
""")

# File upload section
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"],
    help="Upload the RVU Daily Master file from X:\\MILV Business Office\\CODING COMPLIANCE\\RVU Daily Report"
)

def process_data(df):
    """Clean and transform raw data"""
    # Convert dates
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # Calculate derived metrics
    df['Points/hour'] = df['Points'] / df['shift'].replace(0, 1)  # Prevent division by zero
    df['Procedures/hour'] = df['Procedure/half'] * 2
    
    # Sort by date
    return df.sort_values('Date', ascending=False)

if uploaded_file:
    # Load and process data
    raw_df = pd.read_excel(uploaded_file)
    df = process_data(raw_df)
    
    # ===== SIDEBAR CONTROLS =====
    st.sidebar.header("Filter Data")
    
    # Date range filter
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Author multi-select
    authors = st.sidebar.multiselect(
        "Select Radiologists",
        options=df['Author'].unique(),
        default=df['Author'].unique()
    )
    
    # Shift filter
    shifts = st.sidebar.slider(
        "Shift Hours",
        min_value=int(df['shift'].min()),
        max_value=int(df['shift'].max()),
        value=(0, int(df['shift'].max()))
    )

    # ===== APPLY FILTERS =====
    filtered_df = df[
        (df['Date'].between(*date_range)) &
        (df['Author'].isin(authors)) &
        (df['shift'].between(*shifts))
    ]

    # ===== MAIN DASHBOARD =====
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Radiologists", filtered_df['Author'].nunique())
    with col2:
        st.metric("Total Points", f"{filtered_df['Points'].sum():,}")
    with col3:
        st.metric("Avg Turnaround", f"{filtered_df['Turnaround'].mean():.1f} hrs")
    with col4:
        st.metric("Avg Points/Hour", f"{filtered_df['Points/hour'].mean():.1f}")

    # Charts
    tab1, tab2, tab3 = st.tabs(["Productivity Trends", "Shift Analysis", "Raw Data"])
    
    with tab1:
        # Time series chart
        st.subheader("Daily Productivity")
        daily_points = filtered_df.groupby('Date')['Points'].sum()
        st.line_chart(daily_points)
        
        # Physician performance
        st.subheader("Top Performers")
        top_10 = filtered_df.groupby('Author')['Points'].sum().nlargest(10)
        st.bar_chart(top_10)

    with tab2:
        # Shift efficiency
        st.subheader("Shift Productivity Distribution")
        fig, ax = plt.subplots()
        sns.boxplot(data=filtered_df, x='shift', y='Points')
        st.pyplot(fig)
        
        # Procedure correlation
        st.subheader("Procedures vs Points")
        st.scatter_chart(filtered_df, x='Procedure/half', y='Points')

    with tab3:
        # Raw data table
        st.subheader("Full Dataset")
        st.dataframe(
            filtered_df,
            column_config={
                "Date": "Date",
                "Author": "Radiologist",
                "shift": st.column_config.NumberColumn(
                    "Shift Hours",
                    help="Weighted shift hours (0-2 scale)"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Export button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Filtered Data",
            data=csv,
            file_name="filtered_rvu_data.csv",
            mime="text/csv"
        )

else:
    st.warning("⚠️ Please upload the latest RVU Daily Master file to begin analysis")

# Add footer
st.divider()
st.caption("Last updated: July 2024 | Maintained by Radiology Analytics Team")
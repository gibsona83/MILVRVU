import streamlit as st
import pandas as pd
from datetime import datetime

# Configure page
st.set_page_config(page_title="RVU Dashboard", layout="wide")
st.title("Radiology Productivity Dashboard")

# File upload
uploaded_file = st.file_uploader("Upload Daily RVU Report", type=["xlsx"])

if uploaded_file:
    # Read and process data
    df = pd.read_excel(uploaded_file)
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # Show latest data first
    df = df.sort_values('Date', ascending=False)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    selected_date = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Author filter
    all_authors = df['Author'].unique()
    selected_authors = st.sidebar.multiselect(
        "Select Radiologists",
        all_authors,
        default=all_authors
    )
    
    # Apply filters
    filtered_df = df[
        (df['Date'].between(*selected_date)) &
        (df['Author'].isin(selected_authors))
    ]
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Points", filtered_df['Points'].sum())
    with col2:
        st.metric("Average Turnaround", f"{filtered_df['Turnaround'].mean():.1f} hrs")
    with col3:
        st.metric("Avg Points/Half Day", f"{filtered_df['Points/half day'].mean():.1f}")
    
    # Main charts
    tab1, tab2 = st.tabs(["Productivity Overview", "Detailed Data"])
    
    with tab1:
        # Points by Author
        st.subheader("Points by Radiologist")
        author_points = filtered_df.groupby('Author')['Points'].sum().sort_values(ascending=False)
        st.bar_chart(author_points)
        
        # Points vs Shift Value
        st.subheader("Points vs Shift Hours")
        shift_points = filtered_df.groupby('shift')['Points'].mean()
        st.line_chart(shift_points)
    
    with tab2:
        # Raw data table
        st.subheader("Detailed Performance Data")
        st.dataframe(
            filtered_df,
            column_order=["Date", "Author", "shift", "Points", 
                         "Points/half day", "Procedure/half", "Turnaround"],
            hide_index=True,
            height=600
        )
        
        # Download button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered Data",
            data=csv,
            file_name="filtered_rvu_data.csv",
            mime="text/csv"
        )

else:
    st.info("👆 Upload the latest RVU Daily Master.xlsx file to begin")
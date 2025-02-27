# rvu.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configure page
st.set_page_config(page_title="MILV RVU Dashboard", layout="wide")
st.image("milv.png", use_column_width=True)
st.title("Radiology Productivity Analytics")

def load_data(uploaded_file):
    """Load and validate Excel data with debug logging"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # Validate required columns
        required_columns = ['Date', 'Author', 'Procedure', 'Points', 
                           'Turnaround', 'shift', 'Points/half day', 'Procedure/half']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return None
            
        # Convert and enhance dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Day_of_Week'] = df['Date'].dt.day_name()
        df['Week_Number'] = df['Date'].dt.isocalendar().week
        
        # Convert numeric columns
        numeric_cols = ['Points', 'Turnaround', 'shift', 'Points/half day', 'Procedure/half']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Calculate derived metrics
        df['Points/Hour'] = df['Points'] / df['shift'].replace(0, 1)
        df['Procedures/Hour'] = df['Procedure/half'] * 2
        
        return df.sort_values('Date', ascending=False)
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def plot_top_bottom(data, metric, title, num=5):
    """Plot top and bottom performers side-by-side"""
    top = data.nlargest(num, metric)
    bottom = data.nsmallest(num, metric)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    sns.barplot(y='Author', x=metric, data=top, ax=ax1, palette='viridis')
    ax1.set_title(f'Top {num} {title}')
    ax1.set_xlabel('')
    
    sns.barplot(y='Author', x=metric, data=bottom, ax=ax2, palette='rocket')
    ax2.set_title(f'Bottom {num} {title}')
    ax2.set_xlabel('')
    
    plt.tight_layout()
    st.pyplot(fig)

# File upload
uploaded_file = st.file_uploader("Upload Daily RVU Report", type=["xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        # ======================
        # SIDEBAR FILTERS
        # ======================
        with st.sidebar:
            st.header("Data Filters")
            
            # Date range filter
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
            selected_dates = st.date_input(
                "1. Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Day of week filter
            days = st.multiselect(
                "2. Select Days of Week",
                options=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
                default=['Monday','Tuesday','Wednesday','Thursday','Friday']
            )
            
            # Shift filter
            shift_range = st.slider(
                "3. Select Shift Values",
                min_value=int(df['shift'].min()),
                max_value=int(df['shift'].max()),
                value=(0, 2)
            )
            
            # Provider filter
            providers = st.multiselect(
                "4. Select Providers (Optional)",
                options=df['Author'].unique(),
                default=[]
            )

        # ======================
        # APPLY FILTERS
        # ======================
        filtered = df[
            (df['Date'].dt.date >= selected_dates[0]) &
            (df['Date'].dt.date <= selected_dates[1]) &
            (df['Day_of_Week'].isin(days)) &
            (df['shift'].between(*shift_range))
        ]
        
        if providers:
            filtered = filtered[filtered['Author'].isin(providers)]

        # ======================
        # DASHBOARD METRICS
        # ======================
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Providers", filtered['Author'].nunique())
        with col2:
            st.metric("Average Points/Hour", f"{filtered['Points/Hour'].mean():.1f}")
        with col3:
            st.metric("Total Procedures", f"{filtered['Procedure/half'].sum():,}")

        # ======================
        # VISUALIZATIONS
        # ======================
        tab1, tab2, tab3 = st.tabs(["Performance Rankings", "Trend Analysis", "Raw Data"])
        
        with tab1:
            st.header("Provider Performance Rankings")
            
            # Points Analysis
            plot_top_bottom(
                filtered.groupby('Author').agg({'Points':'sum', 'Points/Hour':'mean'}).reset_index(),
                'Points',
                'Total Points'
            )
            
            # Efficiency Analysis
            plot_top_bottom(
                filtered.groupby('Author').agg({'Points/Hour':'mean', 'Turnaround':'mean'}).reset_index(),
                'Points/Hour',
                'Points per Hour'
            )

        with tab2:
            st.header("Temporal Trends")
            
            # Daily Points Trend
            st.subheader("Daily Points Trend")
            daily_points = filtered.groupby('Date')['Points'].sum().reset_index()
            st.line_chart(daily_points, x='Date', y='Points')
            
            # Weekly Heatmap
            st.subheader("Weekly Pattern Analysis")
            heatmap_data = filtered.groupby(['Day_of_Week', 'Week_Number'])['Points'].sum().unstack()
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(heatmap_data, cmap='YlGnBu', ax=ax)
            st.pyplot(fig)

        with tab3:
            st.header("Filtered Data View")
            st.dataframe(
                filtered,
                column_config={
                    "Date": "Date",
                    "Author": "Provider",
                    "shift": "Shift Value",
                    "Points/Hour": st.column_config.NumberColumn(format="%.1f")
                },
                hide_index=True,
                use_container_width=True
            )
            
else:
    st.info("Please upload an RVU Daily Master Excel file to begin analysis")

# Footer
st.divider()
st.caption("MILV Radiology Business Intelligence | Updated Daily")
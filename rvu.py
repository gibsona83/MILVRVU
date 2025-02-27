# rvu.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configure page
st.set_page_config(page_title="MILV RVU Dashboard", layout="wide")

# Sidebar setup
with st.sidebar:
    st.image("milv.png", use_container_width=False)
    uploaded_file = st.file_uploader("Upload Daily RVU Report", type=["xlsx"])

st.title("Radiology Productivity Analytics")

def load_data(uploaded_file):
    """Load and validate Excel data"""
    try:
        df = pd.read_excel(uploaded_file)
        
        required_columns = ['Date', 'Author', 'Points', 'Turnaround', 
                          'Procedure/half', 'shift']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return None
            
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Day_of_Week'] = df['Date'].dt.day_name()
        
        numeric_cols = ['Points', 'Turnaround', 'Procedure/half', 'shift']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        return df.sort_values('Date', ascending=False)
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def plot_rankings(data, metric, title, ascending=False):
    """Plot top and bottom performers with dynamic sorting"""
    if metric == 'Turnaround':
        ascending = True  # Override for TAT
        
    sorted_data = data.sort_values(metric, ascending=ascending).dropna(subset=[metric])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Top performers
    top = sorted_data.head(5)
    sns.barplot(x=metric, y='Author', data=top, ax=ax1, palette='viridis')
    ax1.set_title(f'Top 5 {title}')
    
    # Bottom performers
    bottom = sorted_data.tail(5)
    sns.barplot(x=metric, y='Author', data=bottom, ax=ax2, palette='rocket')
    ax2.set_title(f'Bottom 5 {title}')
    
    plt.tight_layout()
    st.pyplot(fig)

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        with st.sidebar:
            # Date range with default to latest date
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
            date_range = st.date_input(
                "Select Date Range",
                value=[max_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            
            # Provider dropdown (exclude those with shift=0 in selected dates)
            valid_providers = df[
                (df['Date'].between(*date_range)) &
                (df['shift'] > 0)
            ]['Author'].unique()
            
            selected_providers = st.multiselect(
                "Select Providers",
                options=valid_providers,
                default=valid_providers
            )

        # Apply filters
        filtered = df[
            (df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
            (df['Author'].isin(selected_providers)) &
            (df['shift'] > 0)
        ]
        
        if not filtered.empty:
            # Daily metrics
            daily_stats = filtered.groupby(['Date', 'Author']).agg({
                'Points': 'sum',
                'Procedure/half': 'sum',
                'Turnaround': 'mean'
            }).reset_index()
            
            daily_stats['Procedures/day'] = daily_stats['Procedure/half'] * 2
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Providers", daily_stats['Author'].nunique())
            with col2:
                st.metric("Average Points/Day", f"{daily_stats['Points'].mean():.1f}")
            with col3:
                st.metric("Avg Daily Procedures", f"{daily_stats['Procedures/day'].mean():.1f}")

            # Performance rankings
            st.subheader("Performance Rankings")
            
            # Points per Day
            plot_rankings(
                daily_stats.groupby('Author')['Points'].mean().reset_index(),
                'Points',
                'Points per Day'
            )
            
            # Procedures per Day
            plot_rankings(
                daily_stats.groupby('Author')['Procedures/day'].mean().reset_index(),
                'Procedures/day',
                'Procedures per Day'
            )
            
            # Turnaround Time
            plot_rankings(
                daily_stats.groupby('Author')['Turnaround'].mean().reset_index(),
                'Turnaround',
                'Average Turnaround Time'
            )

            # Raw data
            st.subheader("Detailed Daily Performance")
            st.dataframe(
                daily_stats,
                column_config={
                    "Date": "Date",
                    "Author": "Provider",
                    "Procedures/day": st.column_config.NumberColumn(format="%d 📋"),
                    "Turnaround": st.column_config.NumberColumn(format="%.1f hrs ⏱️")
                },
                hide_index=True,
                use_container_width=True
            )
            
        else:
            st.warning("No data found for selected filters")
            
else:
    st.info("👆 Upload RVU Daily Master Excel file to begin")

# Footer
st.divider()
st.caption("MILV Radiology Analytics | Data refreshed daily at 8 AM EST")
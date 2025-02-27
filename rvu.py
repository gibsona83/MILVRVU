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
            
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date'])
        
        numeric_cols = ['Points', 'Turnaround', 'Procedure/half', 'shift']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        return df.sort_values('Date', ascending=False)
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def plot_rankings(data, metric, title, ascending=False):
    """Plot top and bottom performers with dynamic sorting"""
    if metric == 'Turnaround':
        ascending = True  # Force ascending for TAT
        
    sorted_data = data.sort_values(metric, ascending=ascending).dropna(subset=[metric])
    
    if sorted_data.empty:
        st.warning(f"No data available for {title}")
        return
    
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
            # Date selection (default to latest date)
            latest_date = df['Date'].max()
            selected_date = st.date_input(
                "Select Date",
                value=latest_date,
                min_value=df['Date'].min(),
                max_value=df['Date'].max()
            )
            
            # Get valid providers (shift > 0 for selected date)
            valid_providers = df[
                (df['Date'] == selected_date) &
                (df['shift'] > 0)
            ]['Author'].unique()
            
            # Provider selection with "All" default
            all_selected = st.checkbox("Select All Providers", value=True)
            
            if all_selected:
                selected_providers = valid_providers
            else:
                selected_providers = st.multiselect(
                    "Select Individual Providers:",
                    options=valid_providers,
                    default=[],
                    placeholder="Start typing to search..."
                )

        # Apply filters
        filtered = df[
            (df['Date'] == selected_date) &
            (df['Author'].isin(valid_providers))  # Always filter by shift > 0
        ]
        
        if all_selected:
            filtered = filtered[filtered['Author'].isin(valid_providers)]
        else:
            filtered = filtered[filtered['Author'].isin(selected_providers)]

        if not filtered.empty:
            # Calculate daily metrics
            daily_stats = filtered.groupby('Author').agg({
                'Points': 'sum',
                'Procedure/half': 'sum',
                'Turnaround': 'mean'
            }).reset_index()
            
            daily_stats['Procedures/day'] = daily_stats['Procedure/half'] * 2
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", daily_stats['Points'].sum())
            with col2:
                st.metric("Total Procedures", daily_stats['Procedures/day'].sum())
            with col3:
                st.metric("Avg Turnaround", f"{daily_stats['Turnaround'].mean():.1f} hrs")

            # Performance rankings
            st.subheader(f"Performance Rankings for {selected_date}")
            
            # Points per Day
            plot_rankings(
                daily_stats,
                'Points',
                'Points per Day',
                ascending=False
            )
            
            # Procedures per Day
            plot_rankings(
                daily_stats,
                'Procedures/day',
                'Procedures per Day',
                ascending=False
            )
            
            # Turnaround Time
            plot_rankings(
                daily_stats,
                'Turnaround',
                'Average Turnaround Time',
                ascending=True
            )

            # Raw data
            st.subheader("Detailed Daily Performance")
            st.dataframe(
                filtered,
                column_config={
                    "Date": "Date",
                    "Author": "Provider",
                    "shift": st.column_config.NumberColumn(
                        "Shift Value",
                        help="0-2 scale based on shift length",
                        format="%d ⏳"
                    )
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
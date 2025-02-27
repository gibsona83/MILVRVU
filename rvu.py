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
    # Add logo to sidebar with normal size
    st.image("milv.png", use_column_width=False)
    
    # File upload in sidebar
    uploaded_file = st.file_uploader("Upload Daily RVU Report", type=["xlsx"])

st.title("Radiology Productivity Analytics")

def load_data(uploaded_file):
    """Load and validate Excel data"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # Validate required columns
        required_columns = ['Date', 'Author', 'Points', 'Turnaround', 
                           'Points/half day', 'Procedure/half']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return None
            
        # Convert and enhance dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Day_of_Week'] = df['Date'].dt.day_name()
        
        # Convert numeric columns
        numeric_cols = ['Points', 'Turnaround', 'Points/half day', 'Procedure/half']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        return df.sort_values('Date', ascending=False)
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def plot_provider_comparison(data, metric, title):
    """Plot provider comparison chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=metric, y='Author', data=data, palette='viridis', ax=ax)
    ax.set_title(title)
    ax.set_xlabel(metric)
    ax.set_ylabel('Provider')
    st.pyplot(fig)

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        # ======================
        # SIDEBAR FILTERS
        # ======================
        with st.sidebar:
            # Provider multi-select
            selected_providers = st.multiselect(
                "Select Providers for Comparison",
                options=df['Author'].unique(),
                default=df['Author'].unique()
            )
            
            # Date selection (default to latest date)
            latest_date = df['Date'].max()
            selected_date = st.date_input(
                "Select Date",
                value=latest_date,
                min_value=df['Date'].min(),
                max_value=df['Date'].max()
            )

        # ======================
        # APPLY FILTERS
        # ======================
        filtered = df[
            (df['Date'] == pd.to_datetime(selected_date)) &
            (df['Author'].isin(selected_providers))
        ]

        # ======================
        # DASHBOARD METRICS
        # ======================
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Providers", filtered['Author'].nunique())
        with col2:
            st.metric("Total Points", f"{filtered['Points'].sum():,}")
        with col3:
            st.metric("Avg Turnaround", f"{filtered['Turnaround'].mean():.1f} hrs")

        # ======================
        # VISUALIZATIONS
        # ======================
        st.subheader(f"Performance Comparison for {selected_date.strftime('%Y-%m-%d')}")
        
        # Points Comparison
        plot_provider_comparison(
            filtered.sort_values('Points', ascending=False),
            'Points',
            'Total Points by Provider'
        )
        
        # Efficiency Comparison
        plot_provider_comparison(
            filtered.sort_values('Points/half day', ascending=False),
            'Points/half day',
            'Points per Half Day'
        )

        # Raw Data
        st.subheader("Detailed Data")
        st.dataframe(
            filtered,
            column_config={
                "Date": "Date",
                "Author": "Provider",
                "Points/half day": st.column_config.NumberColumn(format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )
        
else:
    st.info("Please upload an RVU Daily Master Excel file to begin analysis")

# Footer
st.divider()
st.caption("MILV Radiology Business Intelligence | Updated Daily")
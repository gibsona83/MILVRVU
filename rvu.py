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

@st.cache_data
def load_data(uploaded_file):
    """Load and validate Excel data"""
    try:
        df = pd.read_excel(uploaded_file, sheet_name="powerscribe Data")

        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        required_columns = ['Date', 'Author', 'Points', 'Turnaround', 'Procedure/half', 'shift']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return None
            
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date'])
        
        numeric_cols = ['Points', 'Procedure/half', 'shift']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # Convert Turnaround Time (handles both D.hh:mm:ss and hh:mm:ss formats)
        def parse_turnaround(value):
            try:
                return pd.Timedelta(value).total_seconds() / 3600  # Convert to hours
            except:
                return None  # Handle errors gracefully

        df['Turnaround'] = df['Turnaround'].astype(str).apply(parse_turnaround)

        # Assign "No Shift in Qgenda" to blank shifts
        df['Shift Status'] = df['shift'].apply(lambda x: "No Shift in Qgenda" if pd.isna(x) or x == 0 else "Scheduled Shift")
        df['shift'].fillna(0.5, inplace=True)  # Assign half-day for comparison

        # Extract weekday for filtering
        df['Day of Week'] = pd.to_datetime(df['Date']).dt.day_name()

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
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Top performers
    top = sorted_data.head(5)
    sns.barplot(x=metric, y='Author', data=top, ax=axes[0], palette='viridis')
    axes[0].set_title(f'Top 5 {title}')
    axes[0].set_xlabel("")

    # Bottom performers
    bottom = sorted_data.tail(5)
    sns.barplot(x=metric, y='Author', data=bottom, ax=axes[1], palette='rocket')
    axes[1].set_title(f'Bottom 5 {title}')
    axes[1].set_xlabel("")

    plt.tight_layout()
    st.pyplot(fig)

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        with st.sidebar:
            # Date selection: Single date or range
            date_filter_type = st.radio("Filter by:", ["Single Date", "Date Range", "Day of Week"])
            
            if date_filter_type == "Single Date":
                selected_date = st.date_input("Select Date", value=df['Date'].max(), 
                                              min_value=df['Date'].min(), max_value=df['Date'].max())
                df_filtered = df[df['Date'] == selected_date]
            
            elif date_filter_type == "Date Range":
                start_date, end_date = st.date_input(
                    "Select Date Range", 
                    value=[df['Date'].min(), df['Date'].max()],
                    min_value=df['Date'].min(),
                    max_value=df['Date'].max()
                )
                df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
            
            else:  # Filter by day of the week
                selected_days = st.multiselect("Select Day(s) of the Week", 
                                               options=df['Day of Week'].unique(), 
                                               default=df['Day of Week'].unique())
                df_filtered = df[df['Day of Week'].isin(selected_days)]

            # Only show providers with data for the selected date(s)
            valid_providers = sorted(df_filtered['Author'].unique())
            provider_options = ["ALL"] + valid_providers if valid_providers else ["ALL"]

            selected_providers = st.multiselect(
                "Select Providers",
                options=provider_options,
                default=["ALL"],
                placeholder="Start typing to search..."
            )

            # If "ALL" is selected, use all providers with data
            if "ALL" in selected_providers:
                df_filtered = df_filtered[df_filtered['Author'].isin(valid_providers)]
            else:
                df_filtered = df_filtered[df_filtered['Author'].isin(selected_providers)]

        if not df_filtered.empty:
            # Calculate daily metrics
            daily_stats = df_filtered.groupby('Author').agg({
                'Points': 'sum',
                'Procedure/half': 'sum',
                'Turnaround': 'mean'  # Now correctly converted to hours
            }).reset_index()
            
            daily_stats['Procedures/day'] = daily_stats['Procedure/half'] * 2
            
            # Display metrics with improved spacing
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Points", daily_stats['Points'].sum())
            with col2:
                st.metric("Total Procedures", daily_stats['Procedures/day'].sum())
            with col3:
                avg_tat = daily_stats['Turnaround'].mean()
                if pd.notna(avg_tat):
                    st.metric("Avg Turnaround", f"{avg_tat:.2f} hrs")
                else:
                    st.metric("Avg Turnaround", "N/A")

            st.markdown("---")

            # Performance rankings
            st.subheader(f"Performance Rankings")
            
            # Points per Day
            plot_rankings(daily_stats, 'Points', 'Points per Day', ascending=False)
            
            # Procedures per Day
            plot_rankings(daily_stats, 'Procedures/day', 'Procedures per Day', ascending=False)
            
            # Turnaround Time
            plot_rankings(daily_stats, 'Turnaround', 'Average Turnaround Time', ascending=True)

            # Raw data - Remove unnamed columns
            st.subheader("Detailed Daily Performance")
            cleaned_df = df_filtered.drop(columns=[col for col in df_filtered.columns if "Unnamed" in col])

            st.dataframe(
                cleaned_df,
                column_config={
                    "Date": "Date",
                    "Author": "Provider",
                    "Turnaround": st.column_config.NumberColumn("Turnaround Time (hrs)", help="Avg TAT in hours", format="%.2f"),
                    "shift": st.column_config.NumberColumn("Shift Value", help="0-2 scale based on shift length", format="%d ⏳"),
                    "Shift Status": "Shift Status"
                },
                hide_index=True,
                use_container_width=True
            )
            
        else:
            st.warning("No data found for selected filters")
            
else:
    st.info("👆 Upload RVU Daily Master Excel file to begin")

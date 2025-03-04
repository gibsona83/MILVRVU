import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Title of the dashboard
st.title("📊 MILV Daily Productivity")

# Sidebar for file upload
with st.sidebar:
    st.header("Upload Data File")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

# Function to load data
def load_data(file):
    try:
        df = pd.read_excel(file)
        st.success("Data loaded successfully!")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data if file is uploaded
if uploaded_file:
    df = load_data(uploaded_file)
    st.write("First few rows of the dataset:")
    st.write(df.head())  # Display first few rows for verification

    # Data preprocessing
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Turnaround Time'] = pd.to_numeric(df['Turnaround Time'], errors='coerce')
        df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)
        st.success("Data preprocessing completed!")
    except Exception as e:
        st.error(f"Error during data preprocessing: {e}")

    # Date range selection
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Filter data based on date range
    start_date, end_date = date_range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    # Display filtered data for debugging
    st.write("Filtered Data:")
    st.write(df_filtered.head())

    # Check if filtered data is empty
    if df_filtered.empty:
        st.warning("No data available for the selected date range.")
    else:
        # Plot Turnaround Time by Provider
        fig_tat = px.bar(df_filtered, x='Provider', y='Turnaround Time', title='Turnaround Time by Provider')
        st.plotly_chart(fig_tat)

        # Plot Procedures per Half-Day by Provider
        if 'Procedures per Half-Day' in df_filtered.columns:
            fig_proc = px.bar(df_filtered, x='Provider', y='Procedures per Half-Day', title='Procedures per Half-Day by Provider')
            st.plotly_chart(fig_proc)
        else:
            st.warning("'Procedures per Half-Day' column is missing in the data.")

        # Plot Points per Half-Day by Provider
        if 'Points per Half-Day' in df_filtered.columns:
            fig_points = px.bar(df_filtered, x='Provider', y='Points per Half-Day', title='Points per Half-Day by Provider')
            st.plotly_chart(fig_points)
        else:
            st.warning("'Points per Half-Day' column is missing in the data.")
else:
    st.info("Please upload an Excel file to proceed.")

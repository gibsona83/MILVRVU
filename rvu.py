import streamlit as st
import pandas as pd
import plotly.express as px

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")
st.title("📊 MILV Daily Productivity")

# Sidebar for file upload
with st.sidebar:
    st.header("Upload Data File")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

def load_data(file):
    """Loads data from an uploaded Excel file."""
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def preprocess_data(df):
    """Preprocesses the dataset: converts dates, numeric values, and handles missing data."""
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Turnaround Time'] = pd.to_numeric(df['Turnaround Time'], errors='coerce')
        df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Error during data preprocessing: {e}")
        return None

def filter_data_by_date(df, date_range):
    """Filters the dataset based on the selected date range."""
    start_date, end_date = date_range
    return df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

def plot_bar_chart(df, x_col, y_col, title):
    """Generates a bar chart if the required columns are present."""
    if y_col in df.columns:
        st.plotly_chart(px.bar(df, x=x_col, y=y_col, title=title))
    else:
        st.warning(f"'{y_col}' column is missing in the data.")

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success("Data loaded successfully!")
        st.write("First few rows of the dataset:", df.head())

        df = preprocess_data(df)

        if df is not None:
            st.success("Data preprocessing completed!")

            # Sidebar date selection
            min_date, max_date = df['Date'].min(), df['Date'].max()
            date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
            
            # Filter and display data
            df_filtered = filter_data_by_date(df, date_range)
            st.write("Filtered Data:", df_filtered.head())

            if df_filtered.empty:
                st.warning("No data available for the selected date range.")
            else:
                plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider")
                plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider")
                plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider")
else:
    st.info("Please upload an Excel file to proceed.")

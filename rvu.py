import streamlit as st
import pandas as pd
import plotly.express as px

# Set Streamlit page configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")
st.title("📊 MILV Daily Productivity")

# Sidebar for file upload
with st.sidebar:
    st.header("Upload RVU File")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["xlsx"])

def load_data(file):
    """Loads data from an uploaded Excel file."""
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def preprocess_data(df):
    """Preprocesses the dataset: converts dates, cleans employment types, and removes NaNs."""
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Turnaround Time'] = pd.to_numeric(df['Turnaround Time'], errors='coerce')

        # Exclude rows where 'Employment Type' is NaN
        df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        # Standardize 'Employment Type': Remove anything in square brackets
        if 'Employment Type' in df.columns:
            df['Employment Type'] = df['Employment Type'].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()

        return df
    except Exception as e:
        st.error(f"Error during data preprocessing: {e}")
        return None

def filter_data(df, date_range, providers, employment_type, subspecialty):
    """Filters data based on selected criteria."""
    start_date, end_date = date_range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if providers and "ALL" not in providers:
        df_filtered = df_filtered[df_filtered["Provider"].isin(providers)]
    
    if employment_type and "ALL" not in employment_type:
        df_filtered = df_filtered[df_filtered["Employment Type"].isin(employment_type)]

    if subspecialty and "ALL" not in subspecialty:
        df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(subspecialty)]

    return df_filtered

def plot_bar_chart(df, x_col, y_col, title, color_col=None):
    """Generates a bar chart if the required columns are present."""
    if y_col in df.columns:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        st.plotly_chart(fig)
    else:
        st.warning(f"'{y_col}' column is missing in the data.")

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success(f"✅ Loaded {len(df)} records")
        df = preprocess_data(df)

        if df is not None:
            st.success(f"✅ Preprocessed {len(df)} records")

            # Sidebar filters
            min_date, max_date = df['Date'].min(), df['Date'].max()
            date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

            provider_options = ["ALL"] + sorted(df["Provider"].dropna().unique().tolist())
            selected_providers = st.sidebar.multiselect("Select Provider(s)", provider_options, default=["ALL"])

            employment_options = ["ALL"] + sorted(df["Employment Type"].dropna().unique().tolist())
            selected_employment = st.sidebar.multiselect("Select Employment Type", employment_options, default=["ALL"])

            subspecialty_options = ["ALL"] + sorted(df["Primary Subspecialty"].dropna().unique().tolist())
            selected_subspecialty = st.sidebar.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])

            # Apply filters
            df_filtered = filter_data(df, date_range, selected_providers, selected_employment, selected_subspecialty)
            st.success(f"✅ Records after filtering: {len(df_filtered)}")

            # Display data
            st.write("Filtered Data:", df_filtered.head())

            if df_filtered.empty:
                st.warning("No data available for the selected filters.")
            else:
                # Visualizations
                plot_bar_chart(df_filtered, "Provider", "Turnaround Time", "Turnaround Time by Provider", "Primary Subspecialty")
                plot_bar_chart(df_filtered, "Provider", "Procedures per Half-Day", "Procedures per Half-Day by Provider", "Primary Subspecialty")
                plot_bar_chart(df_filtered, "Provider", "Points per Half-Day", "Points per Half-Day by Provider", "Primary Subspecialty")
else:
    st.info("Please upload an Excel file to proceed.")

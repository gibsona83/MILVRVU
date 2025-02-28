import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def load_data(file):
    xls = pd.ExcelFile(file)
    df = pd.read_excel(xls, sheet_name='powerscribe Data')
    df = df.drop(columns=[col for col in df.columns if 'Unnamed' in col], errors='ignore')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Turnaround'] = pd.to_timedelta(df['Turnaround'], errors='coerce')
    df['Shift'] = df['shift'].fillna('No Shift in Qgenda')
    numeric_columns = ['Procedure', 'Points', 'Points/half day', 'Procedure/half']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
    return df

st.set_page_config(page_title="RVU Daily Dashboard", layout="wide")

# Load and display MILV logo in sidebar
st.sidebar.image("milv.png", use_column_width=True)

st.title("📊 RVU Daily Productivity Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload RVU Daily Master File", type=["xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    # Sidebar Filters
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
    provider_list = st.sidebar.multiselect("Select Provider(s)", df['Author'].unique(), default=df['Author'].unique())
    
    # Apply Filters
    df_filtered = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]
    df_filtered = df_filtered[df_filtered['Author'].isin(provider_list)]
    
    # Overview Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Points", df_filtered['Points'].sum())
    col2.metric("Total Procedures", df_filtered['Procedure'].sum())
    avg_tat = df_filtered['Turnaround'].mean()
    col3.metric("Avg Turnaround Time", str(avg_tat).split('.')[0])
    
    # Visualizations
    st.subheader("Daily Trends")
    df_trend = df_filtered.groupby('Date').sum().reset_index()
    fig = px.line(df_trend, x='Date', y=['Points', 'Procedure'], title="Daily Trends of Points & Procedures")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Provider Comparison")
    df_provider = df_filtered.groupby('Author').sum().reset_index()
    fig = px.bar(df_provider, x='Author', y='Points', title="Provider Performance (Points)", color='Author')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Turnaround Time Analysis")
    df_tat = df_filtered[['Author', 'Turnaround']].sort_values(by='Turnaround')
    fig = px.bar(df_tat, x='Author', y='Turnaround', title="Turnaround Time by Provider", color='Author')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Filtered Data Table")
    st.dataframe(df_filtered)
    st.download_button("Download Data as CSV", df_filtered.to_csv(index=False), "filtered_data.csv", "text/csv")

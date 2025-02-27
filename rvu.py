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
        df = pd.read_excel(uploaded_file)
        
        required_columns = ['Date', 'Author', 'Points', 'Turnaround', 'Procedure/half', 'shift']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return None
            
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df = df.dropna(subset=['Date'])
        
        numeric_cols = ['Points', 'Turnaround', 'Procedure/half', 'shift']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # Assign "No Shift in Qgenda" to blank shifts
        df['Shift Status'] = df['shift'].apply(lambda x: "No Shift in Qgenda" if pd.isna(x) or x == 0 else "Scheduled Shift")
        df['shift'].fillna(0.5, inplace=True)  # Assign half-day for comparison

        return df.sort_values('Date', ascending=False)
    
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def plot_rankings(data, metric, title, ascending=False):
    """Plot top and bottom performers with dynamic sorting"""
    if metric == 'Turnaround':
        ascending = True  # Force ascending for TAT
        
    sorted_data = data.sort_values(metric, ascending=ascending).dropna(sub

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
    st.image("milv.png", use_container_width=False)  # Updated parameter here
    
    # File upload in sidebar
    uploaded_file = st.file_uploader("Upload Daily RVU Report", type=["xlsx"])

st.title("Radiology Productivity Analytics")

# ... (rest of the code remains the same) ...

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
            use_container_width=True  # This was already correct
        )
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Constants
LAST_FILE_PATH = "latest_uploaded_file.xlsx"

# Function to load the last uploaded file
def load_last_uploaded_file():
    if os.path.exists(LAST_FILE_PATH):
        return pd.read_excel(LAST_FILE_PATH)
    return None

# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    with open(LAST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return pd.read_excel(LAST_FILE_PATH)

# UI - Header & Upload Section
st.title("MILV Data Viewer")
st.subheader("Upload your daily RVU file")

# File Upload Handling
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    df = save_uploaded_file(uploaded_file)
    st.success("New file uploaded successfully!")
else:
    df = load_last_uploaded_file()

# Display Data & Visualization if file exists
if df is not None:
    st.subheader("Latest RVU Data")
    st.dataframe(df)

    # Example Visualization: Histogram of first numeric column
    numeric_cols = df.select_dtypes(include="number").columns
    if not numeric_cols.empty:
        st.subheader("Data Distribution")
        fig, ax = plt.subplots()
        df[numeric_cols[0]].hist(ax=ax, bins=20)
        st.pyplot(fig)
else:
    st.warning("No data available. Please upload an RVU file.")

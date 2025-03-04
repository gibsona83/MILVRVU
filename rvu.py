import streamlit as st
import pandas as pd
import os

# File path to store latest uploaded file
LAST_FILE_PATH = "latest_uploaded_file.xlsx"

# Function to check if a previous file exists
def load_last_uploaded_file():
    if os.path.exists(LAST_FILE_PATH):
        return pd.read_excel(LAST_FILE_PATH)
    return None

# Function to save the uploaded file persistently
def save_uploaded_file(uploaded_file):
    with open(LAST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return pd.read_excel(LAST_FILE_PATH)

# UI Layout
st.title("MILV Data Viewer")
st.subheader("Upload your daily RVU file")

# File Upload Handling
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    df = save_uploaded_file(uploaded_file)
    st.success("New file uploaded successfully! All users will now see the updated file.")
else:
    df = load_last_uploaded_file()

# Display Latest Data
if df is not None:
    st.subheader("Latest RVU Data")
    st.dataframe(df)
else:
    st.warning("No data available. Please upload an RVU file.")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Streamlit page configuration
st.set_page_config(page_title="Dynamic Data Dashboard", layout="wide")

# File storage
UPLOAD_DIR = "./uploaded_files"
SAVED_FILE_PATH = os.path.join(UPLOAD_DIR, "latest_uploaded_file.xlsx")

# Ensure the directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Upload new file
st.sidebar.header("Upload New Excel File")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

# Save uploaded file if present
if uploaded_file is not None:
    with open(SAVED_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("File uploaded successfully!")

# Load the latest available file
if os.path.exists(SAVED_FILE_PATH):
    df = pd.read_excel(SAVED_FILE_PATH, sheet_name=0)  # Load first sheet dynamically
    st.sidebar.info("Using the latest uploaded file.")
else:
    st.warning("No file uploaded yet. Please upload an Excel file.")
    st.stop()

# Display dataset overview
st.header("📊 Data Overview")
st.dataframe(df.head())

# Auto-detect numeric columns for visualization
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
if not numeric_cols:
    st.warning("No numeric data found for visualization.")
    st.stop()

# Sidebar filtering options
st.sidebar.header("Filters")
selected_column = st.sidebar.selectbox("Select Numeric Column to Visualize", numeric_cols)

# Create visualization
st.subheader(f"Distribution of {selected_column}")
fig, ax = plt.subplots()
df[selected_column].hist(bins=20, edgecolor='black', ax=ax)
ax.set_xlabel(selected_column)
ax.set_ylabel("Frequency")
ax.set_title(f"Histogram of {selected_column}")
st.pyplot(fig)

# Summary statistics
st.subheader("📈 Summary Statistics")
st.write(df[selected_column].describe())

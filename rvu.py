import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Streamlit page configuration
st.set_page_config(page_title="Dynamic Data Dashboard", layout="wide")

# Load MILV logo
MILV_LOGO_PATH = "milv.png"  # Ensure this file is in the same directory
if os.path.exists(MILV_LOGO_PATH):
    st.sidebar.image(MILV_LOGO_PATH, use_column_width=True)

# MILV color scheme
PRIMARY_COLOR = "#003366"  # Dark blue
ACCENT_COLOR = "#0099CC"   # Light blue
TEXT_COLOR = "#FFFFFF"     # White

# File storage path
UPLOAD_DIR = "./uploaded_files"
SAVED_FILE_PATH = os.path.join(UPLOAD_DIR, "latest_uploaded_file.xlsx")

# Ensure the directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Upload new file
st.sidebar.header("Upload New Excel File")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is not None:
    with open(SAVED_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("File uploaded successfully!")

# Load the latest available file
if os.path.exists(SAVED_FILE_PATH):
    try:
        df = pd.read_excel(SAVED_FILE_PATH, sheet_name=0)  # Load first sheet dynamically
        st.sidebar.info("Using the latest uploaded file.")
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()
else:
    st.warning("No file uploaded yet. Please upload an Excel file.")
    st.stop()

# Display dataset overview
st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>📊 Data Overview</h1>", unsafe_allow_html=True)
st.write("### First 5 Rows of Data")
st.dataframe(df.head())

# Detect numeric columns for visualization
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
if not numeric_cols:
    st.warning("No numeric data found for visualization.")
    st.stop()

# Sidebar filtering options
st.sidebar.header("Filters")
selected_column = st.sidebar.selectbox("Select Numeric Column to Visualize", numeric_cols)

# Create histogram visualization
st.markdown(f"<h2 style='color: {ACCENT_COLOR};'>Distribution of {selected_column}</h2>", unsafe_allow_html=True)
fig, ax = plt.subplots()
df[selected_column].hist(bins=20, edgecolor='black', ax=ax, color=ACCENT_COLOR)
ax.set_xlabel(selected_column)
ax.set_ylabel("Frequency")
ax.set_title(f"Histogram of {selected_column}")
st.pyplot(fig)

# Summary statistics
st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>📈 Summary Statistics</h2>", unsafe_allow_html=True)
st.write(df[selected_column].describe())

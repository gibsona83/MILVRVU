import streamlit as st
import pandas as pd
import os
import io
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV RVU Dashboard", layout="wide")

st.title("📊 MILV RVU Dashboard")

# Define storage path for the latest uploaded file
FILE_STORAGE_PATH = "latest_rvu.xlsx"

def load_data(file_path):
    """Loads data from an Excel file and ensures columns are correctly formatted."""
    xls = pd.ExcelFile(file_path)
    df = xls.parse(xls.sheet_names[0])

    # Standardize column names (strip spaces, lowercase)
    df.columns = df.columns.str.strip().str.lower()

    # Convert "Date" column to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Handle Turnaround column safely
    df["turnaround"] = df["turnaround"].astype(str).str.strip()  # Remove spaces
    df["turnaround"] = pd.to_timedelta(df["turnaround"], errors="coerce")  # Convert to timedelta
    df["turnaround"] = df["turnaround"].dt.total_seconds() / 60  # Convert to minutes

    # Fill NaN values with 0 for Turnaround (if necessary)
    df["turnaround"] = df["turnaround"].fillna(0)

    return df

# Check if there is a stored file
if os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
    latest_file_status = "✅ Using last uploaded file."
else:
    df = None
    latest_file_status = "⚠️ No previously uploaded file found."

# File Upload Section
uploaded_file = st.file_uploader("Upload the RVU Excel File (Optional)", type=["xlsx"])

if uploaded_file:
    # Save the uploaded file
    with open(FILE_STORAGE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load the newly uploaded file
    df = load_data(FILE_STORAGE_PATH)
    st.success("✅ File uploaded successfully! Using new file.")

# If no upload happened, but a previous file exists, load it
if df is not None:
    st.info(latest_file_status)

    # Sidebar - Date Range Selection
    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Sidebar - Provider Selection
    providers = df["author"].unique()
    selected_providers = st.sidebar.multiselect("Select Provider(s)", providers, default=providers)

    # Filter data by selected date range and providers
    df_filtered = df[(df["date"] >= pd.to_datetime(date_range[0])) & 
                     (df["date"] <= pd.to_datetime(date_range[1])) & 
                     (df["author"].isin(selected_providers))]

    # Summary Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Date Range", f"{date_range[0]} to {date_range[1]}")
    col2.metric("🔢 Total Points", df_filtered["points"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["turnaround"].mean(), 2))

    # Turnaround Time by Provider
    st.subheader("⏳ Turnaround Time by Provider")
    fig, ax = plt.subplots()
    df_filtered.groupby("author")["turnaround"].mean().sort_values().plot(kind="bar", ax=ax)
    ax.set_ylabel("Minutes")
    ax.set_xlabel("Provider")
    ax.set_title("Average Turnaround Time per Provider")
    st.pyplot(fig)

    # Points per Provider
    st.subheader("📈 Points per Provider")
    fig, ax = plt.subplots()
    if "points/half day" in df_filtered.columns:
        df_filtered.groupby("author")["points/half day"].sum().sort_values().plot(kind="bar", ax=ax)
        ax.set_ylabel("Points")
        ax.set_xlabel("Provider")
        ax.set_title("Total Points per Provider")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Points/half day' not found in the dataset.")

    # Procedures per Provider
    st.subheader("🛠️ Procedures per Provider")
    fig, ax = plt.subplots()
    if "procedure/half" in df_filtered.columns:  # Corrected column name
        df_filtered.groupby("author")["procedure/half"].sum().sort_values().plot(kind="bar", ax=ax)
        ax.set_ylabel("Procedures")
        ax.set_xlabel("Provider")
        ax.set_title("Total Procedures per Provider")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Procedure/half' not found in the dataset.")

else:
    st.warning("Please upload an Excel file to start analyzing data.")

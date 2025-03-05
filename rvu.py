import streamlit as st
import pandas as pd
import os
import io
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

st.title("📊 MILV Daily Productivity")

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

    # Sidebar - Date Range Selection (Pre-select latest date)
    st.sidebar.subheader("Filter Data")
    latest_date = df["date"].max()
    min_date, max_date = df["date"].min(), latest_date
    date_range = st.sidebar.date_input("Select Date Range", [latest_date, latest_date], min_value=min_date, max_value=max_date)

    # Sidebar - Provider Selection (Hidden by Default)
    providers = df["author"].unique()
    with st.sidebar.expander("📋 Select Provider(s)"):
        selected_providers = st.multiselect(
            "Choose Provider(s)", providers, default=providers, help="De-select or filter providers as needed."
        )

    # Filter data for selected date range and providers
    df_filtered = df[(df["date"] >= pd.to_datetime(date_range[0])) & 
                     (df["date"] <= pd.to_datetime(date_range[1])) & 
                     (df["author"].isin(selected_providers))]

    # Ensure sorting and reduce clutter if too many providers
    top_n = 30  # Limit to top N providers in charts
    df_grouped = df_filtered.groupby("author").mean()
    
    # Summary Metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Date Range", f"{date_range[0]} to {date_range[1]}")
    col2.metric("🔢 Total Points", df_filtered["points"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["turnaround"].mean(), 2))

    # Turnaround Time by Provider (Ascending Order)
    st.subheader("⏳ Turnaround Time by Provider")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_sorted = df_grouped["turnaround"].sort_values(ascending=True)  # Fixed: Ascending order
    if len(df_sorted) > top_n:
        df_sorted = df_sorted.head(top_n)
    df_sorted.plot(kind="bar", ax=ax)
    ax.set_ylabel("Minutes")
    ax.set_xlabel("Provider")
    ax.set_title("Turnaround Time per Provider (Lowest First)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    # Points per Provider (Descending Order)
    st.subheader("📈 Points per Provider")
    fig, ax = plt.subplots(figsize=(12, 6))
    if "points/half day" in df_filtered.columns:
        df_sorted = df_grouped["points/half day"].sort_values(ascending=False)  # Fixed: Descending order
        if len(df_sorted) > top_n:
            df_sorted = df_sorted.head(top_n)
        df_sorted.plot(kind="bar", ax=ax)
        ax.set_ylabel("Points")
        ax.set_xlabel("Provider")
        ax.set_title("Total Points per Provider (Highest First)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Points/half day' not found in the dataset.")

    # Procedures per Provider (Descending Order)
    st.subheader("🛠️ Procedures per Provider")
    fig, ax = plt.subplots(figsize=(12, 6))
    if "procedure/half" in df_filtered.columns:
        df_sorted = df_grouped["procedure/half"].sort_values(ascending=False)  # Fixed: Descending order
        if len(df_sorted) > top_n:
            df_sorted = df_sorted.head(top_n)
        df_sorted.plot(kind="bar", ax=ax)
        ax.set_ylabel("Procedures")
        ax.set_xlabel("Provider")
        ax.set_title("Total Procedures per Provider (Highest First)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Procedure/half' not found in the dataset.")

    # Display Filtered Data as Table (Only for Selected Date Range)
    st.subheader("📄 Detailed Data")
    df_sorted = df_filtered.sort_values(by=["turnaround"], ascending=[True])  # Fixed: Ascending for TAT
    st.dataframe(df_sorted)

    # Download Filtered Data as CSV
    csv = df_sorted.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"MILV_Daily_Productivity_{date_range[0]}_to_{date_range[1]}.csv", "text/csv")

else:
    st.warning("Please upload an Excel file to start analyzing data.")

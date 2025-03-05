import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - MILV Logo
st.sidebar.image("milv.png", width=250)  # Load logo in sidebar

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
    df["turnaround"] = pd.to_timedelta(df["turnaround"], errors="coerce").dt.total_seconds() / 60  # Convert to minutes
    df["turnaround"] = df["turnaround"].fillna(0)  # Replace NaN with 0

    return df

# Check if a stored file exists
if os.path.exists(FILE_STORAGE_PATH):
    df = load_data(FILE_STORAGE_PATH)
    latest_file_status = "✅ Using last uploaded file."
else:
    df = None
    latest_file_status = "⚠️ No previously uploaded file found."

# File Upload Section
uploaded_file = st.file_uploader("Upload the RVU Excel File (Optional)", type=["xlsx"])

if uploaded_file:
    with open(FILE_STORAGE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    df = load_data(FILE_STORAGE_PATH)
    st.success("✅ File uploaded successfully! Using new file.")

# If no upload happened, but a previous file exists, load it
if df is not None:
    st.sidebar.info(latest_file_status)

    # Sidebar Filters
    st.sidebar.subheader("📅 Filter Data")
    latest_date = df["date"].max()
    min_date, max_date = df["date"].min(), latest_date

    # Ensure correct handling of single-date selection
    date_selection = st.sidebar.date_input("Select Date Range", [latest_date], min_value=min_date, max_value=max_date)

    # Convert selected dates to a valid datetime range
    if isinstance(date_selection, list) and len(date_selection) == 2:
        start_date, end_date = pd.to_datetime(date_selection[0]), pd.to_datetime(date_selection[1])
    else:
        start_date = end_date = pd.to_datetime(date_selection)  # Single date selected

    # Sidebar - Provider Selection
    st.sidebar.subheader("👩‍⚕️ Provider Selection")
    providers = df["author"].unique().tolist()
    all_option = "ALL Providers"

    # Ensure "ALL Providers" is always the first option
    selected_providers = st.sidebar.multiselect("Select Provider(s)", [all_option] + providers, default=[all_option])

    # Handle Selection Logic
    if all_option in selected_providers or not selected_providers:
        selected_providers = providers  # Select all providers

    # Filter data
    df_filtered = df[
        (df["date"] >= start_date) & 
        (df["date"] <= end_date) & 
        (df["author"].isin(selected_providers))
    ]

    # **AGGREGATE METRICS AT THE TOP**
    st.subheader(f"📊 Aggregate Measures for {start_date.strftime('%Y-%m-%d')}" if start_date == end_date else 
                 f"📊 Aggregate Measures from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Total Points", df_filtered["points"].sum())
    col2.metric("🛠️ Total Procedures", df_filtered["procedure"].sum())
    col3.metric("⏳ Avg Turnaround Time (min)", round(df_filtered["turnaround"].mean(), 2))

    # Show Detailed Data at the Top
    st.subheader("📄 Detailed Data Overview")
    df_sorted = df_filtered.sort_values(by=["turnaround"], ascending=[True])  # TAT ascending
    st.dataframe(df_sorted)

    # Download Data
    csv = df_sorted.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"MILV_Daily_Productivity_{start_date}_to_{end_date}.csv", "text/csv")

    # Visualization Controls
    st.subheader("📊 Visualizations")
    expand_charts = st.toggle("🔍 Click to Expand Charts", value=False)

    chart_size = (12, 4) if not expand_charts else (16, 6)  # Adjust chart size dynamically

    df_grouped = df_filtered.groupby("author").mean()
    top_n = 30  # Limit provider count in charts

    if not df_grouped.empty:
        # Turnaround Time by Provider (Ascending Order)
        st.subheader("⏳ Turnaround Time by Provider")
        fig, ax = plt.subplots(figsize=chart_size)
        df_sorted = df_grouped["turnaround"].sort_values(ascending=True)
        if not df_sorted.empty:
            df_sorted.head(top_n).plot(kind="bar", ax=ax, color="#0072CE")
            ax.set_ylabel("Minutes")
            ax.set_xlabel("Provider")
            ax.set_title("Turnaround Time per Provider (Lowest First)")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)
        else:
            st.warning("⚠️ No turnaround time data available for the selected filters.")

        # Points per Provider (Per Half Day)
        st.subheader("📈 Points per Provider (Per Half Day)")
        fig, ax = plt.subplots(figsize=chart_size)
        if "points/half day" in df_filtered.columns:
            df_sorted = df_grouped["points/half day"].sort_values(ascending=False)
            if not df_sorted.empty:
                df_sorted.head(top_n).plot(kind="bar", ax=ax, color="#002F6C")
                ax.set_ylabel("Points per Half Day")
                ax.set_xlabel("Provider")
                ax.set_title("Total Points per Provider (Per Half Day)")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)
            else:
                st.warning("⚠️ No points data available for the selected filters.")

        # Procedures per Provider (Per Half Day)
        st.subheader("🛠️ Procedures per Provider (Per Half Day)")
        fig, ax = plt.subplots(figsize=chart_size)
        if "procedure/half" in df_filtered.columns:
            df_sorted = df_grouped["procedure/half"].sort_values(ascending=False)
            if not df_sorted.empty:
                df_sorted.head(top_n).plot(kind="bar", ax=ax, color="#0072CE")
                ax.set_ylabel("Procedures per Half Day")
                ax.set_xlabel("Provider")
                ax.set_title("Total Procedures per Provider (Per Half Day)")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)
            else:
                st.warning("⚠️ No procedures data available for the selected filters.")

else:
    st.warning("Please upload an Excel file to start analyzing data.")

import streamlit as st
import pandas as pd
import os
import io
import matplotlib.pyplot as plt

# Page Configuration with Logo
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Load MILV logo
st.image("milv.png", width=300)  # Load logo from repository

# Set Custom Colors for Light & Dark Mode
PRIMARY_COLOR = "#0072CE"  # MILV Blue
SECONDARY_COLOR = "#002F6C"  # MILV Dark Blue
TEXT_COLOR = "#FFFFFF" if st.get_option("theme.base") == "dark" else "#333333"

st.markdown(
    f"""
    <style>
        body {{
            color: {TEXT_COLOR};
            background-color: #F8F9FA;
        }}
        .sidebar .sidebar-content {{
            background-color: {PRIMARY_COLOR};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {SECONDARY_COLOR};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

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
    df["turnaround"] = df["turnaround"].astype(str).str.strip()
    df["turnaround"] = pd.to_timedelta(df["turnaround"], errors="coerce")
    df["turnaround"] = df["turnaround"].dt.total_seconds() / 60  # Convert to minutes

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
    st.info(latest_file_status)

    # Sidebar Filters
    st.sidebar.subheader("Filter Data")
    latest_date = df["date"].max()
    min_date, max_date = df["date"].min(), latest_date
    date_range = st.sidebar.date_input("Select Date Range", [latest_date, latest_date], min_value=min_date, max_value=max_date)

    # Hidden Provider Selection with Search
    providers = df["author"].unique()
    with st.sidebar.expander("📋 Search & Select Provider(s)"):
        provider_selection = st.selectbox("Start typing a provider name", ["All Providers"] + list(providers))
        selected_providers = providers if provider_selection == "All Providers" else st.multiselect("Select multiple providers", providers, default=[provider_selection])

    # Filter data
    df_filtered = df[(df["date"] >= pd.to_datetime(date_range[0])) & 
                     (df["date"] <= pd.to_datetime(date_range[1])) & 
                     (df["author"].isin(selected_providers))]

    # Show Detailed Data at the Top
    st.subheader("📄 Detailed Data Overview")
    df_sorted = df_filtered.sort_values(by=["turnaround"], ascending=[True])  # TAT ascending
    st.dataframe(df_sorted)

    # Download Data
    csv = df_sorted.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"MILV_Daily_Productivity_{date_range[0]}_to_{date_range[1]}.csv", "text/csv")

    # Visualization Controls
    st.subheader("📊 Visualizations")
    expand_charts = st.toggle("🔍 Click to Expand Charts", value=False)

    chart_size = (12, 4) if not expand_charts else (16, 6)  # Adjust chart size dynamically

    df_grouped = df_filtered.groupby("author").mean()
    top_n = 30  # Limit provider count in charts

    # Turnaround Time by Provider (Ascending Order)
    st.subheader("⏳ Turnaround Time by Provider")
    fig, ax = plt.subplots(figsize=chart_size)
    df_sorted = df_grouped["turnaround"].sort_values(ascending=True)
    df_sorted.head(top_n).plot(kind="bar", ax=ax, color=PRIMARY_COLOR)
    ax.set_ylabel("Minutes")
    ax.set_xlabel("Provider")
    ax.set_title("Turnaround Time per Provider (Lowest First)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    # Points per Provider (Descending Order)
    st.subheader("📈 Points per Provider")
    fig, ax = plt.subplots(figsize=chart_size)
    if "points/half day" in df_filtered.columns:
        df_sorted = df_grouped["points/half day"].sort_values(ascending=False)
        df_sorted.head(top_n).plot(kind="bar", ax=ax, color=SECONDARY_COLOR)
        ax.set_ylabel("Points")
        ax.set_xlabel("Provider")
        ax.set_title("Total Points per Provider (Highest First)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Points/half day' not found in the dataset.")

    # Procedures per Provider (Descending Order)
    st.subheader("🛠️ Procedures per Provider")
    fig, ax = plt.subplots(figsize=chart_size)
    if "procedure/half" in df_filtered.columns:
        df_sorted = df_grouped["procedure/half"].sort_values(ascending=False)
        df_sorted.head(top_n).plot(kind="bar", ax=ax, color=PRIMARY_COLOR)
        ax.set_ylabel("Procedures")
        ax.set_xlabel("Provider")
        ax.set_title("Total Procedures per Provider (Highest First)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    else:
        st.warning("⚠️ Column 'Procedure/half' not found in the dataset.")

else:
    st.warning("Please upload an Excel file to start analyzing data.")

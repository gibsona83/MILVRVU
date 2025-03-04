import streamlit as st
import pandas as pd
import plotly.express as px
import os  # Ensure os is imported

# Load MILV logo from GitHub
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"

# File path for storing the latest uploaded file
LAST_FILE_PATH = "latest_uploaded_file.xlsx"

# Function to load the last uploaded file
def load_last_uploaded_file():
    if os.path.exists(LAST_FILE_PATH):
        return pd.read_excel(LAST_FILE_PATH)
    return None

# Function to save uploaded file persistently
def save_uploaded_file(uploaded_file):
    with open(LAST_FILE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return pd.read_excel(LAST_FILE_PATH)

# Convert Turnaround Time safely to minutes
def convert_turnaround(time_value):
    try:
        return pd.to_timedelta(time_value).total_seconds() / 60  # Convert to minutes
    except:
        return None  # Return None for invalid values

# Set Streamlit theme settings
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - Logo & Filters
with st.sidebar:
    # Display MILV Logo from GitHub
    st.image(LOGO_URL, use_container_width=True)

    # Load existing file
    df = load_last_uploaded_file()

    # Sidebar - Date Selection
    st.subheader("📅 Select Date or Range")

    if df is not None:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date  # 🔥 Remove timestamps
        latest_date = df["Date"].max()

        date_filter_option = st.radio("Select Date Filter:", ["Single Date", "Date Range"], horizontal=True)

        if date_filter_option == "Single Date":
            selected_date = st.date_input("Select Date", latest_date)
            df_filtered = df[df["Date"] == selected_date]
        else:
            start_date = st.date_input("Start Date", df["Date"].min())
            end_date = st.date_input("End Date", latest_date)
            df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

        # Multi-Select Provider Filtering with "ALL" Default
        st.subheader("👨‍⚕️ Providers")
        provider_options = df_filtered["Provider"].dropna().unique()
        provider_options = ["ALL"] + list(provider_options)  # Add "ALL" option

        selected_providers = st.multiselect(
            "Select Provider(s)", provider_options, default=["ALL"]
        )

        # Apply provider filter if not "ALL"
        if "ALL" not in selected_providers:
            df_filtered = df_filtered[df_filtered["Provider"].isin(selected_providers)]

    # Move Upload File Section to the Bottom If File is Loaded
    st.markdown("---")
    st.subheader("📂 Upload Daily RVU File")
    uploaded_file = st.file_uploader("", type=["xlsx"])

# Load data from uploaded file
if uploaded_file:
    df = save_uploaded_file(uploaded_file)
    st.sidebar.success("✅ File uploaded successfully!")
    df["Date"] = pd.to_datetime(df["Date"]).dt.date  # 🔥 Remove timestamps
    latest_date = df["Date"].max()

if df is not None and not df_filtered.empty:
    # Clean up column names
    df_filtered = df_filtered.rename(columns={
        "Author": "Provider",
        "Procedure": "Total Procedures",
        "Points": "Total Points",
        "Turnaround": "Turnaround Time",
        "Points/half day": "Points per Half-Day",
        "Procedure/half": "Procedures per Half-Day"
    })

    # Convert Turnaround Time safely
    df_filtered["Turnaround Time"] = df_filtered["Turnaround Time"].astype(str).apply(convert_turnaround)
    df_filtered = df_filtered.dropna(subset=["Turnaround Time"])  # Remove rows where conversion failed

    # Drop unnecessary columns
    df_filtered = df_filtered.drop(columns=[col for col in df_filtered.columns if "Unnamed" in col], errors="ignore")

    # Display Summary Statistics
    st.title("📊 MILV Daily Productivity Dashboard")
    st.subheader(f"📋 Productivity Summary")

    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    if "Turnaround Time" in df_filtered.columns:
        avg_turnaround = df_filtered["Turnaround Time"].mean()
        metrics_col1.metric("⏳ Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")

    if "Procedures per Half-Day" in df_filtered.columns:
        avg_procs = df_filtered["Procedures per Half-Day"].mean()
        metrics_col2.metric("🔬 Avg Procedures per Half Day", f"{avg_procs:.2f}")

    if "Points per Half-Day" in df_filtered.columns:
        avg_points = df_filtered["Points per Half-Day"].mean()
        metrics_col3.metric("📈 Avg Points per Half Day", f"{avg_points:.2f}")

    # Visualization Section
    st.subheader("📊 Performance Insights")

    # Plot Turnaround Time Trends
    if "Turnaround Time" in df_filtered.columns:
        fig1 = px.line(df_filtered, x="Date", y="Turnaround Time", color="Provider",
                       title="Turnaround Time Trends (Minutes)", markers=True)
        st.plotly_chart(fig1, use_container_width=True)

    # Plot Procedures per Half Day
    if "Procedures per Half-Day" in df_filtered.columns:
        fig2 = px.bar(df_filtered, x="Date", y="Procedures per Half-Day", color="Provider",
                      title="Procedures per Half Day by Provider", barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

    # Plot Points per Half Day
    if "Points per Half-Day" in df_filtered.columns:
        fig3 = px.line(df_filtered, x="Date", y="Points per Half-Day", color="Provider",
                       title="Points per Half Day Over Time", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

    # Display filtered data in a table
    st.subheader("📋 Detailed Data")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.warning("⚠️ No data available for the selected filters. Please adjust your selections.")

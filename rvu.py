import streamlit as st
import pandas as pd
import os
import plotly.express as px

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

# UI Layout
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

st.title("📊 MILV Daily Productivity")
st.subheader("Upload your daily RVU file and analyze productivity metrics")

# File Upload Handling
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

# Load data
if uploaded_file:
    df = save_uploaded_file(uploaded_file)
    st.success("New file uploaded! Displaying the latest data.")
else:
    df = load_last_uploaded_file()

if df is not None:
    # Clean up column names
    df = df.rename(columns={
        "Author": "Provider",
        "Procedure": "Total Procedures",
        "Points": "Total Points",
        "Turnaround": "Turnaround Time",
        "Points/half day": "Points per Half-Day",
        "Procedure/half": "Procedures per Half-Day"
    })

    # Ensure 'Date' column exists and is in datetime format
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

        # Convert Turnaround Time (H:M:S) into minutes
        df["Turnaround Time"] = pd.to_timedelta(df["Turnaround Time"]).dt.total_seconds() / 60

        # Drop unnecessary columns
        df = df.drop(columns=[col for col in df.columns if "Unnamed" in col], errors="ignore")

        # Select Date Range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", df["Date"].min().date())
        with col2:
            end_date = st.date_input("End Date", df["Date"].max().date())

        # Filter by Date Range
        df_filtered = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)]

        # Multi-Select Provider Filtering
        provider_options = df_filtered["Provider"].dropna().unique()
        selected_providers = st.multiselect("Select Provider(s)", provider_options, default=provider_options)

        if selected_providers:
            df_filtered = df_filtered[df_filtered["Provider"].isin(selected_providers)]

        # Display Summary Statistics
        st.subheader(f"📋 Productivity Summary ({start_date} - {end_date})")
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
        st.subheader(f"📋 Detailed Data for {start_date} - {end_date}")
        st.dataframe(df_filtered, use_container_width=True)

    else:
        st.error("No 'Date' column found in the uploaded file. Please check your data format.")
else:
    st.warning("No data available. Please upload an RVU file.")

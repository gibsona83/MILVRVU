import streamlit as st
import pandas as pd
import plotly.express as px
import os

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

# Function to clean employment type (removes anything in brackets)
def clean_employment_type(value):
    import re
    return re.sub(r"\[.*?\]", "", str(value)).strip()

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

    # File uploader
    uploaded_file = st.file_uploader("Upload Daily RVU File", type=["xlsx"])
    
    if uploaded_file:
        df = save_uploaded_file(uploaded_file)
    else:
        df = load_last_uploaded_file()

    # Load MILVRoster.csv for employment type and subspecialty mapping
    roster_path = "MILVRoster.csv"
    if os.path.exists(roster_path):
        roster_df = pd.read_csv(roster_path)
        roster_df["Provider"] = roster_df["Provider"].str.title()
        roster_df["Employment Type"] = roster_df["Employment Type"].apply(clean_employment_type)
    else:
        roster_df = pd.DataFrame()

    if df is not None:
        # Rename columns before filtering
        df = df.rename(columns={
            "Author": "Provider",
            "Procedure": "Total Procedures",
            "Points": "Total Points",
            "Turnaround": "Turnaround Time",
            "Points/half day": "Points per Half-Day",
            "Procedure/half": "Procedures per Half-Day"
        })

        # Merge provider info from roster
        if not roster_df.empty:
            df = df.merge(roster_df, on="Provider", how="left")

        # Convert Turnaround Time to numeric
        df["Turnaround Time"] = pd.to_numeric(df["Turnaround Time"], errors="coerce")

        # Filters
        date_selection = st.date_input("Select Date", pd.to_datetime(df["Date"]).max())
        provider_filter = st.multiselect("Select Provider(s)", df["Provider"].unique(), default=df["Provider"].unique())
        employment_filter = st.multiselect("Select Employment Type", df["Employment Type"].dropna().unique(), default=df["Employment Type"].dropna().unique())
        subspecialty_filter = st.multiselect("Select Primary Subspecialty", df["Primary Subspecialty"].dropna().unique(), default=df["Primary Subspecialty"].dropna().unique())

        # Apply filters
        df_filtered = df[
            (df["Date"] == str(date_selection)) &
            (df["Provider"].isin(provider_filter)) &
            (df["Employment Type"].isin(employment_filter)) &
            (df["Primary Subspecialty"].isin(subspecialty_filter))
        ]

        # Display summary metrics
        avg_turnaround = df_filtered["Turnaround Time"].mean()
        avg_procedures = df_filtered["Procedures per Half-Day"].mean()
        avg_points = df_filtered["Points per Half-Day"].mean()

        st.markdown(f"### Productivity Summary: {date_selection}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")
        col2.metric("Avg Procedures per Half-Day", f"{avg_procedures:.2f}")
        col3.metric("Avg Points per Half-Day", f"{avg_points:.2f}")

        # Visualization
        if not df_filtered.empty:
            # Turnaround Time Visualization - Descending
            tat_chart = px.bar(
                df_filtered.sort_values("Turnaround Time", ascending=False),
                x="Provider", y="Turnaround Time", color="Primary Subspecialty",
                title="Turnaround Time by Provider within Subspecialty",
                labels={"Provider": "Provider", "Turnaround Time": "Minutes"},
                hover_data=["Provider"]
            )
            st.plotly_chart(tat_chart, use_container_width=True)

            # Procedures per Half-Day - Ascending
            proc_chart = px.bar(
                df_filtered.sort_values("Procedures per Half-Day", ascending=True),
                x="Provider", y="Procedures per Half-Day", color="Primary Subspecialty",
                title="Procedures per Half Day by Provider",
                labels={"Provider": "Provider", "Procedures per Half-Day": "Procedures"},
                hover_data=["Provider"]
            )
            st.plotly_chart(proc_chart, use_container_width=True)

            # Points per Half-Day - Ascending
            points_chart = px.bar(
                df_filtered.sort_values("Points per Half-Day", ascending=True),
                x="Provider", y="Points per Half-Day", color="Primary Subspecialty",
                title="Points per Half Day by Provider",
                labels={"Provider": "Provider", "Points per Half-Day": "Points"},
                hover_data=["Provider"]
            )
            st.plotly_chart(points_chart, use_container_width=True)
        else:
            st.warning("⚠️ No data available. Please upload an RVU file or adjust filters.")

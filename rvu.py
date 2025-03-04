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

        # Remove blank employment types (ensuring they are non-null)
        roster_df = roster_df.dropna(subset=["Employment Type"])
    else:
        roster_df = pd.DataFrame()

# Ensure `df_filtered` is initialized before use
df_filtered = pd.DataFrame()

if df is not None and not df.empty:
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

    # Ensure 'Date' column is formatted correctly
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # Debugging output: Check data before filtering
    st.write(f"🔍 Total records before filtering: {len(df)}")

    # **Dropdown Filters**
    date_selection = st.date_input("Select Date", pd.to_datetime(df["Date"]).max())

    # Provider Dropdown (Multi-Select with "ALL" Default)
    provider_list = ["ALL"] + list(df["Provider"].dropna().unique())
    selected_providers = st.multiselect("Select Provider(s)", provider_list, default="ALL")

    # Employment Type Dropdown (Multi-Select with "ALL" Default)
    employment_list = ["ALL"] + list(df["Employment Type"].dropna().unique())
    selected_employment = st.multiselect("Select Employment Type", employment_list, default="ALL")

    # Primary Subspecialty Dropdown (Multi-Select with "ALL" Default)
    subspecialty_list = ["ALL"] + list(df["Primary Subspecialty"].dropna().unique())
    selected_subspecialties = st.multiselect("Select Primary Subspecialty", subspecialty_list, default="ALL")

    # **Apply Filters**
    df_filtered = df[df["Date"] == date_selection]

    if "ALL" not in selected_providers:
        df_filtered = df_filtered[df_filtered["Provider"].isin(selected_providers)]

    if "ALL" not in selected_employment:
        df_filtered = df_filtered[df_filtered["Employment Type"].isin(selected_employment)]

    if "ALL" not in selected_subspecialties:
        df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(selected_subspecialties)]

    # Debugging output: Check data after filtering
    st.write(f"✅ Records after filtering: {len(df_filtered)}")

# Ensure `df_filtered` is not empty before rendering charts
if df_filtered.empty:
    st.warning("⚠️ No data available after filtering. Try adjusting the filters.")
else:
    # Compute Aggregate Metrics (Prevent NaN values)
    avg_turnaround = df_filtered["Turnaround Time"].mean() if not df_filtered["Turnaround Time"].isna().all() else 0
    avg_procedures = df_filtered["Procedures per Half-Day"].mean() if not df_filtered["Procedures per Half-Day"].isna().all() else 0
    avg_points = df_filtered["Points per Half-Day"].mean() if not df_filtered["Points per Half-Day"].isna().all() else 0

    # **Display Dashboard Title & Summary**
    st.title("📊 MILV Daily Productivity")
    st.subheader(f"📋 Productivity Summary: {date_selection}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")
    col2.metric("Avg Procedures per Half-Day", f"{avg_procedures:.2f}")
    col3.metric("Avg Points per Half-Day", f"{avg_points:.2f}")

    # **Turnaround Time - Sorted Descending**
    tat_chart = px.bar(
        df_filtered.sort_values("Turnaround Time", ascending=False),
        x="Provider", y="Turnaround Time", color="Primary Subspecialty",
        title="Turnaround Time by Provider within Subspecialty",
        hover_data=["Provider"]
    )
    st.plotly_chart(tat_chart, use_container_width=True)

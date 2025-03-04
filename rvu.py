import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re  # For regex filtering of employment type

# Load MILV logo from GitHub
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"

# File paths
LAST_FILE_PATH = "latest_uploaded_file.xlsx"
ROSTER_FILE_PATH = "MILVRoster.csv"

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
        return pd.to_timedelta(time_value).total_seconds() / 60
    except:
        return None  # Return None for invalid values

# Load MILV Roster Data
def load_roster():
    if os.path.exists(ROSTER_FILE_PATH):
        return pd.read_csv(ROSTER_FILE_PATH)
    return None

# Function to clean Employment Type (remove brackets and content inside)
def clean_employment_type(value):
    return re.sub(r"\s*\[.*?\]", "", str(value)).strip()

# Function to handle sidebar selection logic (removing "ALL" if another selection is made)
def single_selection_logic(selection_list, all_label="ALL"):
    if all_label in selection_list and len(selection_list) > 1:
        selection_list.remove(all_label)  # Remove "ALL" when another selection is made
    elif not selection_list:  # If everything was removed, reset to "ALL"
        selection_list.append(all_label)
    return selection_list

# Set Streamlit theme settings
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Sidebar - Logo & Filters
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)

    # Load Roster Data
    roster_df = load_roster()

    # Upload File Section
    st.markdown("---")
    st.subheader("📂 Upload Daily RVU File")
    uploaded_file = st.file_uploader("", type=["xlsx"])

    # Load RVU Data
    df = save_uploaded_file(uploaded_file) if uploaded_file else load_last_uploaded_file()

    if df is not None:
        df = df.rename(columns={
            "Author": "Provider",
            "Procedure": "Total Procedures",
            "Points": "Total Points",
            "Turnaround": "Turnaround Time",
            "Points/half day": "Points per Half-Day",
            "Procedure/half": "Procedures per Half-Day"
        })

        # Merge Roster Data with RVU Data - **Case Insensitive Merge Fix**
        if roster_df is not None:
            roster_df["Provider"] = roster_df["Provider"].str.strip().str.lower()
            df["Provider"] = df["Provider"].str.strip().str.lower()

            df = df.merge(roster_df, on="Provider", how="left")

            # Clean Employment Type column
            if "Employment Type" in df.columns:
                df["Employment Type"] = df["Employment Type"].apply(clean_employment_type)

        # Ensure 'Date' column is formatted correctly
        df["Date"] = pd.to_datetime(df["Date"]).dt.date  # ✅ Remove timestamps

        # Load default data as the latest date in dataset
        latest_date = df["Date"].max()
        df_filtered = df[df["Date"] == latest_date]

        # Date Filter UI
        st.subheader("📅 Select Date or Range")
        date_filter_option = st.radio("Select Date Filter:", ["Single Date", "Date Range"], horizontal=True)

        if date_filter_option == "Single Date":
            selected_date = st.date_input("Select Date", latest_date)
            df_filtered = df[df["Date"] == selected_date]
        else:
            start_date = st.date_input("Start Date", df["Date"].min())
            end_date = st.date_input("End Date", latest_date)
            df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

        # Provider Filter
        if "Provider" in df_filtered.columns:
            st.subheader("👨‍⚕️ Providers")
            provider_options = ["ALL"] + list(df_filtered["Provider"].dropna().unique())
            selected_providers = st.multiselect("Select Provider(s)", provider_options, default=["ALL"])
            selected_providers = single_selection_logic(selected_providers)

            if "ALL" not in selected_providers:
                df_filtered = df_filtered[df_filtered["Provider"].isin(selected_providers)]

        # **Employment Type Filter (Remove NaN/empty values)**
        if "Employment Type" in df_filtered.columns:
            valid_employment_types = df_filtered["Employment Type"].dropna().replace("", None).dropna().unique()
            if valid_employment_types.size > 0:
                st.subheader("💼 Employment Type")
                employment_options = ["ALL"] + list(valid_employment_types)
                selected_employment = st.multiselect("Select Employment Type", employment_options, default=["ALL"])
                selected_employment = single_selection_logic(selected_employment)

                if "ALL" not in selected_employment:
                    df_filtered = df_filtered[df_filtered["Employment Type"].isin(selected_employment)]

        # **Primary Subspecialty Filter (Remove NaN/empty values)**
        if "Primary Subspecialty" in df_filtered.columns:
            valid_subspecialties = df_filtered["Primary Subspecialty"].dropna().replace("", None).dropna().unique()
            if valid_subspecialties.size > 0:
                st.subheader("🔬 Primary Subspecialty")
                subspecialty_options = ["ALL"] + list(valid_subspecialties)
                selected_subspecialties = st.multiselect("Select Primary Subspecialty", subspecialty_options, default=["ALL"])
                selected_subspecialties = single_selection_logic(selected_subspecialties)

                if "ALL" not in selected_subspecialties:
                    df_filtered = df_filtered[df_filtered["Primary Subspecialty"].isin(selected_subspecialties)]
    else:
        df_filtered = None

# Ensure valid data for visualization
if df_filtered is not None and not df_filtered.empty:
    if "Turnaround Time" in df_filtered.columns:
        df_filtered["Turnaround Time"] = df_filtered["Turnaround Time"].astype(str).apply(convert_turnaround)
        df_filtered = df_filtered.dropna(subset=["Turnaround Time"])

    df_filtered = df_filtered.drop(columns=[col for col in df_filtered.columns if "Unnamed" in col], errors="ignore")

    # ✅ Remove timestamps from visualizations
    df_filtered["Date"] = df_filtered["Date"].astype(str)

    # Display Summary Statistics
    st.title("📊 MILV Daily Productivity Dashboard")
    st.subheader(f"📋 Productivity Summary for {latest_date}")

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

    # **Visualizations**
    st.subheader("📊 Performance Insights")
    st.plotly_chart(px.scatter(df_filtered, x="Date", y="Turnaround Time", color="Primary Subspecialty", title="Turnaround Time Trends"), use_container_width=True)
    st.plotly_chart(px.bar(df_filtered, x="Date", y="Procedures per Half-Day", color="Primary Subspecialty", title="Procedures per Half Day by Provider", barmode="group"), use_container_width=True)
    st.plotly_chart(px.line(df_filtered, x="Date", y="Points per Half-Day", color="Primary Subspecialty", title="Points per Half Day Over Time", markers=True), use_container_width=True)

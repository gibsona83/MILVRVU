import streamlit as st
import pandas as pd
import traceback
from rapidfuzz import process  # Using rapidfuzz for fuzzy matching

# Debugging: Show that the script has started
st.write("🚀 App is loading...")

# Caching for performance
@st.cache_data
def load_roster():
    """Loads MILV Roster from CSV file."""
    try:
        roster_df = pd.read_csv("MILVRoster.csv")
        roster_df["Provider"] = roster_df["Provider"].str.strip().str.title()  # Normalize names
        return roster_df
    except Exception as e:
        st.error(f"❌ Error loading MILV Roster: {e}")
        return None

def convert_turnaround(value):
    """Converts turnaround time to a numeric format."""
    try:
        return float(value.replace(" hrs", ""))
    except Exception as e:
        st.error(f"❌ Error converting turnaround time: {e}")
        return None

def fuzzy_match_providers(rvu_df, roster_df):
    """Performs fuzzy matching to align provider names."""
    try:
        provider_names = roster_df["Provider"].tolist()
        matched_providers = []

        for provider in rvu_df["Provider"]:
            match, score = process.extractOne(provider, provider_names, score_cutoff=85)
            matched_providers.append(match if match else provider)

        rvu_df["Matched Provider"] = matched_providers
        return rvu_df.merge(roster_df, left_on="Matched Provider", right_on="Provider", how="left")
    except Exception as e:
        st.error(f"❌ Error in fuzzy matching: {e}")
        return rvu_df

@st.cache_data
def load_data(file):
    """Loads and processes the RVU Daily Master file, ensuring proper merging."""
    try:
        if file is None:
            st.warning("⚠️ No file uploaded.")
            return None  

        rvu_df = pd.read_excel(file, sheet_name="powerscribe Data")
        st.write("✅ File successfully loaded.")

        # Dynamically rename columns if they exist
        rename_map = {
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }
        rvu_df.rename(columns={k: v for k, v in rename_map.items() if k in rvu_df.columns}, inplace=True)

        # Convert date safely
        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date

        # Convert turnaround time if column exists
        if "Turnaround Time" in rvu_df.columns:
            rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        # Normalize provider names
        rvu_df["Provider"] = rvu_df["Provider"].str.strip().str.title()

        # Load and merge with MILV Roster using fuzzy matching
        roster_df = load_roster()
        if roster_df is not None:
            rvu_df = fuzzy_match_providers(rvu_df, roster_df)
            rvu_df.drop(columns=["Matched Provider"], inplace=True)  # Remove temp column

        # Ensure missing values are assigned correctly
        rvu_df["Employment Type"].fillna("NON MILV", inplace=True)
        rvu_df["Primary Subspecialty"].fillna("NON MILV", inplace=True)

        # Warn about missing dates before dropping
        missing_dates = rvu_df[rvu_df["Date"].isna()]
        if not missing_dates.empty:
            st.warning(f"⚠️ {len(missing_dates)} rows have missing Date values.")
            st.write(missing_dates.head())

        # Drop rows with critical missing values
        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.write(traceback.format_exc())  # Print detailed error traceback
        return None

# UI Section
st.title("RVU Daily Dashboard")

uploaded_file = st.file_uploader("Upload the latest Daily RVU file", type=["xlsx"])
if uploaded_file:
    rvu_data = load_data(uploaded_file)
    if rvu_data is not None:
        st.write("✅ Data successfully loaded!")
        st.dataframe(rvu_data.head())  # Display first few rows
    else:
        st.error("❌ Failed to load data.")

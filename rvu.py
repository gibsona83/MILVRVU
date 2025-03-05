import streamlit as st
import pandas as pd
from thefuzz import process  # Using 'thefuzz' (formerly fuzzywuzzy) for better provider name matching

# Caching to improve performance
@st.cache_data
def load_roster():
    """Loads MILV Roster from CSV file."""
    try:
        roster_df = pd.read_csv("MILVRoster.csv")
        roster_df["Provider"] = roster_df["Provider"].str.strip().str.title()  # Normalize provider names
        return roster_df
    except Exception as e:
        st.error(f"Error loading MILV Roster: {e}")
        return None

def convert_turnaround(value):
    """Converts turnaround time to a numeric format."""
    try:
        return float(value.replace(" hrs", ""))
    except:
        return None

def fuzzy_match_providers(rvu_df, roster_df):
    """Performs fuzzy matching for provider names to improve merge accuracy."""
    provider_names = roster_df["Provider"].tolist()
    rvu_df["Matched Provider"] = rvu_df["Provider"].apply(
        lambda x: process.extractOne(x, provider_names, score_cutoff=85)[0] if process.extractOne(x, provider_names, score_cutoff=85) else x
    )
    return rvu_df.merge(roster_df, left_on="Matched Provider", right_on="Provider", how="left")

@st.cache_data
def load_data(file):
    """Loads and processes the RVU Daily Master file, ensuring Provider names match correctly."""
    try:
        if file is None:
            return None  # Prevent errors if no file is uploaded

        rvu_df = pd.read_excel(file, sheet_name="powerscribe Data")

        # Dynamically rename columns if they exist
        rename_map = {
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }
        available_columns = set(rvu_df.columns)
        rename_map = {key: val for key, val in rename_map.items() if key in available_columns}
        rvu_df.rename(columns=rename_map, inplace=True)

        # Convert date column safely
        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date

        # Convert turnaround time
        if "Turnaround Time" in rvu_df.columns:
            rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        # Normalize provider names
        rvu_df["Provider"] = rvu_df["Provider"].str.strip().str.title()

        # Load and merge with MILV Roster
        roster_df = load_roster()
        if roster_df is not None:
            rvu_df = fuzzy_match_providers(rvu_df, roster_df)
            rvu_df.drop(columns=["Matched Provider"], inplace=True)  # Remove temp column

        # Assign default values for missing data
        if "Employment Type" not in rvu_df.columns:
            rvu_df["Employment Type"] = "NON MILV"
        else:
            rvu_df["Employment Type"].fillna("NON MILV", inplace=True)

        if "Primary Subspecialty" not in rvu_df.columns:
            rvu_df["Primary Subspecialty"] = "NON MILV"
        else:
            rvu_df["Primary Subspecialty"].fillna("NON MILV", inplace=True)

        # Log missing dates before dropping
        missing_dates = rvu_df[rvu_df["Date"].isna()]
        if not missing_dates.empty:
            st.warning(f"⚠️ {len(missing_dates)} rows have missing Date values.")
            st.write(missing_dates.head())

        # Drop rows with critical missing values
        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

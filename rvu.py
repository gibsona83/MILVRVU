import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_roster():
    """Downloads the MILV Roster from GitHub and loads it."""
    github_url = "https://raw.githubusercontent.com/gibsona83/MILVRVU/main/MILVRoster.csv"
    local_path = "/mnt/data/MILVRoster.csv"

    try:
        # Download from GitHub only if the file doesn't exist locally
        if not os.path.exists(local_path):
            df = pd.read_csv(github_url)
            df.to_csv(local_path, index=False)  # Save locally to avoid multiple downloads
        else:
            df = pd.read_csv(local_path)

        # Clean up employment type formatting
        df["Employment Type"] = df["Employment Type"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip()
        df["Employment Type"].fillna("Unknown", inplace=True)  # Ensure no NaN

        return df
    except Exception as e:
        st.error(f"Error loading MILV Roster from GitHub: {e}")
        return None

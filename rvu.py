import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Constants
FILE_STORAGE_PATH = "latest_rvu.xlsx"
REQUIRED_COLUMNS = {
    "date", "author", "procedure", "points", 
    "turnaround", "shift", "points/half day", "procedure/half"
}

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Load and preprocess data from Excel file with caching."""
    try:
        df = pd.read_excel(file_path)
        
        # Clean column names (preserve original formatting)
        original_columns = df.columns.tolist()
        normalized_columns = [col.strip().lower() for col in original_columns]
        column_mapping = dict(zip(original_columns, normalized_columns))
        
        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in normalized_columns]
        if missing:
            st.error(f"❌ Missing required columns: {', '.join(missing)}")
            return None

        # Restore original column names while keeping normalized versions for processing
        df.columns = [f"{col}_normalized" if col in REQUIRED_COLUMNS else col 
                     for col in original_columns]
        
        # Convert and filter dates
        df["date_normalized"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        initial_count = len(df)
        df = df.dropna(subset=["date_normalized"])
        if diff := initial_count - len(df):
            st.warning(f"⚠️ Removed {diff} rows with invalid dates")

        # Convert numeric columns
        numeric_cols = [
            "points_normalized", "procedure_normalized", "shift_normalized",
            "points/half day_normalized", "procedure/half_normalized"
        ]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Preserve original author name formatting
        df["author"] = df["author"].astype(str).str.strip()
        
        return df.sort_values("date_normalized")
    except Exception as e:
        st.error(f"🚨 Data loading error: {str(e)}")
        return None

# ... (rest of the functions remain the same but use the normalized column names)

def display_metrics(df, prefix=""):
    """Display standardized metrics in columns."""
    cols = st.columns(4)
    metrics = {
        "Total Points": df["points_normalized"].sum(),
        "Total Procedures": df["procedure_normalized"].sum(),
        "Points/Half-Day": df["points/half day_normalized"].mean(),
        "Procedures/Half-Day": df["procedure/half_normalized"].mean()
    }
    
    for (title, value), col in zip(metrics.items(), cols):
        col.metric(
            label=f"{prefix}{title}",
            value=f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
        )

# ... (update all other functions to use the normalized column names where needed)
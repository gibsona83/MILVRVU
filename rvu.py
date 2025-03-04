@st.cache_data
def load_data():
    """Loads and processes the most recent RVU Daily Master file."""
    latest_file = get_latest_rvu_file()

    if latest_file is None:
        st.error("No RVU file found. Please upload an RVU Master file.")
        return None

    st.success(f"✅ Using latest RVU file: {os.path.basename(latest_file)}")  # Show filename

    try:
        rvu_df = pd.read_excel(latest_file, sheet_name="powerscribe Data")

        # Rename columns for consistency
        rvu_df.rename(columns={
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }, inplace=True)

        # Convert 'Date' column to datetime
        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date

        # Convert Turnaround Time to minutes
        rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        # Load and merge MILV Roster
        roster_df = load_roster()
        if roster_df is not None:
            rvu_df = rvu_df.merge(roster_df, on="Provider", how="left")
        else:
            # If no roster file, add default values
            rvu_df["Employment Type"] = "Unknown"
            rvu_df["Primary Subspecialty"] = "Unknown"

        # Drop NaNs in essential columns
        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

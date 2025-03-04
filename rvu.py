@st.cache_data
def load_data(file):
    """Loads and processes the RVU Daily Master file, ensuring Provider names match correctly."""
    try:
        if file is None:
            return None  # Prevent errors if no file is uploaded

        rvu_df = pd.read_excel(file, sheet_name="powerscribe Data")

        rvu_df.rename(columns={
            "Author": "Provider",
            "Turnaround": "Turnaround Time",
            "Procedure/half": "Procedures per Half-Day",
            "Points/half day": "Points per Half-Day"
        }, inplace=True)

        rvu_df['Date'] = pd.to_datetime(rvu_df['Date'], errors='coerce').dt.date
        rvu_df["Turnaround Time"] = rvu_df["Turnaround Time"].apply(convert_turnaround)

        roster_df = load_roster()
        if roster_df is not None:
            # 🔥 FIX: Ensure Provider names match exactly by stripping spaces and normalizing case
            rvu_df["Provider"] = rvu_df["Provider"].str.strip().str.title()
            roster_df["Provider"] = roster_df["Provider"].str.strip().str.title()

            # 🔥 FIX: Perform a LEFT MERGE to preserve all RVU data and ensure unmatched rows are visible
            rvu_df = rvu_df.merge(roster_df, on="Provider", how="left", indicator=True)

            # 🔍 Debugging: Display any mismatched providers
            unmatched = rvu_df[rvu_df["_merge"] != "both"]
            if not unmatched.empty:
                st.warning("⚠️ Some providers in the RVU data do not match MILVRoster.csv.")
                st.write("Unmatched Providers:", unmatched[["Provider", "_merge"]].head())

            # Drop merge indicator column
            rvu_df.drop(columns=["_merge"], inplace=True)

        else:
            rvu_df["Employment Type"] = "Unknown"
            rvu_df["Primary Subspecialty"] = "NON MILV"

        rvu_df.dropna(subset=['Date', 'Turnaround Time'], inplace=True)

        return rvu_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

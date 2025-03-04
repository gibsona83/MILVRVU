# Ensure df_filtered is always initialized
df_filtered = pd.DataFrame()

# Only filter and process data if df is not empty
if df is not None and not df.empty:
    df = df.rename(columns={
        "Author": "Provider",
        "Procedure": "Total Procedures",
        "Points": "Total Points",
        "Turnaround": "Turnaround Time",
        "Points/half day": "Points per Half-Day",
        "Procedure/half": "Procedures per Half-Day"
    })

    # Merge Roster Data with RVU Data
    if roster_df is not None:
        roster_df["Provider"] = roster_df["Provider"].str.strip().str.lower()
        df["Provider"] = df["Provider"].str.strip().str.lower()
        df = df.merge(roster_df, on="Provider", how="left")

    # Ensure 'Date' column is formatted correctly
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # Format Provider names as "Last, First"
    df["Provider"] = df["Provider"].apply(format_provider_name)

    # Get latest available date
    latest_date = df["Date"].max()

    # Apply filtering if latest_date exists
    if latest_date:
        df_filtered = df[df["Date"] == latest_date].copy()

        # Drop NaN values before filtering
        df_filtered.dropna(subset=["Employment Type", "Primary Subspecialty", "Turnaround Time"], inplace=True)

# **Ensure df_filtered exists before calculations**
if not df_filtered.empty:
    # Convert numeric fields properly
    df_filtered["Turnaround Time"] = pd.to_numeric(df_filtered["Turnaround Time"], errors="coerce")
    df_filtered["Procedures per Half-Day"] = pd.to_numeric(df_filtered["Procedures per Half-Day"], errors="coerce")
    df_filtered["Points per Half-Day"] = pd.to_numeric(df_filtered["Points per Half-Day"], errors="coerce")

    # Drop rows where critical data is missing
    df_filtered.dropna(subset=["Turnaround Time", "Procedures per Half-Day", "Points per Half-Day"], inplace=True)

    # Compute Aggregate Metrics (Prevent NaN values)
    avg_turnaround = df_filtered["Turnaround Time"].mean() if not df_filtered["Turnaround Time"].isna().all() else 0
    avg_procs = df_filtered["Procedures per Half-Day"].mean() if not df_filtered["Procedures per Half-Day"].isna().all() else 0
    avg_points = df_filtered["Points per Half-Day"].mean() if not df_filtered["Points per Half-Day"].isna().all() else 0

    # **Display Dashboard Title & Summary**
    st.title("📊 MILV Daily Productivity")
    st.subheader(f"📋 Productivity Summary: {df_filtered['Date'].min()} - {df_filtered['Date'].max()}")

    col1, col2, col3 = st.columns(3)
    col1.metric("⏳ Avg Turnaround Time (mins)", f"{avg_turnaround:.2f}")
    col2.metric("📑 Avg Procedures per Half-Day", f"{avg_procs:.2f}")
    col3.metric("📈 Avg Points per Half-Day", f"{avg_points:.2f}")

    # **Turnaround Time - Grouped Bar Chart (Subspecialty & Providers)**
    df_filtered.sort_values(by="Turnaround Time", ascending=False, inplace=True)
    fig1 = px.bar(df_filtered, x="Provider", y="Turnaround Time", color="Primary Subspecialty",
                  title="Turnaround Time by Provider within Subspecialty",
                  hover_data=["Provider", "Employment Type"],
                  barmode="group")
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("⚠️ No valid data available. Try uploading a new file or adjusting the filters.")

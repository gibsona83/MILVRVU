# Convert Turnaround Time from string to total seconds
def convert_time_to_seconds(time_str):
    try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return np.nan  # Handle errors by returning NaN

# Ensure "Turnaround" column is a string before conversion
df["Turnaround"] = df["Turnaround"].astype(str)

# Apply conversion function
df["Turnaround_Seconds"] = df["Turnaround"].apply(convert_time_to_seconds)

# Calculate mean turnaround time in seconds
avg_turnaround = df["Turnaround_Seconds"].mean()

# Convert back to H:M:S for display
if not np.isnan(avg_turnaround):
    avg_turnaround_hms = f"{int(avg_turnaround // 3600)}:{int((avg_turnaround % 3600) // 60)}:{int(avg_turnaround % 60)}"
else:
    avg_turnaround_hms = "N/A"

# Display KPI metrics with the corrected turnaround time
col1, col2, col3 = st.columns([1, 1, 1])
col1.metric("Total Procedures", latest_data["Procedure"].sum(), help="Total number of procedures completed on this date.")
col2.metric("Total Points", latest_data["Points"].sum(), help="Custom productivity metric based on workload weighting.")
col3.metric("Avg Turnaround Time", avg_turnaround_hms, help="Average time taken to complete a report, calculated from submission to finalization.")

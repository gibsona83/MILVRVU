# Ensure df_filtered is defined before using it
if 'df_filtered' in locals() and not df_filtered.empty:
    # Convert "Turnaround Time" to numeric, handle errors
    df_filtered["Turnaround Time"] = pd.to_numeric(df_filtered["Turnaround Time"], errors="coerce")

    # Drop NaN values before computing aggregates
    df_filtered.dropna(subset=["Turnaround Time"], inplace=True)

    # Compute Aggregate Metrics
    avg_turnaround = df_filtered["Turnaround Time"].mean()
    avg_procs = df_filtered["Procedures per Half-Day"].mean()
    avg_points = df_filtered["Points per Half-Day"].mean()

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
    st.warning("⚠️ No data available. Please upload an RVU file or adjust filters.")

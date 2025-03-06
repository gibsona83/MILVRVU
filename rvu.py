def main():
    st.sidebar.image("milv.png", width=250)
    uploaded_file = st.sidebar.file_uploader("Upload RVU File", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_uploaded = pd.read_excel(uploaded_file)
            df_uploaded.to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")
    
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    st.title("MILV Daily Productivity")
    tab1, tab2, tab3 = st.tabs(["📅 Daily View", "📊 Provider Analysis", "📈 Trend Analysis"])
    
    # TAB 1: Latest Day
    with tab1:
        st.subheader(f"Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df["date"] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            search_query = st.text_input("Search Providers (Daily):", key="search_daily")
            if search_query:
                df_latest = df_latest[df_latest["author"].str.contains(search_query, case=False, na=False)]

            st.dataframe(df_latest, use_container_width=True)

            st.subheader("📊 Performance")
            col1, col2 = st.columns(2)
            with col1:
                fig = create_performance_chart(df_latest, "points/half day", "author", "Points per Half-Day")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = create_performance_chart(df_latest, "procedure/half", "author", "Procedures per Half-Day")
                st.plotly_chart(fig, use_container_width=True)

    # TAB 2: Provider Analysis (New)
    with tab2:
        st.subheader("📊 Provider Performance Over Time")

        date_range = st.date_input(
            "Select Date Range", 
            [max_date - pd.DateOffset(days=7), max_date], 
            min_value=min_date, 
            max_value=max_date
        )
        
        if len(date_range) != 2 or date_range[0] > date_range[1]:
            st.error("❌ Invalid date range selected.")
            return
        
        start, end = date_range
        df_prov = df[df["date"].between(pd.Timestamp(start), pd.Timestamp(end))]

        if not df_prov.empty:
            search_prov = st.text_input("Search Providers (Provider Analysis):", key="search_prov")
            if search_prov:
                df_prov = df_prov[df_prov["author"].str.contains(search_prov, case=False, na=False)]
            
            st.dataframe(df_prov, use_container_width=True)

            st.subheader("📊 Performance Averages")
            st.metric("Average Points/Half Day", f"{df_prov['points/half day'].mean():.2f}")
            st.metric("Average Procedures/Half Day", f"{df_prov['procedure/half'].mean():.2f}")

    # TAB 3: Trend Analysis (Same as before)
    with tab3:
        st.subheader("📈 Trends Over Time")

        dates = st.date_input(
            "Select Trend Date Range",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date
        )

        if len(dates) != 2:
            st.error("❌ Please select both start and end dates")
            st.stop()
        if dates[0] > dates[1]:
            st.error("❌ End date must be after start date")
            st.stop()

        start, end = dates
        df_range = df[df["date"].between(pd.Timestamp(start), pd.Timestamp(end))]

        if df_range.empty:
            st.warning("⚠️ No data available for the selected date range.")
            st.stop()

        trend_metrics = ["points/half day", "procedure/half"]
        valid_metrics = [col for col in trend_metrics if col in df_range.columns]

        if valid_metrics:
            trend_fig = create_trend_chart(df_range, "date", ["points/half day", "procedure/half"])
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.warning("⚠️ No valid metrics available for trend analysis.")

        # Searchable Table
        st.subheader("🔍 Filtered Data")
        search_query_trend = st.text_input("Search Providers in Trends:", key="search_trends")
        if search_query_trend:
            df_range = df_range[df_range["author"].str.contains(search_query_trend, case=False, na=False)]
        
        st.dataframe(df_range, use_container_width=True)

if __name__ == "__main__":
    main()

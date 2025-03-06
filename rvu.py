def create_trend_chart(df, date_col, metrics):
    """Create a clean time series line chart with proper aggregation."""
    df = df.copy()
    df['date_only'] = df[date_col].dt.date

    # Ensure columns exist before grouping
    valid_metrics = [col for col in metrics if col in df.columns]
    if not valid_metrics:
        st.error("❌ No valid numeric columns found for trend analysis.")
        return None

    # Aggregate data by date (ensures one record per date)
    trend_df = df.groupby('date_only', as_index=False)[valid_metrics].sum()

    # Drop NaN rows
    trend_df = trend_df.dropna()

    if trend_df.empty:
        st.warning("⚠️ No trend data available for selected range.")
        return None

    # Melt the dataframe for Plotly
    trend_df_melted = trend_df.melt(
        id_vars=['date_only'],
        value_vars=valid_metrics,
        var_name='Metric',
        value_name='Value'
    )

    # Convert to numeric (ensures Plotly handles it correctly)
    trend_df_melted["Value"] = pd.to_numeric(trend_df_melted["Value"], errors="coerce").fillna(0)

    # Prevent empty or malformed values
    if trend_df_melted["Value"].sum() == 0:
        st.warning("⚠️ Trend data is all zeros or missing.")
        return None

    # Create an improved line chart
    fig = px.line(
        trend_df_melted,
        x='date_only',
        y='Value',
        color='Metric',
        title="📈 Aggregate Performance Trends",
        labels={'date_only': 'Date', 'Value': 'Total Value'},
        height=500,
        markers=True,
        line_shape='spline',  # Smoother curve
        color_discrete_sequence=["#1f77b4", "#ff7f0e"]
    )

    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=6, symbol='circle', opacity=0.8),
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%b %d",
            rangeslider=dict(visible=True),
            gridcolor='#EAEAEA'
        ),
        yaxis=dict(
            tickformat=".2f",
            gridcolor='#EAEAEA'
        ),
        plot_bgcolor='white',
        hovermode='x unified'
    )

    return fig

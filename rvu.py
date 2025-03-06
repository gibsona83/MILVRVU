def create_trend_chart(df, date_col, metrics):
    """Create an area chart for performance trends without duplication in the slider."""
    df = df.copy()
    df['date_only'] = df[date_col].dt.date

    # Aggregate data by date (ensure one row per date)
    trend_df = df.groupby('date_only', as_index=False)[metrics].mean()

    if trend_df.empty:
        return None

    # Melt the dataframe to long format for Plotly
    trend_df_melted = trend_df.melt(
        id_vars=['date_only'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Value'
    )

    # Create an area chart with proper transparency to avoid overlap
    fig = px.area(
        trend_df_melted,
        x='date_only',
        y='Value',
        color='Metric',
        title="Daily Performance Trends",
        labels={'date_only': 'Date', 'Value': 'Average Value'},
        height=500
    )

    # Formatting updates
    fig.update_traces(
        line=dict(width=2),
        opacity=0.4,  # Reduce fill opacity to make it more readable
        marker_line_width=1.5,
        marker_line_color='black'
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%b %d",
            rangeslider=dict(visible=False),  # Disable the duplicating rangeslider
            gridcolor='#F0F2F6'
        ),
        yaxis=dict(
            tickformat=".2f",
            gridcolor='#F0F2F6'
        ),
        plot_bgcolor='white',
        hovermode='x unified'
    )

    return fig

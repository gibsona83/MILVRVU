# [Keep all previous imports and configuration code the same]

def create_sorted_bar_chart(df, metric_col, title):
    """Create a sorted horizontal bar chart with Plotly."""
    # Sort descending and remove invalid entries
    sorted_df = df.sort_values(metric_col, ascending=False)
    
    fig = px.bar(
        sorted_df,
        x=metric_col,
        y="Author",
        orientation='h',
        text=metric_col,
        color=metric_col,
        color_continuous_scale='Viridis',
        title=title,
        height=600
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total descending'},
        xaxis_title=metric_col,
        yaxis_title="Provider",
        hovermode='y unified',
        coloraxis_colorbar=dict(title=metric_col)  # Corrected line
    
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside'
    )
    
    return fig

# [Rest of the code remains unchanged]
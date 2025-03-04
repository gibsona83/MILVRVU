import plotly.express as px

# **Turnaround Time - Switch to Box Plot for better outlier handling**
fig1 = px.box(df_filtered, y="Turnaround Time", color="Primary Subspecialty",
              title="Turnaround Time Distribution by Subspecialty")

# **Procedures per Half-Day - Keep as Bar Chart, Sort Descending**
df_filtered.sort_values(by="Procedures per Half-Day", ascending=False, inplace=True)
fig2 = px.bar(df_filtered, x="Provider", y="Procedures per Half-Day", color="Primary Subspecialty",
              title="Procedures per Half Day by Provider")

# **Points per Half-Day - Use Line Chart for trends, Bar Chart if 1-day**
if df_filtered["Date"].nunique() > 1:
    fig3 = px.line(df_filtered, x="Date", y="Points per Half-Day", color="Primary Subspecialty",
                   title="Points per Half Day Over Time", markers=True)
else:
    fig3 = px.bar(df_filtered, x="Provider", y="Points per Half-Day", color="Primary Subspecialty",
                  title="Points per Half Day by Provider")

# **Render Charts**
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

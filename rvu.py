# Visualization: Bar chart for top 20 productivity per half-day
st.subheader("📈 Productivity per Half-Day")

# Sort data and select top providers
top_providers = filtered_data.groupby("Author")["Points/half day"].sum().sort_values(ascending=False).head(20)

fig, ax = plt.subplots(figsize=(12, 8))  # Increased figure size for readability
top_providers.plot(kind="barh", ax=ax, color="skyblue", fontsize=10)

ax.set_xlabel("Total Points per Half-Day", fontsize=12)
ax.set_ylabel("Provider", fontsize=12)
ax.set_title("Top 20 Provider Productivity per Half-Day", fontsize=14)

plt.xticks(fontsize=10)
plt.yticks(fontsize=8)

# Rotate provider labels for better readability
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, ha="right")

st.pyplot(fig)

# Display column names for debugging
st.sidebar.write("Columns in dataset:", df.columns.tolist())

# Standardized column mapping (case-insensitive)
columns_mapping = {col.lower(): col for col in df.columns}
points_col = columns_mapping.get("points per half-day")
procedures_col = columns_mapping.get("procedures per half-day")

# Handle missing columns gracefully
if points_col:
    df[points_col] = df[points_col].fillna(0)
else:
    st.warning("⚠️ 'Points per Half-Day' column not found in dataset.")

if procedures_col:
    df[procedures_col] = df[procedures_col].fillna(0)
else:
    st.warning("⚠️ 'Procedures per Half-Day' column not found in dataset.")

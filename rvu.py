import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# ---- Constants ----
FILE_STORAGE_PATH = "latest_rvu.xlsx"
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = "Viridis"

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Load and preprocess data from an Excel file."""
    try:
        uploaded_file.seek(0)  # Reset file pointer for re-reads
        xls = pd.ExcelFile(file_path)
        df = xls.parse(xls.sheet_names[0])

        # Clean column names (case-insensitive)
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in lower_columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None

        # Map actual column names
        col_map = {col.lower(): col for col in df.columns}

        # Process date column
        date_col = col_map["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df.dropna(subset=[date_col], inplace=True)

        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

# ---- Main Application ----
def main():
    # Sidebar (mobile-friendly adjustments)
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader("📤 Upload RVU File", type=["xlsx"])

    if uploaded_file:
        try:
            pd.read_excel(uploaded_file).to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")

    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}

    min_date, max_date = df[display_cols["date"]].min().date(), df[display_cols["date"]].max().date()

    st.title("📊 MILV Daily Productivity")
    tab1, tab2 = st.tabs(["📅 Daily View", "📈 Trend Analysis"])

    # ---- Daily View ----
    with tab1:
        st.subheader(f"📅 Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]

        if not df_latest.empty:
            # Multi-select searchable dropdown for filtering
            selected_providers = st.multiselect(
                "🔍 Select providers:",
                options=df_latest[display_cols["author"]].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}",
            )

            # Apply filtering
            filtered_latest = df_latest[df_latest[display_cols["author"]].isin(selected_providers)] if selected_providers else df_latest

            # Bar charts sorted high to low
            col1, col2 = st.columns(1 if st.session_state.get("mobile") else 2)
            with col1:
                st.plotly_chart(
                    px.bar(
                        filtered_latest.sort_values(display_cols["points/half day"], ascending=False),
                        x=display_cols["points/half day"],
                        y=display_cols["author"],
                        orientation="h",
                        text=display_cols["points/half day"],
                        color=display_cols["points/half day"],
                        color_continuous_scale=COLOR_SCALE,
                        title="🏆 Points per Half-Day",
                    ),
                    use_container_width=True,
                )
            with col2:
                st.plotly_chart(
                    px.bar(
                        filtered_latest.sort_values(display_cols["procedure/half"], ascending=False),
                        x=display_cols["procedure/half"],
                        y=display_cols["author"],
                        orientation="h",
                        text=display_cols["procedure/half"],
                        color=display_cols["procedure/half"],
                        color_continuous_scale=COLOR_SCALE,
                        title="⚡ Procedures per Half-Day",
                    ),
                    use_container_width=True,
                )

            st.subheader("📋 Detailed Data")
            st.dataframe(filtered_latest, use_container_width=True)

    # ---- Trend Analysis ----
    with tab2:
        st.subheader("📈 Date Range Analysis")

        dates = st.date_input(
            "🗓️ Select Date Range (Start - End)",
            value=[max_date - pd.DateOffset(days=7), max_date],
            min_value=min_date,
            max_value=max_date,
        )

        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            return

        df_range = df[df[display_cols["date"]].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]

        if df_range.empty:
            st.warning("⚠️ No data available for the selected range")
            return

        # Multi-select searchable dropdown for filtering
        selected_providers_trend = st.multiselect(
            "🔍 Select providers:",
            options=df_range[display_cols["author"]].unique(),
            default=None,
            placeholder="Type or select provider...",
            format_func=lambda x: f"👤 {x}",
        )

        # Apply filtering
        df_filtered_trend = df_range[df_range[display_cols["author"]].isin(selected_providers_trend)] if selected_providers_trend else df_range

        st.subheader("📊 Provider Performance Over Time")
        fig = px.line(
            df_filtered_trend,
            x=display_cols["date"],
            y=[display_cols["points/half day"], display_cols["procedure/half"]],
            title="📈 Performance Trends",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Detailed Data")
        st.dataframe(df_filtered_trend, use_container_width=True)

if __name__ == "__main__":
    main()

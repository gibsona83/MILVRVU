import streamlit as st
import pandas as pd
import plotly.express as px

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# ---- Constants ----
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}
COLOR_SCALE = "Viridis"

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    """Load and preprocess data from an uploaded Excel file."""
    try:
        uploaded_file.seek(0)  # Reset file pointer for re-reads
        xls = pd.ExcelFile(uploaded_file)
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
    st.sidebar.image("milv.png", width=200)
    uploaded_file = st.sidebar.file_uploader("📤 Upload RVU File", type=["xlsx"])

    if not uploaded_file:
        return st.info("ℹ️ Please upload a file to begin analysis")

    with st.spinner("📊 Processing data..."):
        df = load_data(uploaded_file)

    if df is None:
        return

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
            selected_providers = st.multiselect(
                "🔍 Select providers:",
                options=df_latest[display_cols["author"]].unique(),
                default=None,
                placeholder="Type or select provider...",
                format_func=lambda x: f"👤 {x}",
            )

            filtered_latest = df_latest[df_latest[display_cols["author"]].isin(selected_providers)] if selected_providers else df_latest

            col1, col2 = st.columns(2)
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

        selected_providers_trend = st.multiselect(
            "🔍 Select providers:",
            options=df_range[display_cols["author"]].unique(),
            default=None,
            placeholder="Type or select provider...",
            format_func=lambda x: f"👤 {x}",
        )

        df_filtered_trend = df_range[df_range[display_cols["author"]].isin(selected_providers_trend)] if selected_providers_trend else df_range

        st.subheader("📊 Overall Performance Trends")
        fig = px.line(
            df_filtered_trend.groupby(display_cols["date"]).mean(numeric_only=True).reset_index(),
            x=display_cols["date"],
            y=[display_cols["points/half day"], display_cols["procedure/half"]],
            title="📈 Average Daily Performance Trends",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Aggregate provider-level performance
        provider_summary = df_filtered_trend.groupby(display_cols["author"]).agg({
            display_cols["points/half day"]: "sum",
            display_cols["procedure/half"]: "sum",
        }).reset_index()

        # Sorted bar charts for total provider performance
        st.subheader("📊 Total Provider Performance")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.bar(
                    provider_summary.sort_values(display_cols["points/half day"], ascending=False),
                    x=display_cols["points/half day"],
                    y=display_cols["author"],
                    orientation="h",
                    text=display_cols["points/half day"],
                    color=display_cols["points/half day"],
                    color_continuous_scale=COLOR_SCALE,
                    title="🏆 Total Points per Provider",
                ),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                px.bar(
                    provider_summary.sort_values(display_cols["procedure/half"], ascending=False),
                    x=display_cols["procedure/half"],
                    y=display_cols["author"],
                    orientation="h",
                    text=display_cols["procedure/half"],
                    color=display_cols["procedure/half"],
                    color_continuous_scale=COLOR_SCALE,
                    title="⚡ Total Procedures per Provider",
                ),
                use_container_width=True,
            )

        st.subheader("📋 Detailed Data")
        st.dataframe(df_filtered_trend, use_container_width=True)

if __name__ == "__main__":
    main()

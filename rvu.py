import streamlit as st
import pandas as pd
from github import Github, UnknownObjectException
import io
from datetime import datetime
import base64

# --- Configuration ---
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_USERNAME = st.secrets["github"]["username"]
GITHUB_REPO = st.secrets["github"]["repo"]
FILE_PATH = "RVU_Daily_Master.xlsx"

# --- GitHub Setup ---
try:
    g = Github(GITHUB_TOKEN, timeout=15)
    repo = g.get_user().get_repo(GITHUB_REPO)
except Exception as e:
    st.error(f"GitHub connection failed: {e}")
    st.stop()

# --- Core Functions ---
def upload_to_github(file_bytes: bytes, file_name: str) -> None:
    """Uploads or updates an Excel file in GitHub repository as Base64."""
    try:
        commit_msg = f"Update {file_name} via MILV app - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Encode file in Base64 to store it properly in GitHub
        encoded_content = base64.b64encode(file_bytes).decode("utf-8")

        try:
            contents = repo.get_contents(file_name, ref="main")
            repo.update_file(
                path=contents.path,
                message=commit_msg,
                content=encoded_content,
                sha=contents.sha,
                branch="main"
            )
            st.success("File updated successfully in GitHub!")
        except UnknownObjectException:  # File doesn't exist
            repo.create_file(
                path=file_name,
                message=f"Initial upload: {commit_msg}",
                content=encoded_content,
                branch="main"
            )
            st.success("New file uploaded successfully to GitHub!")
    except Exception as e:
        st.error(f"GitHub operation failed: {e}")

def fetch_latest_file() -> pd.DataFrame:
    """Fetches the latest file from GitHub, decodes Base64, and loads it into a DataFrame."""
    try:
        file_content = repo.get_contents(FILE_PATH, ref="main")
        
        # Decode Base64 back to binary content
        decoded_content = base64.b64decode(file_content.content)

        with st.spinner("Loading data..."):
            df = pd.read_excel(io.BytesIO(decoded_content), engine="openpyxl")
        return df
    except UnknownObjectException:
        st.warning("File not found in repository. Upload a new file to get started.")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

# --- Streamlit UI ---
st.title("MILV Daily Productivity File Upload")
st.caption(f"GitHub Repository: {GITHUB_REPO}")

# File upload section
uploaded_file = st.file_uploader(
    "Upload the latest RVU Daily Master",
    type=["xlsx"],
    help="Upload only XLSX files with the correct format"
)

if uploaded_file is not None:
    try:
        upload_to_github(uploaded_file.getvalue(), FILE_PATH)
        st.session_state["last_upload"] = uploaded_file.getvalue()
        st.experimental_rerun()  # Refresh UI to reflect the update
    except Exception as e:
        st.error(f"Upload failed: {e}")

# Data display section
st.write("## Latest File Data")
df = fetch_latest_file()

if df is not None:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric("Latest Date", df["Date"].max() if "Date" in df.columns else "N/A")
    
    # Data exploration options
    with st.expander("Data Preview"):
        num_rows = st.slider("Rows to display", 5, 100, 20, key="row_slider")
        st.dataframe(df.head(num_rows), height=400)
    
    with st.expander("Data Summary"):
        st.write("### Summary Statistics")
        st.write(df.describe())
        
        st.write("### Column Information")
        st.write(df.dtypes.rename("Data Type").to_frame())
    
    # Add download button
    csv = df.to_csv(index=False).encode()
    st.download_button(
        label="Download Current Data as CSV",
        data=csv,
        file_name="current_data.csv",
        mime="text/csv"
    )
elif df is None:
    st.info("No data available - upload a file to initialize the repository")

import streamlit as st
import pandas as pd
from github import Github, UnknownObjectException
import io
from pathlib import Path
from typing import Optional
from datetime import datetime

# --- Configuration ---
# Load GitHub credentials from Streamlit secrets
GITHUB_TOKEN: str = st.secrets["github"]["token"]
GITHUB_USERNAME: str = st.secrets["github"]["username"]
GITHUB_REPO: str = st.secrets["github"]["repo"]
FILE_PATH: Path = Path(st.secrets.get("file_path", "RVU_Daily_Master.xlsx"))

# --- GitHub Setup ---
try:
    g = Github(GITHUB_TOKEN, timeout=15)
    repo = g.get_user().get_repo(GITHUB_REPO)
    # Verify main branch exists
    repo.get_branch("main")
except Exception as e:
    st.error(f"GitHub connection failed: {e}")
    st.stop()

# --- Core Functions ---
def upload_to_github(file_bytes: bytes, file_name: str) -> None:
    """Uploads or updates a file in GitHub repository.
    
    Args:
        file_bytes: Binary content of the file
        file_name: Target file path in repository
        
    Raises:
        github.GithubException: For GitHub API errors
    """
    try:
        commit_msg = f"Update {file_name} via MILV app - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            contents = repo.get_contents(str(file_name), ref="main")
            repo.update_file(
                path=contents.path,
                message=commit_msg,
                content=file_bytes,
                sha=contents.sha,
                branch="main"
            )
            st.success("File updated successfully in GitHub!")
            
        except UnknownObjectException:  # File doesn't exist
            repo.create_file(
                path=str(file_name),
                message=f"Initial upload: {commit_msg}",
                content=file_bytes,
                branch="main"
            )
            st.success("New file uploaded successfully to GitHub!")
            
    except Exception as e:
        st.error(f"GitHub operation failed: {e}")
        raise

def fetch_latest_file() -> Optional[pd.DataFrame]:
    """Fetches the latest file from GitHub and loads it into a DataFrame.
    
    Returns:
        pd.DataFrame or None: Loaded data or None if failed
    """
    try:
        file_content = repo.get_contents(str(FILE_PATH), ref="main")
        
        if not file_content.decoded_content:
            st.warning("File exists but is empty")
            return None
            
        with st.spinner("Loading data..."):
            return pd.read_excel(
                io.BytesIO(file_content.decoded_content),
                engine="openpyxl",
                parse_dates=True,
                dtype_backend="pyarrow"
            )
            
    except UnknownObjectException:
        st.warning("File not found in repository")
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
    # Validate file type
    if uploaded_file.type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        st.error("Invalid file format. Please upload a valid Excel XLSX file.")
        st.stop()
        
    # Check for duplicate upload
    if "last_upload" in st.session_state and st.session_state.last_upload == uploaded_file.getvalue():
        st.warning("This file was already uploaded")
        st.stop()
        
    try:
        upload_to_github(uploaded_file.getvalue(), str(FILE_PATH))
        st.session_state.last_upload = uploaded_file.getvalue()
        st.rerun()  # Refresh data display
        
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
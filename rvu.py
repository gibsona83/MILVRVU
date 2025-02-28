import streamlit as st
import pandas as pd
from github import Github
import base64
import io

# Load GitHub credentials from Streamlit secrets
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_USERNAME = st.secrets["github"]["username"]
GITHUB_REPO = st.secrets["github"]["repo"]
FILE_PATH = "RVU_Daily_Master.xlsx"  # Adjust if file is inside a folder

# Authenticate with GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_user().get_repo(GITHUB_REPO)

def upload_to_github(file_content, file_name):
    """Uploads or updates a file in GitHub repository with base64 encoding."""
    try:
        file_path = file_name
        file_base64 = base64.b64encode(file_content).decode("utf-8")  # Encode file

        try:
            contents = repo.get_contents(file_path)  # Check if file exists
            repo.update_file(file_path, "Updating latest file", file_base64, contents.sha)
            st.success("File updated successfully in GitHub!")
        except:
            repo.create_file(file_path, "Uploading new file", file_base64)
            st.success("New file uploaded successfully to GitHub!")
    
    except Exception as e:
        st.error(f"File upload failed: {e}")

def fetch_latest_file():
    """Fetches the latest file from GitHub and loads it into a DataFrame."""
    try:
        file_content = repo.get_contents(FILE_PATH)  # Get file from GitHub
        decoded_content = base64.b64decode(file_content.content)  # Decode from base64

        # Read Excel file with explicit engine
        df = pd.read_excel(io.BytesIO(decoded_content), engine="openpyxl")
        return df
    except Exception as e:
        st.warning(f"Could not fetch the latest file: {e}")
        return None

# Streamlit UI
st.title("MILV Daily Productivity File Upload")

uploaded_file = st.file_uploader("Upload the latest RVU Daily Master", type=["xlsx"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    upload_to_github(file_bytes, FILE_PATH)

st.write("### Latest File Data")
df = fetch_latest_file()
if df is not None:
    st.dataframe(df)

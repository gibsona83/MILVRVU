import streamlit as st
import pandas as pd
from github import Github
import base64
import io

# Load GitHub credentials from Streamlit secrets
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_USERNAME = st.secrets["github"]["username"]
GITHUB_REPO = st.secrets["github"]["repo"]
FILE_PATH = "RVU_Daily_Master.xlsx"  # File name in GitHub

# Authenticate with GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_user().get_repo(GITHUB_REPO)

def upload_to_github(file_content, file_name):
    """Uploads or updates a file in GitHub repository."""
    try:
        file_path = file_name
        contents = repo.get_contents(file_path)  # Check if file exists
        repo.update_file(file_path, "Updating latest file", file_content, contents.sha)
        st.success("File updated successfully in GitHub!")
    except:
        repo.create_file(file_path, "Uploading new file", file_content)
        st.success("New file uploaded successfully to GitHub!")

def fetch_latest_file():
    """Fetches the latest file from GitHub and loads it into a DataFrame."""
    try:
        file_content = repo.get_contents(FILE_PATH)
        decoded_content = base64.b64decode(file_content.content)
        df = pd.read_excel(io.BytesIO(decoded_content))
        return df
    except Exception as e:
        st.error(f"Could not fetch latest file: {e}")
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

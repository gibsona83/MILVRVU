import matplotlib
matplotlib.use('Agg')  # Required for headless environments

import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
import os
import requests

# Constants & Configurations
def get_config():
    return {
        "github_repo": "gibsona83/milvrvu",
        "latest_file_url": "https://raw.githubusercontent.com/gibsona83/milvrvu/main/latest_uploaded_file.xlsx",
        "logo_url": "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png",
        "latest_file_path": "latest_uploaded_file.xlsx"
    }

# File Handling: Download latest file from GitHub
def download_file(url, save_path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        with open(save_path, "wb") as file:
            file.write(response.content)
        return save_path
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading file: {e}")
        return None

# Data Loading: Load latest file into DataFrame
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    st.warning("Data file not found.")
    return None

# UI Rendering: Display Logo and Header
def render_ui(logo_url):
    st.image(logo_url, width=200)
    st.title("MILV Data Viewer")

# Main Execution Flow
def main():
    config = get_config()
    
    render_ui(config["logo_url"])
    
    file_path = download_file(config["latest_file_url"], config["latest_file_path"])
    
    if file_path:
        df = load_data(file_path)
        if df is not None:
            st.dataframe(df)

if __name__ == "__main__":
    main()

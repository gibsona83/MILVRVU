# Set Matplotlib backend first
import matplotlib
matplotlib.use('Agg')  # Required for headless environments
import matplotlib.pyplot as plt

import streamlit as st
import pandas as pd
import numpy as np
import os
import requests

# Rest of your existing code follows below...
# [Keep all your original code from here downward unchanged]
# ----------------------------------------------------------
# Define GitHub repository details
GITHUB_REPO = "gibsona83/milvrvu"
LATEST_FILE_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/latest_uploaded_file.xlsx"
LOGO_URL = "https://raw.githubusercontent.com/gibsona83/milvrvu/main/milv.png"
LATEST_FILE_PATH = "latest_uploaded_file.xlsx"

# Function to download the latest file from GitHub
def download_latest_file():
    try:
        response = requests.get(LATEST_FILE_URL)
    # ... [Keep all other functions and logic exactly as before]
# sheets_interface.py
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
#from drive_interface import create_root_drive_folder, move_file_to_folder

# --- Scopes for Sheets + Drive ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send"
]

# --- Paths for credentials / token ---
CREDENTIALS_FILE = "Tokens/credentials.json"   # Your OAuth client JSON
TOKEN_FILE = "Tokens/token.json"        # Your saved token

# --- 1. Token creation function ---
def create_token():
    """
    Run OAuth flow for first-time authorization.
    Saves token.json for reuse.
    """
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # Ensure folder exists
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)

    # Save token to file
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    return creds

# --- 2. Refresh token function ---
def refresh_token(creds):
    """
    Refreshes token if expired and updates token.json
    """
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

# --- 3. Load token helper ---
from google.auth.exceptions import RefreshError

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return create_token()

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    try:
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            else:
                return create_token()

        return creds

    except RefreshError:
        # Refresh token revoked or invalid
        print("Refresh token invalid. Re-authenticating...")
        return create_token()




"""def setup_project(title="Job Application Tracker"):
    
    Initializes the project by ensuring token exists and creating a new spreadsheet.
    Call this function the first time you run the project.
    Returns the created spreadsheet object.
    
    # Load or create token
    creds = load_token()
    # Create a new spreadsheet
    root_folder_id = create_root_drive_folder("JobAgent")

    spreadsheet = create_job_spreadsheet("JobAgent Main")
    spreadsheet_id = spreadsheet["spreadsheetId"]

    move_file_to_folder(spreadsheet_id, root_folder_id)

    print(f"Project initialized! Spreadsheet '{title}' created with ID: {spreadsheet.get('spreadsheetId')}")
    print(f"Spreadsheet URL: {spreadsheet.get('spreadsheetUrl')}")
    
    return spreadsheet"""




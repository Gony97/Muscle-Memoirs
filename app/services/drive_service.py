import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRETS_DIR = PROJECT_ROOT / ".secrets"
TOKEN_PATH = SECRETS_DIR / "drive_token.json"
CREDS_PATH = PROJECT_ROOT / "credentials.json"  # or put in .secrets too

def drive_service():
    SECRETS_DIR.mkdir(exist_ok=True)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds)

def find_file_in_folder(service, folder_id: str, filename: str):
    q = f"'{folder_id}' in parents and name='{filename}' and trashed=false"
    res = service.files().list(q=q, fields="files(id,name,modifiedTime)").execute()
    files = res.get("files", [])
    return files[0] if files else None

def upload_or_replace(service, folder_id: str, local_path: str, drive_filename: str | None = None) -> str:
    local_path = str(local_path)
    drive_filename = drive_filename or os.path.basename(local_path)

    existing = find_file_in_folder(service, folder_id, drive_filename)
    media = MediaFileUpload(local_path, resumable=True)

    if existing:
        file_id = existing["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        return file_id
    else:
        metadata = {"name": drive_filename, "parents": [folder_id]}
        created = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return created["id"]
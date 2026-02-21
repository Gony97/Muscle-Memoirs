import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

def drive_service():
    creds = None

    # Load saved token if exists
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def find_folder_id(service, folder_name):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])

    if not items:
        raise Exception(f"Folder '{folder_name}' not found in your Drive.")
    return items[0]["id"]


def upload_file(service, folder_id, local_file):
    file_metadata = {
        "name": os.path.basename(local_file),
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_file, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return file.get("id")


if __name__ == "__main__":
    service = drive_service()
    folder_id = find_folder_id(service, "MuscleMemoirs")

    with open("hello_drive.txt", "w") as f:
        f.write("OAuth upload success!")

    file_id = upload_file(service, folder_id, "hello_drive.txt")

    print("Uploaded successfully. File ID:", file_id)
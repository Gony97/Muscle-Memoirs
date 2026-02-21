from googleapiclient.discovery import Resource

FOLDER_MIME = "application/vnd.google-apps.folder"

def find_child_folder(service: Resource, parent_id: str, name: str) -> str | None:
    q = (
        f"'{parent_id}' in parents and "
        f"mimeType='{FOLDER_MIME}' and "
        f"name='{name}' and trashed=false"
    )
    res = service.files().list(q=q, fields="files(id,name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def create_child_folder(service: Resource, parent_id: str, name: str) -> str:
    metadata = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
    created = service.files().create(body=metadata, fields="id").execute()
    return created["id"]

def ensure_subfolder(service: Resource, parent_id: str, name: str) -> str:
    existing = find_child_folder(service, parent_id, name)
    return existing if existing else create_child_folder(service, parent_id, name)
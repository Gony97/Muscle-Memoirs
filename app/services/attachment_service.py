import os
from pathlib import Path

from app.services.drive_service import drive_service, upload_or_replace
from app.services.drive_folders import ensure_subfolder
from app.services.asset_registry import upsert_drive_asset, get_asset

def upload_attachment(logical_key: str, path: str) -> str:
    root_folder_id = os.environ["MUSCLEMEMOIRS_DRIVE_FOLDER_ID"]
    svc = drive_service()

    attachments_id_asset = get_asset("folders/attachments")
    attachments_id = attachments_id_asset.drive_file_id if attachments_id_asset else ensure_subfolder(svc, root_folder_id, "attachments")

    file_path = Path(path).resolve()
    drive_file_id = upload_or_replace(svc, attachments_id, str(file_path), drive_filename=file_path.name)

    upsert_drive_asset(logical_key, drive_file_id, file_path.name, notes="Attachment")
    return drive_file_id
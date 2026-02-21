import os
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload

from app.db.database import DB_PATH
from app.services.drive_service import drive_service
from app.services.asset_registry import get_asset

def _download_file(svc, file_id: str, out_path: Path) -> None:
    request = svc.files().get_media(fileId=file_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

def restore_db_from_logical_key(logical_key: str) -> Path:
    asset = get_asset(logical_key)
    if not asset:
        raise RuntimeError(f"No asset found for key: {logical_key}")

    svc = drive_service()

    temp_path = DB_PATH.with_suffix(".restore_tmp.db")
    _download_file(svc, asset.drive_file_id, temp_path)

    # Swap in restored DB
    if DB_PATH.exists():
        DB_PATH.rename(DB_PATH.with_suffix(".pre_restore.db"))
    temp_path.rename(DB_PATH)

    return DB_PATH
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.db.database import DB_PATH
from app.services.drive_service import drive_service, upload_or_replace
from app.services.drive_folders import ensure_subfolder
from app.services.asset_registry import upsert_drive_asset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def ensure_drive_folders(svc, root_folder_id: str) -> dict[str, str]:
    backups_id = ensure_subfolder(svc, root_folder_id, "backups")
    attachments_id = ensure_subfolder(svc, root_folder_id, "attachments")

    # Save folder IDs in DB for convenience
    upsert_drive_asset("folders/backups", backups_id, "backups", notes="Drive subfolder id")
    upsert_drive_asset("folders/attachments", attachments_id, "attachments", notes="Drive subfolder id")
    return {"backups": backups_id, "attachments": attachments_id}

def create_and_upload_backup() -> str:
    root_folder_id = os.environ["MUSCLEMEMOIRS_DRIVE_FOLDER_ID"]
    svc = drive_service()
    folders = ensure_drive_folders(svc, root_folder_id)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"musclememoirs_{ts}.db"
    local_backup_path = LOCAL_BACKUP_DIR / backup_name

    # Snapshot local DB (full history in one file)
    shutil.copy2(DB_PATH, local_backup_path)

    drive_file_id = upload_or_replace(
        svc,
        folders["backups"],
        str(local_backup_path),
        drive_filename=backup_name
    )

    # Store history key + latest pointer
    upsert_drive_asset(f"backup/{ts}", drive_file_id, backup_name, mime_type="application/x-sqlite3", notes="SQLite backup")
    upsert_drive_asset("backup/latest", drive_file_id, backup_name, mime_type="application/x-sqlite3", notes="Latest SQLite backup")

    return drive_file_id
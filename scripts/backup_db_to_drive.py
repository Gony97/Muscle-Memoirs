import os
import shutil
from datetime import datetime
from pathlib import Path

from app.db.database import DB_PATH
from app.services.drive_service import drive_service, upload_or_replace
from app.services.asset_registry import upsert_drive_asset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def main():
    folder_id = os.environ["MUSCLEMEMOIRS_DRIVE_FOLDER_ID"]
    svc = drive_service()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"musclememoirs_{ts}.db"
    local_backup_path = BACKUP_DIR / backup_name

    # simple + safe local backup
    shutil.copy2(DB_PATH, local_backup_path)

    # upload to Drive (new file each time)
    drive_file_id = upload_or_replace(
        svc,
        folder_id,
        str(local_backup_path),
        drive_filename=backup_name
    )

    # record in DB
    upsert_drive_asset(
        logical_key=f"backup/{ts}",
        drive_file_id=drive_file_id,
        filename=backup_name,
        mime_type="application/x-sqlite3",
        notes="SQLite backup"
    )

    # also maintain "backup/latest" pointer
    upsert_drive_asset(
        logical_key="backup/latest",
        drive_file_id=drive_file_id,
        filename=backup_name,
        mime_type="application/x-sqlite3",
        notes="Latest SQLite backup"
    )

    print("✅ Backup uploaded. drive_file_id:", drive_file_id)

if __name__ == "__main__":
    main()